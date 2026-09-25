# BACKUP / DR VALIDATION — 2026-08-24

---

## Backup Configuration

### PostgreSQL

| Property | Value | Evidence |
|----------|-------|----------|
| Backup method | `pg_dump` (custom format, compress=9) | `infra/scripts/backup-db.sh` |
| Schedule | Daily 03:00 UTC | `docker-compose.prod.yml:505-544` |
| Retention | Configurable via `RETENTION_DAYS` | `backup-db.sh:54-59` |
| Checksums | SHA-256 per backup file | `backup-db.sh:44-52` |
| Offsite | S3 upload via `aws` CLI or `rclone` | `backup-db.sh:62-71` |
| WAL archiving | Drill-proven (archive_mode=on) | DR_RUNBOOK.md |
| PITR | Drill-proven (pgBackRest) | DR_RUNBOOK.md |

### Neo4j

| Property | Value | Evidence |
|----------|-------|----------|
| Backup method | `neo4j-admin database dump` or APOC | `infra/scripts/backup-neo4j.sh` |
| Schedule | Daily 04:00 UTC | `docker-compose.prod.yml:505-544` |
| Online backup | APOC `dbms.backup()` | `backup-neo4j.sh:30-45` |

### Redis

| Property | Value | Evidence |
|----------|-------|----------|
| Persistence | AOF (`appendonly yes`) | `docker-compose.prod.yml:210` |
| Backup | Not separately backed up | Acceptable — cache only |

---

## Managed Backups (Railway)

| Property | Status | Notes |
|----------|:------:|-------|
| Railway managed backup | **NOT ENABLED** | Requires Railway Owner/Admin |
| PITR via Railway UI | **NOT ENABLED** | Requires Railway Owner/Admin |
| Custom backup schedule | ✅ ACTIVE | `docker-compose.prod.yml` cron |

---

## RPO / RTO

| Metric | Target | Current Capability | Evidence |
|--------|--------|-------------------|----------|
| RPO | < 1 hour | Minutes-class (WAL archive when healthy) | DR_RUNBOOK.md:78-168 |
| RTO | < 4 hours | ~5-10 min for pgBackRest PITR drill | DR_RUNBOOK.md |
| Backup window | 02:00-04:00 UTC | Continuous WAL + proven offsite dump | DR_RUNBOOK.md |

---

## Restore Procedure

### PostgreSQL Restore (Documented)

1. Stop application traffic
2. Download latest backup from S3
3. Verify SHA-256 checksum
4. `pg_restore --clean --if-exists -d salesos <backup_file>`
5. Apply WAL archives for PITR
6. Verify data integrity
7. Resume application traffic

### Restore Verification

| Check | Status |
|-------|:------:|
| Automated restore CI job | ❌ NOT IMPLEMENTED |
| Manual restore drill | ✅ PROVEN (DR-GA-GAPS-CHECKLIST) |
| Restore time documented | ✅ ~5-10 min |

---

## DR Gaps (from DR-GA-GAPS-CHECKLIST)

| Row | Requirement | Status | Blocker |
|-----|-------------|:------:|---------|
| 1 | Offsite backup | ⚠️ PARTIAL | Automated schedule not confirmed |
| 2 | WAL archive | ✅ DONE* | Managed schedule BLOCKED-HUMAN |
| 3 | PITR restore drill | ✅ DONE* | Native UI BLOCKED-HUMAN |
| 4 | Staging soak | ❌ OPEN | Staging not created |
| 5 | Go-live signatures | ❌ OPEN | Human signatures required |
| 8 | RPO/RTO acceptance | ❌ OPEN | Human signature required |

*DONE* = machine facts proven; human gates remain open.

---

## Acceptance

| Criterion | Status |
|-----------|:------:|
| Managed backup enabled | ❌ BLOCKED — Railway Owner/Admin |
| Retention documented | ✅ |
| PITR verified/configured | ✅ (drill-proven) |
| RPO/RTO documented | ✅ |
| Restore procedure documented | ✅ |
| Restore test completed | ⚠️ Manual proven, automated NOT IMPLEMENTED |

---

## External Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Railway managed backup enablement | Platform (Railway Owner/Admin) | NOT AVAILABLE |
| RPO/RTO human acceptance | Management | NOT SIGNED |
| Automated restore CI job | DevOps | NOT IMPLEMENTED |

**This condition CANNOT be fully closed without Railway Owner/Admin access.**
