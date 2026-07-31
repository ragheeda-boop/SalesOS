# R-14 Enterprise Closure — Independent Verification

**Date:** 2026-07-31
**Verifier:** independent verification pass over `R-14_ENTERPRISE_CLOSURE_REPORT.md` (2026-07-31), `DECISION_LOG.md` DEC-013/DEC-014/DEC-015, `RISK_REGISTER.md` R-14, `OPERATIONS_MANUAL.md` §14, and the working-tree wiring (`02-app-role.sql`, `ci.yml`, `docker-smoke.yml`, env templates, `config.py`, `database.py`).
**Verdict:** **PARTIALLY CLOSED is the correct status — accepted, with two blocking wiring defects that must be closed before any environment is actually deployed or merged with this wiring (V-01, V-02 below).**

---

## Summary

The R-14 **security remediation itself is sound**: the `salesos_app` role design (NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION), the engine split (`engine` → `salesos_app`, `owner_engine` → `salesos`), the fallback (empty-password → owner), the dynamic `current_database()` grant, and the CI provisioning step are all correct and independently reproduced. Railway left open by explicit user decision, with a documented runbook and no blind edit or live connection, is the right governance call.

However, the **rollout wiring as shipped is not deployable as documented**. Two concrete, file-level defects (one empirically reproduced end-to-end) would break docker-smoke on its first real GitHub Actions run and would break a fresh staging/prod deploy that follows the shipped env templates. Neither is acknowledged anywhere in the closure report, the RISK_REGISTER row, or DEC-015.

---

## Findings

### V-01 (P1) — docker-smoke.yml will fail its first real run: app-role password never matches what init provisions

- `docker-smoke.yml` "Setup .env" writes `APP_POSTGRES_PASSWORD=salesos_app_smoke_test` (line 38).
- The workflow's postgres is `salesos/docker-compose.yml`'s service, which mounts `./infra/docker/postgres/init` (line 20). On the runner's fresh volume, `02-app-role.sql` provisions `salesos_app` with the hardcoded `PASSWORD 'salesos_app_dev_password'` (line 25).
- There is **no `ALTER ROLE` reconciliation step** in docker-smoke.yml. This is the same class of gap the engineer correctly fixed for CI — `ci.yml` runs `02-app-role.sql` then `ALTER ROLE salesos_app WITH PASSWORD 'ci_app_role_test_password'` (lines 171–172 and 290–291) and passes that exact value to pytest (lines 177–178, 297–298). docker-smoke has no equivalent.
- `config.py`'s fallback does not save it: it triggers only when `app_postgres_password` is **empty** (config.py:99–105), and the smoke `.env` sets it non-empty.
- **Empirically reproduced** (throwaway `pgvector/pgvector:pg16` container, same env/mount, torn down after): over the bridge network (the `postgres:5432` path the app actually uses; loopback is `trust` in the official image and must not be used for this check):
  - `psql -h <bridge-ip> -U salesos_app` with `salesos_app_smoke_test` → `FATAL: password authentication failed` (exit 2)
  - same with `salesos_app_dev_password` → succeeds
  - after `ALTER ROLE salesos_app WITH PASSWORD 'ci_app_role_test_password'` (the CI pattern): the new password succeeds, the old dev password fails — confirming the intended fix shape.
- Failure mechanism in the workflow: backend `/health` returns HTTP 200 even with the DB unreachable (main.py:255–328 returns `HealthResponse(status="degraded", ...)`), so the smoke passes its health waits and `Ping`/`Health` checks, then fails at the first DB-touching test (`Register Test User`, `Decision Evaluate`). Workflow ends red.

### V-02 (P1) — Fresh staging/prod template deploys hit an auth-failure trap, or are forced onto a publicly-known credential

- The env templates direct the operator to generate their own app-role password:
  - `salesos/.env.production.template:32` → `APP_POSTGRES_PASSWORD=CHANGE_ME   # openssl rand -hex 32`
  - `salesos/backend/.env.production.template:22` → `<CHANGE_ME: secure app-role password, openssl rand -hex 32>`
  - `salesos/.env.staging.example:32` and `salesos/.env.staging.local.example:36` → `CHANGE_ME_RUN_openssl_rand_hex_24`
- But on a fresh volume, `02-app-role.sql:25` provisions `salesos_app` with the repo-committed, publicly-known `salesos_app_dev_password`. config.py:99 falls back to the owner role only when `app_postgres_password` is empty.
- Consequence: a fresh `docker compose -f docker-compose.prod.yml up` (or staging equivalent) that follows the template verbatim → backend authenticates as `salesos_app` with a password that does not exist → DB writes fail. The only working paths are (a) set `APP_POSTGRES_PASSWORD` to the known committed dev password (defeats the remediation's purpose — the DB credential is public and identical in every environment), or (b) manually run `ALTER ROLE salesos_app WITH PASSWORD '...'` after first init — documented only in `OPERATIONS_MANUAL.md` §14 step 4, not surfaced in the templates, and racing backend start on fresh compose bring-up.
- The CI pattern (automatic ALTER ROLE step) shows the intended shape; staging/prod templates have no equivalent automated reconciliation.

### V-03 (P2) — "independently verified" for staging/prod verified the role, not the runtime connection

- The closure report's staging/prod-template simulations started only the **postgres service** and ran a psql bypass-probe (`R-14_ENTERPRISE_CLOSURE_REPORT.md` lines 76–78). The backend container was never booted against the shipped env files in those shapes, so the environment matrix's "Runtime Role: `salesos_app`" is asserted from psql evidence (role exists, RLS isolates), not from an app that actually authenticated with the template env. This is precisely the gap through which V-01 and V-02 survived.
- The report is otherwise honest about the limits: CI is "simulated; not yet exercised by a real GitHub Actions run", staging "no live VPS", prod "no live host deployed". The overstatement is limited to the "independently verified — not self-reported" framing plus the unexercised runtime connection.

---

## Confirmed correct (credited, no action needed)

- Local dev end-to-end: `salesos_app` present (`rolsuper=f, rolbypassrls=f`), app engine connects as `salesos_app`, bypass-probe isolates (re-reproduced live this pass), owner role leaks as expected.
- ci.yml R-14 wiring: provisioning step order (migrations → `02-app-role.sql` → ALTER ROLE → env vars on pytest) is self-consistent; the ALTER ROLE pattern was independently reproduced on the throwaway container.
- `current_database()` portability fix (02-app-role.sql:37–41) is correct; the original `GRANT CONNECT ON DATABASE salesos` failure mode described in DEC-015 is a real bug that the fix addresses.
- Dual-engine split (`database.py` engine/owner_engine) and `init_db()` using the owner role for bootstrap DDL are correct; the `CREATE SCHEMA` privilege note is accurate.
- Railway handling: left untouched per explicit decision, no credential use, no blind `railway.json` edit; runbook in OPERATIONS_MANUAL §14 unexecuted. Correct.
- DEC-015 (compose project-name collision) is an honest, self-caught operational incident; report/register/log entries are mutually consistent.
- The "no Python source touched" claim for this pass matches the working-tree diff scope.

---

## Required before this wiring is considered deployable

1. **V-01:** reconcile docker-smoke's app-role password — e.g. set `APP_POSTGRES_PASSWORD=salesos_app_dev_password` in the smoke `.env`, or add the same `ALTER ROLE` step ci.yml uses, or parameterize `02-app-role.sql`'s password via env so init and env files can never drift.
2. **V-02:** give staging/prod an automated, non-racing path to a unique app-role password (parameterize the init password from an env var / secrets, or add an `ALTER ROLE` provisioning step like CI), and make the templates' `APP_POSTGRES_PASSWORD` guidance consistent with how the role is actually provisioned.
3. Re-run V-01-style verification over the bridge network (not loopback — the official image's `host all all 127.0.0.1/32 trust` makes localhost checks unable to detect password mismatches).

---

## Status

R-14 remains **PARTIALLY CLOSED** (Railway open, by explicit user decision). The two P1 wiring defects (V-01, V-02) are new and do not invalidate the role design, but they do invalidate the as-shipped "remediated" wiring until fixed. Nothing was modified during this verification pass.
