import os, httpx, json, csv, time, sys
from datetime import datetime
from pathlib import Path

ENV_PATH = Path(__file__).parent / 'sales-os' / '.env'
DB_ID = '38b69edd-f301-80e2-9a58-c4181d7c31ac'
CSV_PATH = Path(__file__).parent / 'rega_scraper' / 'REGA_Qualified_Companies.csv'
STATE_PATH = Path(__file__).parent / 'notion_push_state.json'

token = None
if ENV_PATH.exists():
    with open(ENV_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('NOTION_TOKEN='):
                token = line.split('=', 1)[1].strip().strip('"\'')
if not token:
    token = os.environ.get('NOTION_TOKEN')
if not token:
    print("ERROR: No Notion token found"); sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28',
}
client = httpx.Client(timeout=30)

ARABIC_MONTHS = {
    'يناير': '01', 'فبراير': '02', 'مارس': '03', 'إبريل': '04',
    'مايو': '05', 'يونيو': '06', 'يوليو': '07', 'أغسطس': '08',
    'سبتمبر': '09', 'أكتوبر': '10', 'نوفمبر': '11', 'ديسمبر': '12',
}

def parse_date(val):
    val = val.strip() if val else ''
    if not val or val == '-':
        return None
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    parts = val.split()
    if len(parts) == 3:
        day, month_ar, year = parts
        month_num = ARABIC_MONTHS.get(month_ar)
        if month_num:
            return f'{year}-{month_num}-{int(day):02d}'
    return None

def insert_page(row):
    name = row.get('Company Name', '').strip()
    if not name:
        return None

    props = {"Company Name": {"title": [{"text": {"content": name}}]}}

    status_val = row.get('Status', '').strip()
    if status_val:
        props["Status"] = {"select": {"name": status_val}}

    city_val = row.get('City', '').strip()
    if city_val:
        props["City"] = {"rich_text": [{"text": {"content": city_val}}]}

    lic_val = row.get('License Number', '').strip()
    if lic_val:
        props["License Number"] = {"rich_text": [{"text": {"content": lic_val}}]}

    lt_val = row.get('License Type', '').strip()
    if lt_val:
        props["License Type"] = {"select": {"name": lt_val}}

    qs_val = parse_date(row.get('Qualification Start', ''))
    if qs_val:
        props["Qualification Start"] = {"date": {"start": qs_val}}

    qe_val = parse_date(row.get('Qualification End', ''))
    if qe_val:
        props["Qualification End"] = {"date": {"start": qe_val}}

    data = {"parent": {"database_id": DB_ID}, "properties": props}
    return data

# Load state
state = {}
if STATE_PATH.exists():
    with open(STATE_PATH) as f:
        state = json.load(f)
inserted_licenses = set(state.get('inserted', []))
last_key = state.get('last_key', '')

print(f"Previously inserted: {len(inserted_licenses)} companies")

# Load CSV
with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
print(f"Total in CSV: {len(rows)}")

# Skip already inserted
to_insert = []
skipped = False
for row in rows:
    lic = row.get('License Number', '').strip()
    if lic in inserted_licenses:
        skipped = True
        continue
    to_insert.append(row)

if skipped:
    print(f"Skipping {len(rows) - len(to_insert)} already inserted, inserting {len(to_insert)} new")

# Insert with rate limiting
success, fail = 0, 0
batch_size = 3
for i in range(0, len(to_insert), batch_size):
    batch = to_insert[i:i+batch_size]
    for row in batch:
        lic = row.get('License Number', '').strip()
        data = insert_page(row)
        if not data:
            continue

        for attempt in range(3):
            r = client.post('https://api.notion.com/v1/pages', headers=HEADERS, json=data)
            if r.status_code == 200:
                success += 1
                inserted_licenses.add(lic)
                break
            elif r.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                fail += 1
                if fail <= 3:
                    print(f"  Error: {r.status_code} for {name[:30]}: {r.text[:100]}")
                break

    # Save progress every batch
    state = {'inserted': list(inserted_licenses), 'last_key': lic}
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False)

    if (i // batch_size) % 10 == 0 or i + batch_size >= len(to_insert):
        done = len(inserted_licenses)
        print(f"  Progress: {done}/{len(rows)} (ok={success}, fail={fail})")

    # Delay between batches to avoid rate limiting
    time.sleep(0.3)

print(f"\n=== DONE ===")
print(f"Total: {len(rows)}, New: {success}, Failed: {fail}, Total in DB: {len(inserted_licenses)}")
