"""Scoring agent — ranks jobs against candidate profile using LLM."""
from typing import List
from app.models.schemas import JobListing, ParsedResume, UserPreferences
from app.services.llm import score_job


def _build_candidate_profile(resume: ParsedResume, prefs: UserPreferences) -> dict:
    return {
        "name": resume.name,
        "current_title": resume.current_title,
        "skills": resume.skills,
        "experience_years": resume.experience_years,
        "experience_level": prefs.experience_level,
        "target_roles": prefs.target_roles,
        "preferred_companies": prefs.preferred_companies,
        "salary_min": prefs.salary_min,
        "salary_max": prefs.salary_max,
        "locations": prefs.locations,
        "remote_pref": prefs.remote_pref,
    }


async def score_and_rank(
    jobs: List[JobListing],
    resume: ParsedResume,
    prefs: UserPreferences,
    threshold: float = 0.55,
    top_n: int = 10,
) -> List[JobListing]:
    """Score all jobs, filter below threshold, return top_n ranked."""
    profile = _build_candidate_profile(resume, prefs)
    scored = []

    for job in jobs:
        # Hard filters first (fast, no LLM cost)
        if any(ex.lower() in job.company.lower() for ex in (prefs.excluded_companies or [])):
            continue

        result = score_job(job.jd_text, profile)
        job.score = result.get("score", 0.5)

        if job.score >= threshold:
            scored.append(job)

    # Sort descending by score, take top N
    scored.sort(key=lambda j: j.score or 0, reverse=True)
    return scored[:top_n]
