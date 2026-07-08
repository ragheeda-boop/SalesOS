import csv
import os
import re
from collections import Counter

filepath = "LeadOpportunity (crm.lead).csv"

if not os.path.exists(filepath):
    print(f"File not found: {filepath}")
    print("Place the CSV file in the same directory as this script and re-run.")
    exit(1)

with open(filepath, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total raw rows: {len(rows)}")
print(f"Columns: {list(rows[0].keys())}")

# Extract company names
companies = []
for row in rows:
    opp = (row.get('Opportunity') or '').strip()
    if opp:
        companies.append(opp)

unique_companies = set(companies)
name_counts = Counter(companies)
dups = {k: v for k, v in name_counts.items() if v > 1}

rows_with_company = [r for r in rows if (r.get('Opportunity') or '').strip()]

missing_website = len(rows_with_company)
missing_linkedin = len(rows_with_company)
missing_industry = len(rows_with_company)
missing_contact_count = sum(1 for r in rows_with_company if not (r.get('Contact Name') or '').strip())
missing_email_count = sum(1 for r in rows_with_company if not (r.get('Email') or '').strip())
missing_phone_count = sum(1 for r in rows_with_company if not (r.get('Phone') or '').strip())

print(f"\n=== Phase 1: Data Audit ===")
print(f"Total Records with company names: {len(companies)}")
print(f"Unique Company Names: {len(unique_companies)}")
print(f"Duplicate Occurrences: {len(companies) - len(unique_companies)}")
print(f"Companies with duplicates: {len(dups)}")
print(f"\nMissing Website: {missing_website} ({100*missing_website/len(rows_with_company):.1f}%)")
print(f"Missing LinkedIn: {missing_linkedin} ({100*missing_linkedin/len(rows_with_company):.1f}%)")
print(f"Missing Industry: {missing_industry} ({100*missing_industry/len(rows_with_company):.1f}%)")
print(f"Missing Contact Name: {missing_contact_count} ({100*missing_contact_count/len(rows_with_company):.1f}%)")
print(f"Missing Email: {missing_email_count} ({100*missing_email_count/len(rows_with_company):.1f}%)")
print(f"Missing Phone: {missing_phone_count} ({100*missing_phone_count/len(rows_with_company):.1f}%)")

print(f"\n=== Duplicate Companies ===")
for name, count in sorted(dups.items(), key=lambda x: -x[1]):
    print(f"  [{count}x] {name}")

print(f"\n=== Sample Companies (first 20) ===")
for c in list(unique_companies)[:20]:
    print(f"  {c}")
