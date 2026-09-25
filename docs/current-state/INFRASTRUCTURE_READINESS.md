# INFRASTRUCTURE READINESS — 2026-08-24

---

## Readiness Matrix

| Component | Current | Required | Evidence | Status |
|-----------|---------|----------|----------|:------:|
| **Railway (Backend)** | Deployed, single authoritative config | Single config (root railway.json + Dockerfile.railway) | `railway.json` (root) — stale `salesos/railway.json` archived | ✅ RESOLVED (Phase A) |
| **PostgreSQL** | pgvector:pg16, RLS on 86+ tables | Production-ready with PITR | `docker-compose.prod.yml`, DR_RUNBOOK.md | ✅ READY |
| **Redis** | Redis 7, AOF persistence, 256MB | Production-ready | `docker-compose.prod.yml:202-226` | ✅ READY |
| **Kafka** | IN-MEMORY only | Decision required | `EVENT_BUS_TYPE=in_memory` | ⚠️ DECISION NEEDED |
| **Neo4j** | OFFLINE per ADR-108 | Keep offline | ADR-108 | ✅ BY DESIGN |
| **OAuth (Google)** | Configured but staging not isolated | Staging + production separate clients | `OAUTH-STAGING-SETUP-2026-08-22.md` | ❌ NOT STARTED |
| **Backups** | Scripts exist, prod cron configured | Automated schedule + restore drill | `backup-db.sh`, `docker-compose.prod.yml:505-544` | ⚠️ PARTIAL |
| **CI/CD** | GitHub Actions, 9 workflows | All stages green | `.github/workflows/` | ✅ READY |
| **Monitoring** | Prometheus + Grafana in compose | Production monitoring | `docker-compose.prod.yml` observability profile | ⚠️ DEV ONLY |
| **SSL/TLS** | Caddy reverse proxy in prod compose | Production SSL | `docker-compose.prod.yml` | ✅ READY |

---

## Detailed Findings

### Railway

| Aspect | Status | Notes |
|--------|:------:|-------|
| Config conflict | ⚠️ | Two `railway.json` files; which is active unknown |
| Build | ✅ | Dockerfile.railway multi-stage, non-root |
| Start command | ✅ | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| preDeployCommand | ✅ | `alembic upgrade head` added to root railway.json (Phase A) |
| Health check | ✅ | `/health` endpoint (root config) |
| Rollback | ✅ | `scripts/railway_rollback.sh` |
| Celery health | ❌ | `Dockerfile.railway.celery` has no HEALTHCHECK |
| PID 1 handling | ✅ | Root Dockerfile updated with tini (Phase A) |

**RESOLVED:** Railway config conflict fixed in Phase A. Root `railway.json` is single source of truth (CI deploy workflow confirmed). Stale `salesos/railway.json` archived to `docs/archive/railway.json.stale`.

### PostgreSQL

| Aspect | Status | Notes |
|--------|:------:|-------|
| Version | ✅ | pgvector:pg16 |
| RLS | ✅ | 86+ tables with tenant isolation |
| Migrations | ✅ | 100 migrations, CI gate verified |
| Connection pooling | ✅ | PgBouncer configured |
| Backup script | ✅ | pg_dump, checksums, S3 upload, retention |
| PITR | ✅ | WAL archiving drill-proven |
| Restore drill | ❌ | No automated restore verification |
| Managed backups | ❌ | Railway managed schedule NOT ENABLED |

### Redis

| Aspect | Status | Notes |
|--------|:------:|-------|
| Version | ✅ | Redis 7 Alpine |
| Persistence | ✅ | AOF enabled |
| Memory | ✅ | 256MB, LRU eviction |
| Password | ⚠️ | Optional via env var |
| Sentinel/Cluster | ❌ | Single instance |
| Monitoring | ✅ | Redis exporter for Prometheus |

### Kafka

| Aspect | Status | Notes |
|--------|:------:|-------|
| Deployment | ❌ | NOT in docker-compose.prod.yml |
| Mode | — | In-memory only |
| Event ordering | ✅ | Priority-based subscriber ordering |
| DLQ | ✅ | Postgres-backed persistent DLQ |
| Replay | ⚠️ | In-memory only; no replay across restarts |

**Decision required:** See `docs/architecture/KAFKA_PRODUCTION_DECISION.md`

### OAuth

| Aspect | Status | Notes |
|--------|:------:|-------|
| SSO secrets | ✅ | Fail-closed (empty defaults) |
| CSRF state | ✅ | Redis-backed with memory fallback |
| Token encryption | ✅ | Fernet (AES-128-CBC + HMAC) |
| Staging isolation | ❌ | NOT STARTED — shared client across envs |
| Google OAuth setup | ❌ | Client ID/Secret must be provided |
| Microsoft OAuth | ❌ | Client ID/Secret must be provided |

### CI/CD

| Aspect | Status | Notes |
|--------|:------:|-------|
| Lint (Ruff + ESLint) | ✅ | Stage 1 |
| Type check (MyPy + tsc) | ✅ | Stage 2 |
| Unit tests | ✅ | Stage 3, 55% coverage gate |
| Integration tests | ✅ | Stage 4, Postgres + Redis services |
| Security scanning | ✅ | Stage 5, 5 scanners |
| Build (GHCR) | ⚠️ | QUARANTINED (DEC-150 B) |
| Deploy pipeline | ✅ | Schema drift + health + parity gates |
| K8s deploy | ⚠️ | QUARANTINED (DEC-149) |

### Monitoring

| Aspect | Status | Notes |
|--------|:------:|-------|
| Prometheus | ✅ | In dev compose |
| Grafana | ✅ | In dev compose |
| Alertmanager | ✅ | In dev compose |
| Production deploy | ❌ | Observability profile not in prod compose |
| SLA monitoring | ✅ | In health endpoints |
| Structured logging | ✅ | JSON format in prod compose |

---

## Critical Gaps

| Gap | Severity | Owner | Resolution |
|-----|:--------:|-------|------------|
| Railway config conflict | P0 | DevOps | ✅ RESOLVED (Phase A) |
| OAuth staging not started | P1 | DevOps | Create separate Google OAuth client |
| Kafka production decision | P1 | Architecture | Decide: ACTIVATE / DEFER / REJECT |
| Managed backups not enabled | P1 | Platform | Enable Railway managed backup schedule |
| No automated restore verification | P2 | DevOps | Add restore-and-verify CI job |
| Monitoring not in prod | P2 | DevOps | Deploy observability stack to prod |
| Celery health check missing | P2 | DevOps | Add HEALTHCHECK to Dockerfile.railway.celery |
