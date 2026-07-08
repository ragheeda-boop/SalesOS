"""Check the quality of the scraped CSV output."""
import csv

with open("taqeem_scraper/taqeem_facilities.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"Total records: {len(rows)}")

# Classification distribution
classifications = {}
for r in rows:
    c = r.get("Classification", "") or "(empty)"
    classifications[c] = classifications.get(c, 0) + 1

print("\nClassification distribution:")
for c, n in sorted(classifications.items()):
    print(f"  {c}: {n}")

# Records where Classification == Status (potential confusion)
print("\nRecords where Classification == Status:")
for r in rows:
    if r["Classification"] == r["Status"] and r["Classification"]:
        print(f"  {r['Facility Name'][:55]} -> Class={r['Classification']}")

# Records with missing Commercial Registration
print("\nRecords with missing Commercial Registration:")
for r in rows:
    if not r["Commercial Registration"]:
        print(f"  {r['Facility Name'][:55]}")

# Show first record where Classification=Active
print("\nFirst record with Classification=Active:")
for r in rows:
    if r["Classification"] == "Active":
        for k, v in r.items():
            if v:
                print(f"  {k}: {v}")
        break

# Show first record with Classification=VFR3
print("\nFirst record with Classification=VFR3:")
for r in rows:
    if r["Classification"] == "VFR3":
        for k, v in r.items():
            if v:
                print(f"  {k}: {v}")
        break
