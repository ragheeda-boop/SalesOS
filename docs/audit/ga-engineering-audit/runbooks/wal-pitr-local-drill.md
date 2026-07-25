# WAL / PITR local drill (NON-PROD documentation)

**Status:** Primary assess **DONE**; disposable archive **DONE (local)**; primary continuous archive + PITR restore **OPEN**  
**Classification:** Docs + drills — **does not** make PITR production-ready  
**Related:** [DR_RUNBOOK.md](../../../ops/DR_RUNBOOK.md) §3, [PROGRESS-WAVE10-DR-GAPS.md](../PROGRESS-WAVE10-DR-GAPS.md) (PROD-W10-003), `salesos/infra/scripts/wal-pitr-local-assess.sh`  
**Evidence:**
- [../evidence/wave10-dr/postgres-wal-settings-20260722T125025Z.txt](../evidence/wave10-dr/postgres-wal-settings-20260722T125025Z.txt) (primary still `archive_mode=off`)
- [../evidence/wave10-dr/postgres-basebackup-blocked-20260722T125025Z.json](../evidence/wave10-dr/postgres-basebackup-blocked-20260722T125025Z.json)
- [../evidence/wave10-dr/postgres-disposable-archive-20260722T125312Z.json](../evidence/wave10-dr/postgres-disposable-archive-20260722T125312Z.json)

---

## Local compose assessment (primary — unchanged 2026-07-22)

| Setting | Local `salesos-postgres-1` | Implication |
|---------|----------------------------|-------------|
| `wal_level` | `replica` | Compatible with future archive / basebackup |
| `archive_mode` | `off` | **No WAL archive on primary** — PITR impossible |
| `archive_command` | `(disabled)` | No destination |
| `archive_timeout` | `0` | N/A while archive off |
| `max_wal_senders` | `10` | Present, but see hba blocker below |
| `wal_keep_size` | `0` | Relies on checkpoints / slots |
| `pg_stat_archiver.archived_count` | `0` | No files archived on primary |
| Role `salesos` `rolreplication` | `true` | Role flag OK; **hba still blocks** streaming |

Compose (`salesos/docker-compose.yml` postgres service): **no** `-c wal_level=…` / `-c archive_mode=…` overrides — defaults above apply. Primary data volume `salesos_pgdata` was **not** modified.

### What stock compose cannot do without disruptive change

| Drill | Result (2026-07-22) |
|-------|---------------------|
| Enable `archive_mode` on **primary** | **Not done** — requires compose `command:` overrides + **Postgres restart** (data dir already initialized; `archive_mode` is restart-only) |
| `pg_basebackup` from backup profile client | **FAILED** — `pg_hba.conf` has no replication entry for backup-network clients (`no encryption`) |
| Disposable Postgres with `archive_mode=on` at init | **Succeeded** — `archived_count=3`, three 16MiB WAL files (volume must be writable by postgres UID) |

---

## Read-only assess (safe anytime)

```bash
cd salesos
bash infra/scripts/wal-pitr-local-assess.sh
# optional:
# EVIDENCE_OUT=../docs/audit/ga-engineering-audit/evidence/wave10-dr/postgres-wal-settings-$(date -u +%Y%m%dT%H%M%SZ).txt \
#   bash infra/scripts/wal-pitr-local-assess.sh
```

---

## Optional next drills (do **not** destroy primary)

These are **operator procedures**, not automated GA gates. Prefer disposable targets.

### A) Document-only (no primary change)

Keep RPO = daily `pg_dump` until CTO signs PROD-W10-003 (accept 24h pilot **or** require WAL before GA).

### B) Local archive to a volume (requires Postgres **restart** — disruptive)

**Risk:** restarting primary Postgres on a shared stack. Do **not** run on production. Do **not** point `archive_command` at S3 without credentials + bucket.

Sketch (local only, after approved window):

```yaml
# Example ONLY — not applied to compose in this wave pass
command:
  - postgres
  - -c
  - wal_level=replica
  - -c
  - archive_mode=on
  - -c
  - archive_command=test ! -f /wal_archive/%f && cp %p /wal_archive/%f
  - -c
  - archive_timeout=60
volumes:
  - pgdata:/var/lib/postgresql/data
  - wal_archive_data:/wal_archive   # new named volume
```

Then: generate WAL (`CHECKPOINT; SELECT pg_switch_wal();`), confirm files under `/wal_archive`, take `pg_basebackup` to a **disposable** directory/container, practice restore + recovery target. **Never** promote over primary without a wipe window.

### C) Side-car basebackup without enabling archive_mode — **BLOCKED on stock compose**

Attempted 2026-07-22 via `docker compose --profile backup run … pg_basebackup`. Failed: no `pg_hba` replication entry for backup clients. Role has `rolreplication=true`, but hba still refuses. Fixing requires editing hba (init scripts or mount) and likely a restart — **not applied**; primary left untouched.

### D) Disposable Postgres archive (executed 2026-07-22) — preferred safe path

Spin a **separate** `pgvector/pgvector:pg16` container with empty volumes, `archive_mode=on` at init, writable `/wal_archive` (`chmod 777` or chown UID 999). Switch WAL; confirm files. Evidence: `postgres-disposable-archive-20260722T125312Z.json` (`archived_count=3`). Container/volumes removed after drill. **Does not** enable archive on primary and **does not** prove PITR restore-to-timestamp.

---

## What remains OPEN for PITR claims

1. CTO decision (PROD-W10-003) — accept 24h RPO vs require WAL before GA  
2. **Primary** continuous `archive_mode=on` + durable archive (compose change + restart) — disposable-only proven locally  
3. `pg_hba` replication allowlist (and TLS) so basebackup/PITR tooling can connect  
4. Successful restore to a **point-in-time** on a disposable instance  
5. Staging/prod (RDS PITR or equivalent) — **out of scope** for local compose  

**Do not claim PITR production-ready from this document alone.**
