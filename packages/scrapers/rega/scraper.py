import asyncio
import time
import traceback
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

BASE_DIR = Path(__file__).parent.resolve()
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

XLSX_PATH = BASE_DIR / "REGA_Qualified_Companies.xlsx"
CSV_PATH = BASE_DIR / "REGA_Qualified_Companies.csv"

SEARCH_PAGE = (
    "https://rega.gov.sa/rega-services/real-estate-inquiries/"
    "%D8%A7%D8%B3%D8%AA%D8%B9%D9%84%D8%A7%D9%85-%D8%B9%D9%86-%D8%A7%D9%84%D8%B4%D8%B1%D9%83%D8%A7%D8%AA-%D8%A7%D9%84%D9%85%D8%A4%D9%87%D9%84%D8%A9-%D9%81%D9%8A-%D8%A7%D9%84%D8%A8%D9%8A%D8%B9-%D9%88%D8%A7%D9%84%D8%AA%D8%A3%D8%AC%D9%8A%D8%B1-%D8%B9%D9%84%D9%89-%D8%A7%D9%84%D8%AE%D8%A7%D8%B1%D8%B7%D8%A9-%D9%88%D8%A7%D9%84%D9%85%D8%B3%D8%A7%D9%87%D9%85%D8%A7%D8%AA-%D8%A7%D9%84%D8%B9%D9%82%D8%A7%D8%B1%D9%8A%D8%A9/"
)
RESULT_BASE = "https://rega.gov.sa/rega-services/real-estate-inquiries/result-page/"
MAX_RETRIES = 3
NAV_TIMEOUT_MS = 60000
COLUMNS = [
    "Company Name", "Status", "City", "License Number",
    "License Type", "Qualification Start", "Qualification End",
]

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("rega_scraper")


# ── Site opening ──────────────────────────────────────────────────────────


async def open_site():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}, locale="ar-SA"
    )
    page = await context.new_page()
    await page.goto(SEARCH_PAGE, wait_until="networkidle", timeout=NAV_TIMEOUT_MS)
    await page.wait_for_timeout(1500)
    try:
        btn = page.locator("button", has_text="قبول")
        if await btn.is_visible(timeout=4000):
            await btn.click()
            await page.wait_for_timeout(800)
            logger.info("Cookie banner accepted")
    except Exception:
        logger.info("No cookie banner")
    return pw, browser, context, page


async def close_site(pw, browser):
    await browser.close()
    pw.stop()


# ── Search ────────────────────────────────────────────────────────────────


async def perform_search(page):
    inp = page.locator("input[data-alias='facilityName']")
    await inp.wait_for(state="visible", timeout=15000)
    await inp.fill("")
    btns = page.locator("button", has_text="البحث")
    count = await btns.count()
    for i in range(count):
        b = btns.nth(i)
        box = await b.bounding_box()
        if box and box["y"] > 300:
            await b.click()
            logger.info("Search button clicked")
            break
    else:
        await page.evaluate("""
            document.querySelector('form.umbraco-forms-centralized-search')
                ?.dispatchEvent(new Event('submit', {cancelable: true}));
        """)
        logger.info("Form submit dispatched via JS")
    await page.wait_for_load_state("networkidle", timeout=NAV_TIMEOUT_MS)
    await page.wait_for_timeout(1500)
    logger.info("Results page loaded: %s", page.url)


# ── Extraction helpers ────────────────────────────────────────────────────


def extract_company(card_soup):
    d = {}
    t = card_soup.find("div", class_="title")
    d["company_name"] = t.get_text(strip=True) if t else ""

    badge = card_soup.find("span", class_="badge-status")
    if badge:
        spans = badge.find_all("span")
        text_spans = [s for s in spans if s.get_text(strip=True) and "dot" not in s.get("class", [])]
        if text_spans:
            d["status"] = text_spans[0].get_text(strip=True)
        else:
            d["status"] = badge.get_text(strip=True)
    else:
        d["status"] = ""

    field_map = {
        "الموقع": "city",
        "رقم الرخصة": "license_number",
        "نوع الرخصة": "license_type",
        "بداية شهادة التأهيل": "qualification_start",
        "نهاية شهادة التأهيل": "qualification_end",
    }
    for sd in card_soup.find_all("div", class_="small"):
        lbl_span = sd.find("span", class_="fw-bold")
        if not lbl_span:
            continue
        label = lbl_span.get_text(strip=True).replace(":", "").replace(":", "").strip()
        value = sd.get_text(strip=True).replace(lbl_span.get_text(strip=True), "").strip()
        key = field_map.get(label)
        if key:
            d[key] = value

    for f in ("city", "license_number", "license_type", "qualification_start", "qualification_end"):
        d.setdefault(f, "")
    return d


def extract_page(html):
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("div.col-lg-6.col-12.mb-4 > div.card")
    if not cards:
        cards = soup.select("div.col-lg-6.col-12.mb-4")
    return [extract_company(c) for c in cards]


def get_total_pages(html):
    soup = BeautifulSoup(html, "lxml")
    nav = soup.select_one("nav[aria-label='pagination']")
    if not nav:
        return 0
    max_p = 0
    for a in nav.select("a.page-link"):
        try:
            n = int(a.get_text(strip=True))
            if n > max_p:
                max_p = n
        except ValueError:
            pass
    return max_p


# ── Page fetching (Playwright) ────────────────────────────────────────────


async def fetch_page(page, page_num):
    url = f"{RESULT_BASE}?currentDeveloperPage={page_num}&tabActive=Wafi+Developers"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await page.goto(url, wait_until="networkidle", timeout=NAV_TIMEOUT_MS)
            await page.wait_for_timeout(1000)
            html = await page.content()
            if "نتائج" in html:
                return html
            logger.warning("Page %d - no result text, retry %d", page_num, attempt)
        except PwTimeout:
            logger.warning("Page %d - timeout, retry %d", page_num, attempt)
        except Exception:
            logger.warning("Page %d - error: %s", page_num, traceback.format_exc()[:200])
        if attempt < MAX_RETRIES:
            await page.wait_for_timeout(1000 * attempt)
    await page.screenshot(path=str(SCREENSHOTS_DIR / f"page_{page_num}_fail.png"))
    return None


# ── Output ────────────────────────────────────────────────────────────────


def save_output(companies):
    records = [
        {
            "Company Name": c.get("company_name", ""),
            "Status": c.get("status", ""),
            "City": c.get("city", ""),
            "License Number": c.get("license_number", ""),
            "License Type": c.get("license_type", ""),
            "Qualification Start": c.get("qualification_start", ""),
            "Qualification End": c.get("qualification_end", ""),
        }
        for c in companies
    ]
    df = pd.DataFrame(records, columns=COLUMNS)
    df.to_excel(XLSX_PATH, index=False, engine="openpyxl")
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    logger.info("Saved %d rows \u2192 %s / %s", len(df), XLSX_PATH.name, CSV_PATH.name)


# ── Main ──────────────────────────────────────────────────────────────────


async def main():
    t0 = time.time()
    p = browser = page = None
    all_companies = []
    seen_licenses = set()
    total_pages = 0

    try:
        p, browser, context, page = await open_site()
        await perform_search(page)

        first_html = await page.content()
        total_pages = get_total_pages(first_html)
        if total_pages == 0:
            logger.error("Could not determine total pages")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "no_pagination.png"))
            return

        logger.info("Total pages: %s", total_pages)

        for pg in range(1, total_pages + 1):
            html = first_html if pg == 1 else await fetch_page(page, pg)
            if html is None:
                logger.error("Page %d skipped after retries", pg)
                continue
            companies = extract_page(html)
            new_count = 0
            for c in companies:
                lic = c.get("license_number", "")
                if lic and lic not in seen_licenses:
                    seen_licenses.add(lic)
                    all_companies.append(c)
                    new_count += 1
                elif not lic:
                    all_companies.append(c)
                    new_count += 1
            logger.info(
                "Page %3d/%d \u2192 %d cards, %d new (total %d)",
                pg, total_pages, len(companies), new_count, len(all_companies),
            )

    except Exception as exc:
        logger.critical("Fatal: %s", traceback.format_exc())
        if page:
            await page.screenshot(path=str(SCREENSHOTS_DIR / "fatal.png"))
        raise
    finally:
        if browser:
            await close_site(p, browser)

    elapsed = time.time() - t0
    logger.info("=" * 50)
    logger.info("Total Pages:      %d", total_pages)
    logger.info("Total Companies:  %d", len(all_companies))
    logger.info("Execution Time:   %.1f s (%.1f min)", elapsed, elapsed / 60)
    logger.info("=" * 50)

    if all_companies:
        save_output(all_companies)

    print(f"\nTotal Pages: {total_pages}")
    print(f"Total Companies: {len(all_companies)}")
    print(f"Execution Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")


if __name__ == "__main__":
    asyncio.run(main())
