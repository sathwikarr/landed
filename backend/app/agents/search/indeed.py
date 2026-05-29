"""Indeed + Glassdoor search agent."""
import asyncio
import hashlib
from typing import List
from urllib.parse import urlencode, quote
from app.models.schemas import JobListing, UserPreferences
from app.services.browser import new_page, get_page_text, is_captcha_present


def _dedup_key(title: str, company: str) -> str:
    return hashlib.md5(f"{title.lower().strip()}{company.lower().strip()}".encode()).hexdigest()


async def search_indeed(prefs: UserPreferences, seen_keys: set, limit: int = 30) -> List[JobListing]:
    role = prefs.target_roles[0] if prefs.target_roles else ""
    location = prefs.locations[0] if prefs.locations else ""
    params = {"q": role, "l": location, "sort": "date"}
    if prefs.remote_pref == "remote":
        params["remotejob"] = "032b3046-06a3-4876-8dfd-474eb5e7ed11"
    url = f"https://www.indeed.com/jobs?{urlencode(params)}"

    page = await new_page()
    results: List[JobListing] = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        if await is_captcha_present(page):
            return results

        cards = await page.query_selector_all("[data-jk], .job_seen_beacon")
        for card in cards[:limit]:
            try:
                title_el = await card.query_selector("h2.jobTitle span, .jobTitle")
                company_el = await card.query_selector("[data-testid='company-name'], .companyName")
                location_el = await card.query_selector("[data-testid='text-location'], .companyLocation")
                link_el = await card.query_selector("a")

                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                location = (await location_el.inner_text()).strip() if location_el else ""
                href = await link_el.get_attribute("href") if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.indeed.com" + href

                if not title or not company:
                    continue
                if any(ex.lower() in company.lower() for ex in (prefs.excluded_companies or [])):
                    continue

                key = _dedup_key(title, company)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                # Get JD
                jd_text = ""
                if href:
                    jd_page = await new_page()
                    try:
                        await jd_page.goto(href, wait_until="domcontentloaded", timeout=20000)
                        await asyncio.sleep(1)
                        desc_el = await jd_page.query_selector("#jobDescriptionText, .jobsearch-jobDescriptionText")
                        jd_text = (await desc_el.inner_text()).strip() if desc_el else await get_page_text(jd_page)
                    finally:
                        await jd_page.close()

                results.append(JobListing(
                    source="indeed",
                    title=title,
                    company=company,
                    location=location,
                    jd_text=jd_text or f"{title} at {company}",
                    url=href,
                    ats_type="indeed",
                    easy_apply=False,
                    dedup_key=key,
                ))
            except Exception:
                continue
    finally:
        await page.close()
    return results


async def search_glassdoor(prefs: UserPreferences, seen_keys: set, limit: int = 20) -> List[JobListing]:
    role = quote(prefs.target_roles[0] if prefs.target_roles else "")
    location = quote(prefs.locations[0] if prefs.locations else "")
    url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role}&locT=C&locId=1147401"

    page = await new_page()
    results: List[JobListing] = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        if await is_captcha_present(page):
            return results

        cards = await page.query_selector_all("[data-test='jobListing'], .react-job-listing")
        for card in cards[:limit]:
            try:
                title_el = await card.query_selector("[data-test='job-title'], .job-title")
                company_el = await card.query_selector("[data-test='employer-name'], .employer-name")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                if not title or not company:
                    continue
                key = _dedup_key(title, company)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                link_el = await card.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.glassdoor.com" + href
                results.append(JobListing(
                    source="glassdoor",
                    title=title,
                    company=company,
                    jd_text=f"{title} at {company}",
                    url=href,
                    ats_type="glassdoor",
                    dedup_key=key,
                ))
            except Exception:
                continue
    finally:
        await page.close()
    return results
