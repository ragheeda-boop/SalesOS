# False Negative Analysis

**Rule:** A false negative occurs when the previous auditor claimed "no evidence" or "missing" but evidence exists in the repository.

Every false negative below includes: exact repository path, evidence contents, and why the previous conclusion is incorrect.

---

## FN-1: `fe-build.log` — MAJOR

**Original claim (03-missing-evidence.md, Section 2):**  
> `docs/audit/ga-engineering-audit/fe-build.log` (Wave 4 FE image): **MISSING**

**Original claim (04-false-claims.md, F4):**  
> Cited `fe-build.log` **MISSING**

**Original claim (02-wave-verification.md, Wave 4):**  
> `docker compose build frontend` exit 0 — Cited `fe-build.log` **MISSING**

**Evidence location:**  
`docs\audit\ga-engineering-audit\fe-build.log` — 427,926 bytes, 1,347 lines

**Evidence contents (verified 2026-07-23):**  
- Full `docker compose build frontend` redirected stdout+stderr  
- Shows Docker buildx multi-stage build: `FROM node:22-alpine`, npm install, `next build`, multi-stage production image  
- Final lines:
```
#19 naming to docker.io/library/salesos-frontend:local
#19 unpacking to docker.io/library/salesos-frontend:local 7.1s done
 Image salesos-frontend:local Built
```
- Build completed successfully; image `salesos-frontend:local` tagged and available

**Why incorrect:**  
The file exists at the EXACT path cited by the auditor (`docs/audit/ga-engineering-audit/fe-build.log`). It was readable at audit time. The auditor either failed to check this path or had a file-read error. This is a direct false negative.

**Caveat:**  
The fe-build.log proves `docker compose build frontend` succeeded (Docker-level). It does NOT prove separate `npm run lint`, `npx tsc --noEmit`, or `npm run build` exit-0 on the host. Those commands run inside Docker as part of the build process (`next build` includes TypeScript compilation). The log IS evidence, but it maps to the Docker build claim (Wave 4), not fully to the host-level command claims (Wave 0).

**Corrected classification for Wave 4 `docker compose build frontend`:**  
🟡 **PARTIALLY VERIFIED** (log exists, build succeeded, but only covers Docker path)

---

## FN-2: `evidence/wave12-gates/` — DIRECTORY MISSING

**Original claim (03-missing-evidence.md, Section 1):**  
> `evidence/wave12-gates/` — **MISSING** (cited from migrate-prep)

**Note:** The auditor's own Section 1 contradicts its "Present" list which includes `wave12-gates`.

**Evidence location:**  
`docs\audit\ga-engineering-audit\evidence\wave12-gates\`

**Directory contents (verified 2026-07-23):**

| File | Type |
|------|------|
| `gate-rerun-2026-07-22T1303Z.log` | Gate rerun log |
| `gate-rerun-2026-07-22T1305Z.log` | Gate rerun log |
| `gate-rerun-2026-07-22T1306Z.log` | Gate rerun log |
| `gate-rerun-2026-07-22T1307Z.log` | Gate rerun log |

**Evidence contents (gate-rerun-T1307Z.log, verified):**
```
============================================
  SalesOS Pre-Deploy Gates (Wave 12)
  2026-07-22 13:06:15
  Classification: NOT Production GO
============================================

[1/4] SALESOS_TESTING trap check
  [PASS] SALESOS_TESTING (host) - unset/empty (safe)
  [PASS] SALESOS_TESTING (container) - unset/empty (safe)
[2/4] Alembic current == heads
  [PASS] Alembic drift - alembic current: ['0039'] | alembic heads: ['0039'] | OK
[3/4] Health endpoint
  [PASS] /health - HTTP 200; status ok
[4/4] Unit pytest (optional)
  [SKIP] Unit pytest - pass -RunUnitTests to enable
[advisory] jsonschema import
  [PASS] jsonschema (container) - import ok

--------------------------------------------
  Passed: 5  Failed: 0  Warnings: 0
  RESULT: PASS (gates green; still not Production GO)
--------------------------------------------
```

**Why incorrect:**  
The directory exists with 4 log files, all containing PASS results. The auditor's classification of this folder as "MISSING" is factually false. The auditor appears to have a self-contradiction — the same document lists it under "Present" while also listing it under "MISSING."

**Corrected classification for Wave 12 gate-rerun logs:**  
✅ **VERIFIED** (gates passed locally; `Passed: 5, Failed: 0` in all 4 runs)

---

## FN-3: `gates-rerun` log in migrate-prep

**Original claim (03-missing-evidence.md, Section 2):**  
> `gates-rerun-*.log` under migrate-prep — **MISSING** (only 3 JSON files in migrate-prep)

**Evidence location:**  
`docs\audit\ga-engineering-audit\evidence\wave12-migrate-prep\`

**Directory contents (verified 2026-07-23):**

| File | Type | Status |
|------|------|--------|
| `local-verify-2026-07-22T124003Z.json` | JSON | Present |
| `local-verify-2026-07-22T124003Z.log` | LOG | Present |
| `local-verify-2026-07-22T131700Z.json` | JSON | Present |
| `gates-rerun-2026-07-22T124305Z.log` | LOG | Present |
| `SUMMARY.json` | JSON | Present |

Total: **5 files** (3 JSON + 2 LOG), not "only 3 JSON files"

**Why incorrect:**  
The auditor counted only JSON files, missing the 2 `.log` files. The `gates-rerun-2026-07-22T124305Z.log` exists and contains:
```
Passed: 5  Failed: 0  Warnings: 0
RESULT: PASS (gates green; still not Production GO)
```
with Alembic at head 0039 (pre-0040 session), SALEOS_TESTING clear, health 200.

**Corrected classification:**  
✅ **VERIFIED** (gates-rerun log present; gate PASS evidence exists)

---

## FN-4: Playwright HTML report

**Original claim (03-missing-evidence.md, Section 2):**  
> Playwright HTML report under `evidence/wave13-*`: **MISSING**

**Evidence location:**  
`salesos\frontend\playwright-report\index.html` — 90 lines, 1.2MB minified React app

**Evidence contents:**  
Complete Playwright HTML test report (React-based viewer). Renders interactive test report with pass/fail results, timeline, trace viewer.

**Why partially incorrect:**  
The claim that the report is "not under evidence/wave13-*" is **technically correct** — the report was NOT copied to the evidence folder. However, the report DOES exist in the repository at `salesos/frontend/playwright-report/`. The auditor's phrasing implies the report doesn't exist at all. A more precise statement would be: "Report exists in project tree but was not archived to evidence/."

**Corrected classification:**  
🟡 **PARTIALLY VERIFIED** — Report exists in repo, not in evidence folder. Should have been noted.

---

## FN-5: Wave 2 "false-PASS" classification — OVERLY STRICT

**Original claim (04-false-claims.md, F2):**  
> Wave 2 load matrix overall PASS with HTTP 500s inside — 🟡 false-PASS / PARTIALLY VERIFIED at best

**Evidence (probe-summary-2026-07-22T125056Z.json):**
```json
{
  "overall": "PASS",
  "pass": 26,
  "fail": 0,
  "note": "probe-wave2-load.ps1 hit ArgumentException building summary object after all checks; this file reconstructed from console + sibling evidence JSONs",
  "competitors_network_http": {
    "competitors": 500,
    "network": 500,
    "cause": "UndefinedTableError: relation graph_edges does not exist (SQL fallback path after Neo4j miss / empty)"
  },
  "validation_label": "light validated",
  "production_secure_claim": false
}
```

**Analysis:**  
The probe is self-documenting and honest. It declares `production_secure_claim: false` and `validation_label: light validated`. The 500s on competitors/network are caused by `graph_edges` table missing (pre-Alembic 0040), not a security probe failure. The 26/26 PASS covers SSRF deny, tenant isolation, health, burst checks. The auditor's "false-PASS" label is **overly strict** but not factually wrong — a PASS with hidden 500s in sibling data could mislead. The probe's own documentation mitigates this concern.

**Corrected classification:**  
🟡 **PARTIALLY VERIFIED** — The probe JSON is honest and self-labeling. The auditor's confidence of 50% is too low; should be **65-75%** given the probe's transparent documentation.

---

## FN-6: Prometheus alert job name — OVERSTATED SEVERITY

**Original claim (04-false-claims.md, F6):**
> Wave 8 alert job name vs root Prometheus scrape job: 🚨 CONTRADICTED for root compose path; split-brain risk

**Analysis:**  
- prometheus.yml (salesos compose): `job_name: "salesos-backend"` — **matches** alerts.yml `up{job="salesos-backend"}`
- prometheus.compose-root.yml: `job_name: "salesos-api"` — **does not match** alerts
- The root compose file header says: "Local/dev: scrapes without Bearer... SalesOS app compose uses prometheus.yml + prometheus-token instead."

The root compose is a **dev-only alternative**, not the production path. The actual salesos compose Prometheus config matches alerts perfectly. The alert mismatch only affects the dev root compose path, which the documentation explicitly distinguishes from the app path. "Split-brain risk" overstates the problem — root compose is not a production configuration.

**Corrected classification:**  
🟡 **PARTIALLY VERIFIED** — Technical observation is correct (name mismatch exists for root compose), but severity is over-stated. The salesos compose path matches correctly. No production risk.

---

## Summary: All false negatives

| ID | Item | Original claim | Actual evidence | Severity |
|----|------|---------------|-----------------|----------|
| FN-1 | fe-build.log | MISSING | Exists at cited path; 427KB Docker build success | **HIGH** |
| FN-2 | wave12-gates/ folder | MISSING | Exists with 4 PASS gate-rerun logs | **MEDIUM** |
| FN-3 | migrate-prep gates-rerun | MISSING (only 3 JSON) | 5 files total including gates-rerun.log | **LOW** |
| FN-4 | Playwright HTML report | MISSING under evidence | Exists in `salesos/frontend/playwright-report/` | **LOW** |
| FN-5 | Wave 2 "false-PASS" | Overly strict | Probe documents residuals and declares `production_secure_claim: false` | **LOW** |
| FN-6 | Alert job "split-brain" | Over-stated severity | Mismatch only on dev root compose; app path matches | **LOW** |
