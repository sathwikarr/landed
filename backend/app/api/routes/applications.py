"""Application records API — backed by Supabase."""
from fastapi import APIRouter, HTTPException
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/{user_id}")
async def get_applications(user_id: str, limit: int = 100, status: str | None = None):
    sb = get_supabase()
    q = sb.table("applications") \
          .select("*, jobs(title, company, url, source, score)") \
          .eq("user_id", user_id) \
          .order("created_at", desc=True) \
          .limit(limit)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    return {"applications": res.data}


@router.post("/{user_id}/record")
async def record_application(user_id: str, record: dict):
    sb = get_supabase()
    # Upsert job first
    job_data = record.pop("job", {})
    job_res = sb.table("jobs").upsert(job_data, on_conflict="dedup_key").execute()
    job_id = job_res.data[0]["id"] if job_res.data else None

    record["user_id"] = user_id
    record["job_id"] = job_id
    res = sb.table("applications").insert(record).execute()
    return {"ok": True, "id": res.data[0]["id"] if res.data else None}


@router.put("/{user_id}/{app_id}/status")
async def update_status(user_id: str, app_id: str, status: str):
    sb = get_supabase()
    sb.table("applications").update({"status": status}).eq("id", app_id).eq("user_id", user_id).execute()
    return {"ok": True}
