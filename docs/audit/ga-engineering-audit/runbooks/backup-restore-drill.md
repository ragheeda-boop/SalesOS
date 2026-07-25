# Backup / Restore Drill Runbook (Wave 10 — DRILL EXECUTED local)

**ID:** PROD-W10-002  
**Status:** **DRILL EXECUTED (local Docker NON-PROD)** — 2026-07-22  
**Classification:** Operational evidence on local compose only; does **not** grant Production GO  
**Related:** [docs/ops/DR_RUNBOOK.md](../../../ops/DR_RUNBOOK.md), `salesos/infra/scripts/backup-db.sh`, `restore-db.sh`  
**Progress report:** [../PROGRESS-WAVE10-BACKUP.md](../PROGRESS-WAVE10-BACKUP.md)  
**Residual gaps (restore safety / Neo4j / WAL / S3):** [../PROGRESS-WAVE10-DR-GAPS.md](../PROGRESS-WAVE10-DR-GAPS.md)  
**WAL local drill docs:** [wal-pitr-local-drill.md](./wal-pitr-local-drill.md)  
**Offsite S3 stub (OPEN):** [offsite-s3-restore-stub.md](./offsite-s3-restore-stub.md)

---

## Purpose

Prove that a PostgreSQL backup can be taken and restored on a **non-production** target, with timing recorded vs documented RPO/RTO.

| Metric (from DR_RUNBOOK) | Target | Current capability (documented) | Gap |
|--------------------------|--------|----------------------------------|-----|
| RPO | < 1 hour | Up to 24h (daily snapshot) | WAL/PITR **still not proven** |
| RTO | < 4 hours | Local restore ~1–2 min for ~21MB dump; S3/K8s path **unproven** | Staging/prod path يحتاج تحقق |

---

## Preconditions

- [x] Staging or disposable DB available (local Docker; never production for first drill)
- [x] `POSTGRES_PASSWORD` / DB credentials set (compose env; not recorded in docs)
- [x] Operator has Docker Compose access under `salesos/`
- [ ] CTO aware of RPO 24h limitation OR WAL decision logged (PROD-W10-003) — **open** (decision stub in [PROGRESS-WAVE10-DR-GAPS.md](../PROGRESS-WAVE10-DR-GAPS.md); no invented approval)

---

## Evidence-based commands (repo)

### A) Compose backup service (preferred local/staging)

From `salesos/docker-compose.yml` — service `backup`, profile `backup`:

```bash
cd salesos
# Manual backup (comment in compose)
docker compose --profile backup run --rm backup backup-db
```

Scripts on image / host:

| Script | Path |
|--------|------|
| PG backup | `salesos/infra/scripts/backup-db.sh` |
| PG restore | `salesos/infra/scripts/restore-db.sh` |
| Neo4j backup | `salesos/infra/scripts/backup-neo4j.sh` |
| Cron wrapper | `salesos/infra/scripts/cron-backup.sh` |
| Windows helper | `salesos/scripts/backup.ps1` (**يحتاج تحقق** path/presence on runner) |
| K8s CronJob | `salesos/infra/k8s/backup-cronjob.yaml` |
| Restore test CronJob | `salesos/infra/k8s/restore-test-cronjob.yaml` |

### B) Direct script (container / Linux)

```bash
export PGPASSWORD=...   # required by backup-db.sh
export DB_HOST=postgres DB_USER=salesos DB_NAME=salesos BACKUP_DIR=/backups
bash salesos/infra/scripts/backup-db.sh
# Produces: ${BACKUP_DIR}/salesos_YYYYMMDD_HHMMSS.dump
```

### C) Restore to clean / disposable DB (safe pattern)

**Do not** restore into primary `salesos` without an approved wipe window + `--force`. Hardened `restore-db.sh` **refuses** unset target and refuses primary without `--force`.

```bash
# Create empty target
docker exec salesos-postgres-1 psql -U salesos -d postgres \
  -c "CREATE DATABASE salesos_restore_drill OWNER salesos;"

# Preferred: hardened restore-db (requires --db / DB_NAME; rebuild backup image once)
# docker compose --profile backup run --rm --entrypoint restore-db backup \
#   /backups/salesos_YYYYMMDD_HHMMSS.dump --db salesos_restore_drill

# Explicit pg_restore into disposable DB only (2026-07-22 drill path)
docker compose --profile backup run --rm --entrypoint sh backup -c \
  'pg_restore -h postgres -U "$DB_USER" -d salesos_restore_drill \
     --clean --if-exists --no-owner --no-acl \
     /backups/salesos_YYYYMMDD_HHMMSS.dump'
```

Primary wipe (NON-PROD only, approved window):

```bash
# Explicit — script exits non-zero without --force
restore-db /backups/salesos_YYYYMMDD_HHMMSS.dump --db salesos --force
```
### D) Alembic sanity after restore

```bash
cd salesos
docker compose exec backend alembic current
docker compose exec backend alembic heads
# Local drill (2026-07-22): SQL on primary + drill showed alembic_version = 0039
```

### E) Smoke after restore

```bash
curl -sf http://localhost:8000/health/live   # or /ping — path needs verify on env
curl -sf http://localhost:8000/health/detailed | jq .
```

**UNVERIFIED:** Exact public URLs (`https://api.salesos.com`) and S3 upload (`S3_BUCKET`) depend on environment secrets — not proven in 2026-07-22 audit / local drill.

---

## Drill procedure (when approved to execute)

1. Record start time (UTC).
2. Take backup; note file size and duration from `backup.log`.
3. Provision empty Postgres (or stop writers + restore to clone).
4. Restore dump; record duration.
5. Compare row counts for critical tables (identity users, companies, opportunities — **list exact tables before run**).
6. Run Alembic current/heads + HTTP smoke.
7. Record end time → actual RTO.
8. File report under `docs/audit/ga-engineering-audit/` (PROGRESS-WAVE10-BACKUP.md).

---

## Evidence — local drill 2026-07-22 (NON-PROD)

| Field | Value |
|-------|-------|
| Host path workspace | `…/Muhide/salesos` compose project |
| Backup command | `docker compose --profile backup run --rm backup backup-db` |
| Backup exit code | **0** |
| Dump file | `/backups/salesos_20260722_075349.dump` on volume `salesos_backup_data` |
| Size | **22,537,373 bytes** (~21.5 MiB) |
| TOC | Archive 2026-07-22 07:53:50 UTC; **431** TOC entries; custom + gzip; PG 16.14 |
| `backup.log` window | 07:53:49 → 07:54:02 UTC (~13 s dump; script `0ms` timer unreliable on Alpine) |
| Compose wall (1st run) | ~286646 ms (includes image build + postgres recreate/health) |
| Restore target | **`salesos_restore_drill`** only — primary `salesos` not wiped |
| Restore exit code | **0** |
| Restore wall | ~77608 ms |
| Spot counts | `tenants` 11=11; `companies` 264760=264760; `users` 10=10; `audit.audit_log` 17=17; public tables 71=71; alembic **0039** |
| Validation label | **light validated** local only |

Full write-up: [PROGRESS-WAVE10-BACKUP.md](../PROGRESS-WAVE10-BACKUP.md).

---

## Acceptance

| Criterion | Status |
|-----------|--------|
| Runbook written with repo paths | Done (this file) |
| Drill executed with dated report | **Done (local Docker)** — 2026-07-22 |
| Staging / S3 / K8s restore path | **Not done** — يحتاج تنفيذ |
| RPO/RTO decision signed (WAL/PITR) | **Not done** — يحتاج CTO (PROD-W10-003); stub in DR-GAPS |
| Neo4j backup dump | **Skipped with evidence** — APOC missing; offline dump not run (DR-GAPS) |
| `restore-db.sh` primary safety | **Hardened** 2026-07-22 — see DR-GAPS |

---

## Do not

- Run restore against production without explicit CTO + backup of current prod.
- Claim DR “PASS” or Production GO solely because local dump/restore succeeded.
- Restore into primary `salesos` on a shared local stack without an approved wipe + `--force`.
- Claim Neo4j DR pass without a dump artifact (APOC / offline dump still open).
