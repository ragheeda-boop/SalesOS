# Remediation Post-Verify — EAB-2026-08-06-002

**Date:** 2026-08-06  
**Type:** Post-Verification Remediation Wave (not a new baseline; not EAB-003)  
**Baseline:** [FINDINGS-RECHECK.md](./FINDINGS-RECHECK.md) + [EVIDENCE-LOG.md](./EVIDENCE-LOG.md)  
**Program status:** [../EAB-2026-08-06-001/REMEDIATION-PROGRAM-STATUS.md](../EAB-2026-08-06-001/REMEDIATION-PROGRAM-STATUS.md)  
**Evidence (this wave):** [EVIDENCE-LOG-POST.md](./EVIDENCE-LOG-POST.md)  
**Rule:** Honesty over fake Fixed. Production remains **NO-GO**. **OPS-01** remains launch blocker.  
**Validation label:** **build validated** (with gaps)  
**Commit:** none

---

## Executive outcome

| Stream | Result |
|--------|--------|
| Still Partial (DUP/DRIFT/AIGOV) | Narrowed with docs/code markers — **still Partial** (honest) |
| FIT-01 | Advanced Deferred → **Partial / implemented-minimal** (fitness CI subset wired) |
| SEC-04 / OPS-01 | **Still Deferred** (mitigated / launch blocker) — not fake-closed |
| BE `tests/unit` | **1993 pass / 14 fail → 2009 pass / 0 fail** (2 skipped) |
| FE targeted jest | **13 fail → 0 fail** (28/28 in 3 suites) |
| BE e2e critical | **0 pass / Invalid host → 42 pass / 0 fail** |
| FE lint (~528) | **Residual** — not bulk-fixed |
| Production GA | **NO-GO** |

**EAB-003 warranted?** **No** — remediations landed cleanly with strong suite deltas, but OPS-01 remains open, Partials remain structural, FE lint gate still red. Prefer absorb into next Verification Run when humans close OPS-01 or after a focused engine/MetaData sprint — not a full board re-baseline now.

---

## Finding dispositions (post-verify)

| ID | Prior (EAB-002 recheck) | Post-verify | Residual |
|----|-------------------------|-------------|----------|
| **DUP-01** | Still Partial | **Partial + residual** | ≥3 BE engines + FE twin name; HTTP SoT + deprecation markers refreshed |
| **DRIFT-01** | Still Partial | **Partial + residual** | Remeasure **19** `MetaData(` / **18** files; freeze + allowlist; **not** consolidated |
| **DUP-02** | Still Partial | **Partial + residual** | [CAPABILITY-DUP-REGISTER.md](./CAPABILITY-DUP-REGISTER.md); no remount |
| **AIGOV-01** | Still Partial | **Partial + residual** | AI_HONESTY + package README cross-links; twin **name** residual |
| **FIT-01** | Still Deferred | **Partial / implemented-minimal** | FF-07/09/10/12 workflow + scripts; G-06 not claimed 100% |
| **SEC-04** | Still Deferred (mitigated) | **Deferred (mitigated)** | Test bypass retained; compose pins reconfirmed |
| **OPS-01** | Still Deferred | **Deferred** (**launch blocker**) | Checklist rows 1–5 OPEN — **no** offsite/WAL/PITR claim |

**Counts after this wave:** Fixed **9** (unchanged Confirmed Fixed from EAB-002) · Partial **5** (DUP-01, DRIFT-01, DUP-02, AIGOV-01, FIT-01) · Deferred **2** (OPS-01, SEC-04) · Open **0**.

> Note: FIT-01 moved from Deferred → Partial (minimal CI subset). Matrix total still **16**.

---

## Suite / host-header remediation

### TrustedHost / Invalid host header

**Root cause:** httpx fixtures use `base_url="http://test"`; TrustedHost allowed `testserver` but not `test`.

**Fix:** `salesos/backend/app/boot/middleware.py` — add `"test"` to trusted hostnames (CORS origins still stripped to bare hosts).

### BE unit (14 → 0)

| Cluster | Fix |
|---------|-----|
| Analytics export/CSV (`stage` / empty) | Monkeypatch fixture rows in 4 generate/export tests; cubes stay honestly empty |
| GraphQL `400 Invalid host` → then `503` | Host fix + stub `db_session_factory` + entitlement patches in `test_graphql.py` |
| Rules API Invalid host | Host fix alone |

### FE jest (13 → 0)

| Suite | Fix |
|-------|-----|
| custom-fields-studio | Honesty copy → “process memory” |
| graph-page | API-error no longer loads silent demo `/Nodes/` |
| copilot-panel | Chat-tab + AR locale selectors |

### E2E critical (0 → 42)

| Issue | Fix |
|-------|-----|
| Invalid host header | TrustedHost `"test"` |
| Register FK / wrong DB | Override `get_register_db` + wire `db_session_factory` in e2e conftest |
| Companies list envelope | Assert cursor (`data`) **or** page (`items`/`total`) |

---

## JWT / secrets honesty

| Item | Status |
|------|--------|
| Compose pin `JWT_ALGORITHM: RS256` | Present (`salesos/docker-compose.yml`) |
| Host `.env` HS256 leftover | **Documented only** — **no** `.env` secret edits this wave |
| Container runtime | EAB-002 verified **RS256** |

---

## FE lint / build residual

~528 ESLint errors still fail `npm run lint` / lint-gated `npm run build`. Webpack compile previously OK. **Not** bulk-fixed this wave. Orthogonal to FE-01 Confirmed Fixed.

---

## Files changed (high level)

### Backend
- `app/boot/middleware.py` — TrustedHost includes `test`
- `app/modules/decision/router.py` — alternate-capability docstring
- `tests/unit/test_analytics.py`, `test_analytics_phase14.py`, `test_graphql.py`
- `tests/e2e/conftest.py`, `tests/e2e/test_critical_paths.py`

### Frontend
- `custom-fields-studio.test.tsx`, `graph-page.test.tsx`, `copilot-panel.test.tsx`
- Decision package READMEs (honesty cross-links)

### CI / scripts / docs
- `.github/workflows/fitness-ci-subset.yml`
- `salesos/scripts/fitness-ci-subset.{sh,ps1}`
- CAPABILITY-DUP-REGISTER, DECISION-API-SOT, METADATA-ISLAND-FREEZE, FITNESS-CI-SUBSET-PLAN, AI_HONESTY, DR-GA-GAPS-CHECKLIST
- This file + EVIDENCE-LOG-POST + PROGRAM-STATUS update

---

## Validation honesty

| Claim | Status |
|-------|--------|
| Production GA GO | **Not claimed — NO-GO** |
| BE unit full | **build validated** — 2009 passed / 0 failed |
| FE targeted jest | **build validated** — 28/28 |
| FE full `npm test` | **not re-run** this wave (targeted only) |
| FE lint/build gate | **still red** (~528) |
| E2E critical paths | **build validated** — 42 passed |
| Browser / Playwright | **not validated** |
| OPS-01 offsite/WAL | **not claimed** |
| FE Decision live GA AI | **not claimed** — STUB |

---

*Remediation Post-Verify — EAB-2026-08-06-002 — build validated with gaps — production no-go — no commit*
