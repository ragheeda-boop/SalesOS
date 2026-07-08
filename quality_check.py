import json, openpyxl, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

companies = json.load(open('companies.json', encoding='utf-8'))

# Analyze email field quality
has_email = 0
has_personal_email = 0
has_corporate_email = 0
has_no_email = 0
email_is_name = 0  # Arabic text in email field

non_personal = {'gmail.com','hotmail.com','yahoo.com','outlook.com','live.com','mail.com','msn.com'}
personal_count = 0

for c in companies:
    em = (c.get('email') or '').strip()
    if not em:
        has_no_email += 1
    else:
        has_email += 1
        if '@' in em and em.count('@') == 1:
            domain = em.split('@')[1].lower()
            if domain in non_personal:
                personal_count += 1
                has_personal_email += 1
            else:
                has_corporate_email += 1
        else:
            email_is_name += 1

print("=== EMAIL FIELD QUALITY ===")
print(f"Total companies:        {len(companies)}")
print(f"With email field:       {has_email}")
print(f"  - Valid email:         {has_personal_email + has_corporate_email}")
print(f"    Corporate domain:    {has_corporate_email}")
print(f"    Personal domain:     {has_personal_email}")
print(f"  - Arabic text (name):  {email_is_name}")
print(f"    (in 'email' field,   - actual person name)")
print(f"No email at all:        {has_no_email}")

# Read the enriched sheet
wb = openpyxl.load_workbook('CRM_Enriched_Final.xlsx')
ws = wb['ENRICHED_COMPANIES']
ws2 = wb['FAILED_LOOKUPS']

print(f"\n=== ENRICHED COMPANIES ({ws.max_row - 1} rows) ===")
conf_dist = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    conf = r[3]  # ws_conf
    if conf is not None:
        conf_dist[conf] = conf_dist.get(conf, 0) + 1

print("Website confidence distribution:")
for k in sorted(conf_dist.keys()):
    print(f"  {k}%: {conf_dist[k]} companies")

li_conf_dist = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    conf = r[5]  # li_conf
    if conf and conf > 0:
        li_conf_dist[conf] = li_conf_dist.get(conf, 0) + 1

print("LinkedIn confidence distribution:")
for k in sorted(li_conf_dist.keys()):
    print(f"  {k}%: {li_conf_dist[k]} companies")

print(f"\n=== FAILED LOOKUPS ({ws2.max_row - 1} rows) ===")
# Count failure reasons
reasons = {}
for r in ws2.iter_rows(min_row=2, values_only=True):
    reason = r[4] or ''
    if 'No verifiable' in reason:
        reasons['No verifiable web presence'] = reasons.get('No verifiable web presence', 0) + 1
    elif 'Email domain' in reason:
        reasons['Has email domain but low quality'] = reasons.get('Has email domain but low quality', 0) + 1
    else:
        reasons['Other: ' + reason[:50]] = reasons.get('Other: ' + reason[:50], 0) + 1

print("Failure reasons breakdown:")
for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
