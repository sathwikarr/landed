"""Run management API — start, stream, query, and persist runs via Supabase."""
import json, uuid, asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis
import os
from app.models.schemas import StartRunRequest
from app.workers.tasks import run_pipeline_task
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/runs", tags=["runs"])
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


@router.post("/start")
async def start_run(body: dict):
    sb = get_supabase()
    run_id = str(uuid.uuid4())
    user_id = body["user_id"]

    # Create run_session row
    sb.table("run_sessions").insert({"id": run_id, "user_id": user_id, "status": "queued"}).execute()

    run_pipeline_task.apply_async(
        args=[run_id, user_id, body["profile"], body["prefs"], body["resume_text"]],
        task_id=run_id,
    )
    return {"run_id": run_id, "status": "queued"}


@router.get("/{run_id}/stream")
async def stream_run(run_id: str):
    """SSE — streams live agent events. Also persists application records to Supabase."""
    sb = get_supabase()

    async def event_generator():
        r = await aioredis.from_url(REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"run:{run_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                event = json.loads(data)

                # Persist application events to Supabase
                if event.get("event") == "application":
                    try:
                        sb.table("applications").insert({
                            "run_id": run_id,
                            "user_id": event.get("user_id"),
                            "status": event.get("status", "pending"),
                            "resume_version": event.get("resume_version"),
                            "cover_letter_sent": event.get("cover_letter_sent", False),
                            "hiring_message_sent": event.get("message_sent", False),
                            "hiring_message_preview": event.get("message_preview"),
                            "notes": event.get("error"),
                        }).execute()
                    except Exception:
                        pass

                # Update run_session stats
                if event.get("event") in ("application", "portal_searched", "complete"):
                    try:
                        updates = {}
                        if event.get("event") == "portal_searched":
                            updates = {"current_portal": event.get("portal"), "jobs_found": event.get("total_found", 0), "status": "running"}
                        elif event.get("event") == "application":
                            col = {"submitted": "apps_submitted", "flagged": "apps_flagged", "failed": "apps_failed"}.get(event.get("status", ""), None)
                            if col:
                                current = sb.table("run_sessions").select(col).eq("id", run_id).single().execute()
                                updates = {col: (current.data or {}).get(col, 0) + 1, "current_job": f"{event.get('title')} @ {event.get('company')}"}
                        elif event.get("event") == "complete":
                            updates = {"status": "completed", "current_portal": None, "current_job": None}
                        if updates:
                            sb.table("run_sessions").update(updates).eq("id", run_id).execute()
                    except Exception:
                        pass

                yield f"data: {data}\n\n"
                if event.get("event") == "complete":
                    break
        finally:
            await pubsub.unsubscribe(f"run:{run_id}")
            await r.aclose()

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                              headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/user/{user_id}")
async def get_user_runs(user_id: str, limit: int = 20):
    sb = get_supabase()
    res = sb.table("run_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return {"runs": res.data}


@router.get("/{run_id}")
async def get_run(run_id: str):
    sb = get_supabase()
    res = sb.table("run_sessions").select("*").eq("id", run_id).single().execute()
    return res.data
