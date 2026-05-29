"""LinkedIn search agent — scrapes job listings matching user preferences."""
import asyncio
import hashlib
from typing import List
from urllib.parse import urlencode
from app.models.schemas import JobListing, UserPreferences
from app.services.browser import new_page, get_page_text, is_captcha_present
import re


def _dedup_key(title: str, company: str) -> str:
    return hashlib.md5(f"{title.lower().strip()}{company.lower().strip()}".encode()).hexdigest()


def _build_linkedin_url(prefs: UserPreferences) -> str:
    role = prefs.target_roles[0] if prefs.target_roles else ""
    location = prefs.locations[0] if prefs.locations else ""
    params = {
        "keywords": role,
        "location": location,
        "f_AL": "true",  # Easy Apply filter
        "sortBy": "DD",  # Most recent
    }
    if prefs.experience_level in ["senior", "staff", "principal"]:
        params["f_E"] = "4"  # Senior level
    elif prefs.experience_level in ["mid"]:
        params["f_E"] = "3"
    elif prefs.experience_level in ["junior"]:
        params["f_E"] = "2"
    if prefs.remote_pref == "remote":
        params["f_WT"] = "2"
    elif prefs.remote_pref == "hybrid":
        params["f_WT"] = "3"
    return f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"


async def _parse_job_cards(page) -> List[dict]:
    """Extract job cards from LinkedIn search results page."""
    jobs = []
    cards = await page.query_selector_all(".job-card-container, .jobs-search-results__list-item")
    for card in cards:
        try:
            title_el = await card.query_selector(".job-card-list__title, h3")
            company_el = await card.query_selector(".job-card-container__company-name, h4")
            location_el = await card.query_selector(".job-card-container__metadata-item")
            link_el = await card.query_selector("a.job-card-list__title, a")

            title = (await title_el.inner_text()).strip() if title_el else ""
            company = (await company_el.inner_text()).strip() if company_el else ""
            location = (await location_el.inner_text()).strip() if location_el else ""
            href = await link_el.get_attribute("href") if link_el else ""

            if title and company:
                jobs.append({"title": title, "company": company, "location": location, "url": href or ""})
        except Exception:
            continue
    return jobs


async def _get_job_description(page, job_url: str) -> str:
    """Click into a job and extract the full description."""
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1.5)
        desc_el = await page.query_selector(".job-view-layout, .jobs-description, .description__text")
        if desc_el:
            return (await desc_el.inner_text()).strip()
        return await get_page_text(page)
    except Exception:
        return ""


async def search_linkedin(prefs: UserPreferences, seen_keys: set, limit: int = 30) -> List[JobListing]:
    """Search LinkedIn and return new (deduped) job listings."""
    url = _build_linkedin_url(prefs)
    page = await new_page()
    results: List[JobListing] = []

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        if await is_captcha_present(page):
            print("[LinkedIn] CAPTCHA on search page — skipping")
            return results

        raw_cards = await _parse_job_cards(page)

        for card in raw_cards[:limit]:
            title = card["title"]
            company = card["company"]

            # Skip excluded companies
            if any(ex.lower() in company.lower() for ex in (prefs.excluded_companies or [])):
                continue

            key = _dedup_key(title, company)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # Fetch full JD
            jd_text = ""
            if card["url"]:
                jd_text = await _get_job_description(page, card["url"])

            # Filter by salary if provided
            if prefs.salary_min and jd_text:
                salary_match = re.search(r'\$(\d{2,3})[kK,]', jd_text)
                if salary_match:
                    jd_salary = int(salary_match.group(1)) * 1000
                    if jd_salary < prefs.salary_min * 0.8:
                        continue

            job = JobListing(
                source="linkedin",
                title=title,
                company=company,
                location=card.get("location", ""),
                jd_text=jd_text or f"{title} at {company}",
                url=card["url"],
                ats_type="linkedin",
                easy_apply=True,
                dedup_key=key,
            )
            results.append(job)

            if len(results) >= limit:
                break

    finally:
        await page.close()

    return results
