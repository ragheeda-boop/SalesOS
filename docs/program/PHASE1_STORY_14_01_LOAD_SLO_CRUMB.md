# STORY-14-01 — Load/SLO harness companion (50-tenant pooled tier)

> **Honesty:** Not Production GO. Live prod traffic / prod kill not performed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**. Stage 6 GHCR stays quarantined.  
> **BE status: CLOSED** (tip HTTP companion complete). DevOps owns field 50-tenant / 2h soak residual.  
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

## Field residual — HTTP Soak acceptance (authoritative)

> Acceptance = **HTTP Soak against published Railway URL**, not Companion mode, not docs-only close.  
> Prefer `https://salesos-production-96c0.up.railway.app` until `api.salesos.com` DNS residual is fixed separately.  
> No Production GO. Stage 6 GHCR quarantined. Credentials not invented.

### Root-cause verdict (2026-08-02 field) — **BOTH; A primary for 404**

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| **A) Published build stale** (missing `load_slo` / no `/api/v1/load/*`) | **PRIMARY — CONFIRMED** | Live process `uptime_seconds≈104243` (~28.96h) ⇒ process start ≈ **2026-08-01T14:25Z**, **before** first tip with mount `8a369f1` (2026-08-02). OpenAPI has **0** `/api/v1/load*` paths; `GET /api/v1/load/meta` → **404**. Also missing tip routes from same era: `/api/v1/chaos/meta`, `/api/v1/dr/meta`, `/api/v1/studio/ai-memory/meta` → **404** (OpenAPI 0 hits). Tip `06a8923` Deploy [30760184115](https://github.com/ragheeda-boop/SalesOS/actions/runs/30760184115) claimed SUCCESS + Health Gate HTTP 200, but **runtime was not replaced** (uptime ≫ deploy age). |
| **B) DB readiness** | **ALSO CONFIRMED** (independent) | `GET /health` → 200 `status=degraded` `database=unavailable`; `GET /health/ready` → 200 `status=not_ready`. Blocks login/token mint even after routes land. |

**Tip compare:** first `/api/v1/load/*` mount = `8a369f1`; origin tip `06a8923` ⊇ `8a369f1`. Published runtime **not proven ≥ `8a369f1`** — treat as **Phase 1 FAIL** (SHA/runtime mismatch).

### Human operator unblock (required — agent cannot finish Phase 1)

| Blocker | Detail |
|---------|--------|
| Railway MCP | Server error / not authenticated in this workspace (`mcp_auth` timed out; tools unavailable) |
| Local `railway` CLI | Not logged in (`railway whoami` empty) — no token in agent env |
| CI `railway up --detach` | Fire-and-forget: logs show Indexing → Uploading → Build Logs URL then exit; **does not wait** for deploy success or process restart |
| Possible wrong service | `RAILWAY_SERVICE_ID` may not be the service serving `salesos-production-96c0.up.railway.app` (agent cannot read secret values) |
| Health gate false green | Only checks `/health` HTTP 200 — passes on degraded/stale process |

**Operator actions:** In Railway dashboard for the service that owns `salesos-production-96c0.up.railway.app`: confirm service ID matches GH secret; redeploy/restart from GitHub tip ≥ `8a369f1` (ideally `06a8923`); wait until new deployment **Active** and process uptime resets; then re-probe `GET /api/v1/load/meta` (401 OK, 404 FAIL).

**CI harden (landed, parallel):** `deploy.yml` drops `railway up --detach`; uses `railway up --ci` (wait for roll) and Health Gate requires fresh `uptime_seconds` + `/api/v1/load/meta` ≠ 404. Does **not** claim Production GO or close STORY-14-01.

### Phase progress

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Verify Railway runs commit with `load_slo` | **PARKED (human)** | Agent redeploy false-green [30763336159](https://github.com/ragheeda-boop/SalesOS/actions/runs/30763336159). Live URL still ~29h uptime + load 404. **Resume when operator** restarts service for `salesos-production-96c0.up.railway.app` onto tip ≥ `8a369f1` and confirms load/meta ≠ 404. |
| 2 `/health/ready` → 200 | **BLOCKED** on Phase 1 + DB restore | database=unavailable residual |
| 3 Non-prod test user | **BLOCKED** | needs ready |
| 4 `SALESOS_TOKEN` | **BLOCKED** | needs ready + user |
| 5 HTTP Soak harness | **not validated** | harness tip-landed; do not run as acceptance until Phases 1–4 |

### Domain residual (separate)

- `api.salesos.com` DNS broken — prefer Railway URL above; do not block Phase 1–5 on custom domain.

## DevOps field harness (Stream C)

| Piece | Detail |
|-------|--------|
| Script | `salesos/scripts/story_14_01_nonprod_load_harness.py` @ tip `06a8923` |
| Companion | **not acceptance** (CI synthetic only; light validated locally) |
| HTTP Soak | **not validated** — blocked Phase 1 (stale runtime) + Phase 2 (DB) |

## Non-goals

- Companion-mode story close / docs-only close
- Live prod kill / Production GO
- Enabling `feature_ai_copilot`
- Inventing credentials / scraping `.env*`
- Stage 6 GHCR reopen
