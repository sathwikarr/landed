"""Tailoring agent — customises resume, cover letter, and hiring message per job."""
import os
import tempfile
from app.models.schemas import JobListing, ParsedResume, TailoredApplication, UserPreferences
from app.services.llm import tailor_resume, generate_cover_letter, generate_hiring_message


async def tailor_for_job(
    job: JobListing,
    resume: ParsedResume,
    prefs: UserPreferences,
    run_id: str,
    version: int,
) -> TailoredApplication:
    # 1. Tailor resume text
    tailored_text = tailor_resume(resume.raw_text, job.jd_text, job.title)

    # 2. Write tailored resume to temp file (for upload)
    resume_path = os.path.join(tempfile.gettempdir(), f"resume_{run_id}_{job.id}.txt")
    with open(resume_path, "w") as f:
        f.write(tailored_text)

    # 3. Cover letter (if requested)
    cover_letter = None
    if prefs.generate_cover_letter:
        cover_letter = generate_cover_letter(resume.raw_text, job.jd_text, job.company, job.title)

    # 4. Hiring message (if requested)
    hiring_message = None
    if prefs.send_hiring_message:
        hiring_message = generate_hiring_message(resume.raw_text, job.company, job.title)

    return TailoredApplication(
        job=job,
        tailored_resume_text=tailored_text,
        cover_letter=cover_letter,
        hiring_message=hiring_message,
        resume_version=f"v{version}_{job.company[:8].replace(' ', '_')}",
    )
