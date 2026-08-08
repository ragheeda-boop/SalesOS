# Staging vs Production — Verified Diff (UPDATED)

**Run:** EAB-2026-08-06-003 · **Update:** 2026-08-07 · **Mode:** EXECUTE + VERIFY
**All comparisons are machine verified (live probes / GraphQL / SQL / redacted var hashes).**
**Supersedes:** the 2026-08-06 version of this file (staging was 409 commits behind).

| # | Dimension | Staging (2026-08-07) | Production | Parity |
|---|-----------|----------------------|-----------|:------:|
| 1 | Source commit | `4750038c` (baseline freeze; deployed from clean worktree) | `4750038c` | **SAME** |
| 2 | Backend code (schema) | `/openapi.json` 881,643 B | `/openapi.json` 881,643 B | **SAME** (byte-identical) |
| 3 | Alembic migration | `e5f9a32b0c08` (repo head) | `d1a8c35e7f09` | **STAGING AHEAD — prod is 11 revisions behind its own deployed code** |
| 4 | Data volume | companies=0, tenants=0, audit_logs=1 (clean baseline) | companies=141,221, tenants=57, audit_logs=683 | Intentionally empty (staging pre-seed) |
| 5 | Postgres volume size | small (clean) | 1,619.9 MB | N/A (data difference) |
| 6 | `DEBUG` | `false` | `false` | **SAME** |
| 7 | Google SSO (`SSO_GOOGLE_CLIENT_ID/SECRET`, `GOOGLE_REDIRECT_URI`) | `GOOGLE_REDIRECT_URI` set for staging; **CLIENT_ID/SECRET absent — needs own Google OAuth app** | configured | PARTIAL — human task |
| 8 | `FRONTEND_URL` | `https://sales-os-jet.vercel.app` | `https://sales-os-jet.vercel.app` | **SAME** |
| 9 | `FEATURE_HTTPONLY_ACCESS_COOKIE` | `false` | `false` | **SAME** |
| 10 | `JWT_SECRET_KEY` | `sha256=BF9D04AA99` (NEW) | `sha256=06823858C2` | **DIFFERENT — isolated** |
| 11 | `SECRET_KEY` | `sha256=AB16182BED` (NEW) | `sha256=73534985DF` | **DIFFERENT — isolated** |
| 12 | `DATABASE_URL` / DB creds | isolated (staging) | isolated (prod) | Isolated (OK) |
| 13 | `REDIS_URL` | isolated (staging) | isolated (prod) | Isolated (OK) |
| 14 | Neo4j | **connected** | **connected** (repaired 2026-08-07) | **SAME** |
| 15 | Deploy method | manual CLI (baseline deploy + worker/beat synced manually) | CI `deploy.yml` (push master) | PARTIAL — staging CI not yet exercised |
| 16 | CI/CD wiring | `RAILWAY_STAGING_SERVICE_ID` + `ENVIRONMENT_ID` repo secrets set; `deploy-staging.yml` hard-fails if absent; YAML validated (5 jobs) | active, health gate | **FIXED** (not yet triggered) |
| 17 | Rollback path | Railway redeploy (UI/CLI) — untested | Railway redeploy (UI/CLI) | PARTIAL for staging |
| 18 | WAL archive / PITR | **absent** on staging Postgres | ON, base+WAL to `salesos-pitr-w-…` | FAIL |
| 19 | Offsite backup | none configured | `salesos-backups-iwrweogrr` | FAIL |
| 20 | Restart this session | restarted 2026-08-06 21:55 (env + secret changes) | last deploy 2026-08-05 21:29 | — |
| 21 | `/health` | 200, all subsystems connected (`database`, `redis`, `graph` = connected) | 200, all subsystems connected | **SAME** |
| 22 | `/docs` (DEBUG) | 404 (docs disabled) | 404 (docs disabled) | **SAME** |
| 23 | Frontend | FE points to Vercel prod URL | Vercel `sales-os-jet.vercel.app` | **SAME** |
| 24 | Replicas | 1 | 1 | SAME |
| 25 | `SERVICE_VERSION` / `EVENT_BUS_TYPE` / `POSTGRES_*` / `NEXT_PUBLIC_API_URL` | same values | same values | SAME |
| 26 | celery-worker | **redeployed 2026-08-07 to `4750038c`, `Dockerfile.railway`** (was 409 commits behind) | `Dockerfile.railway`, prod commit | **SAME** |
| 27 | celery-beat | **redeployed 2026-08-07 to `4750038c`, `Dockerfile.railway`** (was 409 commits behind) | `Dockerfile`, prod commit | **SAME code** (minor build-path diff) |
| 28 | Postgres `max_connections` | **100** | **500** | **FAIL — capacity gap** |
| 29 | Postgres connection saturation | **cleared 2026-08-07 13:41 UTC** (active=12/100 after worker/beat redeploy) | healthy (active=15/500) | **FIXED** (capacity gap remains) |

## Severity classification (2026-08-07)

| Severity | Items |
|----------|-------|
| **P0 — blocks soak start** | none at code level. **Human prerequisite:** staging Google OAuth app (SSO_CLIENT_ID/SECRET). |
| **P1 — parity blocker / risk** | 3 (**prod DB 11 revisions behind own code — needs human-approved prod migration to `e5f9a32b0c08`**), 18 (staging WAL/PITR absent), 19 (staging offsite backup none), 28 (staging max_connections 100 vs prod 500) |
| **P1 — security** | none remaining between environments: JWT/SECRET keys now distinct (rows 10–11). Staging password `VPGcEjKY…` was exposed once in a transcript — **rotate the staging DB password** at next human touchpoint. |
| **OK — isolation verified** | 12, 13, 24, 25 |

## Bottom line

Staging now runs **the exact production baseline commit** with an **identical OpenAPI schema**, `DEBUG=false`, **distinct secrets**, working Neo4j in **both** environments, and CI wiring in place. Remaining gaps are operational capacity/config (staging WAL/backups/max_connections) and one human prerequisite (staging Google OAuth app) — plus the **critical production finding** that prod's DB is behind its own deployed code. A soak can start on staging once the Google OAuth app exists and the WAL/backup gap is accepted or closed.
