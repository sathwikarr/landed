"""Run management API — start, stream, and query runs."""
import json
import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis
import os
from app.models.schemas import StartRunRequest, RunStatusResponse, RunSession, RunStatus
from app.workers.tasks import run_pipeline_task

router = APIRouter(prefix="/runs", tags=["runs"])
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


@router.post("/start")
async def start_run(req: StartRunRequest, profile: dict, prefs: dict, resume_text: str):
    run_id = str(uuid.uuid4())
    run_pipeline_task.apply_async(
        args=[run_id, req.user_id, profile, prefs, resume_text],
        task_id=run_id,
    )
    return {"run_id": run_id, "status": "queued"}


@router.get("/{run_id}/stream")
async def stream_run(run_id: str):
    """SSE endpoint — streams live progress events for a run."""
    async def event_generator():
        r = await aioredis.from_url(REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"run:{run_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode()
                    yield f"data: {data}\n\n"
                    event = json.loads(data)
                    if event.get("event") == "complete":
                        break
        finally:
            await pubsub.unsubscribe(f"run:{run_id}")
            await r.aclose()

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                              headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/{run_id}/status")
async def get_run_status(run_id: str):
    task = run_pipeline_task.AsyncResult(run_id)
    return {"run_id": run_id, "celery_status": task.status, "result": task.result}
