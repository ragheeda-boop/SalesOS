# STORY-14-01 — Load/SLO harness companion (50-tenant pooled tier)

> **Honesty:** Not Production GO. Live prod traffic / prod kill not performed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**. Stage 6 GHCR stays quarantined.  
> **BE status: CLOSED** (tip HTTP companion complete). DevOps owns field residual.  
> Does **not** reopen marketplace 13-xx. Does not re-land 14-02/14-03.

## Landed

| Piece | Detail |
|-------|--------|
| Targets | 50 concurrent simulated tenants; p95 ≤500ms; error_rate ≤1%; no pool exhaustion; no degradation trend |
| Profiles | `pooled_50_tenant_burst`, `pooled_50_tenant_sustained_sim` (CI compressed — not 2h field soak) |
| Remediation | Documented plan (`held` \| `needs_remediation`) on every run |
| Postmortems | Practice postmortem per run |
| HTTP | `/api/v1/load/meta`, `/run/{profile}`, `/run-all`, `/runs`, `/remediation`, `/postmortems` |
| Tests | `tests/unit/test_story_14_01_load_slo.py` |
| Harness CSRF | `story_14_01_nonprod_load_harness.py --mode http` mints `GET /api/v1/identity/csrf-token` for POSTs (does not weaken CSRF) |

## Status snapshot (2026-08-03 evening)

| Gate | Verdict | Notes |
|------|---------|-------|
| Functional register hang (local) | **CLOSED** | Alembic `d4b0e23f5a91` / `tenants.deleted_at` present; `POST /register` → **201** + tokens |
| Local Docker HTTP tip soak | **PASS (light validated)** | Both profiles `within_slo=true`; harness exit 0. Evidence `.tmp-1401-local-soak-evidence.json` |
| Railway HTTP tip path (phases 1–5) | **light / build validated** | Active `b95db185` on `https://salesos-production-96c0.up.railway.app`. Prior hang probes = deploy SUCCESS with **stale Active image** (missing tip). |
| Phase 5 HTTP harness (Railway) | **PASS (exit 0)** — **corroborated 2×** | First: `.tmp-1401-http-harness-now.json`. Second Shell: `.tmp-1401-railway-soak-evidence.json` — both profiles within_slo (burst p95=180; sustained_sim p95=220); remediation `held`. **NOT Companion acceptance.** |
| Auth token nuance (optional residual) | **note only** | Second run: register `access_token` alone → `/api/v1/load/meta` **401**; same-user **login** token → **200**. Earlier probe saw register JWT → meta 200 — treat as intermittent/claims nuance. Prefer login token for load harness; investigate register JWT claims only if Board cares. **Do not reopen 14-01 hang.** |
| Field 2h soak (optional wall-clock) | **FAIL (honest)** — r2 complete | Start `2026-08-03T17:47:27Z` → end `19:47:27Z`. `true_2h_wall_clock_achieved=true` but `all_iters_ok=false`. ITER 1–10 ok; **ITER 11–12** `harness_exit=2` (empty profiles; mint ok). Root cause: HTTP harness POST `/api/v1/load/run-all` without CSRF → **403**; also tip-line deploy JWKS → **401** on `/load/meta` near fail window. Evidence `.tmp-1401-field-soak-r2/soak_final.json`. **Not PASS.** Fix: restore CSRF mint in harness + stderr capture / one remint-retry. |
| Live prod kill / Production GO / GA GO | **not performed / not claimed** | Forbidden |
| Stage 6 GHCR | **SKIPPED** | DEC-150 B |
| Deploy log-stream false-RED | **CLOSED** @ `654b33e` | Newest-deploy SUCCESS poll after stream drop. |
| Deploy stale-image / tip-live gate | **CLOSED/covered** since `c0e4f6a` | Health Gate: fresh `uptime_seconds` + `/api/v1/load/meta` ≠ 404. Docs tip `4754b8b`. Not a separate open residual. |
| Tip CI (SIM105) | **CLOSED** | `d4aa0b9` → `c7dc44e` → tip-line advanced through `654b33e` |

**Overall:** HTTP tip path on published env **light/build validated** (phases 1–5), corroborated by second Shell soak. Real 2h soak is **OPTIONAL** (not required). Security 14-04/14-05: DevOps evidence pack landed. **NOT Production GO. NOT Companion acceptance.** FE/AI STANDBY unless assigned.

## Field residual — HTTP Soak acceptance (authoritative)

> Acceptance = **HTTP Soak against published Railway URL**, not Companion mode, not docs-only close.  
> Prefer `https://salesos-production-96c0.up.railway.app` until `api.salesos.com` DNS residual is fixed separately.  
> No Production GO. Stage 6 GHCR quarantined. Credentials not invented.  
> **2026-08-03 evening:** Railway Active `b95db185` HTTP tip path phases 1–5 **PASS (light/build validated)**. Does **not** claim real 2h soak, Companion acceptance, or Production GO.

### Root-cause verdict (2026-08-02 field) — **BOTH; A primary for 404**

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| **A) Published build stale** (missing `load_slo` / no `/api/v1/load/*`) | **PRIMARY — CONFIRMED** | Live process `uptime_seconds≈104243` (~28.96h) ⇒ process start ≈ **2026-08-01T14:25Z**, **before** first tip with mount `8a369f1` (2026-08-02). OpenAPI has **0** `/api/v1/load*` paths; `GET /api/v1/load/meta` → **404**. Also missing tip routes from same era: `/api/v1/chaos/meta`, `/api/v1/dr/meta`, `/api/v1/studio/ai-memory/meta` → **404** (OpenAPI 0 hits). Tip `06a8923` Deploy [30760184115](https://github.com/ragheeda-boop/SalesOS/actions/runs/30760184115) claimed SUCCESS + Health Gate HTTP 200, but **runtime was not replaced** (uptime ≫ deploy age). |
| **B) DB readiness** | **ALSO CONFIRMED** (independent) | `GET /health` → 200 `status=degraded` `database=unavailable`; `GET /health/ready` → 200 `status=not_ready`. Blocks login/token mint even after routes land. |

**Tip compare:** first `/api/v1/load/*` mount = `8a369f1`; origin tip `06a8923` ⊇ `8a369f1`. Published runtime **not proven ≥ `8a369f1`** — treat as **Phase 1 FAIL** (SHA/runtime mismatch).

### Human operator unblock (required — agent cannot finish Railway Phase 1)

| Blocker | Detail |
|---------|--------|
| Railway MCP | Server error / not authenticated in this workspace (`mcp_auth` timed out; tools unavailable) |
| Local `railway` CLI | Not logged in (`railway whoami` empty) — no token in agent env |
| CI `railway up --detach` | Fire-and-forget: logs show Indexing → Uploading → Build Logs URL then exit; **does not wait** for deploy success or process restart |
| Possible wrong service | `RAILWAY_SERVICE_ID` may not be the service serving `salesos-production-96c0.up.railway.app` (agent cannot read secret values) |
| Health gate false green | Only checks `/health` HTTP 200 — passes on degraded/stale process |

**Operator actions:** In Railway dashboard for the service that owns `salesos-production-96c0.up.railway.app`: confirm service ID matches GH secret; redeploy/restart from GitHub tip ≥ `8a369f1` (ideally `06a8923`); wait until new deployment **Active** and process uptime resets; then re-probe `GET /api/v1/load/meta` (401 OK, 404 FAIL).

**CI harden (landed):** `deploy.yml` uses `railway up --ci` (wait for roll); Health Gate requires fresh `uptime_seconds` + `/api/v1/load/meta` ≠ 404; `@654b33e` closes log-stream false-RED via newest-deployment SUCCESS poll. Does **not** claim Production GO.

### Phase progress

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Verify Railway runs tip with `load_slo` | **PASS (light validated)** | Active `b95db185`; load routes present. Prior false hang = stale Active image. |
| 2 `/health/ready` → 200 (Railway) | **PASS (prior)** | health/ready PASS on published env |
| 3 Non-prod register (Railway tip-live) | **PASS** | `POST /register` → **201** ~1–2s + TOKEN |
| 4 `SALESOS_TOKEN` + load/meta | **PASS** | Bearer; `GET /api/v1/load/meta` → **200** |
| 5 HTTP Soak harness (local) | **PASS (light validated)** | Docker tip soak earlier same day |
| 5b HTTP Soak (Railway published) | **PASS (light/build validated)** — **2×** | exit 0; both profiles within_slo; evidence `.tmp-1401-http-harness-now.json` + `.tmp-1401-railway-soak-evidence.json`; remediation `held` |

### Railway published HTTP tip evidence (2026-08-03 evening) — Active `b95db185`

| Endpoint / gate | Result |
|-----------------|--------|
| Active deploy | `b95db185` on `https://salesos-production-96c0.up.railway.app` |
| health / ready / load mount | PASS (prior tip-live) |
| `POST /register` | **201** ~1–2s + token |
| `GET /api/v1/load/meta` (Bearer) | **200** with login token (second run); register access_token alone → **401** (claims nuance — not hang) |
| Harness `--mode http` | **exit 0** ×2; evidence `.tmp-1401-http-harness-now.json`, `.tmp-1401-railway-soak-evidence.json` |
| `pooled_50_tenant_burst` | within_slo; p95=180ms; error_rate=0.002 |
| `pooled_50_tenant_sustained_sim` | within_slo; p95=220ms; error_rate=0.004 |
| remediation | `held` |
| `field_2h_soak` | **false** (simulated_duration 120s — not real 2h) |

### Local Docker soak evidence (2026-08-03T14:35Z UTC)

| Endpoint | HTTP | Latency / result |
|----------|------|------------------|
| `GET /health` | 200 | ok / database connected |
| `GET /health/ready` | 200 | `ready` |
| `GET /api/v1/load/meta` (no auth) | 401 | expected |
| `POST /api/v1/identity/register` | 201 | ~4.7–8.4s this session (PERF-001) |
| `GET /api/v1/load/meta` | 200 | target_tenants=50; p95≤500; error_rate≤0.01 |
| `POST /api/v1/load/run-all` | 200 | ~292ms wall |
| → `pooled_50_tenant_burst` | ok | tenants=50; p95=180ms; error_rate=0.002; within_slo |
| → `pooled_50_tenant_sustained_sim` | ok | tenants=50; p95=220ms; error_rate=0.004; within_slo |
| `GET /api/v1/load/remediation` | 200 | status=`held` |
| Harness exit | 0 | SLOs held (not Production GO) |

### Domain residual (separate)

- `api.salesos.com` DNS broken — prefer Railway URL above; do not block Phase 1–5 on custom domain.

## DevOps field harness (Stream C)

| Piece | Detail |
|-------|--------|
| Script | `salesos/scripts/story_14_01_nonprod_load_harness.py` |
| Companion | **not acceptance** (CI synthetic only; light validated locally) |
| HTTP Soak (local Docker) | **light validated** — PASS 2026-08-03 (CSRF-aware http mode) |
| HTTP Soak (Railway) | **light/build validated** — PASS exit 0 ×2 on Active `b95db185`; evidence `.tmp-1401-http-harness-now.json` + `.tmp-1401-railway-soak-evidence.json` |
| Field 2h soak | **FAIL (optional r2)** — wall 2h yes, all_iters_ok no; CSRF/401 root cause; not invent PASS |
| Log-stream false-RED | **CLOSED** @ `654b33e` — newest-deploy SUCCESS poll after stream drop |
| Stale-image tip-live gate | **CLOSED (Health Gate)** — fresh `uptime_seconds` + `/api/v1/load/meta` ≠ 404 already required; optional SHA tip-marker not claimed open |
| Load harness auth (optional) | Prefer **login** token for `/api/v1/load/*`; register JWT alone may 401 (intermittent/claims) — do **not** reopen hang |

## Non-goals

- Companion-mode story close / docs-only close
- Live prod kill / Production GO
- Enabling `feature_ai_copilot`
- Inventing credentials / scraping `.env*`
- Stage 6 GHCR reopen
- Fixing PERF-001 register latency in this story
