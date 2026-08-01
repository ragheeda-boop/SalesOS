# Principal Software Audit — DEC-016 / Railway / Secrets / Swarm / CI

> **Auditor role:** Independent Principal Software Auditor (adversarial)  
> **Date:** 2026-08-01  
> **Repo tip at close:** `20fa049` (`feat(rls): DEC-117 Category B5…`)  
> **Evidence hierarchy:** Tier 1 (live CLI/DB/API/GHA) > Tier 2 (source/workflows) > Tier 3 (docs). Tier 3 never overrides Tier 1/2.  
> **Canvas:** open beside chat — `principal-audit-dec016-railway-ci.canvas.tsx` under the workspace canvases directory  

> **Validation label:** **build validated** for field probes cited below; **production no-go** unchanged.

Secrets are redacted (prefix/suffix or presence/length only). Do not commit secret values.

---

## A. DEC-016 — Closure verdict: **CONTRADICTED**

DEC-016 (`docs/program/decisions/DEC-016-RAILWAY-R14-OPTION-A.md`) is treated as a **claim to test**, not evidence.

| # | Claim | Evidence | Confidence | Impact | Remediation |
|---|--------|----------|------------|--------|-------------|
| A1 | Staging deploy `7d33a0bc` SUCCESS | `railway deployment list --service SalesOS` (staging): `7d33a0bc-3687-47b8-b45d-a09721450d64 \| SUCCESS` | **VERIFIED** | Redeploy occurred | None |
| A2 | Prod deploy `1328309a` SUCCESS | `railway deployment list` (production): `1328309a-b887-4977-8e06-29ba93148682 \| SUCCESS` | **VERIFIED** | Env redeploy; consistent with “no image promote” | None |
| A3 | `APP_POSTGRES_USER=salesos_app` + password set (both envs) | `railway variables --service SalesOS --kv`: USER present len=11 (`salesos_app`); PASSWORD present len=64 | **VERIFIED** | Env step done | None for presence |
| A4 | `/health` 200 staging + prod | `Invoke-WebRequest` staging → 200 `version":"5.1.0-rc1","database":"connected"`; prod → 200 `version":"3.1.0","database":"connected"` | **VERIFIED** | Liveness only | Do not treat as RLS proof |
| A5 | `salesos_app` NOSUPERUSER NOBYPASSRLS | Tunnel + `psql`: staging+prod `salesos_app \| f \| f \| t` | **VERIFIED** | Role exists | Insufficient alone |
| A6 | Runtime connects as `salesos_app` | `pg_stat_activity`: staging 81× `postgres`, prod 85× `postgres`; **0** `salesos_app` | **FALSE** | BYPASSRLS owner still serves | Wire app to `app_database_url` on running image; prove sessions |
| A7 | Bypass-probe PASS (isolation) | Prod: as `salesos_app`, `SELECT count(*) FROM companies` → **141221** (same as owner) with no `app.tenant_id`; `pg_policies` tenant_isolation\_\* = **0**; `relrowsecurity` count = **0** | **FALSE** | No tenant isolation on Railway DB | Apply RLS migrations; re-probe; require zero cross-tenant rows |
| A8 | Prod honors `APP_POSTGRES_*` | Health `3.1.0`; git `12761d4^` / `d6981e5` `database.py` uses only `resolved_database_url` (no `app_database_url`); R-14 land `5e7023f` is 2026-07-31 **after** 3.1.0 era | **FALSE** | Env vars inert on prod binary | Authorized image promote with R-14 code |
| A9 | S04-04 / R-14 Railway **CLOSED** | Tier-3 board/DAG/RISK_REGISTER vs A6–A8 | **CONTRADICTED** | False Phase 0 clearance on R-14 | Reopen S04-04; amend DEC-016; revoke Phase 0 GO on R-14 |

**Overall A:** Partial infrastructure steps (role + env + health + matching deploy IDs) are real. The **security closure** (least-privilege runtime + bypass-probe + RLS) is **not**. Verdict: **CONTRADICTED**.

Railway MCP: `GetMcpTools` serverStatus error; `whoami` → Not connected. CLI used instead (authenticated as `ragheed.a@ratlfintech.com`).

---

## B. Railway production

| # | Claim | Evidence | Confidence | Impact | Remediation |
|---|--------|----------|------------|--------|-------------|
| B1 | Prod role config | `salesos_app` f/f; `postgres` t/t; `DATABASE_URL` user=`postgres` | **VERIFIED** | Owner path bypasses RLS | Force app URL to app role |
| B2 | Prod RLS behavior | policies=0; rls_on=0; alembic `0051` | **VERIFIED** | Category A/B policies not on Railway | `alembic upgrade` on Railway after backup/change control |
| B3 | Prod app uses least-privilege | activity all `postgres` | **FALSE** | R-14 ineffective | Image + config + session proof |
| B4 | Staging schema readiness | alembic `0049`; empty companies/tenants; policies=0 | **VERIFIED** | Cannot have demonstrated meaningful isolation on empty/no-RLS DB | Migrate + seed or probe with known multi-tenant fixtures |
| B5 | Graph/neo4j prod | `neo4j-prod: Offline`; health `graph":"unavailable"` | **VERIFIED** | Graph features degraded | Restore neo4j-prod if required |

---

## C. Secret exposure

| # | Asset | Classification | Evidence | Active/Expired |
|---|--------|----------------|----------|----------------|
| C1 | `.env.example`, `*.template`, staging examples | **committed** (placeholders) | `git ls-files` | N/A |
| C2 | `salesos/.env.staging` | **was committed** (`93c46a70`); removed (`f837736`); **still in git history** | `git show 93c46a70:salesos/.env.staging` (JWT/DB/Neo4j/Redis redacted in audit notes) | **INSUFFICIENT EVIDENCE** whether still valid elsewhere |
| C3 | `salesos/infra/k8s/secrets.yaml` | committed then removed Sprint 6 | rev-list / remove commit; sampled blob used `CHANGE_ME` | **INSUFFICIENT** |
| C4 | Local `salesos/.env`, `.env.production`, `.env.staging`, `backend/.env`, `frontend/.env.local` | **local only** + **gitignored** | `Test-Path` + `git check-ignore` | Do not classify active without use |
| C5 | Root `.env.production` ignore | **gap**: root `.gitignore` has `.env` but **not** `.env.production`; `salesos/.gitignore` has it | `git check-ignore .env.production` empty at root | Hygiene fix |
| C6 | Railway JWT/REDIS/APP_POSTGRES | **production secrets** on platform | `railway variables --kv` presence | PRESENT; values not logged here |
| C7 | Audit tunnel passwords | Printed by `railway connect --tunnel-only` into agent terminals | terminal capture | **Rotate** staging+prod Postgres passwords |

No full secret values are reproduced in this document.

---

## D. Swarm execution

| # | Claim | Evidence | Confidence | Impact | Remediation |
|---|--------|----------|------------|--------|-------------|
| D1 | No repo `max_agents` cap | `rg max_agents` → hits only DEC-107 / DECISION_LOG; **0** in non-doc code | **VERIFIED** | Under-utilization is behavioral if it occurs | Orchestrator policy (DEC-107), not a code knob |
| D2 | Parent swarm Task parallelism | Parent transcript `6baea6ce…`: **97** `"name":"Task"` launches; **204** subagent jsonl files | **STRONGLY SUPPORTED** | Parallel Task usage exists | Continue DEC-107 always-on READY |
| D3 | GHA cancel-in-progress throughput tax | `.github/workflows/ci.yml` `concurrency.group: ci-${{ github.ref }}` `cancel-in-progress: true`; run `30693781994` conclusion **cancelled** when superseded | **VERIFIED** | Cancels in-flight CI on rapid push | Note only unless DEC revises |
| D4 | ~234 min READY-idle claim | Docs/DEC-107 only in this pass | **INSUFFICIENT EVIDENCE** | Do not treat as measured fact | Reconstruct from transcript timestamps if needed |

---

## E. CI

| # | Claim | Evidence | Confidence | Impact | Remediation |
|---|--------|----------|------------|--------|-------------|
| E1 | Tip CI failing | Run **30697267315** @ `20fa049` conclusion **failure** | **VERIFIED** | CI GREEN not met | Fix lint |
| E2 | Root cause Stage 1 Backend Lint | Log: `I001` `tests/contract/test_openapi_auth_errors.py:7`; `E501` ×2 in `test_adversarial_rls_remaining.py` | **VERIFIED** | Skips backend unit/integration/build (`needs: [lint-backend,…]`) | `ruff check --fix` / wrap lines |
| E3 | Deploy Staging blocked (GHCR) | Run **30693795470**: push `403 Forbidden` to `ghcr.io/.../frontend:staging` | **VERIFIED** | CI-08 | Fix GHCR permissions |
| E4 | Deploy Production blocked (VPS SSH) | Run **30693795496**: `Error: missing server host` | **VERIFIED** | CI-09 | Set deploy host secret / fix workflow |
| E5 | Concurrency cancel | `30693781994` cancelled | **VERIFIED** | Lost mid-run signal | Batch pushes or revise concurrency |

Security Scan / Docker Smoke succeeded on tip; they do **not** imply CI GREEN.

---

## Executive risk register

| Severity | Item |
|----------|------|
| **Critical** | Railway production: 0 RLS policies; sessions as `postgres` (BYPASSRLS); `salesos_app` reads all 141,221 companies without tenant |
| **Critical** | DEC-016 / S04-04 / R-14 Railway “CLOSED” **contradicted** by live DB |
| **High** | Prod image `3.1.0` lacks `APP_POSTGRES_*` consumption |
| **High** | Git history retains `.env.staging` secrets — rotate if reused |
| **High** | CI-08 GHCR 403; CI-09 missing SSH host |
| **Medium** | Tip CI Ruff failures blocking backend test chain |
| **Medium** | Tunnel password exposure during this audit — rotate |
| **Low** | Root `.env.production` ignore gap; Railway MCP down |

---

## Claims requiring live verification before acceptance as fact

1. Railway R-14 / S04-04 CLOSED or bypass-probe PASS  
2. Phase 0 (DEC-008) GO that depends only on S04-04 (DEC-086)  
3. Runtime traffic uses `salesos_app` on Railway  
4. Railway alembic / RLS policy counts match tip  
5. Active vs expired status of historical git secrets  
6. Exact swarm READY-idle duration (~234 min)  
7. Any production GO / external pilot-ready claim  

---

## Commands run (non-exhaustive)

- `railway whoami` / `status` / `variables --kv` / `deployment list` / `connect Postgres --tunnel-only`
- `docker run postgres:16-alpine psql …` (roles, activity, policy counts, company counts)
- `Invoke-WebRequest` staging+prod `/health`
- `gh run list` / `gh run view … --log-failed`
- `git ls-files` / `git check-ignore` / `git log` / `git show` (secret history, version dating)
- Transcript / `rg max_agents` / `ci.yml` concurrency read

**Honesty:** production **no-go**. DEC-016 security closure **not verified**.
