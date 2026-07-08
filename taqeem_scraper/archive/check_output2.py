"""Check scraped output quality."""
import csv

with open("taqeem_scraper/taqeem_facilities.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"Total records: {len(rows)}\n")

# Classification distribution
classifications = {}
for r in rows:
    c = r.get("Classification", "") or "(empty)"
    classifications[c] = classifications.get(c, 0) + 1
print("Classification distribution:")
for c, n in sorted(classifications.items()):
    print(f"  {c}: {n}")

# Records where Classification == Status
print("\nRecords where Classification == Status (potential confusion):")
confused = [r for r in rows if r["Classification"] == r["Status"] and r["Classification"]]
for r in confused:
    print(f"  {r['Facility Name'][:55]} -> Class={r['Classification']}")

# CR number coverage
has_cr = sum(1 for r in rows if r["Commercial Registration"])
print(f"\nRecords with CR: {has_cr}/{len(rows)}")
has_membership = sum(1 for r in rows if r["Membership Number"])
print(f"Records with Membership: {has_membership}/{len(rows)}")
has_mobile = sum(1 for r in rows if r["Mobile"])
print(f"Records with Mobile: {has_mobile}/{len(rows)}")
has_email = sum(1 for r in rows if r["Email"])
print(f"Records with Email: {has_email}/{len(rows)}")

# Show a few sample records
print("\n=== Sample Record 1 ===")
for k, v in rows[0].items():
    if v:
        print(f"  {k}: {v}")

print("\n=== Sample Record 2 ===")
for k, v in rows[1].items():
    if v:
        print(f"  {k}: {v}")

print("\n=== Sample Record (no VFR) ===")
for r in rows:
    if not r["Classification"]:
        for k, v in r.items():
            if v:
                print(f"  {k}: {v}")
        break

print("\n=== Sample Record with VFR===")
for r in rows:
    if r["Classification"].startswith("VFR"):
        for k, v in r.items():
            if v:
                print(f"  {k}: {v}")
        break
