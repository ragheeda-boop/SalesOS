# Environment Map — SalesOS Railway + Vercel

**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-06 · **Mode:** VERIFY FIRST (read-only, no changes made)
**Author:** agent ops verification · **Validation:** machine verified (live probes + GraphQL + local psql via tunnel)
**Evidence:** [evidence/ops01-staging/ops01-env-verification.json](./evidence/ops01-staging/ops01-env-verification.json)

---

## 1. Railway account & projects

Account: `ragheed.a@ratlfintech.com` · CLI: `railway` (local, authenticated).

`railway list` → 3 projects:

| Project | Role | Contents |
|---------|------|----------|
| **responsible-comfort** | **SalesOS** — production + staging envs | See below |
| luminous-recreation | NOT SalesOS | Redis service only |
| positive-strength | NOT SalesOS | Postgres service only (deploy reason: rollback) |

Only `responsible-comfort` is relevant to SalesOS. The other two are excluded from GA scope.

## 2. responsible-comfort — environments & services

Project ID: `96032c9a-38cf-4792-8168-b78d5353e26b`

| Environment | Env ID | SalesOS domain | Last SalesOS deploy |
|-------------|--------|----------------|---------------------|
| production | `652c450a-1473-4445-98e4-15aceefd49c3` | `https://salesos-production-96c0.up.railway.app` (region sfo) | `bdce3450` 2026-08-05T21:29:24Z |
| staging | `5ce7864a-27c5-43c7-847d-667aecfbf773` | `https://salesos-staging.up.railway.app` | `98bf85bf` 2026-08-01T11:34:53Z |

Services are project-level; each environment runs its own **instance** + own deployment of each service.

| Service | Service ID | Production | Staging |
|---------|-----------|-----------|---------|
| SalesOS (backend) | `668122aa-523b-4ec3-a7d8-c3b579c90f66` | deploy `bdce3450` (Aug 5), digest `sha256:11b14ac5…` | deploy `98bf85bf` (Aug 1), digest `sha256:1f7f845f…` (CLI `skill:use-railway` DEC-120 B) |
| Postgres | `2744b8e0-0f7a-4b95-acd4-57415d95bd0f` | archive-managed, WAL on, 1619.9MB volume | no `WAL_ARCHIVE_*`, 163MB volume |
| Postgres-wFil | `9b452e57-caf2-4406-b4f3-0dc12fced7b9` | deployed Jul 26 | deployed Jul 28 |
| Postgres-gg8s | `7afd1297-f429-44c9-924f-6edaa95aacd4` | deployed Jul 26 | deployed Jul 28 |
| Redis | `b57af540-68e5-4ee1-bc1a-22bccb73bad3` | deployed Jul 26 | deployed Jul 28 |
| neo4j | prod: `2e84ce72-6381-42c1-85dd-7169449e3582` (`neo4j-prod`, **OFFLINE**) / staging: `71717189-5ec9-45b7-90e1-0aa37133d1c0` | **OFFLINE — no active deployment, `/health` graph=unavailable** | connected (`graph=connected`) |
| celery-worker | prod `90499aec…` (Copy 3091) / staging `c4f37167…` | deployed Aug 5 | deployed Jul 29 |
| celery-beat | prod `485f439a…` (Copy 5338) / staging `e66f1d0d…` | deployed Aug 1 | deployed Jul 29 |

## 3. Object storage (project-level)

| Bucket | Actual name | Used by |
|--------|-------------|---------|
| salesos-backups | `salesos-backups-iwrweogrr` | OPS-01 row 1 offsite pg_dump (S3-compatible) |
| salesos-pitr | `salesos-pitr-w-857q3fjjrr` | OPS-01 rows 2–3 pgBackRest WAL + base backup |

Backup/PITR infrastructure exists at project level (backed by production Postgres archive). Staging Postgres has **no** `WAL_ARCHIVE_*` config and no PITR.

## 4. Frontend — Vercel

- App: `sales-os` → `https://sales-os-jet.vercel.app` (single Vercel app, Git integration, build from `master`, Root Directory `salesos/frontend`).
- `NEXT_PUBLIC_API_URL=https://sales-os-jet.vercel.app/` is **identical in both envs** → there is **no staging-specific frontend**; any FE build talks to the production Vercel URL.
- Production deploy: push to `master` → `deploy.yml` (`railway up` backend) + Vercel Git (frontend). `deploy-production.yml` (K8s) is **QUARANTINED** under DEC-149.

## 5. GitHub Actions wiring

| Workflow | Trigger | Target | Status |
|----------|---------|--------|--------|
| `deploy.yml` | push `master` + manual | Railway production (single-env) + Vercel | ACTIVE |
| `deploy-staging.yml` | manual dispatch only | Railway staging | **SOFT-SKIP** — requires `CONFIRM-STAGING-DEPLOY` input AND `RAILWAY_STAGING_SERVICE_ID`/`RAILWAY_STAGING_ENVIRONMENT_ID` secrets; both absent |
| `deploy-production.yml` | manual + quarantine ACK | K8s (legacy) | QUARANTINED (DEC-149) |

GitHub repo secrets (5, repo-level): `RAILWAY_TOKEN`, `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID`, `RAILWAY_ENVIRONMENT_ID`, `RAILWAY_HEALTH_URL`. GitHub environment `staging` exists (id 18978929506) but has **0 secrets**; environment `Production` also 0 (all at repo level).

## 6. Topology diagram

```
GitHub (ragheeda-boop/SalesOS, master)
 ├─ push master → deploy.yml → railway up --ci → Railway prod env (SalesOS backend)
 │                        └→ Vercel (sales-os-jet.vercel.app) — frontend
 ├─ deploy-staging.yml → SOFT-SKIP (no RAILWAY_STAGING_* secrets) — staging is manual-only today
 └─ deploy-production.yml → QUARANTINED (K8s, DEC-149)

Railway project responsible-comfort
 ├─ production env: SalesOS + celery-worker/beat + Postgres(WAL)+Redis+Postgres-wFil+Postgres-gg8s + neo4j-prod(OFFLINE)
 ├─ staging env:    SalesOS + celery-worker/beat + Postgres(no-WAL)+Redis+Postgres-wFil+Postgres-gg8s + neo4j(connected)
 └─ buckets: salesos-backups-iwrweogrr, salesos-pitr-w-857q3fjjrr
```
