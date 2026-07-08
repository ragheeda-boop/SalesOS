import json, openpyxl, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

wb = openpyxl.load_workbook('CRM_Enriched_Final.xlsx')
ws2 = wb['FAILED_LOOKUPS']

# Show first 10 failed rows
print("=== FIRST 20 FAILED LOOKUPS ===")
count = 0
for r in ws2.iter_rows(min_row=2, values_only=True):
    if count >= 20:
        break
    name = str(r[1])[:40] if r[1] else ''
    print(f"{r[0]}: {name} | ws={r[2]} li={r[3]} | reason={r[4]}")
    count += 1

# Count how many have "Email domain" in reason
email_domain_failed = 0
others = 0
for r in ws2.iter_rows(min_row=2, values_only=True):
    if r[4] and 'Email domain' in str(r[4]):
        email_domain_failed += 1
    else:
        others += 1

print(f"\nFailed with 'Email domain': {email_domain_failed}")
print(f"Failed with other reasons: {others}")

# Show a sample of "Email domain" failed
print("\n=== SAMPLE 'EMAIL DOMAIN' FAILURES ===")
count = 0
for r in ws2.iter_rows(min_row=2, values_only=True):
    if r[4] and 'Email domain' in str(r[4]):
        name = str(r[1])[:40] if r[1] else ''
        print(f"{r[0]}: {name} | {r[4]}")
        count += 1
        if count >= 10:
            break
