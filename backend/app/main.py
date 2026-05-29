"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import runs, resume, applications, fields

app = FastAPI(title="JobApply API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(fields.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
