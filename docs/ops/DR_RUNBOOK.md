# SalesOS Disaster Recovery Runbook

> **Audience**: On-call SRE / DevOps responding to disaster scenarios.
> **Last updated**: 2026-08-12 (RPO/PITR honesty aligned to EAB-003 DONE\* drills; cutover gate still Human-Gate)
> **Version**: 1.1

> **GA / cutover gate:** [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md) — human CLOSE still **OPEN** for rows 1–3; soak (row 4) **OPEN** → **no evidence-based Production GO**.  
> **Rows 1–3 CLOSE packet (unsigned):** [DR-ROWS-1-3-CLOSE-PACKET.md](./DR-ROWS-1-3-CLOSE-PACKET.md)  
> **OPS-01 pack (EAB-003):** [../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md)  
> **Machine facts:** Offsite + WAL + PITR drills **DONE\*** (2026-08-06/07). Managed schedule / native `volumeInstancePITRRestore` = **BLOCKED-HUMAN** — [railway-managed-backup-schedule.md](../audit/ga-engineering-audit/runbooks/railway-managed-backup-schedule.md).  
> **Compose SoT:** [COMPOSE-SOURCE-OF-TRUTH.md](./COMPOSE-SOURCE-OF-TRUTH.md) (`salesos/docker-compose.yml`). Compose-local `archive_mode` often **off** — do not cite as prod denial.

---

## Table of Contents

1. [RPO and RTO Targets](#1-rpo-and-rto-targets)
2. [Backup Strategy](#2-backup-strategy)
3. [PITR / WAL Archiving](#3-pitr--wal-archiving)
4. [Multi-Region DR Strategy](#4-multi-region-dr-strategy)
5. [Restore Procedures](#5-restore-procedures)
6. [Disaster Scenarios](#6-disaster-scenarios)
7. [DR Testing Schedule](#7-dr-testing-schedule)
8. [Communication Plan](#8-communication-plan)

---

## 1. RPO and RTO Targets

| Metric | Target | Current Capability (honest) | Gap / residual |
|--------|--------|------------------------------|----------------|
| **RPO** (Data loss tolerance) | < 1 hour | **Minutes-class** on production path when WAL archive healthy (`archive_mode=on`, pgBackRest → `salesos-pitr-*`; reverify 2026-08-07 `failed_count=0`). Snapshot-only fallback still ~24h if WAL path unavailable. | **Human:** RPO acceptance ink (OPS01-08) UNSIGNED; managed backup **schedule** BLOCKED-HUMAN |
| **RTO** (Time to restore) | < 4 hours | **~5–10 min** measured for pgBackRest PITR drill (Row 3); logical `pg_dump`→S3→disposable restore also proven (Row 1, ~minutes–tens of minutes) | Native Railway `volumeInstancePITRRestore` **Not Authorized** (use drill-proven pgBackRest path until HG-04) |
| **Backup window** | 02:00-04:00 UTC | Continuous WAL + proven offsite dump; recurring Railway volume schedule **not** agent-enabled | Enable schedule via [HG-04 runbook](../audit/ga-engineering-audit/runbooks/railway-managed-backup-schedule.md) |
| **DR failover** | < 30 minutes | Not implemented (single-region) | Multi-region needed |

### Current Limitations

1. **PITR is drill-proven (DONE\*), not “absent”:** Production WAL archive + restore-to-timestamp evidenced under EAB-003 `evidence/ops01-pitr/`. Do **not** claim “No PITR.” Residual = managed schedule + native Railway PITR UI (**BLOCKED-HUMAN**), not missing recoverability.
2. **Cutover gate ≠ machine facts:** Checklist CLOSE and Production GO require human ink + soak — see [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md).
3. **Single-region:** Backups/infra primarily single-region; region failure remains a residual risk.

---

## 2. Backup Strategy

### 2.1 Backup Components

| Component | Method | Schedule | Retention | Storage |
|-----------|--------|----------|-----------|---------|
| PostgreSQL | `pg_dump` custom format (compress=9) | Daily 03:00 UTC | 7 days local + 30 days S3 | `/backups` volume + `s3://salesos-backups` |
| PostgreSQL WAL | Streaming archive (when configured) | Continuous | 7 days | S3 (separate bucket) |
| Neo4j | APOC export / `neo4j-admin dump` | Daily 04:00 UTC | 7 days | Local + S3 |
| Redis | `SAVE` + RDB copy | Every 6 hours | 3 days | Local |
| Application config | `.env.production` + volume snapshots | On change | Indefinite | S3 + git |
| Terraform state | S3 backend (versioned) | On every apply | Indefinite | S3 |

### 2.2 Backup Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `backup-db.sh` | `salesos/infra/scripts/backup-db.sh` | PostgreSQL backup (Linux/Docker) |
| `backup.ps1` | `salesos/scripts/backup.ps1` | Full backup (PG + Neo4j + Redis, Windows) |
| `backup-neo4j.sh` | `salesos/infra/scripts/backup-neo4j.sh` | Neo4j backup |
| `cron-backup.sh` | `salesos/infra/scripts/cron-backup.sh` | Cron wrapper for Docker backup container |

### 2.3 Backup Verification

| Test | Frequency | Script | What It Checks |
|------|-----------|--------|----------------|
| Restore test | Weekly (Saturday 05:00 UTC) | `restore-test.ps1` | Full backup → destroy → restore → verify cycle |
| Row count check | Weekly | Part of restore test | Compares every table row count |
| Index verification | Weekly | Part of restore test | Validates all indexes exist |
| Smoke test | Weekly | Part of restore test | Health endpoints respond correctly |

---

## 3. PITR / WAL Archiving

### 3.1 Overview

Point-in-Time Recovery (PITR) enables restoring the database to any moment within the WAL retention period, reducing the recovery window from 24 hours to minutes.

### 3.2 Configuration Requirements

**PostgreSQL config (`postgresql.conf`):**

```ini
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://salesos-wal-archives/%f'
archive_timeout = 60
max_wal_senders = 3
wal_keep_size = 1024   # MB
```

**S3 bucket structure:**

```
s3://salesos-wal-archives/
  └── {YYYY}/{MM}/{DD}/
      ├── 0000000100000000
      ├── 0000000100000001
      └── ...
```

**Docker Compose integration** (add to `docker-compose.prod.yml`):

```yaml
postgres:
  image: pgvector/pgvector:pg16
  command:
    - "postgres"
    - "-c"
    - "wal_level=replica"
    - "-c"
    - "archive_mode=on"
    - "-c"
    - "archive_command=aws s3 cp %p s3://salesos-wal-archives/%f"
  environment:
    AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
    AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    AWS_DEFAULT_REGION: me-south-1
```

**Managed RDS (recommended for production):**

- Enable automated backups with 7-day retention
- Enable WAL archiving (automatic in RDS)
- Configure cross-region snapshot copy to secondary region

### 3.3 PITR Restore Procedure

```bash
# 1. Stop backend (prevent writes)
docker compose -f docker-compose.prod.yml stop backend

# 2. Identify target timestamp
# "2026-07-17 14:30:00 UTC"

# 3. Restore from base backup + WAL archive
pg_basebackup -h postgres -D /tmp/pg_restore -X stream -P
pg_ctl -D /tmp/pg_restore start
# Apply WAL up to target timestamp
pg_ctl -D /tmp/pg_restore promote

# 4. Verify data integrity
psql -d salesos -c "SELECT COUNT(*) FROM identity.users;"

# 5. Promote restored database to primary
# Update DNS / connection strings

# 6. Restart backend
docker compose -f docker-compose.prod.yml start backend
```

### 3.4 Monitoring WAL Status

```sql
-- Check WAL archive status
SELECT * FROM pg_stat_archiver;

-- Check last WAL file archived
SELECT last_archived_wal, last_archived_time FROM pg_stat_archiver;

-- Check replication slots
SELECT slot_name, slot_type, active, restart_lsn FROM pg_replication_slots;
```

---

## 4. Multi-Region DR Strategy

### 4.1 Architecture Overview

```
Primary Region (me-south-1)          DR Region (eu-central-1)
┌─────────────────────────┐         ┌─────────────────────────┐
│  Application (EKS)      │         │  Application (EKS)       │
│  PostgreSQL (RDS Multi-AZ)│        │  PostgreSQL (RDS Read)   │
│  Neo4j (standalone)     │         │  Neo4j (standby)         │
│  Redis (standalone)     │         │  Redis (standalone)      │
│  S3 Backups (primary)   │───复制──►│  S3 Backups (replica)    │
│  WAL Archive S3         │───复制──►│  WAL Archive S3         │
└─────────────────────────┘         └─────────────────────────┘
```

### 4.2 S3 Cross-Region Replication

**Primary bucket:** `salesos-backups` (me-south-1)
**Replica bucket:** `salesos-backups-dr` (eu-central-1)

Enable S3 Cross-Region Replication (CRR):

```bash
aws s3api put-bucket-replication \
  --bucket salesos-backups \
  --replication-configuration '{
    "Role": "arn:aws:iam::ACCOUNT:role/s3-crr-role",
    "Rules": [{
      "Status": "Enabled",
      "Priority": 1,
      "Filter": {},
      "Destination": {
        "Bucket": "arn:aws:s3:::salesos-backups-dr",
        "Region": "eu-central-1"
      }
    }]
  }'
```

**WAL archive bucket:**

- `salesos-wal-archives` (me-south-1) → CRR to `salesos-wal-archives-dr` (eu-central-1)
- Same-day replication (S3 CRR typically completes within 15 minutes)

### 4.3 RDS Cross-Region Read Replica

```bash
# Create cross-region read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier salesos-dr \
  --source-db-instance-identifier salesos-primary \
  --source-region me-south-1 \
  --db-instance-class db.r6g.large \
  --region eu-central-1

# Promote to standalone (during failover)
aws rds promote-read-replica \
  --db-instance-identifier salesos-dr \
  --region eu-central-1
```

### 4.4 DNS Failover (Route53)

```
Primary:   api.salesos.com → ALB (me-south-1)
Failover:  api.salesos.com → ALB (eu-central-1)
```

Configure Route53 with active-passive failover routing:
- Health check on `/health` endpoint
- Failover threshold: 3 consecutive failures
- TTL: 60 seconds

### 4.5 DR Failover Procedure

```bash
# 1. Confirm primary region is down
curl -sf https://api.salesos.com/health || echo "Primary UNREACHABLE"

# 2. Promote RDS read replica to primary
aws rds promote-read-replica --db-instance-identifier salesos-dr --region eu-central-1

# 3. Update application config to point to DR database
# (Handled via environment variable change in CI/CD)

# 4. Deploy application stack to DR region
./infra/scripts/deploy.sh --region eu-central-1

# 5. Restore latest backup if needed
aws s3 cp s3://salesos-backups-dr/latest.dump ./latest.dump --region eu-central-1
pg_restore -d salesos -U salesos --clean --if-exists ./latest.dump

# 6. Update Route53 DNS to point to DR load balancer

# 7. Verify health
curl -sf https://api.salesos.com/health

# 8. Notify stakeholders
```

### 4.6 Failback Procedure

```
1. Primary region is restored and operational
2. Take final backup from DR region
3. Restore to primary region
4. Switch DNS back to primary
5. Verify health
6. Notify stakeholders
```

---

## 5. Restore Procedures

### 5.1 PostgreSQL Restore (from daily dump)

```bash
# 1. Find latest backup
LATEST=$(ls -t /opt/salesos/backups/postgres/salesos_*.dump | head -1)

# 2. Stop applications
docker compose -f docker-compose.prod.yml stop backend

# 3. Restore
PGPASSWORD=$POSTGRES_PASSWORD pg_restore \
  -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --clean --if-exists --no-owner --no-acl "$LATEST"

# 4. Verify
psql -d $DB_NAME -c "SELECT COUNT(*) FROM identity.users;"

# 5. Restart applications
docker compose -f docker-compose.prod.yml start backend
```

### 5.2 PITR Restore (to specific time)

```bash
# 1. Restore base backup
pg_basebackup -h $DB_HOST -D /tmp/pg_restore -X stream -P

# 2. Configure recovery.conf
echo "restore_command = 'aws s3 cp s3://salesos-wal-archives/%f %p'" > /tmp/pg_restore/recovery.conf
echo "recovery_target_time = '2026-07-17 14:30:00 UTC'" >> /tmp/pg_restore/recovery.conf

# 3. Start PostgreSQL in recovery mode
pg_ctl -D /tmp/pg_restore start

# 4. Verify
psql -d salesos -c "SELECT NOW() - pg_last_xact_replay_timestamp() AS replication_lag;"

# 5. Promote when ready
pg_ctl -D /tmp/pg_restore promote
```

### 5.3 Full Stack Restore

```bash
# 1. Provision new infrastructure (Terraform)
cd salesos/infra/terraform
terraform init
terraform apply

# 2. Restore PostgreSQL
./infra/scripts/restore-db.sh s3://salesos-backups/latest.dump

# 3. Restore Neo4j
./infra/scripts/backup-neo4j.sh --restore

# 4. Deploy application
./infra/scripts/deploy.sh

# 5. Verify
curl -sf https://api.salesos.com/health | jq .
```

---

## 6. Disaster Scenarios

### Scenario 1: Database Corruption

| Step | Action | Owner | ETA |
|------|--------|-------|-----|
| 1 | Detect: alerts fire (HighErrorRate, DB errors in logs) | On-call | 0 min |
| 2 | Identify: check `pg_stat_activity`, error logs for corruption | On-call | 5 min |
| 3 | Stop: `docker compose stop backend` | On-call | 2 min |
| 4 | Restore: run restore-db.sh with latest clean backup | On-call | 30 min |
| 5 | Verify: row counts, run smoke tests | On-call | 10 min |
| 6 | Resume: `docker compose start backend` | On-call | 2 min |
| 7 | Investigate: root cause of corruption | Engineering Lead | 1 hour |
| **Total RTO** | | | **~50 min** |

### Scenario 2: Complete Region Failure

| Step | Action | Owner | ETA |
|------|--------|-------|-----|
| 1 | Detect: all health checks fail, cloudwatch alarms | On-call | 0 min |
| 2 | Confirm: verify from multiple locations | On-call | 5 min |
| 3 | Escalate: notify Engineering Lead, CTO | On-call | 5 min |
| 4 | Activate DR: run DR failover procedure | DevOps | 15 min |
| 5 | Promote RDS replica | DevOps | 10 min |
| 6 | Deploy to DR region | DevOps | 20 min |
| 7 | Update DNS | DevOps | 5 min |
| 8 | Verify: health check, smoke tests | On-call | 10 min |
| 9 | Notify: all stakeholders | Engineering Lead | 5 min |
| **Total RTO** | | | **~75 min** |

### Scenario 3: Accidental Data Deletion

| Step | Action | Owner | ETA |
|------|--------|-------|-----|
| 1 | Detect: user reports missing data, or audit log shows bulk delete | On-call | 0 min |
| 2 | Stop: `docker compose stop backend` | On-call | 2 min |
| 3 | Identify: find timestamp of deletion from audit log | On-call | 5 min |
| 4 | PITR Restore: restore to timestamp before deletion | On-call | 30 min |
| 5 | Verify: confirm restored data | On-call | 10 min |
| 6 | Resume: `docker compose start backend` | On-call | 2 min |
| 7 | Investigate: how did bulk deletion happen? | Engineering Lead | 1 hour |
| **Total RTO** | | | **~50 min** |

### Scenario 4: Security Breach / Credential Rotation

| Step | Action | Owner | ETA |
|------|--------|-------|-----|
| 1 | Detect: security alert, unauthorized access | Security | 0 min |
| 2 | Isolate: block compromised access | Security | 5 min |
| 3 | Rotate: all secrets (DB passwords, API keys, JWT) | DevOps | 15 min |
| 4 | Restart: all services with new credentials | DevOps | 10 min |
| 5 | Verify: health check, auth flow | On-call | 10 min |
| 6 | Investigate: root cause, forensic analysis | Security | Ongoing |
| **Total RTO** | | | **~40 min** |

---

## 7. DR Testing Schedule

| Test | Frequency | Owner | Success Criteria |
|------|-----------|-------|-----------------|
| Backup integrity check | Daily (automated) | DevOps | All backup files non-empty and uncorrupted |
| Restore test (full) | Weekly | DevOps | 4-phase test passes (backup → destroy → restore → verify) |
| PITR restore drill | Monthly | DevOps | Successful point-in-time recovery to random timestamp |
| DR failover drill | Quarterly | DevOps | Full region failover and failback within RTO |
| Backup encryption audit | Quarterly | Security | All backup files encrypted at rest |
| Dependency restore test | Per release | QA | All data stores restorable from latest backup |

### Automated DR Test Script

```bash
#!/bin/bash
# dr-test.sh — Automated DR readiness test

set -euo pipefail

echo "=== DR Test: $(date) ==="

# 1. Verify backup exists
echo "--- Check latest backup ---"
LATEST=$(ls -t /backups/salesos_*.dump | head -1)
test -f "$LATEST" || { echo "FAIL: No backup found"; exit 1; }

# 2. Test backup integrity
echo "--- Verify backup integrity ---"
pg_restore --list "$LATEST" > /dev/null 2>&1 || { echo "FAIL: Corrupt backup"; exit 1; }

# 3. Test S3 accessibility
echo "--- Check S3 ---"
aws s3 ls s3://salesos-backups/ --summarize > /dev/null 2>&1 || { echo "WARN: S3 not accessible"; }

# 4. Test DR region S3
echo "--- Check DR S3 ---"
aws s3 ls s3://salesos-backups-dr/ --region eu-central-1 --summarize > /dev/null 2>&1 || { echo "WARN: DR S3 not accessible"; }

echo "=== DR Test: PASS ==="
```

---

## 8. Communication Plan

### 8.1 Incident Notification

| Severity | Channels | Response Time | Notify |
|----------|----------|---------------|--------|
| P0 — Critical | Slack #salesos-critical + PagerDuty + Email | Immediate | On-call + Engineering Lead + CTO |
| P1 — High | Slack #salesos-alerts | 15 min | On-call + Engineering Lead |
| P2 — Medium | Slack #salesos-alerts | 1 hour | On-call |

### 8.2 DR Activation Template

```
🚨 DR ACTIVATED — {Scenario}

Region:     me-south-1 (PRIMARY UNREACHABLE)
Impact:     All services unavailable
Started:    {timestamp UTC}
DR region:  eu-central-1
Team:       {on-call engineer}, {engineering lead}

Next steps:
1. Promoting RDS read replica in eu-central-1
2. Deploying application stack to DR region
3. Updating DNS

Estimated RTO: 75 minutes
```

### 8.3 Post-Recovery Report

After any DR event, a post-mortem must be filed within 48 hours covering:

1. Timeline of events
2. Root cause analysis
3. Recovery actions taken
4. Gaps identified
5. Remediation items with owners and deadlines

---

## Appendix: Key Contacts

| Role | Name | Contact |
|------|------|---------|
| On-call Engineer | Rotation | PagerDuty |
| Engineering Lead | TBD | Slack @eng-lead |
| CTO | TBD | Slack @cto |
| DevOps Lead | TBD | Slack @devops |
| Security Lead | TBD | Slack @security |

---

*Document version: 1.0*
*Last updated: 2026-07-17*
*Owner: DevOps / SRE*
