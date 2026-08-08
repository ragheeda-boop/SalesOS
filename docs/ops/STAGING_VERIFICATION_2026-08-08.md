# Staging Verification Report — 2026-08-08

> **Status:** VERIFICATION IN PROGRESS
> **Source:** `deploy-staging.yml`, `.env.staging`, `docker-compose.staging.yml`
> **Previous audit:** [STAGING_PARITY.md](../../ops/STAGING_PARITY.md) (2026-07-25)

---

## Quick Assessment

| Check | Status | Detail |
|-------|:------:|--------|
| Compose file exists | PASS | `infra/staging/docker-compose.staging.yml` — 447 lines, 16 services |
| Deploy workflow exists | PASS | `.github/workflows/deploy-staging.yml` — 215 lines |
| `.env.staging` exists | PASS | 58 lines |
| `.env.staging.example` exists | PASS | 106 lines |
| Secrets are real values | FAIL | 4/8 secrets = `CHANGE_ME_*` |
| Flag parity with prod | FAIL | `SALESOS_DEBUG=true` (should be `false`) |
| SMTP configured | FAIL | All SMTP vars missing |
| SSO/OIDC configured | FAIL | All SSO vars missing |
| Sentry configured | FAIL | `SENTRY_DSN=` empty |
| Rate limiting | FAIL | RATE_LIMIT_* vars missing |
| Celery broker | FAIL | CELERY_* vars missing |
| CORS origins | FAIL | CORS_ORIGINS missing |
| Audit retention | FAIL | AUDIT_* vars missing |

---

## Critical Blocks (must fix before staging is useful)

### P0: CHANGE_ME passwords

```ini
POSTGRES_PASSWORD=CHANGE_ME_STAGING_PASSWORD    # ← MUST be a real 64+ char token
NEO4J_PASSWORD=CHANGE_ME_STAGING_NEO4J          # ← MUST be a real token
JWT_SECRET=CHANGE_ME_USE_OPENSSL_rand_hex_32    # ← MUST be 64+ char distinct from prod
GRAFANA_PASSWORD=CHANGE_ME_STAGING_GRAFANA      # ← MUST be a real token
```

**Fix:** generate with `python -c "import secrets; print(secrets.token_hex(32))"` for each. Never reuse prod values.

### P0: DEBUG=true in staging

```yaml
# docker-compose.staging.yml:219
- SALESOS_DEBUG=true
```

Staging should mirror production: **change to `false`**. Debug mode enables traceback details in responses and may disable security middleware.

### P1: Missing env vars (prod has them, staging doesn't)

```ini
# Add these to .env.staging:

# SMTP (use Mailpit or similar for staging)
SMTP_HOST=
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=staging@staging.local

# SSO / OIDC (use a test OAuth app for staging)
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_ISSUER=
OIDC_REDIRECT_URI=

# Sentry
SENTRY_DSN=
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.1

# Rate Limiting
RATE_LIMIT_WINDOW=60
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_BURST=200

# Celery / Tasks
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Audit
AUDIT_RETENTION_DAYS=90
AUDIT_LOG_LEVEL=INFO
```

### P1: Feature flag alignment

Staging compose currently runs with all features enabled by default. Per STAGING_PARITY.md, 5 flags differ between staging and prod. The `.env.staging` should explicitly set them to match production:

```ini
FEATURE_SEARCH=false
FEATURE_GRAPH=false
FEATURE_ENTITY=false
FEATURE_DECISION=false
FEATURE_AI_COPILOT=false
FEATURE_AI_COPILOT_STUB=true
```

---

## Verification Steps (after fixing P0 items)

### Step 1: Startup smoke test

```bash
cd salesos/infra/staging
docker compose -f docker-compose.staging.yml up -d
```

Expected: 14/16 services healthy (without backup profile):

| Service | Healthcheck | Expected |
|---------|:----------:|:--------:|
| postgres | `pg_isready` | healthy |
| pgbouncer | `pg_isready` | healthy |
| neo4j | HTTP `:7474` | healthy |
| redis | `redis-cli ping` | healthy |
| zookeeper | `ruok` | healthy |
| kafka | `kafka-broker-api-versions` | healthy |
| migrations | `alembic upgrade head` | exit 0 |
| backend | `curl :8000/health` | healthy |
| frontend | `wget :3000` | healthy |
| prometheus | `/-/ready` | healthy |
| grafana | `/api/health` | healthy |
| alertmanager | `/-/healthy` | healthy |
| postgres-exporter | `/metrics` | healthy |
| redis-exporter | `/metrics` | healthy |

### Step 2: Health endpoint

```bash
curl -s http://localhost:8000/health | jq .
```

Verify: `database.connected: true`, `redis` connected, `event_bus` status.

### Step 3: Alembic migrations

```bash
docker compose -f docker-compose.staging.yml exec backend alembic current
```

Should show the same head as production.

### Step 4: Neo4j connectivity

```bash
docker compose -f docker-compose.staging.yml exec backend python -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', '${NEO4J_PASSWORD}'))
with d.session() as s: print('Neo4j:', s.run('RETURN 1').single())
"
```

### Step 5: Data seeding (staging baseline)

```bash
# Minimal seed for staging — avoids the full production 141k companies
docker compose -f docker-compose.staging.yml exec backend python -c "
from app.database import async_session; print('DB accessible')
"
# Or: run the staging-specific seed if one exists
```

---

## Verification Scorecard

| Step | Command | Expected | Actual |
|------|---------|:--------:|:------:|
| 1. Startup | `docker compose up -d` | 14/14 healthy | |
| 2. Health | `curl :8000/health` | 200, db=true, redis=true | |
| 3. Migrations | `alembic current` | Head matches prod | |
| 4. Neo4j | `cypher-shell RETURN 1` | connected | |
| 5. Frontend | `curl :3000` | 200 | |
| 6. Grafana | `curl :3001/api/health` | 200 | |
| 7. Alertmanager | `curl :9093/-/healthy` | 200 | |

> **Fill the Actual column with results after each verification step.**

---

## What's NOT tested in staging (acceptable)

| Item | Reason |
|------|--------|
| SSL/TLS termination | Self-signed/localhost; prod uses ingress |
| DB read replicas | Single PostgreSQL; prod has read-replica |
| Multi-node K8s | Single-node compose; architecture acceptable |
| Google OAuth live | Needs real OAuth credentials (test app) |
| Stripe live | Needs Stripe sandbox keys |
| 141k company load | Not needed; staging baseline can be lighter |

---

## Next Actions

```
[ ] Generate real staging passwords (P0)
[ ] Set SALESOS_DEBUG=false in compose (P0)
[ ] Add missing env vars (SMTP, SSO, Sentry, RateLimit, Celery, CORS, Audit) (P1)
[ ] Set feature flags to match prod (P1)
[ ] Run 14-service startup smoke test
[ ] Verify /health endpoint
[ ] Verify Alembic migrations match prod
[ ] Record results in scorecard above
[ ] Run Neo4j backup/restore drill on staging (per NEO4J_VOLUME_RUNBOOK.md)
[ ] Run credential rotation drill on staging (per CREDENTIAL_ROTATION_RUNBOOK.md)
[ ] 72h soak: leave staging running, monitor /health every 5 min, record any crashes
```
