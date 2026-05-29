"""
LLM service — uses Google Gemini Flash (free tier: 1500 req/day).
Falls back to Groq (Llama 3.1) for lightweight classification tasks.
"""
import os
import json
from typing import Optional
import google.generativeai as genai
from groq import Groq


genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_gemini = genai.GenerativeModel("gemini-1.5-flash")
_groq = Groq(api_key=os.environ["GROQ_API_KEY"])


def _gemini_call(prompt: str) -> str:
    response = _gemini.generate_content(prompt)
    return response.text.strip()


def _groq_call(prompt: str) -> str:
    response = _groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def parse_resume(resume_text: str) -> dict:
    """Extract structured data from raw resume text."""
    prompt = f"""Extract structured info from this resume. Return ONLY valid JSON with keys:
name, email, phone, skills (list), experience_years (int), current_title, education (list of strings), 
work_history (list of {{title, company, duration, bullets}}), summary.

Resume:
{resume_text[:4000]}

JSON:"""
    raw = _gemini_call(prompt)
    try:
        return json.loads(raw.strip("```json").strip("```").strip())
    except Exception:
        return {"raw_text": resume_text, "skills": [], "work_history": []}


def score_job(jd_text: str, candidate_profile: dict) -> dict:
    """Score a job description against the candidate profile. Returns score 0-1 + reasoning."""
    prompt = f"""Score how well this candidate matches this job. Return JSON only:
{{"score": 0.0-1.0, "match_level": "strong/moderate/weak/reach", "matching_skills": [], "missing_skills": [], "reason": "1 sentence"}}

Candidate: {json.dumps(candidate_profile, indent=2)[:1500]}

Job Description: {jd_text[:1500]}

JSON:"""
    raw = _groq_call(prompt)
    try:
        return json.loads(raw.strip("```json").strip("```").strip())
    except Exception:
        return {"score": 0.5, "match_level": "moderate", "matching_skills": [], "missing_skills": [], "reason": "Unable to parse"}


def tailor_resume(resume_text: str, jd_text: str, job_title: str) -> str:
    """Rewrite resume to match JD keywords while staying truthful."""
    prompt = f"""You are a professional resume writer. Rewrite the resume below to better match the job description.
Rules:
- Keep all facts truthful — do NOT invent experience
- Reorder and reword bullet points to match JD keywords
- Update the summary/objective to target this specific role
- Keep formatting clean (no markdown, plain text)
- Keep it under 600 words

Job Title: {job_title}
Job Description (key requirements): {jd_text[:1500]}

Original Resume:
{resume_text[:2000]}

Tailored Resume:"""
    return _gemini_call(prompt)


def generate_cover_letter(resume_text: str, jd_text: str, company: str, job_title: str) -> str:
    """Generate a concise, personalised cover letter."""
    prompt = f"""Write a short, professional cover letter (150-200 words max) for this job.
- Be specific to the company and role
- Reference 2-3 concrete skills/experiences from the resume that match the JD
- Avoid clichés like "I am passionate about..."
- End with a clear call to action

Company: {company}
Role: {job_title}
JD highlights: {jd_text[:800]}
Resume highlights: {resume_text[:800]}

Cover Letter:"""
    return _gemini_call(prompt)


def generate_hiring_message(resume_text: str, company: str, job_title: str, recruiter_name: Optional[str] = None) -> str:
    """Draft a short LinkedIn/email message to the hiring team."""
    addressee = recruiter_name or "Hiring Manager"
    prompt = f"""Write a brief, genuine outreach message (60-80 words) to send to a recruiter after applying.
- Address: {addressee}
- Company: {company}, Role: {job_title}
- Mention one specific thing about the company that's relevant
- Reference one matching skill from the resume
- Keep it conversational, not salesy

Resume snippet: {resume_text[:600]}

Message:"""
    return _groq_call(prompt)


def extract_form_fields(page_text: str) -> list:
    """Given visible text from an application page, identify required form fields."""
    prompt = f"""List the form fields visible on this job application page. 
Return JSON array of objects: [{{"field": "field name", "type": "text/select/file/checkbox", "required": true/false}}]

Page text: {page_text[:2000]}

JSON:"""
    raw = _groq_call(prompt)
    try:
        return json.loads(raw.strip("```json").strip("```").strip())
    except Exception:
        return []
