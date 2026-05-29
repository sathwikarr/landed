"""Resume upload and parse API."""
import os, tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.llm import parse_resume

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(400, "Only PDF, DOCX, or TXT files accepted")

    content = await file.read()

    # Extract text
    text = ""
    if file.filename.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    elif file.filename.endswith(".pdf"):
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    elif file.filename.endswith(".docx"):
        import docx, io
        doc = docx.Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)

    parsed = parse_resume(text)
    parsed["raw_text"] = text
    return {"parsed": parsed, "char_count": len(text)}
