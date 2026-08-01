# DEC-016 — Authorize and execute Railway R-14 remediation (Option A)

> **Status:** **Accepted**  
> **Date:** 2026-08-01  
> **Supersedes:** [`DEC-DRAFT-RAILWAY-R14-PHASE0`](DEC-DRAFT-RAILWAY-R14-PHASE0.md)  
> **Board:** Architecture Review Board + Risk Manager + DevOps-SRE (SalesOS / AQLIYA)  
> **Human authorization:** Arabic standing approval — Option A full remediation (Ops via Railway CLI; MCP Unauthorized)

---

## Decision

Accept **Option A** from the draft package: execute `OPERATIONS_MANUAL.md` §14 against Railway managed Postgres.

| Field | Value |
|---|---|
| Chosen option | **A** |
| Authorizing role(s) | Program Director / Ops (Arabic standing approval) |
| Environments + order | Railway **staging first** → Railway **production** (env vars / role only; **no app image promote**) |
| Follow-on ID | **DEC-016** (this record) |
| Tooling | Railway **CLI only** (project `responsible-comfort`); MCP Unauthorized |

---

## Execution summary (evidence, secrets redacted)

### Staging (verified first)

1. Live connect as owner role `postgres` via Railway CLI SSH tunnel to service `Postgres` (DB `railway`).
2. Idempotent provision of `salesos_app` (`NOSUPERUSER NOBYPASSRLS … LOGIN`) + `GRANT` / default privileges on existing schemas (`public`, `audit`, `identity`, `company`, `activity`, `crm`).
3. SalesOS service env (derived host/db from existing `DATABASE_URL` / plugin; app role password per §14 `openssl rand -hex 32` — **not** committed):
   - `APP_POSTGRES_USER=salesos_app`
   - `APP_POSTGRES_PASSWORD` present (len 64)
   - `POSTGRES_HOST=postgres.railway.internal`
   - `POSTGRES_PORT=5432`
   - `POSTGRES_DB=railway`
4. Env-triggered redeploy of existing SalesOS image (deployment `7d33a0bc-…`, **SUCCESS**).
5. Bypass-probe: owner SELECT returned both tenants; `salesos_app` isolated to session tenant — **PASS**.
6. Role flags: `salesos_app` → `rolsuper=f`, `rolbypassrls=f`.
7. `GET https://salesos-staging.up.railway.app/health` → **200** (`database":"connected"`).

### Production (after staging verified; env only — no image promote)

1. Same §14 provision on production `Postgres` (`railway`); bypass-probe **PASS**; role flags `f,f`.
2. Same `APP_POSTGRES_*` + `POSTGRES_HOST`/`PORT`/`DB` pattern on SalesOS production (separate app password; not committed).
3. Env-triggered redeploy of **existing** production image (deployment `1328309a-…`, **SUCCESS**). **No new image promote.**
4. `GET https://salesos-production-96c0.up.railway.app/health` → **200** (`database":"connected"`).

---

## Consequence

- S04-04 → **CLOSED**.
- R-14 Railway slice → **Closed** (local/CI/compose staging/prod-template + Railway staging + Railway production).
- Phase 0 exit critical-path gate that was **solely** S04-04 is cleared for R-14 / DEC-008 tenant-isolation honesty on Railway.
- Draft `DEC-DRAFT-RAILWAY-R14-PHASE0` → **Superseded**.
- Do **not** commit secret values; do **not** weaken auth/CSRF/RBAC.
