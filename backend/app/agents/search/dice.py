"""Dice + Jobright search agents."""
import asyncio
import hashlib
from typing import List
from urllib.parse import urlencode
from app.models.schemas import JobListing, UserPreferences
from app.services.browser import new_page, get_page_text, is_captcha_present


def _dedup_key(title: str, company: str) -> str:
    return hashlib.md5(f"{title.lower().strip()}{company.lower().strip()}".encode()).hexdigest()


async def search_dice(prefs: UserPreferences, seen_keys: set, limit: int = 20) -> List[JobListing]:
    role = prefs.target_roles[0] if prefs.target_roles else ""
    location = prefs.locations[0] if prefs.locations else ""
    params = {"q": role, "location": location, "radius": "30", "radiusUnit": "mi", "pageSize": "20", "filters.postedDate": "ONE_DAY"}
    url = f"https://www.dice.com/jobs?{urlencode(params)}"

    page = await new_page()
    results: List[JobListing] = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        if await is_captcha_present(page):
            return results

        cards = await page.query_selector_all("dhi-search-card, [data-cy='card']")
        for card in cards[:limit]:
            try:
                title_el = await card.query_selector("a.card-title-link, h5")
                company_el = await card.query_selector(".company-name-label, span[data-cy='search-result-company-name']")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                href = await title_el.get_attribute("href") if title_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.dice.com" + href
                if not title:
                    continue
                key = _dedup_key(title, company or "unknown")
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                results.append(JobListing(
                    source="dice",
                    title=title,
                    company=company,
                    jd_text=f"{title} at {company}",
                    url=href,
                    ats_type="dice",
                    dedup_key=key,
                ))
            except Exception:
                continue
    finally:
        await page.close()
    return results


async def search_jobright(prefs: UserPreferences, seen_keys: set, limit: int = 20) -> List[JobListing]:
    role = prefs.target_roles[0] if prefs.target_roles else ""
    url = f"https://jobright.ai/jobs?title={role.replace(' ', '+')}"

    page = await new_page()
    results: List[JobListing] = []
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        if await is_captcha_present(page):
            return results

        page_text = await get_page_text(page)
        cards = await page.query_selector_all(".job-card, [class*='job-item'], [class*='JobCard']")
        for card in cards[:limit]:
            try:
                title_el = await card.query_selector("h3, .job-title, [class*='title']")
                company_el = await card.query_selector(".company, [class*='company']")
                link_el = await card.query_selector("a")
                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                href = await link_el.get_attribute("href") if link_el else ""
                if not title:
                    continue
                key = _dedup_key(title, company or "unknown")
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                results.append(JobListing(
                    source="jobright",
                    title=title,
                    company=company,
                    jd_text=f"{title} at {company}",
                    url=href or url,
                    ats_type="jobright",
                    dedup_key=key,
                ))
            except Exception:
                continue
    finally:
        await page.close()
    return results
