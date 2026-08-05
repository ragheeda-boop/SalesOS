"""Verify scraper output"""
import csv
import json

print("=" * 60)
print("SCRAPER OUTPUT VERIFICATION")
print("=" * 60)

# 1. Verify CSV
print("\n--- CSV Verification ---")
with open("engineering_offices_full.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"CSV rows: {len(rows)}")
print(f"Columns ({len(reader.fieldnames)}):")
for c in reader.fieldnames:
    print(f"  - {c}")

# Check required fields
required = [
    "office_name", "license_number", "region_city",
    "classification_grade", "classification_status",
    "phone", "mobile", "fax", "email", "website", "address"
]
print("\nRequired fields check:")
present = 0
for r in required:
    if r in reader.fieldnames:
        print(f"  [OK] {r}")
        present += 1
    else:
        print(f"  [FAIL] {r} MISSING")
print(f"{present}/{len(required)} required fields present")

# Duplicates
ids = [r["office_id"] for r in rows]
hashed = [r["hashed_office_id"] for r in rows]
print(f"\nDuplicate office_id: {len(ids) - len(set(ids))}")
print(f"Duplicate hashed_office_id: {len(hashed) - len(set(hashed))}")

# Field coverage
print("\nField coverage:")
for c in reader.fieldnames:
    non_null = sum(1 for r in rows if r.get(c, "").strip())
    print(f"  {c}: {non_null}/{len(rows)} ({non_null/len(rows)*100:.0f}%)")

# First 5 rows
print("\nFirst 5 rows:")
for i, r in enumerate(rows[:5]):
    print(f"  [{i+1}] id={r.get('office_id','')} | "
          f"name={r.get('office_name','')[:25]} | "
          f"lic={r.get('license_number','')} | "
          f"phone={r.get('phone','')} | "
          f"mobile={r.get('mobile','')} | "
          f"email={r.get('email','')[:25]}")

# 2. Verify JSON
print("\n--- JSON Verification ---")
with open("engineering_offices_full.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)
print(f"JSON records: {len(json_data)}")
print(f"JSON matches CSV: {len(json_data) == len(rows)}")

print("\n" + "=" * 60)
if len(rows) == 4904 and present == len(required) and len(ids) == len(set(ids)):
    print("VERDICT: PASS")
else:
    print("VERDICT: FAIL")
print("=" * 60)
