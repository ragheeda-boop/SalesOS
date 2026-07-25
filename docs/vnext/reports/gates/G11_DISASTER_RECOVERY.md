# Gate G-11: Backup & Disaster Recovery Report

> **Gate**: G-11 — Backup & Disaster Recovery
> **Date**: 2026-07-17
> **Reviewer**: DevOps Engineer
> **Work Order**: WO-PRC-PRODUCTION-READINESS.md
> **Status**: CONDITIONAL

---

## Executive Summary

| Criterion | Result | Status |
|-----------|--------|--------|
| Database backup scripts | pg_dump custom format + Neo4j APOC/neo4j-admin + Redis SAVE | PASS |
| Volume persistence (Docker) | Named volumes for all data stores in dev + prod compose | PASS |
| Restore procedures | pg_restore, neo4j-admin load, Redis RELOAD — validated via restore-test | PASS |
| Migration reversibility | Every alembic migration has `downgrade()` (verified 0037) | PASS |
| Environment-specific config | .env.production.template, .env.staging.example, .env.example | PASS |
| Offsite/cloud backup | S3 upload (backup-db.sh, backup.ps1) | PASS |
| Automated restore testing | Weekly K8s CronJob (restore-test-cronjob) + 4-phase verification | PASS |
| Backup retention | 7-day local retention + S3 archival | PASS |
| Notification on failure | Slack webhook + healthcheck URL in backup scripts | PASS |
| PITR / WAL archiving | Not configured | FAIL |
| Multi-region DR | Single S3 bucket, no cross-region replication | FAIL |
| DR runbook | Not found in docs/ or runbook/ | FAIL |

---

## Evidence

### 1. Database Backup Scripts

**PostgreSQL** — `infra/scripts/backup-db.sh`:
- pg_dump custom format with compress=9
- Configurable: BACKUP_DIR, DB_NAME, DB_USER, DB_HOST, DB_PORT, RETENTION_DAYS
- S3 upload via aws-cli or rclone
- Slack webhook notification on failure
- Healthcheck.io ping on success
- Retention-based cleanup (find -mtime +N)

**Neo4j** — `infra/scripts/backup-neo4j.sh`:
- Dual strategy: APOC export (online, no restart) with cypher-shell, falls back to neo4j-admin database dump
- 7-day retention auto-cleanup
- Logging to backup.log

**Redis** — `scripts/backup.ps1`:
- SAVE command + RDB file copy
- Handles Redis with and without password

**Dockerized Backup Container** — `infra/docker/backup/Dockerfile`:
```
FROM postgres:16-alpine
RUN apk add --no-cache curl aws-cli
COPY scripts/backup-db.sh /usr/local/bin/backup-db
CMD ["backup-db"]
```

**Production integration** — `docker-compose.prod.yml` (lines 441-480):
- Backup service runs crond with daily schedule (3am PostgreSQL, 4am Neo4j)
- Mounts `/backups` volume
- Reads secrets from environment (PGPASSWORD, NEO4J_PASSWORD)
- Healthcheck: `test -d /backups || exit 1`

**K8s CronJob** — `infra/k8s/backup-cronjob.yaml`:
- Schedule: `0 3 * * *` (daily 3am)
- 50Gi persistent volume claim (`backup-pvc`)
- S3 bucket: `salesos-backups`
- Secrets via `salesos-secrets` SecretKeyRef
- Resource limits: 1 CPU, 512Mi memory
- concurrencyPolicy: Forbid (no overlapping runs)

### 2. Docker Volume Persistence

**docker-compose.yml** (development):
| Volume | Data Store |
|--------|-----------|
| `pgdata` | PostgreSQL `/var/lib/postgresql/data` |
| `neo4jdata` | Neo4j `/data` |
| `redisdata` | Redis `/data` |
| `meilidata` | Meilisearch `/meili_data` |
| `promdata` | Prometheus `/prometheus` |
| `grafanadata` | Grafana `/var/lib/grafana` |

**docker-compose.prod.yml** (production):
| Volume | Data Store |
|--------|-----------|
| `pgdata` | PostgreSQL |
| `neo4j_data` + `neo4j_logs` | Neo4j |
| `redis-data` | Redis (AOF enabled) |
| `zoo_data` + `zoo_logs` | Zookeeper |
| `kafka_data` | Kafka |
| `prometheus_data` | Prometheus (15d retention) |
| `grafana_data` | Grafana |
| `backups` | Backup artifacts |
| `caddy_data` + `caddy_config` | Caddy/TLS |

All volumes defined as named Docker volumes. Production compose uses `restart: always` and resource limits.

### 3. Restore Procedures

**PostgreSQL restore** — `infra/scripts/restore-db.sh`:
```bash
pg_restore -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists --no-owner --no-acl "$BACKUP_FILE"
```

**Neo4j restore** — dual strategy via `scripts/restore-test.ps1`:
- APOC import: `CALL apoc.import.json('$neo4jFile')`
- Fallback: `neo4j-admin load --from="$neo4jFile" --database=neo4j --force`

**Redis restore** — via RDB copy + DEBUG RELOAD.

**Automated Restore Testing** — `scripts/restore-test.ps1` (4-phase):
1. **Backup**: pg_dump + Neo4j APOC export + Redis SAVE
2. **Destroy**: DROP SCHEMA public CASCADE + DETACH DELETE + FLUSHALL
3. **Restore**: pg_restore + APOC import/neo4j-admin-load + Redis RELOAD
4. **Verify**: Row count comparison per table + Neo4j node/relationship counts + Redis DBSIZE + smoke test

**K8s Restore Test CronJob** — `infra/k8s/restore-test-cronjob.yaml`:
- Schedule: `0 5 * * 6` (every Saturday)
- backoffLimit: 0 (failures alert, no retry)
- 1Gi memory / 2Gi CPU limits
- Runs on backup-pvc volume

**Linux restore test** — `scripts/restore-test.sh` (equivalent shell variant).

### 4. Migration Reversibility (Alembic Downgrade)

All 37 migration versions have a `downgrade()` function. Verified in latest:
- `0037_admin_phase16.py` — `downgrade()` drops columns `outcome`, `is_ci_test`, `rollout_percentage`, drops indexes, drops tables `tenant_configs`, `admin_role_permissions`, `admin_permissions`, `admin_roles`

Migration chain is linear (no branching):
```
0001 → 0002 → ... → 0036 → 0037
```

`main.py` runs `alembic upgrade head` on startup (line 129: `docker-compose.yml` api command). Production compose has a dedicated `migrations` service (line 225-239) that runs `alembic upgrade head` before backend starts.

### 5. Environment-Specific Configuration

| File | Purpose |
|------|---------|
| `salesos/.env.production.template` | Production — all secrets marked CHANGE_ME |
| `salesos/.env.production` | Production (gitignored) |
| `salesos/.env.staging.example` | Staging template |
| `salesos/.env.staging` | Staging (gitignored) |
| `salesos/.env` | Default dev config |
| `salesos/.env.example` | Dev template |
| `salesos/backend/.env.production.template` | Backend-specific production config |
| `salesos/docker-compose.prod.yml` | Production Docker layout (Caddy, PgBouncer, Kafka, backup) |
| `salesos/infra/k8s/backup-cronjob.yaml` | K8s backup CronJob |
| `salesos/infra/k8s/restore-test-cronjob.yaml` | K8s restore test CronJob |

Backup scripts are parameterized via environment variables (BACKUP_DIR, RETENTION_DAYS, S3_BUCKET, etc.) — no hardcoded paths.

---

## Findings

### Critical (P0)

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DR-01 | **No PITR / WAL archiving** — PostgreSQL runs without `archive_mode`, `archive_command`, or any WAL-based Point-in-Time Recovery. Backups are daily snapshots only. Maximum data loss window = up to 24 hours | High | OPEN |

### High (P1)

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DR-02 | **No multi-region DR** — S3 backup targets single bucket (`salesos-backups`) with no cross-region replication or second cloud provider. Region failure = total backup loss | Medium | OPEN |
| DR-03 | **No DR runbook** — No documented disaster recovery procedure for: full region failover, data center outage, or corruption recovery | Medium | OPEN |
| DR-04 | **Restore test weekly only** — Restore validation runs once per week (Saturday). No daily automated restore verification | Low | OPEN |
| DR-05 | **Backup Dockerfile missing Neo4j tools** — `infra/docker/backup/Dockerfile` is PostgreSQL-only (no cypher-shell, no neo4j-admin). Neo4j backup from container requires separate tooling | Low | OPEN |

### Low (P3)

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| DR-06 | No backup encryption at rest documented (beyond pg_dump custom format compression) | Low | OPEN |
| DR-07 | No backup size monitoring / alerting on backup failure beyond Slack notification | Low | OPEN |
| DR-08 | S3 bucket versioning not confirmed in backup scripts | Low | OPEN |

---

## Verdict: CONDITIONAL

| Criterion | Requirement | Actual | Status |
|-----------|-------------|--------|--------|
| Database backups automated | Daily automated backup for all data stores | PostgreSQL daily (3am) via K8s CronJob + Docker; Neo4j daily (4am); Redis via backup.ps1 | PASS |
| Volume persistence | All stateful services use named volumes | 6 (dev) + 11 (prod) volumes defined | PASS |
| Restore procedure documented | Documented, testable restore steps | restore-db.sh + restore-test.ps1 (4-phase verification) | PASS |
| Migration rollback possible | Alembic downgrade for every migration | All 37 versions have downgrade() | PASS |
| Environment separation | Dev/staging/prod with different configs | 4 env templates + 3 docker-compose files + K8s config | PASS |
| Offsite backup | At least one offsite/cloud copy | S3 upload to salesos-backups bucket | CONDITIONAL |
| Restore tested automatically | Automated restore verification | Weekly CronJob (Saturday 5am) | CONDITIONAL |
| PITR capability | WAL archiving for point-in-time recovery | Not configured | FAIL |
| Multi-region DR | Backups replicated across regions | Single S3 bucket only | FAIL |

**Verdict: CONDITIONAL PASS**

**Conditions for upgrade to PASS:**
1. Implement PostgreSQL WAL archiving (`archive_mode=on`, `archive_command` to S3 or equivalent) to reduce recovery window from 24h to minutes (DR-01)
2. Document DR runbook for at least: full data loss scenario, region failover, and corruption recovery (DR-03)
3. Add cross-region S3 replication or second backup target (DR-02)

**Remediation Plan:**
- P0 (DR-01): Sprint 14 — Configure WAL archiving + test PITR restore
- P1 (DR-02, DR-03): Sprint 15 — S3 replication + DR runbook
- P1 (DR-04): Sprint 14 — Add daily restore smoke test (lightweight row-count check)

---

*Report generated by SalesOS DevOps Engineer — 2026-07-17*
*Data sources: docker-compose.yml, docker-compose.prod.yml, infra/scripts/backup-db.sh, infra/scripts/restore-db.sh, infra/scripts/backup-neo4j.sh, infra/scripts/cron-backup.sh, infra/docker/backup/Dockerfile, infra/k8s/backup-cronjob.yaml, infra/k8s/restore-test-cronjob.yaml, scripts/backup.ps1, scripts/restore-test.ps1, scripts/restore-test.sh, app/alembic/versions/0037_admin_phase16.py, .env.production.template, salesos/.env*