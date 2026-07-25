# Progress — Wave 10 residual DR gaps (LOCAL NON-PROD)

**Date:** 2026-07-22 (updated same day — push-blockers-as-far-as-local-compose-allows)  
**Scope:** Close residual DR gaps after [PROGRESS-WAVE10-BACKUP.md](./PROGRESS-WAVE10-BACKUP.md)  
**Environment:** Local Docker Compose **NON-PROD only**  
**Validation class:** **light validated** (local) — **does not equal production GO**  
**Production / S3 / staging:** **not touched** (no MinIO in any salesos compose file; `S3_BUCKET=""`)

---

## Verdict

| Item | Status |
|------|--------|
| `restore-db.sh` primary-safety harden | **Done** — no default-to-primary; `--force` required for primary |
| Disposable restore pattern documented | **Done** |
| Neo4j backup drill (`neo4j-admin` offline dump) | **Done (local)** — dump artifact produced; APOC still absent |
| Neo4j `database load` restore-verify | **Done (local disposable)** — load into `salesos_neo4j_load_drill`; temp boot + cypher OK; primary never stopped |
| WAL / PITR assess + drill docs | **Done (assess + docs + disposable archive)** — **primary** archive still **off**; PITR restore **not** proven |
| Primary `archive_mode` / stock `pg_basebackup` | **OPEN / blocked** — restart required for archive; hba blocks replication clients |
| WAL / PITR CTO decision (PROD-W10-003) | **Stub only** — awaiting CTO; no invented approval |
| Off-box / MinIO / S3 restore | **OPEN** — no MinIO service/profile; checklist clarified in [runbooks/offsite-s3-restore-stub.md](./runbooks/offsite-s3-restore-stub.md) |

---

## 1. Restore safety harden (`restore-db.sh`)

**Problem (from Wave 10 drill):** prior script defaulted `DB_NAME=salesos`, so a casual run could wipe the primary on a shared local stack.

**Fix:**

| Guard | Behavior |
|-------|----------|
| Target required | `--db <name>` or `DB_NAME` — refuse if unset |
| No primary default | Does **not** default to `salesos` |
| Primary wipe | Target `PRIMARY_DB_NAME` (default `salesos`) requires `--force` |
| Disposable preference | Operators use `salesos_restore_drill` (drill-proven) |

Also installed into backup image via `salesos/infra/docker/backup/Dockerfile` as `/usr/local/bin/restore-db` (rebuild backup image before relying on container path).

### Disposable restore pattern (canonical)

```bash
cd salesos

# 1) Empty clone (does NOT touch primary)
docker exec salesos-postgres-1 psql -U salesos -d postgres \
  -c "CREATE DATABASE salesos_restore_drill OWNER salesos;"

# 2a) Hardened script (after image rebuild, or host + network env)
# docker compose --profile backup run --rm --entrypoint restore-db backup \
#   /backups/salesos_20260722_075349.dump --db salesos_restore_drill

# 2b) Explicit pg_restore (used in 2026-07-22 drill evidence)
docker compose --profile backup run --rm --entrypoint sh backup -c \
  'pg_restore -h postgres -p 5432 -U "$DB_USER" -d salesos_restore_drill \
     --clean --if-exists --no-owner --no-acl \
     /backups/salesos_20260722_075349.dump'
```

**Forbidden without approved wipe window:** `restore-db … --db salesos --force` on shared stacks; **never** against production.

---

## 2. Neo4j — offline dump + disposable load-verify

### Dump (prior same day)

| Field | Value |
|-------|--------|
| Method | `neo4j-admin database dump` after brief `docker compose stop neo4j` |
| Artifact | `/backups/neo4j_wave10_dr/neo4j.dump` — **16,042 bytes**; magic **`DZV1`** |
| Evidence | [evidence/wave10-dr/neo4j-admin-dump-2026-07-22T102946Z.json](./evidence/wave10-dr/neo4j-admin-dump-2026-07-22T102946Z.json) |
| Script | `salesos/infra/scripts/backup-neo4j-offline-compose.sh` (`ALLOW_NEO4J_STOP=1`) |

### Load restore-verify (2026-07-22T124100Z) — **primary never stopped**

| Field | Value |
|-------|--------|
| Method | `neo4j-admin database load neo4j --from-path=… --overwrite-destination=true` into **new** volume `salesos_neo4j_load_drill` |
| Dump info | ZSTD; 43 files; 270,401,702 bytes logical |
| Load exit | **0** — “Done: 43 files, 257.9MiB processed in 43.694 seconds” |
| Post-load store | `/data` ≈ **258.0 MiB**; `databases/neo4j` present |
| Verify | Temporary container `neo4j-wave10-load-drill` with `NEO4J_AUTH=none` (no primary cred reuse); `RETURN 1` OK; `MATCH (n) RETURN count(n)` = **0** |
| Primary | Remained **healthy**; backend **healthy** |
| Evidence | [evidence/wave10-dr/neo4j-admin-load-20260722T124100Z.json](./evidence/wave10-dr/neo4j-admin-load-20260722T124100Z.json) |
| Script | `salesos/infra/scripts/restore-neo4j-load-drill-compose.sh` |

| Acceptance | Status |
|------------|--------|
| Neo4j dump artifact produced | **Yes** |
| Neo4j load into disposable volume | **Yes** |
| Temporary boot + cypher after load | **Yes** (node count 0 — empty graph or dump-time empty; mechanical restore proven) |
| APOC online export | **No** |
| Off-box / CronJob path | **OPEN** |

**Do not claim** production Neo4j DR complete — local dump + disposable load only.

---

## 3. WAL / PITR — as far as stock compose allows (PROD-W10-003 still OPEN)

### Primary settings (reconfirm)

| Setting | Value |
|---------|--------|
| `wal_level` | `replica` |
| `archive_mode` | **off** |
| `archive_command` | `(disabled)` |
| `archived_count` | **0** |
| `salesos` `rolreplication` | **true** |

Evidence: [evidence/wave10-dr/postgres-wal-settings-20260722T125025Z.txt](./evidence/wave10-dr/postgres-wal-settings-20260722T125025Z.txt)

### Stock-compose blockers (honest)

| Attempt | Result |
|---------|--------|
| Enable `archive_mode` on **primary** | **Not done** — needs compose `command:` + **Postgres restart**; would disrupt shared stack |
| `pg_basebackup` via backup profile | **FAILED** — no `pg_hba` replication entry for backup clients ([evidence](./evidence/wave10-dr/postgres-basebackup-blocked-20260722T125025Z.json)) |
| Disposable Postgres + `archive_mode=on` at init | **Done** — `archived_count=3`, three WAL segments (~48 MiB) ([evidence](./evidence/wave10-dr/postgres-disposable-archive-20260722T125312Z.json)); volumes/container removed after drill |

Assess script: `salesos/infra/scripts/wal-pitr-local-assess.sh`  
Drill docs: [runbooks/wal-pitr-local-drill.md](./runbooks/wal-pitr-local-drill.md)

> **This is not CTO approval.** Leave for CTO / PRC. Do not invent a signature.  
> **Do not claim PITR production-ready.**

| Field | Content |
|-------|---------|
| **ID** | PROD-W10-003 |
| **Current capability** | Daily `pg_dump` snapshot → **RPO up to ~24h**; primary WAL archive **off** |
| **Documented target** | RPO **&lt; 1 hour** needs WAL archiving + PITR restore drill |
| **Pilot option A** | **Accept RPO 24h for pilot** — written CTO acceptance required |
| **GA option B** | **Require WAL/PITR before GA** if CTO keeps RPO &lt;1h |
| **Status 2026-07-22** | **OPEN** — no signed decision; disposable archive only |

### Stub decision record (fill when CTO decides)

```text
Decision date: ________
Decider (CTO): ________
Choice: [ ] Accept RPO ~24h for pilot only   [ ] WAL/PITR required before GA
Conditions / expiry of pilot acceptance: ________
Follow-up ticket / owner: ________
```

---

## 4. Offsite / S3 restore path

**OPEN** — MinIO **not** present in any `salesos/docker-compose*.yml`; no compose profile can start it without adding a service. Clarified checklist: [runbooks/offsite-s3-restore-stub.md](./runbooks/offsite-s3-restore-stub.md)

Local dumps remain on `salesos_backup_data` only. Empty `S3_BUCKET`; no upload/download evidence.

---

## 5. Latest dump / drill artifacts (operators)

Volume: Docker `salesos_backup_data` → container `/backups`.

| Path | Size | When |
|------|------|------|
| `/backups/salesos_20260722_075349.dump` | ~21.5 MiB | 2026-07-22 07:54 UTC (PG) |
| `/backups/backup.log` | 141 B | companion log (no secrets) |
| `/backups/neo4j_wave10_dr/neo4j.dump` | 16,042 B | 2026-07-22 10:31 UTC (Neo4j) |
| Volume `salesos_neo4j_load_drill` | ~258 MiB store | Load-verify target (retained) |

---

## Residual gaps (still open)

1. **Primary WAL / PITR** — archive still off; no PITR restore-to-timestamp; CTO stub (PROD-W10-003) unsigned.  
2. **Stock `pg_basebackup`** — blocked by `pg_hba` (would need config change + likely restart).  
3. **Off-box durability (S3/MinIO)** — no MinIO service; stub checklist only.  
4. **Staging / K8s CronJob restore path** — not executed.  
5. **Backup image rebuild** — Dockerfile has `restore-db`; rebuild before container entrypoint.  
6. **PROD-W10-001 cutover / seed** — out of scope.  
7. Neo4j load showed **0 nodes** — fidelity of non-empty graph still unproven if/when graph has data.

---

## Files changed this pass (push blockers)

| File | Change |
|------|--------|
| `salesos/infra/scripts/restore-neo4j-load-drill-compose.sh` | Disposable Neo4j load + temp boot verify |
| `docs/.../evidence/wave10-dr/neo4j-admin-load-20260722T124100Z.json` | Load-verify evidence |
| `docs/.../evidence/wave10-dr/postgres-wal-settings-20260722T125025Z.txt` | Fresh primary WAL assess |
| `docs/.../evidence/wave10-dr/postgres-basebackup-blocked-20260722T125025Z.json` | Negative basebackup evidence |
| `docs/.../evidence/wave10-dr/postgres-disposable-archive-20260722T125312Z.json` | Disposable archive success |
| `docs/.../runbooks/wal-pitr-local-drill.md` | Document blockers + disposable path |
| `docs/.../runbooks/offsite-s3-restore-stub.md` | Clearer MinIO-absent checklist |
| `docs/.../PROGRESS-WAVE10-DR-GAPS.md` | This report |
| `docs/.../GA_STATUS.md` | DR blocker line refresh |

**Commands run (no secrets in evidence):** Neo4j load into disposable volume; temp Neo4j `AUTH=none` cypher; primary WAL `SHOW`/`pg_stat_archiver`; failed `pg_basebackup` (hba); disposable Postgres archive (3 WAL files) then removed; primary/neo4j/backend health checks. **Not run:** primary `archive_mode` enable; PITR restore-to-time; MinIO/S3; production; full npm/pytest.

---

*Classification: light validated local DR-gap close ≠ PITR ready ≠ offsite durable ≠ production GO.*
