"""
Run completeness_scorer on ALL suppliers.
Usage: python run_on_suppliers.py
Reads NOTION_TOKEN from .env file or environment variable.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from notion_api import MuhideNotion, set_number
from completeness_scorer import calculate_score

TOKEN = os.environ.get("NOTION_TOKEN")
if not TOKEN:
    print("ERROR: Set NOTION_TOKEN in .env file or environment variable")
    sys.exit(1)

n = MuhideNotion(TOKEN)
DB_ID = "a4daa26b-89ca-4ef9-89e4-c24f33e5b765"

print("Loading all suppliers (may take a while)...", flush=True)
t0 = time.time()
pages = n.get_all_pages(DB_ID, page_size=100)
t1 = time.time()
print(f"Loaded {len(pages)} records in {t1-t0:.0f}s", flush=True)

updated = 0
errors = 0
t2 = time.time()
for i, page in enumerate(pages):
    props = page["properties"]
    score = calculate_score(props, "suppliers")
    try:
        n.update_page(page["id"], {"Data Completeness Score": set_number(float(score))})
        updated += 1
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"  Error [{page['id'][:12]}]: {e}", flush=True)
    if (i + 1) % 200 == 0:
        elapsed = time.time() - t2
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        print(f"  {i+1}/{len(pages)} updated ({rate:.1f} rec/s, {elapsed:.0f}s)", flush=True)

t3 = time.time()
total = t3 - t0
print(f"\nResults:", flush=True)
print(f"  Updated: {updated}", flush=True)
print(f"  Errors: {errors}", flush=True)
print(f"  Total time: {total:.0f}s", flush=True)

scores = [calculate_score(p["properties"], "suppliers") for p in pages]
avg = sum(scores) / len(scores) if scores else 0
complete = sum(1 for s in scores if s == 100)
poor = sum(1 for s in scores if s < 40)
print(f"  Avg score: {avg:.1f}/100", flush=True)
print(f"  Complete (100): {complete}", flush=True)
print(f"  Poor (< 40): {poor}", flush=True)
print("\nDONE!", flush=True)
