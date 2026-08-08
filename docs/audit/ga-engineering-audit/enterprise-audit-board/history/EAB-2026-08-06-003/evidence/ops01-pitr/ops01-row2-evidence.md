# OPS-01 Row 2 — WAL Continuous Archive (Managed PITR) — Evidence

**Date:** 2026-08-06 · **Method:** Railway managed PITR (preferred over custom) · **Status:** **DONE** (machine-verified)

## What was done

1. Created Railway Bucket `salesos-pitr` (region `sjc`).
2. Set `WAL_ARCHIVE_*` env vars on service **Postgres** (image `ghcr.io/railwayapp-templates/postgres-ssl:18`) —
   the official pgBackRest-enabled image that auto-activates archiving when `WAL_ARCHIVE_BUCKET` is set:
   `WAL_ARCHIVE_BUCKET`, `_ENDPOINT`, `_REGION`, `_KEY`, `_SECRET`. (Values kept out of repo — see AGENTS.md.)
3. Redeployed Postgres (deployment `94982fc3-1efc-405c-a6d2-3c978728721a`, SUCCESS).
4. Verified via service logs, `pg_stat_archiver`, and `pgbackrest info --output=json`.

## Verified facts (command evidence)

### Service logs (deploy 94982fc3, 2026-08-06 19:29 UTC)
- `stanza-create for stanza 'main' on repo1 ... completed successfully`
- `pushed WAL file '00000001000000000000005C' ... asynchronously`
- `backup command end: completed successfully` — `full backup size = 367.8MB, file total = 1949`
- `new backup label = 20260806-192926F`
- `pgbackrest-watcher: pitr anchor emitted` → PITR restore window now live (from 2026-08-06 19:29:26 UTC)

### SQL (via SSH tunnel → psql, docker client)
```
archive_mode       = on
archive_command    = /usr/local/bin/pgbackrest-archive-push-wrapper.sh %p
archived_count     = 6
failed_count       = 0
last_archived_wal  = 000000010000000000000060
last_archived_time = 2026-08-06 19:32:50.875675+00
```

### pgBackRest repo (canonical — `pgbackrest info --output=json`, run as postgres)
```
status: ok (db version 18, system-id 7666941693427392564)
archive: min 00000001000000000000005C, max 000000010000000000000061
backup : 20260806-192926F (full)  delta 385,691,087 B  repo 89,536,749 B
         lsn 0/5D000028 -> 0/5D000158   start 19:29:26 UTC stop 19:29:49 UTC
```

## Retention
pgBackRest `expire` is the sole WAL retention authority: full=4, diff=14, weekly fulls + daily diffs
≈ 4-week PITR window. Bucket lifecycle intentionally not set (per image docs).

## Row 2 verdict
**DONE** — continuous WAL archive on the primary to a durable off-box store, `failed_count=0`,
first full base backup anchored, restore window live. Managed capability used per instruction.

## Residual
- Restore-window proof (Row 3) still required — separate drill.
- Postgres redeploy briefly restarted the service; SalesOS `/health` re-checked **200** after.
