"""Saved form fields — persisted in profiles.saved_fields JSONB column."""
from fastapi import APIRouter
from app.models.schemas import SaveFieldRequest
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/fields", tags=["fields"])


@router.get("/{user_id}")
async def get_fields(user_id: str):
    sb = get_supabase()
    res = sb.table("profiles").select("saved_fields").eq("id", user_id).single().execute()
    return {"fields": res.data.get("saved_fields", {}) if res.data else {}}


@router.post("/save")
async def save_field(req: SaveFieldRequest):
    sb = get_supabase()
    # Merge new field into existing saved_fields
    current = sb.table("profiles").select("saved_fields").eq("id", req.user_id).single().execute()
    fields = current.data.get("saved_fields", {}) if current.data else {}
    fields[req.field_name] = req.field_value
    sb.table("profiles").update({"saved_fields": fields}).eq("id", req.user_id).execute()
    return {"ok": True}
