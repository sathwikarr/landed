"""Saved form fields — store answers to novel application fields so we never ask twice."""
from fastapi import APIRouter
from app.models.schemas import SaveFieldRequest

router = APIRouter(prefix="/fields", tags=["fields"])
_fields: dict = {}  # user_id → {field_name: value}


@router.get("/{user_id}")
async def get_fields(user_id: str):
    return {"fields": _fields.get(user_id, {})}


@router.post("/save")
async def save_field(req: SaveFieldRequest):
    if req.user_id not in _fields:
        _fields[req.user_id] = {}
    _fields[req.user_id][req.field_name] = req.field_value
    return {"ok": True}
