#!/usr/bin/env python3
"""
Scraper for https://es.ncnp.gov.sa/v5/nonprofits/{ID}
IDs 1 → 9040
"""
import asyncio, csv, json, re, sys, time
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = OUTPUT_DIR / "progress.json"
MAX_ID = 9040
START_ID = 1
SEMAPHORE_LIMIT = 8
REQUEST_TIMEOUT = 45.0
MAX_RETRIES = 3

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ---------- Data Storage (append-based, disk-safe) ----------
class CSVWriter:
    def __init__(self, path, fieldnames):
        self.path = path
        self.fieldnames = fieldnames
        self.file = None
        self.writer = None
        self._open()

    def _open(self):
        exists = self.path.exists()
        self.file = open(self.path, "a", newline="", encoding="utf-8-sig")
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        if not exists:
            self.writer.writeheader()
            self.file.flush()

    def write(self, row):
        filtered = {k: row.get(k, "") for k in self.fieldnames}
        self.writer.writerow(filtered)
        self.file.flush()

    def close(self):
        if self.file:
            self.file.close()

# ---------- Progress ----------
def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("processed", [])), data.get("entities", [])
    return set(), []

def save_progress(processed_ids: set, entities: list):
    data = {
        "last_updated": datetime.now().isoformat(),
        "processed_count": len(processed_ids),
        "processed": sorted(processed_ids),
        "entities": entities[-10:] if entities else [],
    }
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- Parsing ----------
def extract_labeled_value(text: str, label: str) -> str:
    """Extract value after a label like 'الهاتف الرسمي : VALUE'.
    Uses newline boundaries to avoid matching across lines."""
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if label in line:
            m = re.search(rf"{re.escape(label)}\s*:\s*(.+)", line)
            if m:
                return m.group(1).strip()
    return ""

def parse_basic_info(soup: BeautifulSoup, entity_id: int) -> dict:
    info = {
        "Entity ID": entity_id,
        "Entity Name": "",
        "License Number": "",
        "Entity Type": "",
        "Supervising Authority": "",
        "Address": "",
        "Region": "",
        "City": "",
        "Postal Code": "",
        "Phone": "",
        "Mobile": "",
        "Fax": "",
        "Email": "",
        "Website": "",
        "PO Box": "",
        "Logo": "",
        "Governance Score": "",
    }

    # Entity Name (first card-title, skip "عودة")
    card_titles = soup.select(".card-title")
    for ct in card_titles:
        name = ct.get_text(strip=True)
        if name and name != "عودة":
            info["Entity Name"] = name
            break

    # Logo
    logo_img = soup.select_one(".square-img img.card-img")
    if logo_img:
        info["Logo"] = logo_img.get("src", "")

    # Main info details
    details = soup.select_one(".main-info-details")
    if not details:
        return info

    full_text = details.get_text("\n", strip=True)

    # Entity Type (span.tag)
    tag = details.select_one("span.tag")
    if tag:
        info["Entity Type"] = tag.get_text(strip=True)

    # License Number
    info["License Number"] = extract_labeled_value(full_text, "رقم الترخيص")

    # Supervising Authority
    info["Supervising Authority"] = extract_labeled_value(full_text, "جهة الاشراف")

    # Address (between license number and supervising authority)
    address_parts = []
    for p in details.select("p"):
        ptext = p.get_text(strip=True)
        if "رقم الترخيص" in ptext or "جهة الاشراف" in ptext:
            continue
        if ptext:
            address_parts.append(ptext)
    info["Address"] = " | ".join(address_parts)

    # Postal Code
    info["Postal Code"] = extract_labeled_value(full_text, "الرمز البريدي")

    # Region / City from address
    m = re.search(r"(منطقة\s*\S+)", info["Address"])
    if m:
        info["Region"] = m.group(1).strip()

    # Phone, Mobile, Email, Website, Fax, PO Box from list items
    for li in details.select("li a"):
        href = li.get("href", "")
        text = li.get_text(strip=True)
        if "tel:" in href:
            num = re.sub(r"\D", "", href.replace("tel:", ""))
            if not info["Phone"]:
                info["Phone"] = num
            else:
                info["Mobile"] = num
        elif "fax:" in href:
            info["Fax"] = href.replace("fax:", "")
        elif "mailto:" in href:
            info["Email"] = href.replace("mailto:", "")
        elif text.startswith("الموقع"):
            if href and href != "#":
                info["Website"] = href
        elif "ص.ب" in text:
            m = re.findall(r"[\d]+", text)
            if m:
                info["PO Box"] = m[0]

    # Line-based fallback extraction (more reliable than cross-line regex)
    if not info["Phone"]:
        info["Phone"] = extract_labeled_value(full_text, "الهاتف الرسمي")
    if not info["Email"]:
        info["Email"] = extract_labeled_value(full_text, "البريد الالكتروني")
    if not info["Fax"]:
        info["Fax"] = extract_labeled_value(full_text, "الفاكس")
    if not info["PO Box"]:
        info["PO Box"] = extract_labeled_value(full_text, "ص.ب")
    if not info["Website"]:
        v = extract_labeled_value(full_text, "الموقع الالكتروني")
        # Only set if it looks like a real URL
        if v and not v.startswith("الفاكس") and not v.startswith("ص.ب"):
            info["Website"] = v

    # Governance Score
    score_elem = soup.select_one("[class*='score'], [class*='rating'], [class*='governance']")
    if score_elem:
        info["Governance Score"] = score_elem.get_text(strip=True)
    m = re.search(r"(درجة|نسبة|Score)\s*(الحوكمة|Governance)[^\d]*(\d+[\d.]*)", full_text, re.IGNORECASE)
    if m:
        info["Governance Score"] = m.group(3)

    return info


def parse_members(soup: BeautifulSoup, entity_id: int) -> list:
    members = []
    member_section = soup.select_one("#memberInfo")
    if not member_section:
        return members
    table = member_section.select_one("table")
    if not table:
        return members
    rows = table.select("tbody tr")
    for row in rows:
        cols = row.select("td")
        if len(cols) < 4:
            continue
        name = cols[1].get_text(strip=True) if len(cols) > 1 else ""
        position = cols[2].get_text(strip=True) if len(cols) > 2 else ""
        role_cell = cols[3] if len(cols) > 3 else None
        role = ""
        if role_cell:
            role_text = role_cell.get_text(strip=True)
            if role_cell.select_one("img[src*='check-mark']"):
                role = "عضو مؤسس"
            elif role_text:
                role = role_text
        members.append({
            "Entity ID": entity_id,
            "Name": name,
            "Position": position,
            "Role": role,
            "Start Date": "",
            "End Date": "",
        })
    return members


def parse_documents(soup: BeautifulSoup, entity_id: int) -> list:
    docs = []
    doc_section = soup.select_one("#document")
    if not doc_section:
        return docs
    sections = doc_section.select("section.border")
    for section in sections:
        h4 = section.select_one("h4")
        if h4 and "لا توجد" in h4.get_text():
            continue
        # The h4 contains the document type name
        doc_type = h4.get_text(strip=True) if h4 else ""
        links = section.select("a[href]")
        for link in links:
            href = link.get("href", "")
            name_elem = link.select_one(".name")
            doc_name = name_elem.get_text(strip=True) if name_elem else doc_type
            docs.append({
                "Entity ID": entity_id,
                "Document Name": doc_name,
                "Document Type": doc_type,
                "Download URL": href if href.startswith("http") else f"https://es.ncnp.gov.sa{href}",
            })
    return docs


def parse_licenses(soup: BeautifulSoup, entity_id: int) -> list:
    licenses = []
    lic_section = soup.select_one("#donation")
    if not lic_section:
        return licenses
    sections = lic_section.select("section.border")
    for section in sections:
        link = section.select_one("a[href*='view_license']")
        if not link:
            continue
        href = link.get("href", "")
        name = link.get_text(strip=True) or "License"
        licenses.append({
            "Entity ID": entity_id,
            "License Number": "",
            "License Type": name,
            "Status": "",
            "Issue Date": "",
            "Expiry Date": "",
            "Download URL": href if href.startswith("http") else f"https://es.ncnp.gov.sa{href}",
        })
    return licenses


# ---------- HTTP Fetch ----------
async def fetch_entity(client: httpx.AsyncClient, sem: asyncio.Semaphore, entity_id: int) -> dict:
    async with sem:
        url = f"https://es.ncnp.gov.sa/v5/nonprofits/{entity_id}"
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.get(url, follow_redirects=True)
                return {"id": entity_id, "status": resp.status_code, "html": resp.text, "url": str(resp.url)}
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {"id": entity_id, "status": 0, "html": "", "url": url, "error": str(e)}


# ---------- Main Processing ----------
async def main():
    processed_ids, _ = load_progress()
    print(f"Resuming from progress: {len(processed_ids)} already processed")

    # Reopen CSV writers for each run
    entities_csv = CSVWriter(OUTPUT_DIR / "entities.csv",
        ["Entity ID", "Entity Name", "License Number", "Entity Type", "Supervising Authority",
         "Address", "Region", "City", "Postal Code", "Phone", "Mobile", "Fax", "Email",
         "Website", "PO Box", "Logo", "Governance Score"])
    members_csv = CSVWriter(OUTPUT_DIR / "members.csv",
        ["Entity ID", "Name", "Position", "Role", "Start Date", "End Date"])
    documents_csv = CSVWriter(OUTPUT_DIR / "documents.csv",
        ["Entity ID", "Document Name", "Document Type", "Download URL"])
    licenses_csv = CSVWriter(OUTPUT_DIR / "licenses.csv",
        ["Entity ID", "License Number", "License Type", "Status", "Issue Date", "Expiry Date", "Download URL"])
    errors_csv = CSVWriter(OUTPUT_DIR / "errors.csv",
        ["ID", "Status", "Error", "Timestamp"])

    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
    all_entities = []
    start_time = time.time()
    batch_size = 100

    async with httpx.AsyncClient(headers=HEADERS, timeout=httpx.Timeout(REQUEST_TIMEOUT)) as client:
        # Process IDs in batches for progress saving
        ids_to_process = [eid for eid in range(START_ID, MAX_ID + 1) if eid not in processed_ids]
        total_remaining = len(ids_to_process)
        print(f"Remaining: {total_remaining} entities")

        batch_tasks = []
        for idx, entity_id in enumerate(ids_to_process):
            batch_tasks.append(fetch_entity(client, sem, entity_id))

            # Process in batches
            if len(batch_tasks) >= batch_size or idx == total_remaining - 1:
                results = await asyncio.gather(*batch_tasks)
                for result in results:
                    eid = result["id"]
                    status = result["status"]
                    html = result["html"]
                    error = result.get("error", "")

                    if status == 200 and len(html) > 500:
                        soup = BeautifulSoup(html, "lxml")

                        entity = parse_basic_info(soup, eid)
                        members = parse_members(soup, eid)
                        documents = parse_documents(soup, eid)
                        lic_records = parse_licenses(soup, eid)

                        # Write to CSVs
                        entities_csv.write(entity)
                        for m in members:
                            members_csv.write(m)
                        for d in documents:
                            documents_csv.write(d)
                        for lr in lic_records:
                            licenses_csv.write(lr)

                        all_entities.append(entity)
                    else:
                        # Not found or error
                        error_row = {
                            "ID": eid,
                            "Status": status if status else "Error",
                            "Error": error or ("Not Found" if status == 404 else f"HTTP {status}"),
                            "Timestamp": datetime.now().isoformat(),
                        }
                        errors_csv.write(error_row)

                    processed_ids.add(eid)

                # Save progress periodically
                save_progress(processed_ids, all_entities)

                elapsed = time.time() - start_time
                done = len(processed_ids)
                rate = done / elapsed if elapsed > 0 else 0
                print(f"Progress: {done}/{MAX_ID} ({done/MAX_ID*100:.1f}%) | "
                      f"Rate: {rate:.1f}/s | Elapsed: {elapsed:.0f}s")

                batch_tasks = []

    # Final save
    save_progress(processed_ids, all_entities)

    # Close CSV writers
    for csvw in [entities_csv, members_csv, documents_csv, licenses_csv, errors_csv]:
        csvw.close()

    # Generate XLSX
    print("Generating XLSX files...")
    try:
        if (OUTPUT_DIR / "entities.csv").exists():
            df = pd.read_csv(OUTPUT_DIR / "entities.csv", encoding="utf-8-sig")
            df.to_excel(OUTPUT_DIR / "entities.xlsx", index=False, engine="openpyxl")
        if (OUTPUT_DIR / "members.csv").exists():
            df = pd.read_csv(OUTPUT_DIR / "members.csv", encoding="utf-8-sig")
            df.to_excel(OUTPUT_DIR / "members.xlsx", index=False, engine="openpyxl")
        if (OUTPUT_DIR / "documents.csv").exists():
            df = pd.read_csv(OUTPUT_DIR / "documents.csv", encoding="utf-8-sig")
            df.to_excel(OUTPUT_DIR / "documents.xlsx", index=False, engine="openpyxl")
        if (OUTPUT_DIR / "licenses.csv").exists():
            df = pd.read_csv(OUTPUT_DIR / "licenses.csv", encoding="utf-8-sig")
            df.to_excel(OUTPUT_DIR / "licenses.xlsx", index=False, engine="openpyxl")
        if (OUTPUT_DIR / "errors.csv").exists():
            df = pd.read_csv(OUTPUT_DIR / "errors.csv", encoding="utf-8-sig")
            df.to_excel(OUTPUT_DIR / "errors.xlsx", index=False, engine="openpyxl")
    except Exception as e:
        print(f"XLSX generation error: {e}")

    elapsed = time.time() - start_time
    print(f"\nDone! Processed {len(processed_ids)} entities in {elapsed:.0f}s ({len(processed_ids)/elapsed:.1f}/s)")
    print(f"Output files in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
