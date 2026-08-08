# Evidence Log — EAB-2026-08-06-003

**Run type:** Verification Run (vs EAB-002 + Post-Verification Remediation)  
**Window:** 2026-08-06 ~16:35–16:50 +03:00  
**Compose SoT:** `salesos/docker-compose.yml`  
**No commit. No `.env` edits.**

---

## A. Backend / Docker

| # | Timestamp (+03) | Command | Exit | Key excerpt |
|---|-----------------|---------|-----:|-------------|
| B0 | 16:35 | `docker compose ps` | 0 | `salesos-backend-1` Up **(healthy)** `:8000`; 14 services up |
| B1 | 16:36 | `docker compose exec -T backend printenv JWT_ALGORITHM` | 0 | **RS256** |
| B2 | 16:36 | `python -m pytest tests/unit/test_middleware.py -q --tb=line` | **0** | **39 passed**, ~2.7s |
| B3 | 16:37–16:39 | `python -m pytest tests/unit -q --tb=line` | **0** | **2009 passed**, **0 failed**, 2 skipped, ~66s |
| B4 | 16:37–16:39 | `python -m pytest tests/e2e/test_critical_paths.py -q --tb=line` | **0** | **42 passed**, **0 failed**, ~77s |

### Deltas vs EAB-002

| Suite | EAB-002 | EAB-003 |
|-------|---------|---------|
| Middleware unit | 39/39 | **39/39** |
| `tests/unit` | 1993 pass / **14 fail** | **2009 pass / 0 fail** |
| e2e critical | **0 pass** (Invalid host) | **42/42** |

TrustedHost `"test"` + post-verify test fixtures **hold** under re-execution.

---

## B. Frontend / npm (`salesos/frontend`)

| # | Timestamp (+03) | Command | Exit | Key excerpt |
|---|-----------------|---------|-----:|-------------|
| F1 | 16:36 | `npx tsc --noEmit` | **0** | Typecheck clean |
| F2 | 16:37–16:38 | `npx jest --testPathPattern="(decision\|custom-fields-studio\|graph-page\|copilot-panel)"` | **0** | **9 suites / 156 tests passed** (includes prior-fail + decision suites) |
| F3 | 16:38–16:41 | `npm test` | **0** | **273 suites passed**; **2492 passed**, 1 skipped |
| F4 | 16:39–16:41 | `npm run lint` | **1** | **~528** ESLint **Error** line hits (warn→error residual) |

### Deltas vs EAB-002

| Suite | EAB-002 | EAB-003 |
|-------|---------|---------|
| tsc | pass | **pass** |
| Targeted / post-verify jest | 13 fail (full run) → post-verify 28/28 | **156/156** targeted pattern; full **2492/2492** |
| Full `npm test` | 2479 / 13 fail | **2492 / 0 fail** |
| lint | ~528 errors | **~528 errors** (unchanged residual) |
| build | fail at lint gate | **not re-run** — lint residual implies same gate |

---

## C. Runtime / API probes

| # | Timestamp (+03) | Probe | Result |
|---|-----------------|-------|--------|
| R1 | 16:36 | `GET /health` | **200** — `status:ok`, version `5.1.0-rc1`, kafka=`in_memory` |
| R2 | 16:36 | `GET /api/v1/decisions` | **401** (not fail-open) |
| R3 | 16:40 | `GET /api/v1/decisions` + `X-API-Key: probe-invalid` | **401** |
| R4 | 16:36 | `GET /api/v1/decision/evaluate` | **405** (POST-only — route live) |
| R5 | 16:36 | `GET /api/v1/decision-runtime/decision/evaluate` | **405** (remount live) |
| R6 | 16:36 | `GET /openapi.json` | **593** paths; decision family **13**; decision-runtime **9** |
| R7 | 16:40 | Compose `JWT_ALGORITHM: RS256` | Present in `salesos/docker-compose.yml` |

---

## D. Drift / governance / fitness proxies

| Check | Result |
|-------|--------|
| `MetaData(` under `salesos/backend` `*.py` | **19** matches / **18** files (unchanged vs EAB-002 / post-verify) |
| `feature_ai_copilot` default | **False** (`config.py`) |
| TrustedHost includes `"test"` | Present (`boot/middleware.py`) |
| `db_session_factory` wired | `startup.py` assignment + log string |
| Fail-closed 503 | entitlement / suspended / API-key middleware |
| SES / Compose SoT / Fitness plan docs | Present |
| `.github/workflows/fitness-ci-subset.yml` | Present |
| Host `fitness-ci-subset.ps1` | **exit 0** — FF-07/09/10/12 **PASS** (light) |
| OPS-01 checklist rows 1–5 | Still **OPEN / UNSIGNED** (`docs/ops/DR-GA-GAPS-CHECKLIST.md`) |
| PROJECT_BIBLE GO deferral | Present (DOC-01) |

---

## E. Not executed / not claimed

| Item | Status |
|------|--------|
| Full `npm run build` | **not re-run** (lint gate residual known) |
| Browser / Playwright | **not validated** |
| Remote GitHub Actions fitness job green | **not validated** this run (workflow + host script only) |
| OPS-01 offsite / WAL / PITR / staging soak | **not done** |
| Chaos inject live 503-without-factory | **not validated** |
| Production GA GO | **not claimed** |

---

## F. Post-run OPS-01 advancement (same calendar day)

In-repo OPS-01 pack after Verification Run (does **not** change board GO/NO-GO):

| Item | Result |
|------|--------|
| Pack | [OPS-01-ADVANCEMENT.md](./OPS-01-ADVANCEMENT.md) |
| Primary WAL | `archive_mode=off` reconfirmed |
| Local backup → `salesos_restore_drill_eab003` | exit 0 — [evidence/ops01-local-backup-20260806.json](./evidence/ops01-local-backup-20260806.json) |
| Offsite / staging soak / signatures | Still **not done** |
| Disposition | **Still Deferred** |

---

*Evidence Log — EAB-2026-08-06-003 — build validated with gaps — OPS-01 local DR light validated — no commit*
