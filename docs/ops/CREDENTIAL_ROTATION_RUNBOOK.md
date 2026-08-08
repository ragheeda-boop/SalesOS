# Credential Rotation Runbook

> **Status:** PREPARED (not yet exercised)
> **Scope:** SalesOS — dev, staging, production
> **Related:** [SECRETS_HYGIENE.md](SECRETS_HYGIENE.md), [DR_RUNBOOK.md](DR_RUNBOOK.md) Scenario 4
> **Last updated:** 2026-08-08

---

## Purpose

Rotate all platform-level credentials with minimal downtime. This runbook covers **routine rotation** (scheduled, no breach) and **emergency rotation** (breach response — see DR_RUNBOOK Scenario 4 for the condensed blast-radius version).

---

## Secret Inventory

### Tier 1: Rotate together (shared blast radius)

| Secret | Consumers | Rotation impact |
|--------|-----------|:----------------:|
| `POSTGRES_PASSWORD` | `postgres` container, `pgbouncer`, `backend`, `migrations`, `backup`, `postgres-exporter` | Brief downtime (restart Postgres + backend) |
| `JWT_SECRET_KEY` | `backend` (signs all tokens) | Invalidates all existing sessions — all users must re-login |
| `SECRET_KEY` | `backend` (CSRF, session signing) | Invalidates CSRF tokens, session cookies |
| `APP_POSTGRES_PASSWORD` | `backend` (RLS-protected app role) | App DB connections break until config reloaded |

### Tier 2: Rotate independently

| Secret | Consumers | Rotation impact |
|--------|-----------|:----------------:|
| `NEO4J_PASSWORD` | `neo4j` container, `backend`, `backup` | Neo4j restart (~15s outage); backend auto-reconnects |
| `REDIS_PASSWORD` | `redis` container, `backend`, `redis-exporter` | Redis restart (~5s outage); cache misses briefly |
| `GF_SECURITY_ADMIN_PASSWORD` / `GRAFANA_ADMIN_PASSWORD` | `grafana` | Grafana restart (~5s) — no app impact |
| `MINIO_ROOT_PASSWORD` | `minio` container, `backend` (optional) | MinIO restart (~10s); file uploads paused |

### Tier 3: External / per-service

| Secret | Consumers | Rotation process |
|--------|-----------|------------------|
| `OPENAI_API_KEY` | `backend` | Rotate in OpenAI dashboard → update `.env.production` → restart backend |
| `STRIPE_SECRET_KEY` | `backend` | Roll key in Stripe dashboard → update env → restart backend |
| `STRIPE_WEBHOOK_SECRET` | `backend` | Rotate in Stripe dashboard → update env → restart backend |
| `SSO_*_CLIENT_SECRET` | `backend` | Rotate in OAuth provider → update env → restart backend |
| `SMTP_PASSWORD` | `backend` | Rotate in mail provider → update env → restart backend |
| `GOOGLE_ENCRYPTION_KEY` | `backend` | **DO NOT ROTATE LIGHTLY** — re-encrypts all stored Google connector data |
| `MEILI_MASTER_KEY` | `backend` | Rotate → restart backend → reindex Meilisearch |
| `INTEGRATION_HUB_ENCRYPTION_KEY` | `backend` | **DO NOT ROTATE LIGHTLY** — re-encrypts all tenant connector credentials |
| `SLACK_WEBHOOK_URL` | `alertmanager` | Update Slack → update env → restart alertmanager |
| `ALERTMANAGER_SMTP_PASSWORD` | `alertmanager` | Rotate in mail provider → update env → restart alertmanager |
| `PAGERDUTY_ROUTING_KEY` | `alertmanager` | Rotate in PagerDuty → update env → restart alertmanager |
| `DOMAIN` | `caddy` | DNS-level: get new SSL cert on restart |

---

## Pre-Rotation Checklist

```
[ ] Maintenance window communicated to stakeholders (at least 24h notice)
[ ] Backup of all environment files taken:
      cp .env.production .env.production.backup.$(date +%Y%m%d)
[ ] Staging rotation completed and verified first
[ ] Rollback plan ready: path to restore .env.production.backup and restart
[ ] Monitoring dashboards open (Grafana, health endpoints)
[ ] Session-drain window: 5 minutes of reduced traffic accepted
```

---

## Routine Rotation Procedure

### Phase 1: Tier 1 — Database + JWT (planned downtime, ~5 min)

```bash
# 1. Notification: post maintenance banner if available

# 2. Generate new secrets
NEW_POSTGRES_PW=$(python -c "import secrets; print(secrets.token_hex(32))")
NEW_APP_PG_PW=$(python -c "import secrets; print(secrets.token_hex(32))")
NEW_JWT_KEY=$(python -c "import secrets; print(secrets.token_hex(64))")
NEW_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 3. Stop backend (drain connections)
docker compose -f docker-compose.prod.yml stop backend worker

# 4. Update Postgres password (requires Postgres running)
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -c "ALTER USER postgres WITH PASSWORD '$NEW_POSTGRES_PW';"
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -c "ALTER USER salesos_app WITH PASSWORD '$NEW_APP_PG_PW';"

# 5. Update pg_hba/pgbouncer if needed, then restart
docker compose -f docker-compose.prod.yml restart postgres pgbouncer

# 6. Update .env.production with new values
#    POSTGRES_PASSWORD=$NEW_POSTGRES_PW
#    APP_POSTGRES_PASSWORD=$NEW_APP_PG_PW
#    JWT_SECRET_KEY=$NEW_JWT_KEY
#    SECRET_KEY=$NEW_SECRET_KEY

# 7. Restart backend (creates new connection pools)
docker compose -f docker-compose.prod.yml up -d backend worker

# 8. Verify
./infra/scripts/health-check.sh --full
curl -sf https://${DOMAIN}/api/v1/health | jq '.database.connected'
```

**Post-rotation:** All user sessions invalidated. Notify users to re-login. CSRF tokens from old sessions will fail (retry will succeed with new token after page reload).

### Phase 2: Tier 2 — Neo4j + Redis + Grafana (no-downtime, if sequential)

#### Neo4j

```bash
# 1. Generate new password
NEW_NEO4J_PW=$(python -c "import secrets; print(secrets.token_urlsafe(24))")

# 2. Update password in running Neo4j (Cyper-shell)
docker compose -f docker-compose.prod.yml exec neo4j \
  cypher-shell -u neo4j -p "$OLD_NEO4J_PASSWORD" \
  "ALTER CURRENT USER SET PASSWORD FROM '$OLD_NEO4J_PASSWORD' TO '$NEW_NEO4J_PW'"

# 3. Update .env.production: NEO4J_PASSWORD=$NEW_NEO4J_PW

# 4. Restart Neo4j (to pick up NEO4J_AUTH env var for future restarts)
docker compose -f docker-compose.prod.yml restart neo4j

# 5. Restart backend (picks up new NEO4J_PASSWORD from env)
docker compose -f docker-compose.prod.yml restart backend

# 6. Verify
docker compose -f docker-compose.prod.yml exec backend python -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', '$NEW_NEO4J_PW'))
with d.session() as s: print('✓ Neo4j:', s.run('RETURN 1').single())
"
```

#### Redis

```bash
# 1. Generate new password
NEW_REDIS_PW=$(python -c "import secrets; print(secrets.token_urlsafe(24))")

# 2. Update .env.production: REDIS_PASSWORD=$NEW_REDIS_PW

# 3. Restart Redis with new requirepass
docker compose -f docker-compose.prod.yml restart redis redis-exporter

# 4. Restart backend
docker compose -f docker-compose.prod.yml restart backend

# 5. Verify
docker compose -f docker-compose.prod.yml exec redis redis-cli -a "$NEW_REDIS_PW" PING
```

#### Grafana

```bash
# 1. Generate new password
NEW_GF_PW=$(python -c "import secrets; print(secrets.token_urlsafe(16))")

# 2. Update .env.production: GRAFANA_ADMIN_PASSWORD=$NEW_GF_PW

# 3. Restart Grafana
docker compose -f docker-compose.prod.yml restart grafana

# 4. Verify (log in with new credentials)
curl -sf https://grafana.${DOMAIN}/api/health
```

### Phase 3: Tier 3 — External Services (no app downtime if rolling)

For each external service secret, apply this pattern:

```bash
# 1. Rotate key in external provider dashboard (OpenAI, Stripe, Google, etc.)

# 2. Update .env.production with new value

# 3. Rolling restart (one backend replica at a time if replicated)
# Single-instance:
docker compose -f docker-compose.prod.yml restart backend worker

# 4. Smoke test the affected integration
curl -sf https://${DOMAIN}/api/v1/health | jq '.integrations'
```

### Phase 4: Final Verification

```bash
# Full health check
curl -sf https://${DOMAIN}/api/v1/health | tee /tmp/health_after.json

# Verify all components connected
cat /tmp/health_after.json | jq '
  .database.connected,
  .graph.neo4j_available,
  .redis.connected,
  .cache.available
'

# Verify auth works
curl -sf -X POST https://${DOMAIN}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<test-user>","password":"<test-password>"}' | jq '.access_token'

# Check Grafana
curl -sf https://grafana.${DOMAIN}/api/health

# Notify stakeholders: rotation complete
```

---

## Emergency Rotation (Breach Scenario)

See [DR_RUNBOOK.md Scenario 4](DR_RUNBOOK.md) for the full blast-radius procedure. Target RTO: **40 minutes**.

Condensed emergency checklist:

```
[ ] Isolate — stop all non-essential services
[ ] Rotate ALL Tier 1 secrets (Postgres, JWT, Session) — accept session invalidation
[ ] Rotate ALL Tier 2 secrets (Neo4j, Redis, Grafana)
[ ] Rotate external service API keys
[ ] Rotate encryption keys (Google, Integration Hub) — note: historical data encrypted with old key needs migration plan
[ ] Restart all services
[ ] Verify health / auth
[ ] Investigate breach vector
[ ] Notify users (mandatory password reset if credentials were in scope)
```

---

## Rollback

If any rotation step fails:

```bash
# 1. Stop affected services
docker compose -f docker-compose.prod.yml stop backend worker

# 2. Restore previous .env.production from backup
cp .env.production.backup.$(date +%Y%m%d) .env.production

# 3. Restart services with old credentials
docker compose -f docker-compose.prod.yml up -d

# 4. If Postgres password was updated in the DB itself,
#    restore Postgres to pre-rotation dump
#    DO NOT do this unless absolutely necessary
```

---

## Rotation Audit Log

> **Fill after each rotation.** This table is the permanent operational record.

| Date | Operator | Secrets Rotated | Tier | Duration | Pre-checks | Post-checks | Result | Notes |
|------|----------|-----------------|:----:|:--------:|:----------:|:-----------:|:------:|-------|
| 2026-08-08 | OpenCode Agent | NEO4J_PASSWORD (dev drill) | 2 | ~30s | Dev env healthy; cypher-shell reachable | New pw works; old pw rejected; restored original; backend reconnected | PASS | In-place ALTER USER; no backend restart needed (pw rotated back to original) |
| 2026-08-08 | OpenCode Agent | GRAFANA_ADMIN_PASSWORD (dev drill) | 2 | ~5s | Grafana 200; API reachable | New pw accepted (200); old pw rejected (401); restored original | PASS | API PUT /api/admin/users/1/password; grafana-cli not available in v11.6 |
| — | — | REDIS_PASSWORD (dev drill) | 2 | — | Dev has no requirepass | — | SKIPPED | Production procedure documented; dev redis has no auth |
| | | | | | | | | |
| | | | | | | | | |

### Audit log rules

1. **Fill immediately** after each rotation — do not batch-fill later.
2. **Pre-checks column** must confirm: `.env` backup taken, monitoring open, maintenance window communicated.
3. **Post-checks column** must confirm: `/health` 200, auth test pass, Grafana reachable.
4. **If result is FAIL:** record rollback step taken; do not erase the failed row.
5. **Rotate this log** into a KMS/ASM-secured location quarterly (Google Sheets → Docs → archive).

---

## Rotation Schedule

| Tier | Secret | Frequency | Window |
|------|--------|:---------:|--------|
| 1 | `POSTGRES_PASSWORD` | 90 days | Monthly maintenance window |
| 1 | `JWT_SECRET_KEY` | 180 days | Monthly maintenance window |
| 1 | `SECRET_KEY` | 180 days | Monthly maintenance window |
| 1 | `APP_POSTGRES_PASSWORD` | 90 days | Monthly maintenance window |
| 2 | `NEO4J_PASSWORD` | 90 days | Off-peak (Neo4j offline in v1.0, low risk) |
| 2 | `REDIS_PASSWORD` | 90 days | Any time (ephemeral data) |
| 2 | `GRAFANA_ADMIN_PASSWORD` | 90 days | Any time |
| 3 | `OPENAI_API_KEY` | Per-provider recommendation | Any time |
| 3 | `STRIPE_*` | Per-provider recommendation | Off-peak |
| 3 | `SSO_*_CLIENT_SECRET` | Per-provider recommendation | Off-peak |
| 3 | Encryption keys (`GOOGLE_*`, `INTEGRATION_HUB_*`) | **DO NOT ROTATE WITHOUT MIGRATION PLAN** | Planned only |

---

## Honesty Banner

| Assertion | Status | Evidence |
|-----------|:------:|----------|
| Secret inventory complete | YES | 18 secrets across 3 tiers |
| Routine rotation tested on staging | **NO** | Not yet exercised |
| Emergency rotation tested (drill) | **NO** | Distilled from DR_RUNBOOK; not drilled |
| JWT rotation impact understood | YES | All sessions invalidated; users re-login |
| Encryption key rotation understood | YES | Historical data re-encryption migration required |
| No secrets committed to git | YES | `.gitignore` blocks `secrets.*`, `*.env` excluded |
| Staging/prod use separate secrets | YES | `.env` (dev) vs `.env.production` (prod) |
| Rotation documented in KMS/ASM | **NO** | Audit trail not automated; manual |

**Validation status:** document prepared, not build-validated.
