# R-14 Remediation Implementation Report

**Date:** 2026-07-31
**Scope:** Local development environment only, per explicit authorization (see `docs/program/DECISION_LOG.md` DEC-014). CI, staging, self-hosted prod template, and the live Railway production database are **explicitly out of scope** and were not touched.
**Predecessor documents:** R-14 Production Security Validation Findings Report (this session, pasted directly — not a repo file), `docs/program/RISK_REGISTER.md` R-14, `docs/program/DECISION_LOG.md` DEC-013/DEC-014.

---

## Independent Verification Before Implementing

Before executing anything, every factual claim in the validation report was independently re-checked, not taken on faith:

| Claim | Verification method | Result |
|---|---|---|
| `infra/docker/postgres/init/01-init.sql` never demotes the bootstrap role | Read the file directly | Confirmed — only `CREATE EXTENSION`/`CREATE SCHEMA`, zero role management |
| CI/staging/prod-template all provision `POSTGRES_USER=salesos` via the same official-image pattern | Grepped `.github/workflows/ci.yml`, `infra/staging/docker-compose.staging*.yml`, `docker-compose.prod.yml`, `.env.production.template`, `backend/.env.production.template` | Confirmed, all four |
| `backend/.env` (apparent live Railway snapshot) shows role `postgres`, diverging from the `salesos` templates | Cross-checked against this session's own earlier reading of that exact file | Confirmed |
| The core empirical claim: FORCE-enabled RLS + correct policy + correct session var still leaks under `salesos` | Reproduced independently, from scratch, with a freshly-created probe table (not a re-run of the same script) | **Confirmed — identical result** |

Every claim held up. Implementation proceeded on that basis.

---

## What Was Implemented

### 1. New database role
`infra/docker/postgres/init/02-app-role.sql` — idempotent (`DO $$ ... IF NOT EXISTS ... $$`), creates `salesos_app` (`NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION LOGIN`), grants `CONNECT`, schema `USAGE`, and `SELECT/INSERT/UPDATE/DELETE` on all current tables across `public, audit, identity, company, activity, crm`, plus `ALTER DEFAULT PRIVILEGES` so tables created by future migrations (run as `salesos`, the owning role) are automatically covered — verified: after running `alembic upgrade head` (see below), all 86 resulting tables had `salesos_app` SELECT grants with zero additional manual grant statements.

Runs automatically for a fresh container (mounted alongside `01-init.sql`); applied manually this session to the already-initialized `salesos` and `salesos_test` databases via `psql < 02-app-role.sql` (the `salesos_test` run correctly errored on the five schemas that don't exist there — expected, since that database's schema is managed dynamically by test fixtures, not this init script).

### 2. Application configuration
`app/config.py` — added `app_postgres_user` (default `salesos_app`), `app_postgres_password` (default empty), `app_database_url_override`, and a `app_database_url` property mirroring `resolved_database_url`'s URL-normalization logic. **Falls back to `resolved_database_url` when `app_postgres_password` is unset** — the entire reason this is safe to ship to every environment simultaneously without breaking CI/staging/prod, which haven't been remediated yet.

### 3. Application wiring — the part that needed real judgment, not just plumbing
`app/database.py` originally had one module-level `engine`, used both for request-serving sessions (via `get_db()`) and for bootstrap DDL in `init_db()` (`CREATE EXTENSION`, `CREATE SCHEMA IF NOT EXISTS audit`) and the Alembic-version check. Naively repointing that single engine to `app_database_url` would have broken `init_db()`: **verified directly** that `CREATE SCHEMA IF NOT EXISTS audit` still raises `permission denied for database` under `salesos_app` even though `audit` already exists — Postgres checks the database-level CREATE privilege before checking whether the schema exists, contrary to what might be assumed. The fix: split into two engines — `engine` (request-serving, now `app_database_url`) and `owner_engine` (bootstrap DDL + Alembic-version check, still `resolved_database_url`). `alembic/env.py` itself was not touched at all; it already constructs its own independent engine from `resolved_database_url` directly.

### 4. Local environment activation
`salesos/.env` — added `APP_POSTGRES_USER=salesos_app` and `APP_POSTGRES_PASSWORD=salesos_app_dev_password`.

---

## A Real Gotcha Hit Along the Way

`docker compose restart backend` does **not** reload `.env` changes — it restarts the existing container process in place. The new environment variables only took effect after `docker compose up -d --force-recreate backend`, which actually recreates the container. First attempt silently showed the old behavior (still connecting as `salesos`) until this was caught by checking `docker compose exec backend env` directly rather than assuming the restart had worked.

## A Separate, Pre-Existing Finding, Disclosed Not Fixed-In-Passing

While verifying the fix, the local `salesos` database was found to have **zero application tables** — only `information_schema`/`pg_catalog`. The backend container had been running (healthy, per `docker ps`, 13+ hours uptime) the entire time against an empty schema. Root cause: `init_db()`'s automatic migration path has a deliberate `try/except` that logs a warning and lets the app start "with degraded schema" rather than crashing on migration failure — and for whatever reason, migrations had never successfully run against this particular database. Running `alembic upgrade head` manually resolved it cleanly (0001 → 0052, zero errors, 86 tables created). This is disclosed as a distinct, pre-existing operational gap — not caused by this remediation, not fixed as a general solution (why the automatic path didn't self-heal over 13 hours is not investigated here), and worth its own risk-register entry if the owner wants to track it, which this report does not create unilaterally.

---

## End-to-End Verification

| Check | Result |
|---|---|
| Container recreation, clean startup | `Alembic current=0052 head=0052`, `SalesOS startup complete in 3.1s`, `Uvicorn running` — zero errors |
| `pg_stat_activity` during live operation | Both roles connected simultaneously: `salesos` (owner_engine, bootstrap) and `salesos_app` (request engine) |
| Real HTTP requests | `GET /health` → 200; `GET /ping` → `{"ping":"pong"}` |
| **The definitive test:** exact bypass-probe from the validation report, re-run against `salesos_app` | **Returns only the querying tenant's row** — the identical FORCE-enabled policy that leaked both tenants under `salesos` now isolates correctly under `salesos_app`, with zero changes to the policy itself |
| Full backend regression suite | 1,957 passed / 11 failed / 4 skipped — identical to the pre-change baseline; the 11 are the same pre-existing, unrelated failures carried since Sprint 01. Zero regressions from the engine split. |

---

## Explicitly Not Done

- CI, staging, and the self-hosted prod template were not touched. They remain exactly as before — unbroken (the fallback guarantees this), unprotected (no `salesos_app` there yet).
- The live Railway production database was not connected to, per the original validation report's own stated Rules of Engagement, unchanged by this pass.
- No investigation into why the local backend's migrations had never run automatically before this session — flagged, not diagnosed.

## Recommendation

R-14 is closed for local dev, with end-to-end proof, not a self-report. It remains open and blocking for Sprint 03's STORY-02-01 against any other environment until the same three steps (provision `salesos_app`, set `APP_POSTGRES_PASSWORD`, re-run the bypass-probe there specifically) are repeated for that environment.
