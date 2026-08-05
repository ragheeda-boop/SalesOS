"""
Taqeem Facility Directory Scraper

Scrapes every licensed valuation facility from https://www.taqeem.gov.sa/facilities
Opens each facility's detail page to extract all available information.
"""

import asyncio
import csv
import json
import os
import re
import time

import openpyxl
from playwright.async_api import async_playwright

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(OUTPUT_DIR, "taqeem_facilities.csv")
XLSX_PATH = os.path.join(OUTPUT_DIR, "taqeem_facilities.xlsx")
JSON_PATH = os.path.join(OUTPUT_DIR, "taqeem_facilities.json")
PROGRESS_PATH = os.path.join(OUTPUT_DIR, "progress.json")
MAX_RETRIES = 3
ITEMS_PER_PAGE = 9

COLUMNS = [
    "Facility Name",
    "Facility Type",
    "Membership Number",
    "Commercial Registration",
    "License Number",
    "Classification",
    "Status",
    "Sector",
    "Region",
    "City",
    "Address",
    "Postal Code",
    "Building Number",
    "Phone",
    "Mobile",
    "Email",
    "Website",
    "Google Maps",
    "Valuation Fields",
    "Details URL",
]


class TaqeemScraper:
    def __init__(self):
        self.results = []
        self.failed = []
        self.duplicates_removed = 0
        self.seen_cr = set()
        self.seen_membership = set()
        self.start_time = None
        self.total_pages = 0
        self.total_facilities = 0
        self.expected_total = 0

    def load_progress(self):
        if os.path.exists(PROGRESS_PATH):
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.results = data.get("results", [])
            self.seen_cr = set(data.get("seen_cr", []))
            self.seen_membership = set(data.get("seen_membership", []))
            self.duplicates_removed = data.get("duplicates_removed", 0)
            print(f"Loaded {len(self.results)} existing results from progress.")
            return True
        return False

    def save_progress(self, final=False):
        data = {
            "results": self.results,
            "seen_cr": list(self.seen_cr),
            "seen_membership": list(self.seen_membership),
            "duplicates_removed": self.duplicates_removed,
        }
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if final:
            self.write_csv()
            self.write_xlsx()
            self.write_json()

    def is_duplicate(self, record):
        cr = (record.get("Commercial Registration") or "").strip()
        mem = (record.get("Membership Number") or "").strip()
        if cr and cr in self.seen_cr:
            self.duplicates_removed += 1
            return True
        if mem and mem in self.seen_membership:
            self.duplicates_removed += 1
            return True
        if cr:
            self.seen_cr.add(cr)
        if mem:
            self.seen_membership.add(mem)
        return False

    def write_csv(self):
        with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            for r in self.results:
                writer.writerow(r)
        print(f"CSV: {CSV_PATH} ({len(self.results)} records)")

    def write_xlsx(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Taqeem Facilities"
        ws.append(COLUMNS)
        for r in self.results:
            ws.append([r.get(c, "") for c in COLUMNS])
        wb.save(XLSX_PATH)
        print(f"XLSX: {XLSX_PATH} ({len(self.results)} records)")

    def write_json(self):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"JSON: {JSON_PATH} ({len(self.results)} records)")

    async def get_card_data(self, page, card_el):
        """Extract summary info and details URL from a listing card element."""
        info = {}

        name_el = await card_el.query_selector("span.text-lg-bold.text-gray-800")
        info["name"] = (await name_el.inner_text()).strip() if name_el else ""

        class_el = await card_el.query_selector("span.ot-rec-active.border-active.ow-hint-container")
        info["classification"] = (await class_el.inner_text()).strip().split("\n")[0].strip() if class_el else ""

        status_el = await card_el.query_selector(
            "div.text-medium.text-dark.ms-2 span.ot-rec-active, div.text-medium.text-dark.ms-2 span.text-s-medium"
        )
        info["status"] = (await status_el.inner_text()).strip() if status_el else ""

        region_spans = await card_el.query_selector_all("div.text-medium.text-dark.ms-2 span.text-dark")
        info["region"] = ""
        for rs in region_spans:
            t = (await rs.inner_text()).strip()
            if t:
                info["region"] = t
                break

        cr_number = ""
        cr_labels = await card_el.query_selector_all(".text-gray-700")
        for label in cr_labels:
            text = (await label.inner_text()).strip()
            if "Commercial number" in text:
                parent = await label.evaluate_handle("(el) => el.closest('div.d-flex')")
                if parent:
                    cr_val = await parent.query_selector(".text-medium")
                    if cr_val:
                        cr_text = (await cr_val.inner_text()).strip()
                        nums = re.findall(r"\d+", cr_text.replace(",", ""))
                        if nums:
                            cr_number = nums[0]
                break
        info["cr_number"] = cr_number

        sector_el = await card_el.query_selector("span.ot-rec-muted.border-muted")
        info["sector"] = (await sector_el.inner_text()).strip() if sector_el else ""

        link_el = await card_el.query_selector("a.btn-primary")
        if link_el:
            href = await link_el.get_attribute("href")
            if href:
                info["details_url"] = (
                    href if href.startswith("http") else "https://www.taqeem.gov.sa" + href
                )

        return info

    async def extract_detail_page(self, page):
        """Extract all fields from a facility detail page."""
        data = {}

        name_el = await page.query_selector(".text-l-bold.text-dark")
        if name_el:
            data["Facility Name"] = (await name_el.inner_text()).strip()

        # Look for classification badge in the Basic information section
        class_el = await page.query_selector(".text-xs-semibold.text-dark ~ div span.ot-rec-active, .text-xs-semibold.text-dark + * span.ot-rec-active")
        if not class_el:
            class_el = await page.query_selector("span.ot-rec-active.border-active.ow-hint-container")
        if class_el:
            data["Classification"] = (await class_el.inner_text()).strip().split("\n")[0].strip()

        pairs = await page.evaluate("""
            () => {
                const results = [];
                const containers = document.querySelectorAll(
                    '.col-lg-6.col-md-6.col-12.d-flex, .col-12.d-lg-flex.d-md-flex.d-block'
                );
                containers.forEach(container => {
                    const labelEl = container.querySelector('.text-md-regular.text-dark');
                    if (!labelEl) return;
                    let label = labelEl.textContent.replace(/:\\s*$/, '').trim();
                    let value = '';
                    if (container.classList.contains('d-lg-flex')) {
                        const allText = container.textContent.trim();
                        const lbl = labelEl.textContent.trim();
                        let rest = allText.substring(lbl.length).replace(/^:/, '').trim();
                        value = rest.split(/\\n/).map(s => s.trim()).filter(Boolean).join(', ');
                    } else {
                        const valueEl = container.querySelector('.text-md-semibold');
                        if (valueEl) value = valueEl.textContent.trim();
                    }
                    if (label && value) results.push({ label, value });
                });
                return results;
            }
        """)

        label_map = {
            "Facility type": "Facility Type",
            "Facility membership number": "Membership Number",
            "Commercial registration/Cr entity number": "Commercial Registration",
            "License number": "License Number",
            "Mobile number": "Mobile",
            "Phone number": "Phone",
            "Email": "Email",
            "Website link": "Website",
            "Address": "Address",
            "City": "City",
            "Postal code": "Postal Code",
            "Building number": "Building Number",
            "Google Maps": "Google Maps",
        }

        for pair in pairs:
            # Collapse all whitespace (newlines, multiple spaces) into single spaces
            normalized = " ".join(pair["label"].split())
            if normalized in label_map:
                data[label_map[normalized]] = pair["value"]

        sectors = await page.evaluate("""
            () => {
                const secs = [];
                const headings = document.querySelectorAll('.text-xs-semibold.text-dark');
                let sectorSection = null;
                for (const h of headings) {
                    if (h.textContent.trim() === 'Sectors') { sectorSection = h; break; }
                }
                if (sectorSection) {
                    const row = sectorSection.closest('.row');
                    if (row) {
                        row.querySelectorAll('.ot-rec-muted.border-muted').forEach(b => secs.push(b.textContent.trim()));
                    }
                }
                return secs;
            }
        """)
        if sectors:
            data["Valuation Fields"] = ", ".join(sectors)
            if not data.get("Sector"):
                data["Sector"] = sectors[0]

        return data

    def make_record(self, card_info, detail_info):
        record = {c: "" for c in COLUMNS}
        record["Facility Name"] = detail_info.get("Facility Name") or card_info.get("name", "")
        record["Facility Type"] = detail_info.get("Facility Type", "")
        record["Membership Number"] = detail_info.get("Membership Number", "")
        commercial_reg = detail_info.get("Commercial Registration") or card_info.get("cr_number", "")
        record["Commercial Registration"] = commercial_reg
        record["License Number"] = detail_info.get("License Number", "")
        # Classification: prefer VFR pattern from card, fallback to detail
        cl_card = card_info.get("classification", "")
        cl_detail = detail_info.get("Classification", "")
        if cl_detail and cl_detail.startswith("VFR"):
            record["Classification"] = cl_detail
        elif cl_card and cl_card.startswith("VFR"):
            record["Classification"] = cl_card
        else:
            record["Classification"] = cl_detail or cl_card
        record["Status"] = card_info.get("status", "")
        record["Sector"] = detail_info.get("Sector") or card_info.get("sector", "")
        record["Region"] = card_info.get("region", "")
        record["City"] = detail_info.get("City", "")
        record["Address"] = detail_info.get("Address", "")
        record["Postal Code"] = detail_info.get("Postal Code", "")
        record["Building Number"] = detail_info.get("Building Number", "")
        record["Phone"] = detail_info.get("Phone", "")
        record["Mobile"] = detail_info.get("Mobile", "")
        record["Email"] = detail_info.get("Email", "")
        record["Website"] = detail_info.get("Website", "")
        record["Google Maps"] = detail_info.get("Google Maps", "")
        record["Valuation Fields"] = detail_info.get("Valuation Fields", "")
        record["Details URL"] = card_info.get("details_url", "")
        return record

    async def process_one_facility(self, page, listing_url, card_info):
        """Navigate to one facility's detail page, extract data, return record or None."""
        details_url = card_info.get("details_url", "")
        if not details_url:
            return None

        await page.goto(details_url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)
        try:
            await page.wait_for_selector(".text-xs-semibold.text-dark", timeout=15000)
        except Exception:
            pass

        detail_info = await self.extract_detail_page(page)
        record = self.make_record(card_info, detail_info)

        if self.is_duplicate(record):
            return None

        return record

    async def process_page(self, page, page_num):
        """Process all facilities on a given page number."""
        listing_url = (
            f"https://www.taqeem.gov.sa/en/facilities/page/{page_num}?classification=all&sector=all&region=all&search_in=all&step={ITEMS_PER_PAGE}"
            if page_num > 1
            else f"https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step={ITEMS_PER_PAGE}"
        )

        print(f"\n{'='*60}")
        print(f"Page {page_num}: {listing_url}")
        await page.goto(listing_url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)
        await page.wait_for_selector("div.border.rounded.p-3.h-100", timeout=15000)
        await page.wait_for_timeout(2000)

        # Extract all card data upfront (text-based, no stale handles issue)
        card_infos = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('div.col-lg-4.col-md-6.col-12');
                const results = [];
                cards.forEach(card => {
                    const body = card.querySelector('div.border.rounded.p-3.h-100');
                    if (!body) return;
                    const getText = (sel) => {
                        const el = body.querySelector(sel);
                        return el ? el.textContent.trim() : '';
                    };
                    const name = getText('span.text-lg-bold.text-gray-800');
                    const classEl = body.querySelector('span.ot-rec-active.border-active.ow-hint-container');
                    const classification = classEl ? classEl.textContent.trim().split('\\n')[0].trim() : '';
                    const statusEl = body.querySelector('div.text-medium.text-dark.ms-2 span.ot-rec-active, div.text-medium.text-dark.ms-2 span.text-s-medium');
                    const status = statusEl ? statusEl.textContent.trim() : '';
                    const regionEls = body.querySelectorAll('div.text-medium.text-dark.ms-2 span.text-dark');
                    let region = '';
                    regionEls.forEach(el => { const t = el.textContent.trim(); if (t && !region) region = t; });
                    // Find CR number by locating the label
                    let crNumber = '';
                    const crLabel = Array.from(body.querySelectorAll('.text-gray-700'))
                        .find(el => el.textContent.includes('Commercial number'));
                    if (crLabel) {
                        const crRow = crLabel.closest('div.d-flex');
                        if (crRow) {
                            const crValEl = crRow.querySelector('.text-medium');
                            if (crValEl) {
                                const t = crValEl.textContent.trim();
                                const nums = t.match(/\\d+/g);
                                if (nums) crNumber = nums[0];
                            }
                        }
                    }
                    const sector = getText('span.ot-rec-muted.border-muted');
                    const linkEl = body.querySelector('a.btn-primary');
                    let detailsUrl = '';
                    if (linkEl) {
                        let href = linkEl.getAttribute('href') || '';
                        detailsUrl = href.startsWith('http') ? href : 'https://www.taqeem.gov.sa' + href;
                    }
                    results.push({ name, classification, status, region, cr_number: crNumber, sector, details_url: detailsUrl });
                });
                return results;
            }
        """)

        print(f"Found {len(card_infos)} facilities on page {page_num}")

        for idx, card_info in enumerate(card_infos):
            name = card_info.get("name", "UNKNOWN")
            print(f"\n  [{page_num}-{idx+1}] {name[:60]}")

            # Re-load listing page before each card to get fresh handles
            # (Skip reload for first card since we're already on listing)
            if idx > 0:
                await page.goto(listing_url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(3000)
                try:
                    await page.wait_for_selector("div.border.rounded.p-3.h-100", timeout=15000)
                except Exception:
                    pass
                await page.wait_for_timeout(1000)

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    record = await self.process_one_facility(page, listing_url, card_info)
                    if record is None:
                        # Duplicate
                        break
                    self.results.append(record)
                    print(f"      Saved: {record['Facility Name'][:50]}")
                    self.save_progress(final=False)
                    break
                except Exception as e:
                    print(f"      Attempt {attempt}/{MAX_RETRIES} FAILED: {e}")
                    if attempt == MAX_RETRIES:
                        self.failed.append({
                            "facility": name,
                            "page": page_num,
                            "index": idx,
                            "error": str(e),
                            "url": card_info.get("detailsUrl", ""),
                        })
                        print(f"      GIVING UP")
                    else:
                        await page.wait_for_timeout(3000)

        return len(card_infos)

    async def run(self):
        self.start_time = time.time()
        self.load_progress()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(locale="en-US", timezone_id="Asia/Riyadh")
            page = await context.new_page()

            print("Determining total facility count...")
            await page.goto(
                "https://www.taqeem.gov.sa/en/facilities?classification=all&sector=all&region=all&search_in=all&step=9",
                wait_until="load",
                timeout=60000,
            )
            await page.wait_for_timeout(3000)

            total_count = await page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('span.my-auto');
                    for (const sp of spans) {
                        const m = sp.textContent.match(/from\\s+(\\d+)/i);
                        if (m) return parseInt(m[1], 10);
                    }
                    return 0;
                }
            """)
            if total_count == 0:
                total_count = 438
            self.expected_total = total_count
            total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            self.total_pages = total_pages
            print(f"Total facilities: {total_count}")
            print(f"Total pages (at {ITEMS_PER_PAGE}/page): {total_pages}")

            start_page = 1
            if self.results:
                start_page = (len(self.results) // ITEMS_PER_PAGE) + 1
                if start_page > total_pages:
                    start_page = total_pages
                print(f"Resuming from page ~{start_page}")

            for page_num in range(start_page, total_pages + 1):
                await self.process_page(page, page_num)

            await browser.close()

        elapsed = time.time() - self.start_time
        self.total_facilities = len(self.results)

        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETE!")
        print(f"{'='*60}")
        expected = getattr(self, 'total_facilities', 0)
        print(f"Expected (from site): {self.expected_total}")
        print(f"Total Pages:          {self.total_pages}")
        print(f"Successful (saved):   {self.total_facilities}")
        print(f"Failed:               {len(self.failed)}")
        print(f"Duplicates Removed:   {self.duplicates_removed}")
        print(f"Execution Time:       {elapsed:.1f}s")

        if self.failed:
            failed_path = os.path.join(OUTPUT_DIR, "failed.json")
            with open(failed_path, "w", encoding="utf-8") as f:
                json.dump(self.failed, f, ensure_ascii=False, indent=2)
            print(f"Failed items saved to: {failed_path}")

        self.save_progress(final=True)


async def main():
    scraper = TaqeemScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
