# Evidence Log — Post-Verify Remediation — EAB-2026-08-06-002

**Window:** 2026-08-06 ~16:00–16:25 +03:00 (approx.)  
**Compose SoT:** `salesos/docker-compose.yml`  
**No commit. No `.env` secret edits.**

---

## A. Backend / Docker pytest

| # | Command | Exit | Key excerpt |
|---|---------|-----:|-------------|
| P1 | `docker compose exec -T backend python -m pytest tests/unit -q --tb=line` (pre-fix baseline retained from EAB-002) | 1 | **1993 passed, 14 failed** |
| P2 | TrustedHost add `"test"` in `app/boot/middleware.py` | — | code change |
| P3 | Analytics monkeypatch tests + GraphQL factory fixture | — | code change |
| P4 | `pytest tests/unit/test_graphql.py tests/unit/test_rules_engine.py::TestRulesAPI -q` | 0 | **12 passed** |
| P5 | `pytest tests/unit -q --tb=line` (post) | **0** | **2009 passed, 2 skipped**, ~137s |
| P6 | `pytest tests/e2e/test_critical_paths.py` (mid: host fixed) | 1 | **7 passed**, 2 failed, 33 errors → then FK/register fixes |
| P7 | e2e conftest: override `get_register_db` + `db_session_factory` | — | code change |
| P8 | companies list assertion accepts cursor envelope | — | code change |
| P9 | `pytest tests/e2e/test_critical_paths.py -q --tb=line` (final) | **0** | **42 passed**, ~141s |

### Unit failure disposition (14 → 0)

| Cluster | Count | Disposition |
|---------|------:|-------------|
| Analytics generate/export | 4 | Fixed — fixture monkeypatch |
| GraphQL | 7 | Fixed — host + factory stub |
| Rules API | 3 | Fixed — TrustedHost `test` |

---

## B. Frontend / npm

| # | Command | Exit | Key excerpt |
|---|---------|-----:|-------------|
| F1 | EAB-002 baseline `npm test` | 1 | **2479 pass / 13 fail** |
| F2 | `npm test -- --testPathPattern="custom-fields-studio\|graph-page\|copilot-panel" --no-coverage` (post) | **0** | **28 passed** / 3 suites |
| F3 | Full `npm test` re-run | — | **not run** (targeted only) |
| F4 | `npm run lint` / `npm run build` | — | **not re-run**; residual ~528 ESLint from EAB-002 |

---

## C. Findings / fitness / ops (static + host script)

| Check | Result |
|-------|--------|
| `MetaData(` under `salesos/backend` | **19** / **18** files (unchanged) |
| Fitness `salesos/scripts/fitness-ci-subset.ps1` | **exit 0** (host; per findings agent) |
| Workflow `.github/workflows/fitness-ci-subset.yml` | Present (FF-07/09/10/12) |
| DR-GA-GAPS rows 1–5 | Still **OPEN** |
| Compose `JWT_ALGORITHM: RS256` | Present |
| Host `.env` JWT edit | **not done** |

---

## D. Deltas (before → after)

| Suite | Before (EAB-002) | After (post-verify) |
|-------|------------------|---------------------|
| BE `tests/unit` | 1993 pass / **14 fail** | **2009 pass / 0 fail** (2 skipped) |
| FE targeted (3 suites) | **13 fail** | **28/28 pass** |
| BE e2e critical | **0 pass** (Invalid host) | **42 pass / 0 fail** |
| FE lint/build | fail ~528 | **residual** (unchanged) |

---

## Overall validation label

**build validated** (BE unit green; e2e critical green; FE targeted jest green; fitness subset host OK) **with gaps** (FE full jest not re-run; FE lint gate; OPS-01; structural Partials).

**Production:** **no-go**.

---

*Evidence Log Post — EAB-2026-08-06-002 — no commit*
