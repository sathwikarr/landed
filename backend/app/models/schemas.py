from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid


class RemotePref(str, Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "on_site"
    any = "any"

class ExperienceLevel(str, Enum):
    intern = "intern"
    junior = "junior"
    mid = "mid"
    senior = "senior"
    staff = "staff"
    principal = "principal"

class ApplicationStatus(str, Enum):
    pending = "pending"
    submitted = "submitted"
    flagged = "flagged"
    failed = "failed"
    skipped = "skipped"

class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"


# ── User & Preferences ──────────────────────────────────────────────────────

class UserPreferences(BaseModel):
    target_roles: List[str]
    locations: List[str]
    remote_pref: RemotePref
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_level: ExperienceLevel
    years_of_experience: Optional[int] = None
    preferred_companies: List[str] = []
    excluded_companies: List[str] = []
    platforms: List[str] = ["linkedin", "indeed", "glassdoor", "dice", "jobright"]
    max_apps_per_day: int = 10
    generate_cover_letter: bool = True
    send_hiring_message: bool = False
    auto_apply: bool = True


class UserProfile(BaseModel):
    id: str = str(uuid.uuid4())
    email: EmailStr
    name: str
    preferences: Optional[UserPreferences] = None
    saved_fields: dict = {}  # stores answers to previously unseen form fields


# ── Resume ──────────────────────────────────────────────────────────────────

class ParsedResume(BaseModel):
    raw_text: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience_years: Optional[int] = None
    current_title: Optional[str] = None
    education: List[str] = []
    work_history: List[dict] = []
    summary: Optional[str] = None


# ── Jobs ────────────────────────────────────────────────────────────────────

class JobListing(BaseModel):
    id: str = str(uuid.uuid4())
    source: str  # linkedin, indeed, etc.
    title: str
    company: str
    location: Optional[str] = None
    remote: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    jd_text: str
    url: str
    ats_type: Optional[str] = None  # greenhouse, lever, linkedin, native
    easy_apply: bool = False
    score: Optional[float] = None  # 0-1 match score
    dedup_key: Optional[str] = None  # hash of title+company


class TailoredApplication(BaseModel):
    job: JobListing
    tailored_resume_text: str
    cover_letter: Optional[str] = None
    hiring_message: Optional[str] = None
    resume_version: str


# ── Run ─────────────────────────────────────────────────────────────────────

class RunSession(BaseModel):
    id: str = str(uuid.uuid4())
    user_id: str
    status: RunStatus = RunStatus.queued
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_portal: Optional[str] = None
    current_job: Optional[str] = None
    jobs_found: int = 0
    jobs_after_dedup: int = 0
    apps_submitted: int = 0
    apps_flagged: int = 0
    apps_failed: int = 0


class ApplicationRecord(BaseModel):
    id: str = str(uuid.uuid4())
    run_id: str
    user_id: str
    job: JobListing
    status: ApplicationStatus = ApplicationStatus.pending
    resume_version: str
    cover_letter_sent: bool = False
    hiring_message_sent: bool = False
    hiring_message_preview: Optional[str] = None
    submitted_at: Optional[datetime] = None
    notes: Optional[str] = None


# ── API payloads ─────────────────────────────────────────────────────────────

class StartRunRequest(BaseModel):
    user_id: str

class RunStatusResponse(BaseModel):
    run: RunSession
    recent_applications: List[ApplicationRecord] = []

class SaveFieldRequest(BaseModel):
    user_id: str
    field_name: str
    field_value: str
