import json

with open("taqeem_facilities.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total records: {len(data)}")

with_cr = sum(1 for r in data if r.get("Commercial Registration"))
vfr = sum(1 for r in data if r.get("Classification", "").startswith("VFR"))
with_mobile = sum(1 for r in data if r.get("Mobile"))
with_email = sum(1 for r in data if r.get("Email"))
with_status = sum(1 for r in data if r.get("Status"))
with_membership = sum(1 for r in data if r.get("Membership Number"))
with_type = sum(1 for r in data if r.get("Facility Type"))
with_sector = sum(1 for r in data if r.get("Sector"))
with_region = sum(1 for r in data if r.get("Region"))
with_address = sum(1 for r in data if r.get("Address"))

print(f"With CR Number:      {with_cr}")
print(f"With Membership:     {with_membership}")
print(f"With Type:           {with_type}")
print(f"With Status:         {with_status}")
print(f"With Sector:         {with_sector}")
print(f"With Region:         {with_region}")
print(f"With Email:          {with_email}")
print(f"With Mobile:         {with_mobile}")
print(f"With Address:        {with_address}")
print(f"VFR Classification:  {vfr}")

class_dist = {}
for r in data:
    c = r.get("Classification", "") or "(empty)"
    class_dist[c] = class_dist.get(c, 0) + 1
print("\nClassification distribution:")
for k, v in sorted(class_dist.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print("\nSample records:")
for r in data[:3]:
    print(f"  Name:   {r['Facility Name']}")
    print(f"  CR:     {r['Commercial Registration']}")
    print(f"  Mem#:   {r['Membership Number']}")
    print(f"  Class:  {r['Classification']}")
    print(f"  Status: {r['Status']}")
    print(f"  Sector: {r['Sector']}")
    print(f"  Mobile: {r['Mobile']}")
    print(f"  Email:  {r['Email']}")
    print()
