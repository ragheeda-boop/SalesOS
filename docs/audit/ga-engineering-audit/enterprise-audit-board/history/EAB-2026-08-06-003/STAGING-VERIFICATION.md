# Staging Verification — SalesOS (Railway `staging`)

**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-06 · **Mode:** VERIFY FIRST (read-only)
**Method:** live HTTP probes, GraphQL (`railway api`), `railway logs`, `railway variable list` (redacted), and **direct SQL** through a temporary `railway connect --tunnel-only` session + disposable `postgres:18` container.
**Validation label:** **machine verified** (live) — no changes made to any environment.

---

## 1. Reachability & health (live, 2026-08-06)

- `GET https://salesos-staging.up.railway.app/health` → **200**
- Payload: `{"status":"ok","version":"5.1.0-rc1","database":"connected","cache":"connected","graph":"connected","kafka":"in_memory","redis":"connected","rate_limiter":"active","uptime_seconds":465240.4}`
- `GET /ready` → **404** (no such route — identical to production)
- `GET /openapi.json` → 200 (621,272 B — differs from production 881,643 B)

## 2. Deployment provenance

| Field | Value |
|-------|-------|
| Last deploy | `98bf85bf-89cc-4198-97d9-d477b2734a23`, 2026-08-01T11:34:53Z, status SUCCESS |
| Image digest | `sha256:1f7f845fd772…` |
| Deploy origin | CLI `railway-skill-dec120-deploy` — "DEC-120 B: tip `0bd73fc` app_database_url wiring to staging (no GHCR)" |
| Source commit | `0bd73fc5672e61aee8fafc9de114492ceb9f2f0c` (2026-08-01) |
| vs production | **409 commits behind** the prod snapshot `4750038c` (which is itself 3 behind local HEAD `2538a7d`) |

Deploy is **manual only** — not driven by CI (see §5).

## 3. Database (direct SQL via tunnel — machine verified)

| Check | Staging value | Production value |
|-------|---------------|------------------|
| `alembic_version` | **`b7e2f65a3f07`** | `d1a8c35e7f09` |
| `companies` count | **0** | 141,221 |
| `tenants` count | **0** | 57 |
| `audit_logs` count | **1** | 683+ |
| `PGPASSWORD` | hash `246F5CB1FF` | `D7A9844452` (different) |
| `DATABASE_URL` | hash `67E6C68423` (== staging Postgres var) | `971975109E` (== prod Postgres var) |

**Isolation: VERIFIED.** Staging DB is a separate Postgres instance, **empty of production data**, on an older Alembic migration head. Each app connects to its own environment's Postgres (SalesOS `DATABASE_URL` hash matches the same environment's Postgres `DATABASE_URL` hash).

## 4. Runtime config (redacted hashes only)

| Variable | Staging | Production | Note |
|----------|---------|-----------|------|
| `ENV` | `staging` | `production` | |
| `DEBUG` | **`true`** | `false` | staging runs debug mode |
| `FRONTEND_URL` | `<EMPTY>` | present | staging has no FE URL var |
| `GOOGLE_REDIRECT_URI` | missing | present | no Google callback on staging |
| `SSO_GOOGLE_CLIENT_ID` | missing | present | **no Google SSO on staging** |
| `SSO_GOOGLE_CLIENT_SECRET` | `<EMPTY>` | present | |
| `FEATURE_HTTPONLY_ACCESS_COOKIE` | missing | `false` | auth cookie flag absent on staging |
| `FEATURE_AI_COPILOT` | `false` | `false` | SAME |
| `JWT_SECRET_KEY` | `sha256=06823858C2` | `sha256=06823858C2` | **SAME as production** |
| `SECRET_KEY` | `sha256=73534985DF` | `sha256=73534985DF` | **SAME as production** |
| `NEXT_PUBLIC_API_URL` | `https://sales-os-jet.vercel.app/` | same | → no staging frontend |
| `ALLOWED_HOSTS` | prod list + `https://salesos-staging.up.railway.app` | prod list | |

## 5. CI/CD wiring

- GitHub env `staging` exists (id 18978929506) with **0 secrets**.
- Repo secrets lack `RAILWAY_STAGING_SERVICE_ID` / `RAILWAY_STAGING_ENVIRONMENT_ID`.
- `deploy-staging.yml` **soft-skips** on every run (`staging_ready=false`) and requires manual `CONFIRM-STAGING-DEPLOY` input even when secrets exist.
- Consequence: staging is **not** deployable/rollbackable via the pipeline; it is CLI-manual only.

## 6. Stability (logs)

- 500-line window spans the entire uptime (boot 2026-08-01T11:36 → now, cache hit "cached since 4.645e+05s").
- Uptime ≈ **5.38 days** with **no restarts** in buffer.
- Warnings only: FastAPI "Duplicate Operation ID" startup warnings (6) + scraper auth-config warnings. **No ERROR / Traceback / CRITICAL.**

## 7. Verdict

| Criterion | Result |
|-----------|--------|
| Reachable / serving `/health` | PASS |
| Isolated (own PG/Redis/neo4j, empty DB) | PASS |
| Stable (no crashes/restarts in window) | PASS |
| Code parity with prod snapshot | **FAIL — 409 commits behind** |
| Data parity (realistic volume) | **FAIL — empty DB** |
| Config parity (DEBUG/SSO/FE vars) | **FAIL — multiple gaps** |
| Deploy/rollback via pipeline | **FAIL — manual only** |
| Secret isolation (JWT/SECRET_KEY) | **FAIL — identical to production** |

**Staging is a real, stable, isolated environment — but it is NOT production-parity.**
