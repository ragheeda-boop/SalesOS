# Evidence Log — EAB-2026-08-06-002

**Run type:** Verification Run (vs EAB-001 + remediation claims)  
**Window:** 2026-08-06 ~14:53–15:10 +03:00  
**Compose SoT:** `salesos/docker-compose.yml`  
**No commit. No `.env` edits.**

---

## A. Backend / Docker

| # | Timestamp (+03) | Command | Exit | Key excerpt |
|---|-----------------|---------|-----:|-------------|
| B1 | 14:53:27 | `cd salesos; docker compose ps` | 0 | `salesos-backend-1` Up ~25m **(healthy)** `:8000` |
| B2 | 14:54:00 | `docker compose exec -T backend grep … db_session_factory app/boot/startup.py` | 0 | `app.state.db_session_factory = async_session`; log `wired (async_session)` |
| B3 | 14:54:02 | grep fail-closed / 503 in entitlement, api_keys, suspended_tenant | 0 | `status_code=503` + fail-closed comments |
| B4 | 14:54:04 | grep decision-runtime prefix in routers | 0 | `prefix="/api/v1/decision-runtime"` |
| B5 | 14:54–15:07 | ContextVar reset greps (`middleware.py`, `database.py`) | 0 | `finally: reset_current_tenant_id(token)` |
| B6 | 14:54:48 | `docker compose exec -T backend printenv JWT_ALGORITHM` | 0 | **RS256** |
| B7 | ~14:55 | First `pytest` / `python -m pytest` | 127 / fail | `pytest` not on PATH; then missing `pygments` |
| B8 | ~14:58 | Transient (container only): `pip install pygments` as root | 0 | Unblocks pytest; **not** image SoT |
| B9 | 15:00:07 | `python -m pytest tests/unit/test_middleware.py -q --tb=line` | **0** | **39 passed**, ~8s |
| B10 | 15:04:00 | `python -m pytest tests/unit -q --tb=line` | **1** | **1993 passed**, **14 failed**, 4 skipped, ~96s |
| B11 | 15:07:44 | `python -m pytest tests/e2e/test_critical_paths.py -q --tb=line` | **1** | **0 passed**, 9 failed, 33 errors — dominant `Invalid host header` |

### Unit failure clusters (B10)

- Analytics export/report assertions  
- GraphQL `assert 400 == 200`  
- Rules API `400 Invalid host header`  
- Setup noise: JWKS key regen / `_keys/rsa_private.pem` permission denied  

### E2E note (B11)

TrustedHost / TestClient Host mismatch blocks critical-path suite — **not** a reversion of SEC-01 factory wiring (unit middleware green; live HTTP auth-gated).

---

## B. Frontend / npm (`salesos/frontend`)

| # | Timestamp (+03) | Command | Exit | Key excerpt |
|---|-----------------|---------|-----:|-------------|
| F1 | static | Read `providers.tsx` | — | No `return null` blank gate; sync `useMemo` runtime; EAB-001-P0-FE-01 comment |
| F2 | static | `globals.css` | — | `@import "@salesos/tokens/css";` |
| F3 | static | decision package | — | STUB labels; `0.0.0-stub`; throws on evaluate |
| F4 | 14:54:38 | `npx tsc --noEmit` | **0** | Typecheck clean (~126s) |
| F5 | 14:56:50 | `npm run lint` | **1** | ~**528** ESLint **Error**s (warn→error hardening) |
| F6 | 14:56–14:58 | Targeted jest: decision stub + decisionQueries + decisionHttp | **0** | **48 passed** |
| F7 | 14:59–15:02 | `npm test` | **1** | **2479 passed**, **13 failed**, 1 skipped / 273 suites (3 failed) |
| F8 | 15:03:31 | `npm run build` | **1** | Webpack **compiled OK** (~101s); failed at lint gate (same ESLint errors) |

### Jest failure suites (F7)

1. `custom-fields-studio.test.tsx` — honesty text mismatch  
2. `graph-page.test.tsx` — missing `/Nodes/` (likely AR locale)  
3. `copilot-panel.test.tsx` — 11 locale/copy assertions  

Decision-related suites **passed** in full run.

---

## C. Runtime / API probes

| # | Timestamp (+03) | Probe | Result |
|---|-----------------|-------|--------|
| R1 | 14:53:41 | `GET /health` | **200** — `status:ok`, version `5.1.0-rc1`, kafka=`in_memory` |
| R2 | 14:53:42 | `GET /api/v1/decisions` | **401** `Not authenticated` (not fail-open 200) |
| R3 | 14:54:13 | `GET /api/v1/decisions` + `X-API-Key: probe-invalid` | **401** |
| R4 | ~14:54 | `GET /api/v1/decision/evaluate` | **405** (POST-only — route live) |
| R5 | ~14:54 | `GET /api/v1/decision-runtime/decision/evaluate` | **405** (remount live) |
| R6 | ~14:54 | `GET /openapi.json` | OK — 593 paths; both `/api/v1/decision/*` and `/api/v1/decision-runtime/*` |
| R7 | logs | `docker compose logs backend` | Startup complete; **0** ERROR lines; string `db_session_factory wired` **not** in retained tail (source wiring confirmed in B2) |

---

## D. Drift / governance proxies (static)

| Check | Result |
|-------|--------|
| `MetaData(` under `salesos/backend` | **19** matches / **18** files |
| ADR-101 / ADR-102 files + `docs/adr/index.md` | Present + indexed Accepted |
| Root `docker-compose.yml` | LEGACY / QUARANTINED banner → COMPOSE-SOURCE-OF-TRUTH |
| `feature_ai_copilot` | `False` (`config.py`) |
| Empty `APP_POSTGRES_PASSWORD` | Refuses boot outside allowed ENV (`config.py` EAB-001-P0-SEC-02) |
| `docs/compliance/SES-BASELINE.md` | Present |
| DR-GA-GAPS-CHECKLIST | Rows 1–5 **OPEN** / UNSIGNED |
| PROJECT_BIBLE GO banner | Audit wins / NO-GO deferral present |

---

## E. Not run / gaps

| Item | Status |
|------|--------|
| Full backend suite beyond `tests/unit` + one e2e file | not validated |
| Browser / Playwright FE e2e | not validated |
| Staging soak / WAL / offsite restore | not validated (OPS-01) |
| Host `.env` JWT_ALGORITHM edit | **not done** (container RS256 via compose; host leftover possible) |
| Fitness CI wiring | not validated (FIT-01 deferred) |
| DTM full re-sample | not re-run (prior sample retained for DM-08) |

---

## Overall validation label

**build validated** (middleware unit green; FE tsc green; FE targeted decision tests green; large unit/jest suites executed with recorded failures) **with gaps** (e2e host-header; FE lint/build gate; 14 BE unit fails; OPS-01 operational).

---

*Evidence Log — EAB-2026-08-06-002 — no commit*
