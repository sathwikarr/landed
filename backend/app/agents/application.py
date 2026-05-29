"""Application agent — drives browser automation to submit each job."""
import os
import tempfile
from app.models.schemas import TailoredApplication, UserProfile, ApplicationRecord, ApplicationStatus
from app.services.browser import new_page, apply_linkedin_easy_apply, apply_greenhouse
from app.services.llm import extract_form_fields
from app.services.browser import get_page_text
from datetime import datetime


def _build_user_data(profile: UserProfile, app: TailoredApplication) -> dict:
    """Merge saved profile fields with application-specific data."""
    base = {
        "first_name": profile.name.split()[0] if profile.name else "",
        "last_name": " ".join(profile.name.split()[1:]) if profile.name else "",
        "email": profile.email,
        "cover_letter": app.cover_letter or "",
        "linkedin_url": profile.saved_fields.get("linkedin_url", ""),
        "phone": profile.saved_fields.get("phone", ""),
        "github_url": profile.saved_fields.get("github_url", ""),
        "website": profile.saved_fields.get("website", ""),
        "location": profile.saved_fields.get("location", ""),
        "work_authorization": profile.saved_fields.get("work_authorization", ""),
        "visa_sponsorship": profile.saved_fields.get("visa_sponsorship", "No"),
        "years_of_experience": str(profile.saved_fields.get("years_of_experience", "")),
        "salary_expectation": str(profile.saved_fields.get("salary_expectation", "")),
    }
    # Overlay any saved custom fields
    base.update(profile.saved_fields)
    return base


async def apply_to_job(
    app: TailoredApplication,
    profile: UserProfile,
    run_id: str,
) -> ApplicationRecord:
    """Attempt to apply. Returns ApplicationRecord with final status."""
    job = app.job
    record = ApplicationRecord(
        run_id=run_id,
        user_id=profile.id,
        job=job,
        resume_version=app.resume_version,
        cover_letter_sent=app.cover_letter is not None,
        hiring_message_sent=app.hiring_message is not None,
        hiring_message_preview=app.hiring_message[:120] if app.hiring_message else None,
    )

    # Write resume to temp file
    resume_path = os.path.join(tempfile.gettempdir(), f"resume_{run_id}_{job.id}.txt")
    if not os.path.exists(resume_path):
        with open(resume_path, "w") as f:
            f.write(app.tailored_resume_text)

    user_data = _build_user_data(profile, app)
    result = {"success": False, "captcha": False, "unknown_fields": [], "error": None}

    try:
        page = await new_page()
        try:
            if job.ats_type == "linkedin" or job.easy_apply:
                result = await apply_linkedin_easy_apply(page, job.url, user_data, resume_path)
            elif job.ats_type == "greenhouse":
                result = await apply_greenhouse(page, job.url, user_data, resume_path)
            else:
                # Generic: navigate and try to fill form
                from playwright.async_api import Page
                from app.services.browser import fill_text_field, safe_click
                await page.goto(job.url, wait_until="domcontentloaded", timeout=30000)
                page_text = await get_page_text(page)
                fields = extract_form_fields(page_text)
                for field in fields:
                    fname = field.get("field", "").lower()
                    value = user_data.get(fname, "")
                    if value:
                        try:
                            await fill_text_field(page, f"[name*='{fname}'], [id*='{fname}'], [placeholder*='{fname}']", str(value))
                        except Exception:
                            pass
                submit = await page.query_selector("button[type='submit'], input[type='submit']")
                if submit:
                    await submit.click()
                    result["success"] = True
                else:
                    result["error"] = "No submit button found"
        finally:
            await page.close()
    except Exception as e:
        result["error"] = str(e)

    # Update record status
    if result.get("captcha"):
        record.status = ApplicationStatus.flagged
        record.notes = "CAPTCHA detected — needs manual review"
    elif result.get("success"):
        record.status = ApplicationStatus.submitted
        record.submitted_at = datetime.utcnow()
    else:
        record.status = ApplicationStatus.failed
        record.notes = result.get("error", "Unknown error")

    return record
