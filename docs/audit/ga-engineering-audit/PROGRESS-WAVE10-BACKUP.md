# Progress — Wave 10 Backup / Restore Drill (LOCAL)

**Date:** 2026-07-22  
**ID:** PROD-W10-002  
**Product:** SalesOS (platform intent; code under `salesos/`)  
**Environment:** Local Docker Compose **NON-PROD only**  
**Validation class:** **light validated** (local only) — **does not equal production GO**  
**Related runbook:** [runbooks/backup-restore-drill.md](./runbooks/backup-restore-drill.md)

---

## Verdict

| Result | Detail |
|--------|--------|
| **SUCCESS (local)** | `pg_dump` custom-format backup + restore into disposable DB `salesos_restore_drill` |
| Primary DB | **Not wiped** — `salesos` remained online with matching row counts after drill |
| Production | **Not touched** |
| Prod GO | **No** — local drill only; WAL/PITR / S3 / staging soak still open |

---

## Evidence summary

| Item | Value |
|------|-------|
| Drill start (local clock) | 2026-07-22T10:49:17+03:00 |
| Backup archive UTC | 2026-07-22 07:53:50 UTC (from `pg_restore -l` TOC) |
| Dump path (container) | `/backups/salesos_20260722_075349.dump` |
| Dump path (Docker volume) | volume `salesos_backup_data` → host mount under Docker Desktop volume store |
| Dump size | **22,537,373 bytes** (~21.5 MiB); log reported 21MB |
| TOC entries | **431** (list lines ~442 including comments) |
| Dump format | PostgreSQL custom (`-Fc`), gzip compress level 9 |
| Source DB / Postgres | `salesos` @ `salesos-postgres-1` (pgvector/pg16, server 16.14) |
| Backup command exit | **0** |
| Restore target | `salesos_restore_drill` (created empty; primary untouched) |
| Restore command exit | **0** |
| Restore wall time | **~77,608 ms** (compose run including health wait) |
| Alembic in dump/target | **0039** (primary and drill both) |
| Public tables | **71** primary / **71** drill |

### Row-count spot check (primary vs drill)

| Relation | Primary `salesos` | Drill `salesos_restore_drill` |
|----------|-------------------|-------------------------------|
| `public.alembic_version` | 1 | 1 |
| `public.tenants` | 11 | 11 |
| `public.companies` | 264760 | 264760 |
| `public.users` | 10 | 10 |
| `audit.audit_log` | 17 | 17 |

Schemas present in dump TOC include: `activity`, `audit`, `company`, `crm`, `identity`, plus extensions `pg_trgm`, `pgcrypto`, `uuid-ossp`, `vector`.

---

## Commands run (no secrets)

```bash
cd salesos

# 1) Backup via compose profile (builds salesos-backup image once)
docker compose --profile backup run --rm backup backup-db
# exit 0; wall ~286646 ms including first image pull/build + postgres recreate/health

# 2) Inspect dump (volume)
docker compose --profile backup run --rm --no-deps --entrypoint sh backup -c \
  "ls -lah /backups; pg_restore -l /backups/salesos_20260722_075349.dump | head"

# 3) Disposable DB (does NOT touch primary)
docker exec salesos-postgres-1 psql -U salesos -d postgres \
  -c "CREATE DATABASE salesos_restore_drill OWNER salesos;"

# 4) Restore into disposable DB only
docker compose --profile backup run --rm --entrypoint sh backup -c \
  'pg_restore -h postgres -p 5432 -U "$DB_USER" -d salesos_restore_drill \
     --clean --if-exists --no-owner --no-acl \
     /backups/salesos_20260722_075349.dump'
# exit 0; wall ~77608 ms
```

`backup.log` (volume, no credentials):

```text
[2026-07-22 07:53:49] Starting backup: salesos@postgres:5432
[2026-07-22 07:54:02] Backup complete: salesos_20260722_075349.dump (21MB, 0ms)
```

**Timing note:** Script-reported `0ms` is unreliable on Alpine/`date +%s%N`. Log timestamps imply **~13 s** pure dump window (07:53:49 → 07:54:02 UTC). First-run compose wall includes image build (~2–3 min) and a postgres container recreate+health wait — data persisted on `pgdata` volume; primary remained usable after healthy.

---

## Acceptance vs runbook

| Criterion | Status |
|-----------|--------|
| Runbook with repo paths | Done |
| Drill executed with dated evidence | **Done (local)** — this file + runbook evidence section |
| RPO/RTO CTO decision (PROD-W10-003) | **Not done** |
| Staging / S3 / K8s CronJob drill | **Not done** |
| Neo4j backup drill | **Local offline dump Done** — see [PROGRESS-WAVE10-DR-GAPS.md](./PROGRESS-WAVE10-DR-GAPS.md) (`neo4j-admin`; load-restore still OPEN) |
| Production restore | **Forbidden / not run** |

---

## Residual gaps (honest)

1. **WAL / PITR** — not configured or proven; RPO remains up to **daily snapshot** (~24h), not &lt;1h target.
2. **Off-box durability** — `S3_BUCKET` empty; dump lives only in local Docker volume `salesos_backup_data`.
3. **RTO vs DR claim** — local restore ~1–2 min for ~21MB; does **not** validate ~2h S3/K8s production path.
4. **`restore-db.sh`** — **hardened 2026-07-22 (DR gaps pass):** no longer defaults to primary; requires `--db` / `DB_NAME`, and `--force` to touch `PRIMARY_DB_NAME` (default `salesos`). Prefer disposable pattern below.
5. **Compose side effect** — first `backup` profile run recreated `salesos-postgres-1` once; recommend documenting `depends_on` recreate risk for shared local stacks.
6. **Seed / cutover (PROD-W10-001)** — out of scope for this drill pass.
7. **HTTP smoke / backend pointed at drill DB** — not required for dump integrity; primary Alembic **0039** observed via SQL only.
8. **Neo4j / WAL-PITR / S3** — Neo4j offline dump local Done; WAL archive+PITR restore + S3 still OPEN — [PROGRESS-WAVE10-DR-GAPS.md](./PROGRESS-WAVE10-DR-GAPS.md).

---

## Disposable restore pattern (operators)

Prefer an empty clone DB — never wipe primary on shared local stacks:

```bash
# Create disposable target
docker exec salesos-postgres-1 psql -U salesos -d postgres \
  -c "CREATE DATABASE salesos_restore_drill OWNER salesos;"

# Via hardened restore-db (after rebuild of backup image, or host script + network)
# DB_NAME=salesos_restore_drill restore-db /backups/salesos_YYYYMMDD_HHMMSS.dump
# or: restore-db /backups/....dump --db salesos_restore_drill

# Explicit pg_restore (drill evidence path used 2026-07-22)
docker compose --profile backup run --rm --entrypoint sh backup -c \
  'pg_restore -h postgres -p 5432 -U "$DB_USER" -d salesos_restore_drill \
     --clean --if-exists --no-owner --no-acl \
     /backups/salesos_20260722_075349.dump'
```

Primary restore requires explicit wipe intent: `--db salesos --force` (NON-PROD only; production forbidden without CTO).

### Latest dump listing (local volume `salesos_backup_data`, 2026-07-22)

| Path (container) | Size | Notes |
|------------------|------|-------|
| `/backups/salesos_20260722_075349.dump` | ~21.5 MiB | PG custom `-Fc`; drill source |
| `/backups/backup.log` | 141 B | No credentials |

No MinIO / S3 in local compose (`S3_BUCKET=""`) — dump is volume-local only.

---

## Files changed

| File | Change |
|------|--------|
| `docs/audit/ga-engineering-audit/runbooks/backup-restore-drill.md` | Status → DRILL EXECUTED (local) + evidence |
| `docs/audit/ga-engineering-audit/PROGRESS-WAVE10-BACKUP.md` | This report (+ disposable pattern / dump listing) |
| `docs/audit/ga-engineering-audit/PROGRESS-WAVE10-DR-GAPS.md` | Residual DR gaps (restore safety, Neo4j, WAL/PITR stub) |
| `salesos/infra/scripts/restore-db.sh` | Primary-safety guardrails |
| `salesos/infra/docker/backup/Dockerfile` | Install `restore-db` alongside `backup-db` |

**Secrets:** none. No `.env` edits. Dump not committed to git.

---

*Classification reminder: light validated local only ≠ pilot-ready ≠ production GO.*
