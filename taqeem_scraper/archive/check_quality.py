import json

with open("taqeem_scraper/progress.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]
dups = data["duplicates_removed"]

print(f"Total unique: {len(results)}")
print(f"Duplicates removed: {dups}")

class_dist = {}
for r in results:
    c = r.get("Classification", "") or "(empty)"
    class_dist[c] = class_dist.get(c, 0) + 1
print("\nClassification distribution:")
for k, v in sorted(class_dist.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

for field in ["Commercial Registration", "Membership Number", "Mobile", "Email"]:
    missing = sum(1 for r in results if not r.get(field))
    print(f"Missing {field}: {missing}/{len(results)}")

print("\n=== Sample records ===")
for r in results[:3]:
    n = r["Facility Name"]
    print(f"  Name: {n}")
    print(f'  CR: {r["Commercial Registration"]}')
    print(f'  Membership: {r["Membership Number"]}')
    print(f'  Classification: {r["Classification"]}')
    print(f'  Status: {r["Status"]}')
    print(f'  Region: {r["Region"]}')
    print(f'  Sector: {r["Sector"]}')
    print(f'  Valuation Fields: {r["Valuation Fields"]}')
    print(f'  Mobile: {r["Mobile"]}')
    print(f'  Email: {r["Email"]}')

with_license = sum(1 for r in results if r.get("License Number"))
print(f"\nWith License Number: {with_license}/{len(results)}")

with_phone = sum(1 for r in results if r.get("Phone"))
print(f"With Phone: {with_phone}/{len(results)}")

with_website = sum(1 for r in results if r.get("Website"))
print(f"With Website: {with_website}/{len(results)}")

with_gmaps = sum(1 for r in results if r.get("Google Maps"))
print(f"With Google Maps: {with_gmaps}/{len(results)}")
