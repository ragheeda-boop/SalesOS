"""
Import scraped NCNP data into Notion database.
Uses the Notion API directly with the integration token.
"""
import os, csv, json, sys, time, random
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding='utf-8')

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = "38d69edd-f301-80a4-93d8-e226f9e2e7bf"
NOTION_API = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

OUTPUT_DIR = Path("output")


def update_database_schema():
    """Add properties to the database."""
    properties = {
        "Entity ID": {"number": {}},
        "License Number": {"rich_text": {}},
        "رقم الترخيص": {"rich_text": {}},
        "Entity Type": {"select": {"options": []}},
        "جهة الاشراف": {"rich_text": {}},
        "Region": {"select": {"options": []}},
        "City": {"rich_text": {}},
        "Phone": {"phone_number": {}},
        "Mobile": {"phone_number": {}},
        "Email": {"email": {}},
        "Website": {"url": {}},
        "PO Box": {"rich_text": {}},
        "Status": {"select": {"options": [
            {"name": "موجود", "color": "green"},
            {"name": "غير موجود", "color": "red"},
        ]}},
    }
    payload = {"properties": properties}
    r = httpx.patch(
        f"{NOTION_API}/databases/{DATABASE_ID}",
        headers=HEADERS,
        json=payload,
    )
    print(f"Schema update: {r.status_code}")
    if r.status_code != 200:
        print(r.text[:500])
    return r.status_code == 200


def get_existing_pages():
    """Get all existing page titles in the database."""
    existing = {}
    has_more = True
    start_cursor = None
    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        r = httpx.post(
            f"{NOTION_API}/databases/{DATABASE_ID}/query",
            headers=HEADERS, json=payload,
        )
        if r.status_code != 200:
            print(f"Query error: {r.text[:300]}")
            break
        data = r.json()
        for page in data.get("results", []):
            props = page.get("properties", {})
            title = ""
            for prop_name, prop_data in props.items():
                if prop_data.get("type") == "title":
                    title_parts = prop_data.get("title", [])
                    title = "".join(t.get("plain_text", "") for t in title_parts)
            existing[title] = page["id"]
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    print(f"Existing pages: {len(existing)}")
    return existing


def create_entity_page(client, entity: dict, members: list, licenses: list) -> bool:
    """Create a page in the Notion database for one entity."""
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            return _create_page(client, entity, members, licenses)
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = (2 ** attempt) + random.random()
                time.sleep(wait)
                continue
            print(f"  Failed after {MAX_RETRIES} attempts: {e}")
            return False


def _create_page(client, entity: dict, members: list, licenses: list) -> bool:
    entity_id_str = entity.get("Entity ID", "")
    try:
        entity_id_int = int(entity_id_str)
    except (ValueError, TypeError):
        entity_id_int = None

    name = entity.get("Entity Name", "")
    entity_type = entity.get("Entity Type", "")

    properties = {
        "الاسم": {"title": [{"text": {"content": name[:2000]}}]},
    }

    if entity_id_int is not None:
        properties["Entity ID"] = {"number": entity_id_int}

    for field, prop_name in [
        ("License Number", "License Number"),
        ("License Number", "رقم الترخيص"),
        ("Supervising Authority", "جهة الاشراف"),
        ("City", "City"),
        ("PO Box", "PO Box"),
    ]:
        val = entity.get(field, "").strip()
        if val:
            properties[prop_name] = {"rich_text": [{"text": {"content": val[:2000]}}]}

    phone = entity.get("Phone", "").strip()
    if phone:
        properties["Phone"] = {"phone_number": phone}
    mobile = entity.get("Mobile", "").strip()
    if mobile:
        properties["Mobile"] = {"phone_number": mobile}
    email = entity.get("Email", "").strip()
    if email:
        properties["Email"] = {"email": email}
    website = entity.get("Website", "").strip()
    if website and website.startswith("http"):
        properties["Website"] = {"url": website}
    if entity_type:
        properties["Entity Type"] = {"select": {"name": entity_type[:100]}}
    region = entity.get("Region", "").strip()
    if region:
        properties["Region"] = {"select": {"name": region[:100]}}
    properties["Status"] = {"select": {"name": "موجود"}}

    # Build content blocks
    blocks = []
    blocks.append({
        "object": "block", "type": "heading_2",
        "heading_2": {"rich_text": [{"text": {"content": "المعلومات الأساسية"}}]}
    })

    info_fields = [
        ("Entity ID", "رقم الكيان"), ("License Number", "رقم الترخيص"),
        ("Entity Type", "نوع الكيان"), ("Supervising Authority", "جهة الإشراف"),
        ("Address", "العنوان"), ("Region", "المنطقة"), ("City", "المدينة"),
        ("Postal Code", "الرمز البريدي"), ("Phone", "الهاتف"),
        ("Mobile", "الجوال"), ("Fax", "الفاكس"), ("Email", "البريد الإلكتروني"),
        ("Website", "الموقع الإلكتروني"), ("PO Box", "ص.ب"),
        ("Governance Score", "درجة الحوكمة"),
    ]
    for field_key, field_label in info_fields:
        val = entity.get(field_key, "").strip()
        if val:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": f"{field_label}: {val}"[:2000]}}]}
            })

    logo = entity.get("Logo", "").strip()
    if logo and logo.startswith("http"):
        blocks.append({
            "object": "block", "type": "image",
            "image": {"type": "external", "external": {"url": logo}}
        })

    if members:
        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "أعضاء الكيان"}}]}
        })
        for m in members:
            parts = [p for p in [m.get("Name"), m.get("Position"), m.get("Role")] if p]
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": " - ".join(parts)[:2000]}}]}
            })

    if licenses:
        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "التراخيص"}}]}
        })
        for lic in licenses:
            lic_url = lic.get("Download URL", "")
            lic_name = lic.get("License Type", "ترخيص")
            if lic_url:
                blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": lic_name, "link": {"url": lic_url}}}
                        ]
                    }
                })

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties,
        "children": blocks[:90],
    }

    r = client.post(f"{NOTION_API}/pages", json=payload, timeout=60)
    if r.status_code != 200:
        # Conflict = already exists
        if r.status_code == 409:
            return True
        print(f"  HTTP {r.status_code}: {r.text[:200]}")
        r.raise_for_status()

    page_id = r.json()["id"]
    remaining = blocks[90:]
    for i in range(0, len(remaining), 90):
        batch = remaining[i:i+90]
        r2 = client.patch(
            f"{NOTION_API}/blocks/{page_id}/children",
            json={"children": batch}, timeout=30,
        )
        if r2.status_code != 200:
            print(f"  Append blocks error: {r2.status_code}")
        time.sleep(0.05)
    return True


def main():
    NOTION_PROGRESS = OUTPUT_DIR / "notion_progress.json"

    print("1. Updating database schema...")
    update_database_schema()
    time.sleep(1)

    print("2. Loading CSV data...")
    entities = []
    with open(OUTPUT_DIR / "entities.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("Entity Name", "").strip():
                entities.append(row)

    members_by_entity = {}
    with open(OUTPUT_DIR / "members.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            eid = row.get("Entity ID", "")
            members_by_entity.setdefault(eid, []).append(row)

    licenses_by_entity = {}
    with open(OUTPUT_DIR / "licenses.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            eid = row.get("Entity ID", "")
            licenses_by_entity.setdefault(eid, []).append(row)

    print(f"   Entities: {len(entities)}, Members: {sum(len(v) for v in members_by_entity.values())}, "
          f"Licenses: {sum(len(v) for v in licenses_by_entity.values())}")

    # Load local progress
    created_set = set()
    if NOTION_PROGRESS.exists():
        with open(NOTION_PROGRESS, "r") as f:
            created_set = set(json.load(f).get("created_ids", []))
        print(f"   Previously created: {len(created_set)} pages")

    print("3. Creating pages...")
    created = len(created_set)
    errors = 0

    with httpx.Client(headers=HEADERS) as client:
        for idx, entity in enumerate(entities):
            eid = entity.get("Entity ID", "")

            if eid in created_set:
                continue

            members = members_by_entity.get(eid, [])
            lic = licenses_by_entity.get(eid, [])

            ok = create_entity_page(client, entity, members, lic)
            if ok:
                created += 1
                created_set.add(eid)
            else:
                errors += 1

            # Save progress every 10 entities
            if (idx + 1) % 10 == 0:
                with open(NOTION_PROGRESS, "w") as f:
                    json.dump({"created_ids": sorted(created_set), "count": len(created_set)}, f)

            # Rate limit: ~3 req/s = ~330ms per request
            time.sleep(0.35)

            if (idx + 1) % 50 == 0 or idx == len(entities) - 1:
                print(f"   {idx+1}/{len(entities)} | Created: {created} | Errors: {errors}")

    # Final progress save
    with open(NOTION_PROGRESS, "w") as f:
        json.dump({"created_ids": sorted(created_set), "count": len(created_set)}, f)

    print(f"\nDone! Created: {created} | Errors: {errors}")


if __name__ == "__main__":
    main()
