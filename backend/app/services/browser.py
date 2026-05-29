"""
Browser service — Playwright-based automation for job applications.
Handles form fill, file upload, Easy Apply, and CAPTCHA detection.
"""
import asyncio
import os
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None


async def get_browser() -> Browser:
    global _browser
    if _browser is None or not _browser.is_connected():
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
    return _browser


async def get_context() -> BrowserContext:
    global _context
    browser = await get_browser()
    if _context is None:
        _context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
    return _context


async def new_page() -> Page:
    ctx = await get_context()
    return await ctx.new_page()


async def is_captcha_present(page: Page) -> bool:
    """Detect common CAPTCHA patterns."""
    captcha_selectors = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        ".g-recaptcha",
        "#captcha",
        "[data-sitekey]",
        "iframe[title*='captcha' i]",
    ]
    for sel in captcha_selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                return True
        except Exception:
            pass
    return False


async def get_page_text(page: Page) -> str:
    return await page.evaluate("document.body.innerText")


async def fill_text_field(page: Page, selector: str, value: str):
    await page.wait_for_selector(selector, timeout=5000)
    await page.fill(selector, value)


async def safe_click(page: Page, selector: str):
    await page.wait_for_selector(selector, timeout=5000)
    await page.click(selector)


async def upload_file(page: Page, selector: str, file_path: str):
    await page.set_input_files(selector, file_path)


async def scrape_job_listings(url: str, scroll_count: int = 3) -> str:
    """Navigate to a URL and return full page text after scrolling."""
    page = await new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        for _ in range(scroll_count):
            await page.keyboard.press("End")
            await asyncio.sleep(1)
        return await get_page_text(page)
    finally:
        await page.close()


async def apply_linkedin_easy_apply(page: Page, job_url: str, user_data: dict, resume_path: str) -> dict:
    """
    Attempt LinkedIn Easy Apply flow.
    Returns: {"success": bool, "captcha": bool, "unknown_fields": list, "error": str}
    """
    result = {"success": False, "captcha": False, "unknown_fields": [], "error": None}
    try:
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        if await is_captcha_present(page):
            result["captcha"] = True
            return result

        # Click Easy Apply button
        easy_apply_btn = await page.query_selector("button[aria-label*='Easy Apply']")
        if not easy_apply_btn:
            result["error"] = "No Easy Apply button found"
            return result
        await easy_apply_btn.click()
        await asyncio.sleep(1.5)

        # Multi-step form — iterate through pages
        for step in range(10):
            if await is_captcha_present(page):
                result["captcha"] = True
                return result

            # Upload resume if file input present
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await upload_file(page, "input[type='file']", resume_path)

            # Fill known fields
            for field_label, value in user_data.items():
                try:
                    # Try matching label text to input
                    label = await page.query_selector(f"label:has-text('{field_label}')")
                    if label:
                        input_id = await label.get_attribute("for")
                        if input_id:
                            await fill_text_field(page, f"#{input_id}", str(value))
                except Exception:
                    pass

            # Check for Next / Submit button
            next_btn = await page.query_selector("button[aria-label='Continue to next step']")
            submit_btn = await page.query_selector("button[aria-label='Submit application']")

            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(2)
                result["success"] = True
                return result
            elif next_btn:
                await next_btn.click()
                await asyncio.sleep(1.5)
            else:
                result["error"] = f"No next/submit button on step {step}"
                return result

        result["error"] = "Exceeded max steps"
    except Exception as e:
        result["error"] = str(e)
    return result


async def apply_greenhouse(page: Page, job_url: str, user_data: dict, resume_path: str) -> dict:
    """Fill a Greenhouse application form."""
    result = {"success": False, "captcha": False, "unknown_fields": [], "error": None}
    try:
        await page.goto(job_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        if await is_captcha_present(page):
            result["captcha"] = True
            return result

        # Upload resume
        resume_input = await page.query_selector("input#resume")
        if resume_input:
            await upload_file(page, "input#resume", resume_path)

        # Standard Greenhouse fields
        field_map = {
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "email": user_data.get("email", ""),
            "phone": user_data.get("phone", ""),
            "job_application[answers_attributes][0][text_value]": user_data.get("cover_letter", ""),
        }
        for field_id, value in field_map.items():
            try:
                await fill_text_field(page, f"#{field_id}", str(value))
            except Exception:
                pass

        # LinkedIn URL if present
        linkedin_input = await page.query_selector("input[name*='linkedin']")
        if linkedin_input and user_data.get("linkedin_url"):
            await linkedin_input.fill(user_data["linkedin_url"])

        # Submit
        submit = await page.query_selector("input[type='submit'], button[type='submit']")
        if submit:
            await submit.click()
            await asyncio.sleep(3)
            result["success"] = True
        else:
            result["error"] = "No submit button found"
    except Exception as e:
        result["error"] = str(e)
    return result
