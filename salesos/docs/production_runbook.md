# SalesOS Production Runbook

> **Audience**: On-call SRE / engineer responding to production incidents.
> **Last updated**: 2026-07-12
> **Version**: 1.0 — GA

---

## Table of Contents

1. [Incident Response Overview](#1-incident-response-overview)
2. [Service Recovery Procedures](#2-service-recovery-procedures)
3. [Database Recovery](#3-database-recovery)
4. [Backup Verification & DR](#4-backup-verification--dr)
5. [Common Issues](#5-common-issues)
6. [Database Maintenance](#6-database-maintenance)
7. [On-Call Procedures](#7-on-call-procedures)
8. [Deployment Procedure](#8-deployment-procedure)
9. [Emergency Procedures](#9-emergency-procedures)

---

## 1. Incident Response Overview

### 1.1 Severity Levels

| Severity | Response Time | Description | Examples |
|----------|--------------|-------------|----------|
| **P0 — Critical** | 15 minutes | Service fully down, data loss, security breach | All API requests failing, database corruption, credential leak |
| **P1 — High** | 1 hour | Feature broken, degraded performance for users | Search returning errors, auth failures for some users, high error rate |
| **P2 — Medium** | 4 hours | Non-critical bug, workaround exists | Slow page load, one integration failing, cosmetic data issue |
| **P3 — Low** | 24 hours | Cosmetic, enhancement request | UI alignment, minor log noise, performance optimization |

### 1.2 Escalation Chain

```
On-Call Engineer (P0: respond in 15min)
    │
    ├── P0 unresolved after 15 minutes ──► Engineering Lead
    │
    └── P0 unresolved after 30 minutes ──► CTO
```

| Role | When to Escalate |
|------|-----------------|
| **On-Call Engineer** | First responder for all alerts. Diagnose, mitigate, resolve. |
| **Engineering Lead** | Escalate if: unable to diagnose within 15 min, need architectural decision, or rollback approval needed. |
| **CTO** | Escalate if: data breach confirmed, customer data at risk, or need business decision on service trade-offs. |

### 1.3 Communication Templates

**Slack — Incident Opened (P0/P1):**

```
🚨 INCIDENT OPENED — P{X}

Service: {service_name}
Impact: {description of user impact}
Started: {timestamp UTC}
On-call: {your_name}
Status: Investigating

Thread: #incident-{YYYY-MM-DD}-{short-desc}
```

**Slack — Incident Update:**

```
📋 INCIDENT UPDATE — P{X}

Status: {Investigating | Identified | Monitoring | Resolved}
Finding: {what we found}
Next step: {what we're doing now}
ETA: {estimated time or "TBD"}
```

**Slack — Incident Resolved:**

```
✅ INCIDENT RESOLVED — P{X}

Service: {service_name}
Duration: {total downtime}
Root cause: {one-line summary}
Resolution: {what fixed it}
Post-mortem: link to doc
```

**Status Page — External (for user-facing outages):**

```
[Investigating] We are aware of issues with {feature}. Our team is investigating. Updates to follow.

[Identified] The issue has been identified. We are implementing a fix. Expected resolution: {ETA}.

[Monitoring] A fix has been deployed. We are monitoring for stability.

[Resolved] The issue has been resolved. All services are operating normally. We apologize for the disruption.
```

---

## 2. Service Recovery Procedures

All Docker commands use the production compose file:

```bash
COMPOSE="docker compose -f docker-compose.prod.yml"
```

### 2.1 Backend API (FastAPI)

**How to detect failure:**

```bash
# Health check
curl -sf https://api.salesos.com/health | jq .

# Expected response:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "database": "connected",
#   "neo4j": "connected",
#   "redis": "connected",
#   "uptime_seconds": 12345
# }

# If unhealthy or no response:
curl -sf https://api.salesos.com/health/ready && echo "READY" || echo "NOT READY"
curl -sf https://api.salesos.com/ping | jq .
```

**Recovery steps:**

```bash
# 1. Check backend logs for root cause
$COMPOSE logs --tail 200 backend | grep -i "error\|exception\|traceback"

# 2. Check if it's a dependency issue (DB/Neo4j/Redis)
curl -s https://api.salesos.com/health | jq '.database, .neo4j, .redis'

# 3. If dependency is healthy, restart the backend
$COMPOSE restart backend

# 4. If restart fails, check container status
$COMPOSE ps backend
docker inspect salesos-backend --format '{{.State.ExitCode}} {{.State.Error}}'

# 5. If exit code is non-zero, check full logs
$COMPOSE logs backend 2>&1 | tail -100

# 6. If memory-related, check and restart
docker stats --no-stream | grep backend

# 7. Nuclear option: stop all and restart in dependency order
$COMPOSE down
$COMPOSE up -d postgres neo4j redis
# Wait 30s for health checks
$COMPOSE up -d pgbouncer migrations
# Wait for migrations to complete
$COMPOSE up -d backend frontend caddy
```

**Verification after restart:**

```bash
# 1. Health endpoint returns healthy
curl -sf https://api.salesos.com/health | jq .status
# Expected: "healthy"

# 2. API responds with version
curl -sf https://api.salesos.com/health | jq .version

# 3. Backend logs show startup
$COMPOSE logs --tail 20 backend | grep "Application startup"

# 4. No errors in last 5 minutes
$COMPOSE logs --since 5m backend 2>&1 | grep -ci "error"
# Expected: 0

# 5. Run smoke test
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/ping
# Expected: 200
```

### 2.2 Frontend (Next.js)

**How to detect failure:**

```bash
# Check frontend serves
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com
# Expected: 200

# Check for JS errors by verifying the HTML loads
curl -sf https://salesos.com | head -5
# Expected: <!DOCTYPE html> or similar HTML

# Check frontend health check
$COMPOSE ps frontend
# Should show "healthy" in status
```

**Recovery steps:**

```bash
# 1. Check frontend logs
$COMPOSE logs --tail 100 frontend | grep -i "error\|fatal\|crash"

# 2. Restart frontend
$COMPOSE restart frontend

# 3. If memory/CPU issue, check limits
docker stats --no-stream | grep frontend

# 4. If persistent crash, rebuild and restart
$COMPOSE down frontend
$COMPOSE up -d frontend

# 5. Full restart if needed
$COMPOSE restart frontend caddy
```

**Verification:**

```bash
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com
# Expected: 200

curl -sf https://salesos.com | grep -o "<title>.*</title>"
# Expected: <title>SalesOS</title> (or similar)

# Verify static assets load
curl -sf -o /dev/null https://salesos.com/_next/static/
# Should not return 404 or 500
```

### 2.3 PostgreSQL + PgBouncer

**How to detect failure:**

```bash
# Check PostgreSQL is accepting connections
$COMPOSE exec postgres pg_isready -U salesos -d salesos
# Expected: "accepting connections"

# Check PgBouncer pool status
$COMPOSE exec pgbouncer psql -h localhost -p 6432 -U salesos -d pgbouncer -c "SHOW POOLS;"
# Expected output should show active pools with clients/svrs counts

# Check total active connections
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT count(*) AS total, state FROM pg_stat_activity GROUP BY state;"
```

**Recovery steps:**

```bash
# 1. If PostgreSQL is down
$COMPOSE ps postgres
$COMPOSE logs --tail 100 postgres | grep -i "fatal\|panic\|shutdown"

# If PostgreSQL crashed, restart it:
$COMPOSE restart postgres
# Wait for health check to pass (~30s)
$COMPOSE exec postgres pg_isready -U salesos

# 2. If PgBouncer is the issue (PostgreSQL is fine but app can't connect)
$COMPOSE exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"
# Check if clients are waiting or svrs are all used

# Restart PgBouncer:
$COMPOSE restart pgbouncer

# 3. If connection exhaustion (too many active connections)
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT pid, state, query, query_start, now() - query_start AS duration
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC
   LIMIT 20;"

# Kill long-running queries if needed:
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# 4. If disk space is full
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT pg_size_pretty(pg_database_size('salesos'));"
df -h /var/lib/docker/volumes/salesos_pgdata/_data

# Emergency: remove old WAL or vacuum
$COMPOSE exec postgres psql -U salesos -d salesos -c "VACUUM FULL VERBOSE;"
```

**Verification:**

```bash
# PostgreSQL accepts connections
$COMPOSE exec postgres pg_isready -U salesos -d salesos

# PgBouncer pool is healthy
$COMPOSE exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"

# API health shows connected
curl -s https://api.salesos.com/health | jq .database
# Expected: "connected"

# Connection count is reasonable
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT count(*) FROM pg_stat_activity;"
# Should be < 80 (PgBouncer max_client_connections is 100)
```

### 2.4 Neo4j

**How to detect failure:**

```bash
# Check Neo4j is responding
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1 AS ok"
# Expected: { ok: 1 }

# Check Neo4j health via API
curl -sf http://localhost:7474 | jq .
# Or check the backend health endpoint:
curl -s https://api.salesos.com/health | jq .neo4j
# Expected: "connected"
```

**Recovery steps:**

```bash
# 1. Check Neo4j logs
$COMPOSE logs --tail 200 neo4j | grep -i "error\|fatal\|out of memory\|shutdown"

# 2. Check if it's an OOM issue
docker stats --no-stream | grep neo4j
# If memory usage is at limit (4GB), increase limit in docker-compose.prod.yml

# 3. Check disk space for Neo4j data
docker volume inspect salesos_neo4j_data --format '{{.Mountpoint}}'
df -h $(docker volume inspect salesos_neo4j_data --format '{{.Mountpoint}}')

# 4. Restart Neo4j (data persists in Docker volume)
$COMPOSE restart neo4j

# 5. If Neo4j won't start, check data integrity
$COMPOSE logs neo4j 2>&1 | grep -i "corrupt\|inconsistent"
# If corrupted, restore from backup (see section 3.2)

# 6. Check connection pool in backend
$COMPOSE logs backend | grep -i "neo4j.*error\|neo4j.*timeout"
```

**Verification:**

```bash
# Neo4j responds to Cypher
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1 AS ok"

# Check graph data integrity
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC LIMIT 10;"

# Backend health shows connected
curl -s https://api.salesos.com/health | jq .neo4j
# Expected: "connected"

# No Neo4j errors in recent backend logs
$COMPOSE logs --since 5m backend | grep -ci "neo4j"
# Expected: 0 error lines
```

### 2.5 Caddy (TLS/Reverse Proxy)

**How to detect failure:**

```bash
# Check Caddy is running
$COMPOSE ps caddy
# Should show "healthy"

# Test HTTPS endpoint
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/health

# Check certificate expiry
echo | openssl s_client -servername salesos.com -connect salesos.com:443 2>/dev/null | openssl x509 -noout -dates

# Check if HTTP redirects to HTTPS
curl -sI http://salesos.com | grep "Location"
# Expected: Location: https://salesos.com/
```

**Recovery steps:**

```bash
# 1. Check Caddy logs for errors
$COMPOSE logs --tail 100 caddy | grep -i "error\|tls\|certificate\|acme"

# 2. Verify DNS resolution
dig +short salesos.com
dig +short api.salesos.com
# Both should return your server's IP

# 3. Verify ports 80 and 443 are open
ss -tlnp | grep -E ":80|:443"

# 4. If TLS certificate provisioning failed:
# Ensure DNS A records point to this server
# Ensure firewall allows ports 80 and 443
# Restart Caddy to trigger re-provisioning
$COMPOSE restart caddy

# 5. If certificate is expired or corrupted:
$COMPOSE exec caddy rm -rf /data/caddy/certificates/
$COMPOSE restart caddy

# 6. Validate Caddyfile syntax
$COMPOSE exec caddy caddy validate --config /etc/caddy/Caddyfile

# 7. If Caddy config is wrong, fix and reload
$COMPOSE exec caddy caddy reload --config /etc/caddy/Caddyfile
```

**Verification:**

```bash
# HTTPS works
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com
# Expected: 200

curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/health
# Expected: 200

# Certificate is valid
echo | openssl s_client -servername salesos.com -connect salesos.com:443 2>/dev/null | \
  openssl x509 -noout -dates
# Should show valid notBefore and notAfter dates

# HTTP redirects to HTTPS
curl -sI http://salesos.com | head -3
# Expected: HTTP/1.1 301 Moved Permanently + Location: https://salesos.com/
```

---

## 3. Database Recovery

### 3.1 PostgreSQL Backup Restore

**When to use**: Data corruption, accidental deletion, need to roll back to a known-good state.

**Prerequisites:**
- Backup files exist in `/backups/postgres/` (or S3)
- Backend must be stopped during restore to prevent writes

**Step-by-step restore:**

```bash
# 1. List available backups
$COMPOSE exec backup ls -la /backups/postgres/
# Backup files are named: salesos_YYYYMMDD_HHMMSS.dump

# 2. Stop the backend and frontend (prevent writes and user access)
$COMPOSE stop backend frontend

# 3. Verify PostgreSQL is running (we only stop app services)
$COMPOSE exec postgres pg_isready -U salesos

# 4. Drop and recreate the database (clean restore)
$COMPOSE exec postgres psql -U salesos -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE datname = 'salesos' AND pid <> pg_backend_pid();"
$COMPOSE exec postgres psql -U salesos -d postgres -c "DROP DATABASE IF EXISTS salesos;"
$COMPOSE exec postgres psql -U salesos -d postgres -c "CREATE DATABASE salesos OWNER salesos;"

# 5. Restore from backup (choose one method)

# Method A: Restore from inside the backup container (recommended)
$COMPOSE run --rm -e PGPASSWORD="$POSTGRES_PASSWORD" backup \
  pg_restore -h postgres -p 5432 -U salesos -d salesos \
  --clean --if-exists --no-owner --no-acl \
  /backups/postgres/salesos_YYYYMMDD_HHMMSS.dump

# Method B: Restore from inside the postgres container
# First copy the backup file into the postgres container:
docker cp /opt/salesos/backups/postgres/salesos_YYYYMMDD_HHMMSS.dump \
  salesos-postgres-1:/tmp/restore.dump
$COMPOSE exec postgres pg_restore -U salesos -d salesos \
  --clean --if-exists --no-owner --no-acl /tmp/restore.dump

# 6. Re-run database initialization (extensions and schemas)
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
   CREATE EXTENSION IF NOT EXISTS pgcrypto;
   CREATE SCHEMA IF NOT EXISTS audit;
   CREATE SCHEMA IF NOT EXISTS identity;
   CREATE SCHEMA IF NOT EXISTS company;
   CREATE SCHEMA IF NOT EXISTS activity;
   CREATE SCHEMA IF NOT EXISTS crm;"

# 7. Verify restore succeeded
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT schemaname, tablename, n_live_tup
   FROM pg_stat_user_tables
   ORDER BY n_live_tup DESC
   LIMIT 20;"

$COMPOSE exec postgres psql -U salesos -d salesos -c "\dx"
# Should show: vector, pg_trgm, uuid-ossp, pgcrypto

# 8. Run Alembic migrations to ensure schema is current
$COMPOSE run --rm migrations alembic upgrade head

# 9. Restart all services
$COMPOSE up -d

# 10. Verify the system is healthy
curl -s https://api.salesos.com/health | jq .
$COMPOSE logs --tail 20 backend | grep "Application startup"
```

**Verify data integrity after restore:**

```bash
# Check critical table counts
$COMPOSE exec postgres psql -U salesos -d salesos -c "
  SELECT 'identity.users' AS tbl, count(*) FROM identity.users
  UNION ALL
  SELECT 'company.companies', count(*) FROM company.companies
  UNION ALL
  SELECT 'crm.leads', count(*) FROM crm.leads;"

# Check referential integrity (example)
$COMPOSE exec postgres psql -U salesos -d salesos -c "
  SELECT count(*) AS orphaned_leads
  FROM crm.leads l
  LEFT JOIN company.companies c ON l.company_id = c.id
  WHERE c.id IS NULL AND l.company_id IS NOT NULL;"

# Check indexes exist and are valid
$COMPOSE exec postgres psql -U salesos -d salesos -c "
  SELECT indexrelname, indrelid::regclass, idx_scan
  FROM pg_stat_user_indexes
  ORDER BY idx_scan DESC
  LIMIT 20;"
```

### 3.2 Neo4j Backup Restore

**When to use**: Knowledge graph corruption, data loss in entity relationships.

**Create a backup (before restore, to capture current state):**

```bash
# Dump Neo4j database
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "CALL dbms.dump.database('/tmp/neo4j-backup')" 2>/dev/null

# Copy backup out of container
mkdir -p /opt/salesos/backups/neo4j
$COMPOSE cp neo4j:/tmp/neo4j-backup /opt/salesos/backups/neo4j/
```

**Restore Neo4j from backup:**

```bash
# 1. Stop the backend (prevent Neo4j access)
$COMPOSE stop backend

# 2. Stop Neo4j
$COMPOSE stop neo4j

# 3. Remove current Neo4j data (DANGEROUS — only if data is corrupted)
docker volume rm salesos_neo4j_data

# 4. Start Neo4j fresh
$COMPOSE up -d neo4j
# Wait for healthy status
sleep 30

# 5. Copy backup into the new Neo4j container
$COMPOSE cp /opt/salesos/backups/neo4j/neo4j-backup neo4j:/tmp/neo4j-backup

# 6. Load the backup
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "CALL dbms.dump.load('/tmp/neo4j-backup')" 2>/dev/null

# 7. Restart backend
$COMPOSE up -d backend

# 8. Verify
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC LIMIT 10;"
```

### 3.3 Verify Data Integrity After Restore

Run these checks after any database restore:

```bash
# PostgreSQL: table row counts
$COMPOSE exec postgres psql -U salesos -d salesos -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  WHERE n_live_tup > 0
  ORDER BY n_live_tup DESC;"

# PostgreSQL: index validity
$COMPOSE exec postgres psql -U salesos -d salesos -c "
  SELECT indexrelname, indisvalid
  FROM pg_stat_user_indexes
  JOIN pg_index ON indexrelid = pg_stat_user_indexes.indexrelid
  WHERE NOT indisvalid;"

# PostgreSQL: foreign key constraints (check for orphaned records)
$COMPOSE exec postgres psql -U salesos -d salesos -c "
  SELECT conname, conrelid::regclass, confrelid::regclass
  FROM pg_constraint
  WHERE contype = 'f';"

# Neo4j: node and relationship counts
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n) RETURN 'nodes' AS type, count(n) AS count
   UNION ALL
   MATCH ()-[r]->() RETURN 'relationships' AS type, count(r) AS count;"

# End-to-end: API health and data access
curl -s https://api.salesos.com/health | jq .
# All fields should show "healthy" / "connected"
```

---

## 4. Backup Verification & Disaster Recovery

### 4.1 Recovery Time & Point Objectives

| Metric | Target | Rationale |
|--------|--------|-----------|
| **RPO** (Recovery Point Objective) | 1 hour | PostgreSQL backups run hourly via cron; WAL archiving provides point-in-time recovery |
| **RTO** (Recovery Time Objective) | 30 minutes | Full restore + migration + service restart within budget |
| **Backup Retention** | 7 days local, 30 days S3 | Local for quick restore, S3 for compliance and disaster recovery |
| **Verification Frequency** | Weekly | Automated verification script runs every Sunday at 03:00 UTC |

### 4.2 Backup Verification Schedule

| Day | Time (UTC) | Action | Script |
|-----|------------|--------|--------|
| **Daily** | 02:00 | pg_dump to local + S3 upload | `backup-db.sh` (cron) |
| **Sunday** | 03:00 | Full backup verification | `scripts/verify-backup.ps1` |
| **Monthly** | 04:00 1st of month | Cross-region S3 copy | Manual / Lambda |

**Crontab entry (production server):**

```bash
# Daily backup at 02:00 UTC
0 2 * * * docker compose -f /opt/salesos/docker-compose.prod.yml run --rm backup /usr/local/bin/backup-db >> /var/log/salesos-backup.log 2>&1

# Weekly backup verification at 03:00 UTC on Sundays
0 3 * * 0 cd /opt/salesos && docker compose -f docker-compose.prod.yml exec -T backend python /app/scripts/verify-backup-ps1-wrapper.py >> /var/log/salesos-backup-verify.log 2>&1
```

### 4.3 Running verify-backup.ps1

The verification script performs an end-to-end backup validation cycle:

```powershell
# Set required environment variables
$env:DB_NAME = "salesos"
$env:DB_HOST = "localhost"       # or postgres container hostname
$env:DB_PORT = "5432"
$env:DB_USER = "salesos"
$env:DB_PASSWORD = "your-password-here"

# Run verification
.\salesos\scripts\verify-backup.ps1
```

**What it does:**
1. **pg_dump** — Dumps the full database to a temporary file (compressed, custom format)
2. **pg_restore** — Creates a temporary database (`salesos_verify_tmp`) and restores the dump
3. **Row count verification** — Queries every user table in both source and restored databases, compares counts
4. **Index verification** — Checks all indexes exist and are valid (`indisvalid`) in the restored database
5. **Cleanup** — Drops the temp database and removes the dump file
6. **Report** — Prints pass/fail summary with detailed findings

**Expected output (success):**
```
============================================
  VERIFICATION SUMMARY
============================================
  Pass: 15
  Fail: 0
  Status: ALL PASSED

All backup verification checks passed.
```

**Docker-based verification (production):**

```bash
# From the production server
docker compose -f docker-compose.prod.yml exec -T backend \
  psql -U salesos -d salesos -t -c "SELECT count(*) FROM pg_stat_user_tables;"
```

### 4.4 PostgreSQL WAL Archiving Setup

WAL (Write-Ahead Log) archiving enables point-in-time recovery (PTR) — restore to any moment, not just the last backup.

**Step 1: Enable archive_mode in postgresql.conf**

```bash
# Inside the postgres container
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "ALTER SYSTEM SET archive_mode = on;
   ALTER SYSTEM SET archive_command = 'test ! -f /archive/%f && cp %p /archive/%f';
   ALTER SYSTEM SET max_wal_senders = 3;
   ALTER SYSTEM SET wal_keep_size = '1GB';"
```

**Step 2: Create archive directory**

```bash
# On the host
mkdir -p /opt/salesos/wal-archive
chmod 700 /opt/salesos/wal-archive

# Mount in docker-compose.prod.yml:
# volumes:
#   - /opt/salesos/wal-archive:/archive
```

**Step 3: Add to docker-compose.prod.yml postgres service**

```yaml
postgres:
  image: postgres:16-alpine
  volumes:
    - pgdata:/var/lib/postgresql/data
    - /opt/salesos/wal-archive:/archive    # WAL archiving
    - ./infra/postgres/postgresql.conf:/etc/postgresql/postgresql.conf  # custom config
  command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

**Step 4: Restart PostgreSQL to apply**

```bash
$COMPOSE restart postgres
# Verify archive_mode is on
$COMPOSE exec postgres psql -U salesos -d salesos -c "SHOW archive_mode;"
# Expected: on
```

**Step 5: Point-in-time recovery procedure**

```bash
# 1. Stop writes
$COMPOSE stop backend frontend

# 2. Archive current WAL
$COMPOSE exec postgres psql -U salesos -d salesos -c "SELECT pg_switch_wal();"

# 3. Restore base backup
pg_restore -h postgres -p 5432 -U salesos -d salesos \
  --clean --if-exists --no-owner --no-acl /backups/postgres/salesos_LATEST.dump

# 4. Create recovery signal file and configure recovery
# Edit postgresql.conf:
#   restore_command = 'cp /archive/%f %p'
#   recovery_target_time = '2026-07-12 14:30:00+00'
#   recovery_target_action = 'promote'

# 5. Create recovery.signal
$COMPOSE exec postgres touch /var/lib/postgresql/data/recovery.signal

# 6. Restart PostgreSQL
$COMPOSE restart postgres

# 7. Verify data up to recovery point
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT max(created_at) FROM domain_events;"
```

### 4.5 Backup Integrity Checklist

Run after any backup or restore operation:

```bash
# 1. Verify backup file exists and is non-empty
ls -lh /backups/postgres/salesos_*.dump | tail -1

# 2. Verify pg_dump can read the backup file
pg_restore --list /backups/postgres/salesos_LATEST.dump | head -20

# 3. Verify database is accessible
$COMPOSE exec postgres pg_isready -U salesos -d salesos

# 4. Run row count verification
.\salesos\scripts\verify-backup.ps1

# 5. Check backup logs
tail -50 /var/log/salesos-backup.log
```

---

## 5. Common Issues

| # | Issue | Symptoms | Root Cause | Resolution Steps |
|---|-------|----------|------------|-----------------|
| 1 | **High API latency** | p95 > 500ms, p99 > 1s, users report slow pages | Slow database queries, connection pool exhaustion, large result sets, missing indexes | 1. Check Grafana API latency dashboard. 2. Query `pg_stat_activity` for long-running queries. 3. Check PgBouncer `SHOW POOLS` for waiting clients. 4. Run `VACUUM ANALYZE` on bloated tables. 5. Add missing indexes if needed. |
| 2 | **Authentication failures** | Users cannot log in, 401 errors on all requests | JWT secret mismatch (post-rotation), token expiry misconfiguration, bcrypt cost too high | 1. Verify `JWT_SECRET_KEY` in `.env.production` matches all instances. 2. Check `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`. 3. Review backend logs for token validation errors. 4. If secret was rotated, all users must re-login. 5. If all else fails: `$COMPOSE restart backend`. |
| 3 | **CSRF errors (403 on POST/PUT/DELETE)** | Mutating API requests return 403, GET requests work | CSRF token missing from request, Origin header mismatch, cookie not set | 1. Verify `DOMAIN` in `.env.production` matches the actual domain. 2. Check that the frontend sends the CSRF cookie. 3. Ensure `Content-Type: application/json` header is set. 4. Verify CORS configuration. 5. Test: `curl -X POST ... -H "Origin: https://salesos.com"` should pass. |
| 4 | **Rate limiting (429 responses)** | HTTP 429 with `Retry-After` header | Client exceeding rate limit, too many concurrent requests, automated scripts | 1. Check which tier is being hit (auth/search/anonymous). 2. Review `RATE_LIMIT_*` values in `.env.production`. 3. For legitimate high-traffic: increase `RATE_LIMIT_AUTHENTICATED` (e.g., 200). 4. For abuse: check IP in logs and block at Cloudflare level. 5. Restart backend to apply new limits. |
| 5 | **DB connection exhaustion** | Backend logs show "connection pool exhausted", API returns 500 | PgBouncer pool full, leaked connections, too many concurrent requests | 1. Check PgBouncer: `$COMPOSE exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"`. 2. Check PostgreSQL connections: `$COMPOSE exec postgres psql -U salesos -d salesos -c "SELECT count(*) FROM pg_stat_activity;"`. 3. Kill idle connections if count is high. 4. Restart PgBouncer: `$COMPOSE restart pgbouncer`. 5. If persistent, increase PgBouncer `default_pool_size` in config. |
| 6 | **Neo4j down or unresponsive** | Backend health shows `neo4j: "disconnected"`, graph queries timeout | OOM kill, disk full, corrupt data, connection pool exhaustion | 1. Check Neo4j status: `$COMPOSE ps neo4j`. 2. Check logs: `$COMPOSE logs --tail 100 neo4j`. 3. Check memory: `docker stats --no-stream \| grep neo4j`. 4. Restart: `$COMPOSE restart neo4j`. 5. If OOM, increase `NEO4J.memory.heap.max_size` in env. 6. If corrupt, restore from backup (section 3.2). |
| 7 | **Search failures** | Search endpoint returns errors or empty results, full-text search broken | PostgreSQL FTS index corruption, pg_trgm extension issue, Meilisearch down | 1. Check search endpoint: `curl -s https://api.salesos.com/api/v1/search?q=test`. 2. Verify FTS index: `$COMPOSE exec postgres psql -U salesos -d salesos -c "SELECT * FROM pg_stat_user_tables WHERE relname LIKE '%search%';"`. 3. Rebuild FTS index if needed. 4. If Meilisearch is used, check: `$COMPOSE ps meilisearch` and restart. 5. Test with simple query to isolate. |
| 8 | **High memory usage / OOM** | Container killed (exit code 137), `docker stats` shows memory at limit | Memory leak, large query results, too many workers, unbounded caches | 1. Identify which container: `docker stats --no-stream`. 2. Check which is at limit (backend=1GB, neo4j=4GB). 3. Restart the affected container. 4. Check backend logs for large result sets or infinite loops. 5. If backend: reduce workers or increase memory limit. 6. If persistent: check for memory leak with `tracemalloc` or increase limit. |
| 9 | **SSL/TLS certificate errors** | Browser shows "Your connection is not private", `curl` shows certificate error | Certificate expired, DNS mismatch, port 80 blocked for ACME challenge | 1. Verify DNS: `dig +short salesos.com` and `dig +short api.salesos.com`. 2. Check cert expiry: `echo \| openssl s_client -servername salesos.com -connect salesos.com:443 2>/dev/null \| openssl x509 -noout -dates`. 3. Verify port 80 is open: `ss -tlnp \| grep :80`. 4. Check Caddy logs: `$COMPOSE logs caddy \| grep -i "acme\|tls\|certificate"`. 5. Force renewal: `$COMPOSE exec caddy rm -rf /data/caddy/certificates/ && $COMPOSE restart caddy`. |
| 10 | **Backup failures** | Backup container logs show errors, no new backup files in `/backups/postgres/` | Disk full, PostgreSQL connection issue, permission error | 1. Check backup logs: `$COMPOSE logs backup`. 2. Check disk space: `df -h`. 3. Check if PostgreSQL is accessible from backup container: `$COMPOSE exec backup pg_isready -h postgres -p 5432 -U salesos`. 4. Manually trigger backup: `$COMPOSE run --rm backup /usr/local/bin/backup-db`. 5. If disk full: remove old backups, expand volume, or configure S3 upload. 6. Verify backup was created: `$COMPOSE exec backup ls -la /backups/postgres/`. |

---

## 6. Database Maintenance

### 5.1 VACUUM / ANALYZE Schedule

PostgreSQL requires regular vacuuming to reclaim space from deleted/updated rows and to update query planner statistics.

**Automated (autovacuum):** Enabled by default in PostgreSQL 16. Verify it's running:

```bash
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT relname, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
   FROM pg_stat_user_tables
   WHERE relname IN ('users', 'companies', 'leads', 'activities')
   ORDER BY last_autovacuum DESC;"
```

**Manual VACUUM (recommended weekly):**

```bash
# Reclaim space from dead tuples (non-blocking)
$COMPOSE exec postgres psql -U salesos -d salesos -c "VACUUM VERBOSE;"

# Update query planner statistics (run after VACUUM)
$COMPOSE exec postgres psql -U salesos -d salesos -c "ANALYZE VERBOSE;"

# For heavily updated tables, use VACUUM FULL (blocking — schedule during maintenance window)
$COMPOSE exec postgres psql -U salesos -d salesos -c "VACUUM FULL VERBOSE;"
```

**Schedule in host crontab:**

```bash
# Weekly VACUUM + ANALYZE (Sundays at 02:00 UTC)
0 2 * * 0 docker compose -f /opt/salesos/docker-compose.prod.yml exec -T postgres psql -U salesos -d salesos -c "VACUUM ANALYZE;" >> /var/log/salesos-vacuum.log 2>&1
```

**Monitor dead tuple accumulation:**

```bash
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "SELECT relname, n_dead_tup, n_live_tup,
          round(n_dead_tup::numeric / greatest(n_live_tup, 1) * 100, 2) AS dead_pct
   FROM pg_stat_user_tables
   WHERE n_dead_tup > 1000
   ORDER BY n_dead_tup DESC;"
```

If `dead_pct` exceeds 20%, increase the autovacuum threshold or run manual VACUUM.

### 5.2 REINDEX Procedures

**When to reindex:**
- After heavy UPDATE/DELETE operations
- When index bloat exceeds 30%
- When queries slow down suddenly despite no schema changes

**Check index bloat:**

```bash
$COMPOSE exec postgres psql -U salesos -d salesos -c "
  SELECT indexrelname, idx_scan,
         pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
  FROM pg_stat_user_indexes
  ORDER BY pg_relation_size(indexrelid) DESC
  LIMIT 15;"
```

**Reindex (non-blocking with REINDEX CONCURRENTLY):**

```bash
# Reindex a specific bloated index
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "REINDEX INDEX CONCURRENTLY index_name;"

# Reindex all indexes in a specific table
$COMPOSE exec postgres psql -U salesos -d salesos -c \
  "REINDEX TABLE CONCURRENTLY identity.users;"

# Full database reindex (blocking — schedule during maintenance window)
$COMPOSE exec postgres psql -U salesos -d salesos -c "REINDEX DATABASE CONCURRENTLY salesos;"
```

**Schedule monthly REINDEX:**

```bash
# Monthly reindex (1st of month, 01:00 UTC)
0 1 1 * * docker compose -f /opt/salesos/docker-compose.prod.yml exec -T postgres psql -U salesos -d salesos -c "REINDEX DATABASE CONCURRENTLY salesos;" >> /var/log/salesos-reindex.log 2>&1
```

### 5.3 Connection Pool Tuning

**PgBouncer settings (in `infra/pgbouncer/pgbouncer.ini`):**

| Setting | Default | Recommended | When to Adjust |
|---------|---------|-------------|----------------|
| `pool_mode` | `transaction` | `transaction` | Never change unless you know why |
| `max_client_conn` | 100 | 100-200 | If backend reports "connection pool exhausted" |
| `default_pool_size` | 25 | 25-50 | If PgBouncer shows many `cl_waiting` |
| `min_pool_size` | 5 | 5-10 | If connections are being created/destroyed frequently |
| `reserve_pool_size` | 5 | 5-10 | For traffic bursts |
| `server_idle_timeout` | 300 | 300-600 | If connections are being dropped too aggressively |

**Monitor pool health:**

```bash
# Show pool status (cl=clients, sv=servers, wait=waiting)
$COMPOSE exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;"
# If cl_waiting > 0, increase default_pool_size

# Show all active connections
$COMPOSE exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW CLIENTS;"
$COMPOSE exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW SERVERS;"

# Show PgBouncer stats
$COMPOSE exec pgbouncer psql -h localhost -p 6432 pgbouncer -c "SHOW STATS;"
```

**Adjust pool size (edit `pgbouncer.ini`):**

```ini
[pgbouncer]
pool_mode = transaction
max_client_conn = 200      # Increased from 100
default_pool_size = 50     # Increased from 25
min_pool_size = 10
reserve_pool_size = 10
server_idle_timeout = 600
```

Then restart PgBouncer:

```bash
$COMPOSE restart pgbouncer
```

**PostgreSQL `max_connections` (should be >= PgBouncer `default_pool_size` + margin):**

```bash
# Check current setting
$COMPOSE exec postgres psql -U salesos -d salesos -c "SHOW max_connections;"
# Default in Docker image: 100

# Adjust if needed (requires restart of PostgreSQL)
# Edit postgresql.conf inside the container or via docker-compose volume mount
$COMPOSE exec postgres psql -U salesos -d salesos -c "ALTER SYSTEM SET max_connections = 200;"
$COMPOSE restart postgres
```

---

## 7. On-Call Procedures

### 6.1 Shift Handover Checklist

When handing over the on-call shift, complete this checklist:

```
ON-CALL SHIFT HANDOVER — Date: ____________

[ ] Current system status: GREEN / YELLOW / RED

[ ] Active incidents:
    - Incident #___: Status: ___

[ ] Recent changes (last 24h):
    - Deployments: ___
    - Config changes: ___
    - Manual interventions: ___

[ ] Pending alerts to watch:
    - ___

[ ] Backup status:
    - Last successful PostgreSQL backup: ___
    - Last successful Neo4j backup: ___
    - Disk usage: ___%

[ ] Notes for next shift:
    ___

Handover from: ____________ to: ____________
```

### 6.2 Daily Health Checks

Run these checks at the start of every shift:

```bash
# ═══════════════════════════════════════════
# DAILY HEALTH CHECK SCRIPT
# Run from /opt/salesos
# ═══════════════════════════════════════════

echo "=== Service Status ==="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== Backend Health ==="
curl -sf https://api.salesos.com/health | jq .

echo ""
echo "=== Frontend Status ==="
curl -sf -o /dev/null -w "HTTP %{http_code}\n" https://salesos.com

echo ""
echo "=== PostgreSQL Connections ==="
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U salesos -d salesos -t -c \
  "SELECT count(*) AS total_connections FROM pg_stat_activity;"

echo ""
echo "=== PgBouncer Pool Status ==="
docker compose -f docker-compose.prod.yml exec -T pgbouncer \
  psql -h localhost -p 6432 pgbouncer -t -c "SHOW POOLS;"

echo ""
echo "=== Disk Usage ==="
df -h / | tail -1

echo ""
echo "=== Docker Disk Usage ==="
docker system df

echo ""
echo "=== Recent Errors (last 1h) ==="
docker compose -f docker-compose.prod.yml logs --since 1h backend 2>&1 | \
  grep -ci "error\|exception\|traceback"

echo ""
echo "=== Container Resource Usage ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "=== Backup Status ==="
ls -lt /opt/salesos/backups/postgres/ 2>/dev/null | head -3

echo ""
echo "=== SSL Certificate ==="
echo | openssl s_client -servername salesos.com -connect salesos.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

**Daily check thresholds (alert if exceeded):**

| Metric | Warning | Critical |
|--------|---------|----------|
| Disk usage | > 80% | > 90% |
| Error rate (last 1h) | > 10 errors | > 50 errors |
| PostgreSQL connections | > 60 | > 80 |
| Backend memory | > 800MB | > 950MB |
| Neo4j memory | > 3GB | > 3.8GB |
| Backup age | > 26 hours | > 48 hours |

### 6.3 Incident Post-Mortem Template

Use this template after every P0/P1 incident:

```markdown
# Incident Post-Mortem: [INCIDENT TITLE]

**Date**: YYYY-MM-DD
**Duration**: X hours Y minutes
**Severity**: P{X}
**Author**: [your name]
**Status**: Draft / Final

---

## Summary

One-paragraph summary of what happened, the impact, and resolution.

## Timeline (UTC)

| Time | Event |
|------|-------|
| HH:MM | First alert received |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Fix deployed |
| HH:MM | Service confirmed recovered |
| HH:MM | Incident closed |

## Impact

- **Users affected**: X
- **Duration of impact**: X hours
- **Data loss**: Yes/No (if yes, describe)
- **Revenue impact**: (if applicable)

## Root Cause Analysis (5 Whys)

1. **Why did the service go down?**
   → [Direct cause]

2. **Why did [direct cause] happen?**
   → [Underlying cause]

3. **Why did [underlying cause] occur?**
   → [Systemic cause]

4. **Why was [systemic cause] not prevented?**
   → [Process/gap cause]

5. **Why did [process/gap cause] exist?**
   → [Root cause]

## What Went Well

- [List things that worked during the response]

## What Went Wrong

- [List things that didn't work or made it worse]

## Action Items

| # | Action | Owner | Priority | Due Date | Status |
|---|--------|-------|----------|----------|--------|
| 1 | [Fix or improvement] | [name] | P{X} | YYYY-MM-DD | Open |
| 2 | [Fix or improvement] | [name] | P{X} | YYYY-MM-DD | Open |

## Lessons Learned

- [Key takeaway 1]
- [Key takeaway 2]
```

---

## 8. Deployment Procedure

### 7.1 Step-by-Step Deploy

**Pre-deployment checklist:**

```
[ ] All tests passing on CI
[ ] PR approved by 2 reviewers
[ ] Security review passed (if touching auth/RBAC)
[ ] Database migration tested locally
[ ] Rollback plan documented
[ ] Deployment window confirmed (avoid peak hours)
[ ] On-call engineer notified
```

**Deploy procedure:**

```bash
# ═══════════════════════════════════════════
# DEPLOYMENT PROCEDURE
# ═══════════════════════════════════════════

# 1. SSH into production server
ssh deploy@your-server

# 2. Navigate to project
cd /opt/salesos

# 3. Create backup BEFORE deploying (safety net)
docker compose -f docker-compose.prod.yml run --rm backup /usr/local/bin/backup-db

# 4. Pull latest changes (or set new image tag)
git pull origin main
# OR for tagged release:
export IMAGE_TAG=v1.1.0

# 5. Pull new Docker images
IMAGE_TAG=v1.1.0 docker compose -f docker-compose.prod.yml pull

# 6. Run database migrations FIRST (before starting new backend)
docker compose -f docker-compose.prod.yml run --rm migrations
# Verify migration succeeded:
docker compose -f docker-compose.prod.yml logs migrations

# 7. Deploy services (rolling restart)
IMAGE_TAG=v1.1.0 docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 8. Wait for all services to become healthy (30-60 seconds)
watch -n 5 'docker compose -f docker-compose.prod.yml ps'

# 9. Run post-deploy smoke tests
curl -sf https://api.salesos.com/health | jq .
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com

# 10. Verify version matches expected
VERSION=$(curl -s https://api.salesos.com/health | jq -r .version)
echo "Deployed version: $VERSION"
# Expected: v1.1.0

# 11. Monitor for 15 minutes
docker compose -f docker-compose.prod.yml logs --since 15m backend 2>&1 | grep -ci "error"
# Expected: 0

# 12. Clean up old images
docker image prune -f
```

### 7.2 Verification Steps

After every deployment, verify:

```bash
# 1. All services are healthy
docker compose -f docker-compose.prod.yml ps
# All should show "healthy" or "Up"

# 2. Backend health endpoint
curl -sf https://api.salesos.com/health | jq .
# status: "healthy", database: "connected", neo4j: "connected", redis: "connected"

# 3. Frontend loads
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com
# Expected: 200

# 4. API version is correct
curl -sf https://api.salesos.com/health | jq -r .version
# Expected: the version you deployed

# 5. Database connection works
docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U salesos

# 6. No errors in logs (last 5 minutes)
docker compose -f docker-compose.prod.yml logs --since 5m backend 2>&1 | grep -ci "error\|exception"
# Expected: 0

# 7. Migrations are current
docker compose -f docker-compose.prod.yml exec -T backend alembic current

# 8. Feature flags are correct
curl -sf https://api.salesos.com/health | jq .

# 9. SSL certificate is valid
echo | openssl s_client -servername salesos.com -connect salesos.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

### 7.3 Rollback Procedure

**When to rollback:**
- Health checks fail after deploy
- Error rate spikes above 5%
- Users reporting critical functionality broken
- Data integrity issues detected

**Docker Compose Rollback:**

```bash
# ═══════════════════════════════════════════
# ROLLBACK PROCEDURE
# ═══════════════════════════════════════════

# 1. STOP all services immediately
docker compose -f docker-compose.prod.yml down

# 2. RESTORE database if a migration was applied
# Check if migrations ran:
docker compose -f docker-compose.prod.yml logs migrations
# If migration was applied, restore from pre-deploy backup:
LATEST_BACKUP=$(ls -t /opt/salesos/backups/postgres/salesos_*.dump | head -1)
echo "Restoring from: $LATEST_BACKUP"

# Restore database (see section 3.1 for full restore steps)
docker compose -f docker-compose.prod.yml run --rm -e PGPASSWORD="$POSTGRES_PASSWORD" backup \
  pg_restore -h postgres -p 5432 -U salesos -d salesos \
  --clean --if-exists --no-owner --no-acl "$LATEST_BACKUP"

# 3. SET the previous working version tag
export IMAGE_TAG=v1.0.0  # <-- the PREVIOUS working version

# 4. RESTART all services with the old image
IMAGE_TAG=v1.0.0 docker compose -f docker-compose.prod.yml up -d

# 5. VERIFY the rollback
docker compose -f docker-compose.prod.yml ps
curl -sf https://api.salesos.com/health | jq .
VERSION=$(curl -s https://api.salesos.com/health | jq -r .version)
echo "Rolled back to version: $VERSION"
# Expected: v1.0.0

# 6. VERIFY no errors
docker compose -f docker-compose.prod.yml logs --since 5m backend 2>&1 | grep -ci "error"
# Expected: 0

# 7. NOTIFY the team
# Post in Slack: "Rollback completed. System is on v1.0.0. Investigating root cause."
```

**Kubernetes Rollback:**

```bash
# Rollback backend
kubectl rollout undo deployment/salesos-backend -n salesos-production

# Rollback frontend
kubectl rollout undo deployment/salesos-frontend -n salesos-production

# Monitor rollout
kubectl rollout status deployment/salesos-backend -n salesos-production
kubectl rollout status deployment/salesos-frontend -n salesos-production

# Verify
curl -sf https://api.salesos.com/health | jq .version
```

---

## 9. Emergency Procedures

### 8.1 Emergency Database Restore

Use when: data corruption detected, accidental mass deletion, or database is unrecoverable.

```bash
# ═══════════════════════════════════════════
# EMERGENCY DATABASE RESTORE
# Target time: < 30 minutes
# ═══════════════════════════════════════════

# 1. STOP all application services IMMEDIATELY
docker compose -f docker-compose.prod.yml stop backend frontend

# 2. NOTIFY team
# Slack: "EMERGENCY: Database restore in progress. System is down."

# 3. IDENTIFY the best backup
ls -lt /opt/salesos/backups/postgres/salesos_*.dump | head -5
# Choose the most recent backup before the corruption event

# 4. TERMINATE all active database connections
docker compose -f docker-compose.prod.yml exec -T postgres psql -U salesos -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE datname = 'salesos' AND pid <> pg_backend_pid();"

# 5. DROP and recreate the database
docker compose -f docker-compose.prod.yml exec -T postgres psql -U salesos -d postgres -c \
  "DROP DATABASE IF EXISTS salesos;"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U salesos -d postgres -c \
  "CREATE DATABASE salesos OWNER salesos;"

# 6. RESTORE from backup
BACKUP_FILE="/backups/postgres/salesos_YYYYMMDD_HHMMSS.dump"  # <-- set actual filename
docker compose -f docker-compose.prod.yml run --rm -e PGPASSWORD="$POSTGRES_PASSWORD" backup \
  pg_restore -h postgres -p 5432 -U salesos -d salesos \
  --clean --if-exists --no-owner --no-acl "$BACKUP_FILE"

# 7. RE-INITIALIZE extensions and schemas
docker compose -f docker-compose.prod.yml exec -T postgres psql -U salesos -d salesos -c \
  "CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
   CREATE EXTENSION IF NOT EXISTS pgcrypto;
   CREATE SCHEMA IF NOT EXISTS audit;
   CREATE SCHEMA IF NOT EXISTS identity;
   CREATE SCHEMA IF NOT EXISTS company;
   CREATE SCHEMA IF NOT EXISTS activity;
   CREATE SCHEMA IF NOT EXISTS crm;"

# 8. RUN migrations to ensure schema is current
docker compose -f docker-compose.prod.yml run --rm migrations alembic upgrade head

# 9. VERIFY data
docker compose -f docker-compose.prod.yml exec -T postgres psql -U salesos -d salesos -c \
  "SELECT schemaname, tablename, n_live_tup
   FROM pg_stat_user_tables WHERE n_live_tup > 0 ORDER BY n_live_tup DESC LIMIT 20;"

# 10. RESTART all services
docker compose -f docker-compose.prod.yml up -d

# 11. VERIFY health
curl -sf https://api.salesos.com/health | jq .
docker compose -f docker-compose.prod.yml logs --tail 20 backend | grep "Application startup"

# 12. NOTIFY team of completion
# Slack: "EMERGENCY RESTORE COMPLETE. System is back online on backup from YYYY-MM-DD HH:MM."
```

### 8.2 Emergency SSL Fix

Use when: HTTPS is broken, users see certificate errors, Caddy cannot provision certificates.

```bash
# ═══════════════════════════════════════════
# EMERGENCY SSL FIX
# Target time: < 10 minutes
# ═══════════════════════════════════════════

# 1. DIAGNOSE
echo | openssl s_client -servername salesos.com -connect salesos.com:443 2>&1 | head -20
dig +short salesos.com
dig +short api.salesos.com

# 2. VERIFY DNS records point to this server
MY_IP=$(curl -s ifconfig.me)
echo "Server IP: $MY_IP"
echo "DNS resolves to: $(dig +short salesos.com)"
# These must match

# 3. VERIFY firewall allows ports 80 and 443
ss -tlnp | grep -E ":80|:443"
# Both ports must be listening

# 4. CHECK Caddy logs for ACME errors
docker compose -f docker-compose.prod.yml logs caddy 2>&1 | \
  grep -i "acme\|certificate\|tls\|challenge" | tail -20

# 5. CLEAR cached certificates (force re-provisioning)
docker compose -f docker-compose.prod.yml exec caddy rm -rf /data/caddy/certificates/

# 6. RESTART Caddy
docker compose -f docker-compose.prod.yml restart caddy

# 7. WAIT 30 seconds for certificate provisioning
sleep 30

# 8. VERIFY new certificate
echo | openssl s_client -servername salesos.com -connect salesos.com:443 2>/dev/null | \
  openssl x509 -noout -dates -subject
# Should show valid dates and correct domain

# 9. TEST HTTPS access
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com
curl -sf -o /dev/null -w "%{http_code}" https://api.salesos.com/health
# Both should return 200
```

### 8.3 Full System Restart Order

Use when: multiple services are failing, system is in an unknown state, or after a server reboot.

```bash
# ═══════════════════════════════════════════
# FULL SYSTEM RESTART
# Follow this exact order to avoid dependency failures
# ═══════════════════════════════════════════

# 1. STOP everything
docker compose -f docker-compose.prod.yml down

# 2. VERIFY all containers are stopped
docker compose -f docker-compose.prod.yml ps
# All should show "Exit" or not appear

# 3. START infrastructure services (no dependencies)
docker compose -f docker-compose.prod.yml up -d postgres neo4j redis

# 4. WAIT for health checks to pass (30-60 seconds)
echo "Waiting for infrastructure..."
for i in $(seq 1 30); do
  PG_STATUS=$(docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U salesos 2>&1)
  if echo "$PG_STATUS" | grep -q "accepting connections"; then
    echo "PostgreSQL: ready"
    break
  fi
  sleep 2
done

# Verify Neo4j
docker compose -f docker-compose.prod.yml exec -T neo4j \
  cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" 2>/dev/null && echo "Neo4j: ready"

# Verify Redis
docker compose -f docker-compose.prod.yml exec -T redis redis-cli ping 2>/dev/null && echo "Redis: ready"

# 5. START connection pooler and run migrations
docker compose -f docker-compose.prod.yml up -d pgbouncer
sleep 5

# Verify PgBouncer
docker compose -f docker-compose.prod.yml exec -T pgbouncer \
  psql -h localhost -p 6432 pgbouncer -c "SHOW POOLS;" && echo "PgBouncer: ready"

# Run migrations
docker compose -f docker-compose.prod.yml up -d migrations
sleep 10
docker compose -f docker-compose.prod.yml logs migrations | tail -5

# 6. START application services
docker compose -f docker-compose.prod.yml up -d backend
sleep 15

# Verify backend
curl -sf https://api.salesos.com/health | jq . && echo "Backend: healthy"

# 7. START frontend and reverse proxy
docker compose -f docker-compose.prod.yml up -d frontend caddy
sleep 10

# Verify frontend
curl -sf -o /dev/null -w "%{http_code}" https://salesos.com && echo "Frontend: OK"

# 8. START backup service
docker compose -f docker-compose.prod.yml up -d backup

# 9. FINAL VERIFICATION
echo ""
echo "=== Full System Status ==="
docker compose -f docker-compose.prod.yml ps
echo ""
echo "=== API Health ==="
curl -sf https://api.salesos.com/health | jq .
echo ""
echo "=== Frontend ==="
curl -sf -o /dev/null -w "HTTP %{http_code}\n" https://salesos.com
echo ""
echo "=== SSL ==="
echo | openssl s_client -servername salesos.com -connect salesos.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# 10. MONITOR for 15 minutes
echo "Monitoring for errors (Ctrl+C to stop)..."
docker compose -f docker-compose.prod.yml logs -f backend 2>&1 | \
  grep --line-buffered -i "error\|exception"
```

---

## Quick Reference — Essential Commands

```bash
COMPOSE="docker compose -f docker-compose.prod.yml"

# ── Status ──────────────────────────────────────
$COMPOSE ps                                # Service health
curl -sf https://api.salesos.com/health | jq .  # Full health check
docker stats --no-stream                   # Resource usage

# ── Logs ────────────────────────────────────────
$COMPOSE logs -f --tail 100 backend        # Follow backend logs
$COMPOSE logs --since 1h backend | grep -i error  # Recent errors

# ── Restart ─────────────────────────────────────
$COMPOSE restart backend                   # Restart one service
$COMPOSE down && $COMPOSE up -d            # Full restart

# ── Database ────────────────────────────────────
$COMPOSE exec postgres psql -U salesos -d salesos  # Connect to PG
$COMPOSE exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD"  # Connect to Neo4j

# ── Backup / Restore ───────────────────────────
$COMPOSE run --rm backup /usr/local/bin/backup-db  # Manual backup
$COMPOSE exec backup ls -la /backups/postgres/     # List backups

# ── Deployment ──────────────────────────────────
IMAGE_TAG=v1.1.0 $COMPOSE pull            # Pull new images
IMAGE_TAG=v1.1.0 $COMPOSE up -d            # Deploy
```

---

*Created: 2026-07-12*
*Version: 1.0 — General Availability*
*Owner: SRE / Release Manager*
*Review: After every P0 incident + quarterly*
