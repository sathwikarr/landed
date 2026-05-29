"""Resume upload — stores file in Supabase Storage, parsed JSON in DB."""
import os, io, uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.llm import parse_resume
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), user_id: str = ""):
    if not file.filename.endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(400, "Only PDF, DOCX, or TXT files accepted")

    content = await file.read()

    # Extract text
    text = ""
    if file.filename.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    elif file.filename.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    elif file.filename.endswith(".docx"):
        import docx
        doc = docx.Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)

    parsed = parse_resume(text)

    sb = get_supabase()
    file_path = f"{user_id}/{uuid.uuid4()}_{file.filename}" if user_id else f"anon/{uuid.uuid4()}_{file.filename}"

    # Upload to Supabase Storage bucket "resumes"
    sb.storage.from_("resumes").upload(file_path, content, {"content-type": file.content_type or "application/octet-stream"})
    file_url = sb.storage.from_("resumes").get_public_url(file_path)

    # Save record to DB
    if user_id:
        # Deactivate previous resumes
        sb.table("resumes").update({"is_active": False}).eq("user_id", user_id).execute()
        res = sb.table("resumes").insert({
            "user_id": user_id,
            "file_url": file_url,
            "file_name": file.filename,
            "parsed_json": parsed,
            "raw_text": text,
            "version": 1,
            "is_active": True,
        }).execute()

    parsed["raw_text"] = text
    return {"parsed": parsed, "file_url": file_url, "char_count": len(text)}


@router.get("/{user_id}/active")
async def get_active_resume(user_id: str):
    sb = get_supabase()
    res = sb.table("resumes").select("*").eq("user_id", user_id).eq("is_active", True).order("created_at", desc=True).limit(1).execute()
    if not res.data:
        raise HTTPException(404, "No resume found")
    return res.data[0]
