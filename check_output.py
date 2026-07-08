import json, openpyxl, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

companies = json.load(open('companies.json', encoding='utf-8'))
for c in companies:
    if c['mid'] in ('COMP-000008', 'COMP-000025', 'COMP-000003', 'COMP-000001'):
        email = c.get('email', '') or ''
        print(f"{c['mid']}: email={email}")

wb = openpyxl.load_workbook('CRM_Enriched_Final.xlsx')
ws = wb['ENRICHED_COMPANIES']
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[0] in ('COMP-000008', 'COMP-000025'):
        print(f"ENRICHED: {r[0]}: ws={r[2]}|{r[3]}, li={r[4]}|{r[5]}")

ws2 = wb['FAILED_LOOKUPS']
for r in ws2.iter_rows(min_row=2, values_only=True):
    if r[0] in ('COMP-000008', 'COMP-000025'):
        print(f"FAILED: {r[0]}: ws={r[2]}, li={r[3]}, reason={r[4]}")

ws_enr = wb['ENRICHED_COMPANIES']
only_li = sum(1 for r in ws_enr.iter_rows(min_row=2, values_only=True) if r[8]=='No' and r[9]=='Yes')
both = sum(1 for r in ws_enr.iter_rows(min_row=2, values_only=True) if r[8]=='Yes' and r[9]=='Yes')
only_ws = sum(1 for r in ws_enr.iter_rows(min_row=2, values_only=True) if r[8]=='Yes' and r[9]=='No')
print(f"Website only: {only_ws}, LinkedIn only: {only_li}, Both: {both}, Total: {only_ws+only_li+both}")
