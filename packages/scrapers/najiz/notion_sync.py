import os
import json
import asyncio
import aiohttp
import requests
from pathlib import Path

API_KEY = os.environ.get("NOTION_TOKEN")
DATABASE_ID = "38b69edd-f301-80f1-8e18-e674ee8f417c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}
BASE = "https://api.notion.com/v1"
DATA_FILE = Path(__file__).parent / "data" / "lawyers.json"
PROGRESS_FILE = Path(__file__).parent / "data" / "notion_progress.json"
MAX_RETRIES = 5

PROPERTY_TYPES = {
    "mobile_number": "rich_text",
    "city": "rich_text",
    "office_name": "rich_text",
    "office_city": "rich_text",
    "office_region": "rich_text",
    "office_street": "rich_text",
    "license_status": "rich_text",
    "license_number": "rich_text",
    "license_expiry_date_hijri": "rich_text",
    "certificate": "rich_text",
    "faculty": "rich_text",
    "specialty": "rich_text",
    "nationality": "rich_text",
    "email": "email",
}


def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


def update_database_schema():
    properties = {}
    for prop_name, prop_type in PROPERTY_TYPES.items():
        if prop_type == "email":
            properties[prop_name] = {"email": {}}
        else:
            properties[prop_name] = {"rich_text": {}}
    url = f"{BASE}/databases/{DATABASE_ID}"
    resp = requests.patch(url, headers=HEADERS, json={"properties": properties})
    if resp.status_code == 200:
        safe_print(f"Database schema updated with {len(properties)} properties")
        return True
    else:
        safe_print(f"Failed to update schema: {resp.status_code} {resp.text[:300]}")
        return False


def make_properties(record):
    props = {
        "\u0627\u0644\u0627\u0633\u0645": {
            "title": [{"text": {"content": record.get("full_name", "") or ""}}]
        }
    }
    email = (record.get("email", "") or "").strip()
    if email:
        props["email"] = {"email": email}
    text_fields = [
        "mobile_number", "city", "office_name", "office_city", "office_region",
        "office_street", "license_status", "license_number",
        "license_expiry_date_hijri", "certificate", "faculty", "specialty",
        "nationality",
    ]
    for field in text_fields:
        val = (record.get(field, "") or "").strip()
        if val:
            props[field] = {"rich_text": [{"text": {"content": val}}]}
    return props


async def create_page_async(session, record, sem, idx):
    props = make_properties(record)
    payload = {
        "parent": {"type": "database_id", "database_id": DATABASE_ID},
        "properties": props,
    }
    for attempt in range(MAX_RETRIES):
        async with sem:
            try:
                async with session.post(
                    f"{BASE}/pages",
                    headers=HEADERS,
                    json=payload,
                ) as resp:
                    if resp.status == 200:
                        safe_print(f"  [{idx}] OK")
                        return True
                    elif resp.status == 409:
                        safe_print(f"  [{idx}] Conflict (duplicate), skipping")
                        return True
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 5))
                        safe_print(f"  [{idx}] Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        body = await resp.text()
                        safe_print(f"  [{idx}] Error {resp.status}: {body[:200]}")
                        if attempt < MAX_RETRIES - 1:
                            wait = 2 ** attempt
                            safe_print(f"    Retry in {wait}s...")
                            await asyncio.sleep(wait)
                        else:
                            safe_print(f"    Giving up")
                            return False
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                safe_print(f"  [{idx}] Connection error: {e}")
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    safe_print(f"    Retry in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    return False
    return False


async def main():
    safe_print("Loading data...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)
    total_records = len(records)
    safe_print(f"Loaded {total_records} records")

    progress = {"completed": 0, "failed": 0, "last_index": -1}
    start_index = 0
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            start_index = saved.get("last_index", -1) + 1
            progress = saved
        safe_print(f"Resuming from index {start_index} "
              f"(completed={progress['completed']}, failed={progress['failed']})")
    else:
        safe_print("Starting fresh")
        safe_print("Updating database schema...")
        if not update_database_schema():
            safe_print("Schema update failed, aborting")
            return
        safe_print("Schema update complete")

    remaining = records[start_index:]
    safe_print(f"Remaining records to process: {len(remaining)}")

    sem = asyncio.Semaphore(3)
    connector = aiohttp.TCPConnector(limit=10)
    failed_list = []

    async with aiohttp.ClientSession(connector=connector) as session:
        for i, record in enumerate(remaining):
            idx = start_index + i + 1
            ok = await create_page_async(session, record, sem, idx)
            if ok:
                progress["completed"] += 1
            else:
                progress["failed"] += 1
                failed_list.append((idx, record.get("full_name", ""), record.get("license_number", "")))
            progress["last_index"] = idx - 1

            if (idx) % 10 == 0:
                with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump(progress, f, ensure_ascii=False)

            await asyncio.sleep(0.35)

    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False)

    safe_print(f"\n{'='*50}")
    safe_print(f"Done! Completed: {progress['completed']}, Failed: {progress['failed']}")
    if failed_list:
        safe_print(f"\nFailed records ({len(failed_list)}):")
        for idx, name, lic in failed_list[:20]:
            safe_print(f"  #{idx}: {name} ({lic})")
        if len(failed_list) > 20:
            safe_print(f"  ... and {len(failed_list) - 20} more")


if __name__ == "__main__":
    asyncio.run(main())
