"""Import Balady Engineering Offices into Notion database"""
import os
import json
import time
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "salesos", "backend"))
from pipeline.notion import MuhideNotion

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = "38d69edd-f301-802c-b2cf-e385ad2a9961"

notion = MuhideNotion(NOTION_TOKEN) if NOTION_TOKEN else None

# ── 1. Update database schema ──────────────────────────────────
SCHEMA = {
    "properties": {
        "office_id": {"rich_text": {}},
        "hashed_office_id": {"rich_text": {}},
        "office_name": {"rich_text": {}},
        "license_number": {"rich_text": {}},
        "region_city": {"rich_text": {}},
        "classification_grade": {"rich_text": {}},
        "classification_status": {"select": {"options": [{"name": "مصنف", "color": "green"}, {"name": "غير مصنف", "color": "red"}]}},
        "mobile": {"phone_number": {}},
        "phone": {"phone_number": {}},
        "fax": {"phone_number": {}},
        "email": {"email": {}},
        "website": {"url": {}},
        "address": {"rich_text": {}},
        "contact_name": {"rich_text": {}},
        "latitude": {"number": {}},
        "longitude": {"number": {}},
        "logo_url": {"url": {}},
        "working_hours": {"rich_text": {}},
        "activities": {"rich_text": {}},
    }
}

def update_schema():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    resp = requests.patch(url, headers=HEADERS, json=SCHEMA)
    if resp.status_code == 200:
        print("OK Schema updated")
    else:
        print(f"✗ Schema update failed: {resp.status_code} {resp.text[:200]}")

# ── 2. Import records ──────────────────────────────────────────
def import_offices(offices):
    total = len(offices)
    created = 0
    errors = 0

    for idx, office in enumerate(offices, 1):
        props = {"الاسم": {"title": [{"text": {"content": office.get("office_name", "")[:100]}}]}}

        field_map = {
            "office_id": ("rich_text", office.get("office_id", "")),
            "hashed_office_id": ("rich_text", office.get("hashed_office_id", "")),
            "office_name": ("rich_text", office.get("office_name", "")),
            "license_number": ("rich_text", office.get("license_number", "")),
            "region_city": ("rich_text", office.get("region_city", "")),
            "classification_grade": ("rich_text", office.get("classification_grade", "")),
            "address": ("rich_text", office.get("address", "")),
            "contact_name": ("rich_text", office.get("contact_name", "")),
            "mobile": ("phone_number", office.get("mobile", "")),
            "phone": ("phone_number", office.get("phone", "")),
            "fax": ("phone_number", office.get("fax", "")),
            "email": ("email", office.get("email", "")),
            "website": ("url", office.get("website", "")),
            "logo_url": ("url", office.get("logo_url", "")),
        }

        for field, (ptype, val) in field_map.items():
            if not val:
                continue
            if ptype == "rich_text":
                props[field] = {"rich_text": [{"text": {"content": str(val)[:2000]}}]}
            elif ptype == "phone_number":
                props[field] = {"phone_number": str(val)}
            elif ptype == "email":
                props[field] = {"email": str(val)}
            elif ptype == "url":
                props[field] = {"url": str(val)}

        # Classification status
        cs = office.get("classification_status", "")
        if cs:
            props["classification_status"] = {"select": {"name": cs}}

        # Latitude/longitude
        lat = office.get("latitude")
        lng = office.get("longitude")
        if lat:
            try:
                props["latitude"] = {"number": float(lat)}
            except ValueError:
                pass
        if lng:
            try:
                props["longitude"] = {"number": float(lng)}
            except ValueError:
                pass

        # Working hours & activities as JSON
        wh = office.get("working_hours")
        if wh:
            props["working_hours"] = {"rich_text": [{"text": {"content": json.dumps(wh, ensure_ascii=False)[:2000]}}]}
        acts = office.get("activities")
        if acts:
            props["activities"] = {"rich_text": [{"text": {"content": json.dumps(acts, ensure_ascii=False)[:2000]}}]}

        data = {"parent": {"type": "database_id", "database_id": DATABASE_ID}, "properties": props}

        for attempt in range(5):
            try:
                resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=data)
                if resp.status_code == 200:
                    created += 1
                    break
                elif resp.status_code == 409:
                    print(f"  [{idx}] Conflict (duplicate), skipping")
                    created += 1
                    break
                elif resp.status_code == 429:
                    wait = 5 * (attempt + 1)
                    print(f"  [{idx}] Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    errors += 1
                    print(f"  [{idx}] Error {resp.status_code}: {resp.text[:100]}")
                    break
            except requests.RequestException as e:
                if attempt == 4:
                    errors += 1
                    print(f"  [{idx}] Failed after retries: {e}")
                else:
                    time.sleep(3)

        if idx % 50 == 0 or idx == total:
            pct = idx / total * 100
            eta_total = (time.time() - start_time) / idx * total if idx > 0 else 0
            eta_remaining = eta_total - (time.time() - start_time)
            print(f"  [{idx}/{total}] {pct:.1f}% | Created: {created} | Errors: {errors} | ETA: {eta_remaining/60:.0f}m")

    return created, errors

# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    with open("engineering_offices_full.json", "r", encoding="utf-8") as f:
        offices = json.load(f)
    print(f"Loaded {len(offices)} offices from JSON")

    print("\nStep 1: Updating database schema...")
    update_schema()

    print("\nStep 2: Importing records...")
    start_time = time.time()
    created, errors = import_offices(offices)
    elapsed = time.time() - start_time

    print(f"\n{'='*50}")
    print(f"Import complete!")
    print(f"  Total: {len(offices)}")
    print(f"  Created: {created}")
    print(f"  Errors: {errors}")
    print(f"  Time: {elapsed/60:.1f} minutes")
    print(f"  Rate: {created/elapsed:.1f} records/sec")
