"""Final Production Smoke Test — Complete User Journey"""
import requests, json, time

BASE = "http://localhost:8000"
TID = "ba73a0e7-7a12-4f5d-9c8e-012345678901"
UID = "d7966ba5-85a4-4b31-8bd0-c61c4b34b4ac"
PASS = 0; FAIL = 0; SKIP = 0

def test(name, fn, skip=False):
    global PASS, FAIL, SKIP
    if skip:
        SKIP += 1; print(f"  [SKIP] {name} — CONFIGURATION REQUIRED"); return None
    t0 = time.time()
    try:
        r = fn(); dur = round((time.time()-t0)*1000)
        if hasattr(r, 'status_code') and r.status_code >= 400:
            FAIL += 1; print(f"  [FAIL] {name} ({dur}ms) HTTP {r.status_code}: {r.text[:100]}"); return None
        PASS += 1; print(f"  [PASS] {name} ({dur}ms)"); return r
    except Exception as e:
        FAIL += 1; print(f"  [FAIL] {name} ({round((time.time()-t0)*1000)}ms): {str(e)[:100]}"); return None

print("=" * 60)
print("SALESOS PRODUCTION SMOKE TEST — End-to-End User Journey")
print("=" * 60)

# ══ LOGIN ══
print("\n1. LOGIN")
r = test("Login as ragheed.a@muhide.com", lambda: requests.post(f"{BASE}/api/v1/identity/login", json={"email":"ragheed.a@muhide.com","password":"Muhide2026!"}))
TOKEN = r.json()["access_token"] if r else None
H = {"Authorization": f"Bearer {TOKEN}", "X-Tenant-Id": TID} if TOKEN else {}

# ══ HEALTH ══
print("\n2. INFRASTRUCTURE HEALTH")
health = test("GET /health", lambda: requests.get(f"{BASE}/health"))
if health:
    h = health.json()
    print(f"    DB={h['database']} Redis={h['redis']} Graph={h['graph']} Version={h['version']}")

# ══ EMPLOYEE360 ══
print("\n3. EMPLOYEE360 DASHBOARD")
dash = test("GET /api/v1/employees/me/360", lambda: requests.get(f"{BASE}/api/v1/employees/me/360", headers=H, timeout=20))
if dash:
    d = dash.json()
    print(f"    Profile: {d['profile']['full_name']} ({d['profile']['role']})")
    print(f"    KPIs: revenue={d['kpis']['revenue']} pipeline={d['kpis']['pipeline']} win_rate={d['kpis']['win_rate']}")
    print(f"    AI Coach: {len(d['ai_coach'])} actions")
    for a in d['ai_coach']:
        print(f"      [{a['priority']}] {a['title']}")
    print(f"    Calendar: today={d['calendar_intelligence']['today_count']} week={d['calendar_intelligence']['week_count']}")
    print(f"    Email: sent={d['email_intelligence']['sent']} received={d['email_intelligence']['received']}")

# ══ SEARCH ══
print("\n4. SEARCH ENGINE")
test("Meilisearch health", lambda: requests.get("http://localhost:7700/health"))
search = test("Arabic search for شركة", lambda: requests.post("http://localhost:7700/indexes/companies/search", json={"q":"شركة","limit":3}, headers={"Authorization":"Bearer muhide-search-key-2026","Content-Type":"application/json"}))
if search:
    s = search.json()
    print(f"    Hits: {s['estimatedTotalHits']} | Processing: {s['processingTimeMs']}ms")

# ══ SCORE + SIGNALS ══
print("\n5. EMPLOYEE SCORING")
test("GET /employees/{id}/score", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/score", headers=H))
test("GET /employees/{id}/signals", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/signals", headers=H))

# ══ CALENDAR + EMAIL KPIs ══
print("\n6. CALENDAR & EMAIL KPIs")
test("GET calendar-kpis", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/calendar-kpis", headers=H))
test("GET email-kpis", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/email-kpis?days=7", headers=H))

# ══ PRODUCTIVITY ══
print("\n7. PRODUCTIVITY")
prod = test("GET productivity", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/productivity?period_days=30", headers=H))
if prod:
    p = prod.json()
    print(f"    Score: {p['productivity_score']} | Burnout: {p['burnout_risk']} | Trend: {p['trend_direction']}")

# ══ EXECUTIVE ══
print("\n8. EXECUTIVE DASHBOARD")
exec_r = test("GET /executive/summary", lambda: requests.get(f"{BASE}/api/v1/executive/summary", headers=H))
if exec_r:
    e = exec_r.json()
    print(f"    Total: {e['total_employees']} | Active: {e['active_employees']} | Avg Score: {e['avg_score']}")
    print(f"    Departments: {len(e['departments'])} | Top Performers: {len(e['top_performers'])}")

# ══ INTEGRATIONS ══
print("\n9. EXTERNAL INTEGRATIONS")
test("Google OAuth connected", None, skip=True)
test("Microsoft OAuth connected", None, skip=True)
test("OpenAI LLM configured", None, skip=True)

# ══ BACKEND API INVENTORY ══
print("\n10. FULL API INVENTORY")
apis = [
    ("GET /ping", lambda: requests.get(f"{BASE}/ping")),
    ("GET /health", lambda: requests.get(f"{BASE}/health")),
    ("GET /health/live", lambda: requests.get(f"{BASE}/health/live")),
    ("GET /health/employee-360", lambda: requests.get(f"{BASE}/health/employee-360")),
    ("GET /employees/me/360", lambda: requests.get(f"{BASE}/api/v1/employees/me/360", headers=H, timeout=20)),
    ("GET /employees/{id}/score", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/score", headers=H)),
    ("GET /employees/{id}/signals", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/signals", headers=H)),
    ("GET /employees/{id}/timeline", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/timeline", headers=H)),
    ("GET /employees/{id}/performance", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/performance", headers=H)),
    ("GET /employees/{id}/calendar-kpis", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/calendar-kpis", headers=H)),
    ("GET /employees/{id}/email-kpis", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/email-kpis", headers=H)),
    ("GET /employees/{id}/productivity", lambda: requests.get(f"{BASE}/api/v1/employees/{UID}/productivity", headers=H)),
    ("GET /executive/summary", lambda: requests.get(f"{BASE}/api/v1/executive/summary", headers=H)),
]
for name, fn in apis:
    test(name, fn)

# ══ FINAL RESULT ══
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} PASS | {FAIL} FAIL | {SKIP} SKIP (configuration required)")
total = PASS + FAIL + SKIP
pct = round(PASS / max(1, PASS + FAIL) * 100)
print(f"OPERATIONAL RATE: {pct}% of executable tests passed")

if FAIL == 0 and SKIP <= 3:
    print("\nDECISION: ENGINEERING GO — All code-level tests pass. Only external credentials remain.")
elif FAIL == 0:
    print(f"\nDECISION: CONDITIONAL GO — {PASS} pass, {SKIP} require configuration")
else:
    print(f"\nDECISION: NO GO — {FAIL} tests failed")
print("=" * 60)
