"""Application records API."""
from fastapi import APIRouter
from typing import List

router = APIRouter(prefix="/applications", tags=["applications"])

# In-memory store for demo — replace with Supabase in production
_store: dict = {}


@router.get("/{user_id}")
async def get_applications(user_id: str):
    return {"applications": _store.get(user_id, [])}


@router.post("/{user_id}/record")
async def record_application(user_id: str, record: dict):
    if user_id not in _store:
        _store[user_id] = []
    _store[user_id].append(record)
    return {"ok": True}


@router.put("/{user_id}/{app_id}/status")
async def update_status(user_id: str, app_id: str, status: str):
    apps = _store.get(user_id, [])
    for app in apps:
        if app.get("id") == app_id:
            app["status"] = status
            return {"ok": True}
    return {"ok": False, "error": "Not found"}
