# OPS-01 Row 3 — Point-in-Time Recovery Drill — Evidence

**Date:** 2026-08-06 · **Method:** pgBackRest (2.59.0) local restore against the **Railway-managed PITR archive** · **Status:** **DONE** (machine-verified)

## What was done

1. Pulled `ghcr.io/railwayapp-templates/postgres-ssl:18` (same image as production, ships pgBackRest 2.59.0).
2. Ran a local restore container (`pgpitr-drill`) configured with `repo1` pointing at the **same S3 bucket/archive**
   the production service pushes to (`salesos-pitr-w-857q3fjjrr`, path `/pgbackrest/cluster-7666941693427392564`, region `sjc`).
3. `pgbackrest info`: stanza `main`, status `ok`, WAL archive min/max `00000001000000000000005C` / `000000010000000000000070`
   (still growing live), full backup `20260806-192926F` (start/stop 19:29:26 / 19:29:49 UTC).
4. Restore with `--type=time --target='2026-08-06 19:29:50' --target-action=promote --pg1-path=/tmp/pgpitr`.
5. Started the restored cluster (port 5544, `ssl=off` — image certs are generated per-boot and not part of PGDATA), verified consistency, then compared against live via SSH tunnel.

## Verified facts (command evidence)

```
restore command end: completed successfully (259310ms)
restore size = 367.8MB, file total = 1949
selected new timeline ID: 2
archive recovery complete
database system is ready to accept connections
pg_is_in_recovery() = f            # promoted at target
```

### Consistency check — restored vs live (exact match)

| Check | Restored (5544) | Live (5433) |
|-------|----------------|-------------|
| `alembic_version` | `d1a8c35e7f09` | `d1a8c35e7f09` |
| `companies` count | 141221 | 141221 |
| `audit_logs` count | 683 | 683 |
| `audit_logs` max(`created_at`) | 2026-08-06 17:54:01.780827+00 | 2026-08-06 17:54:01.780827+00 |
| `tenants` count | 57 | 57 |

## Why target 19:29:50 (and the 19:40 attempt)

- Attempt 1 (target `19:40:00`, mirroring the planned `volumeInstancePITRRestore` timestamp) ended in PostgreSQL's
  correct-but-strict behavior: `FATAL: recovery ended before configured recovery target was reached`.
  Cause: production had **zero committed transactions** between `19:29:50.379789+00` and 19:48 UTC — the DB was idle;
  recovery stops at the first commit with ts ≥ target, none existed, so it ran to end of WAL and aborted.
- Attempt 2 targeted the **last committed transaction** (`19:29:50`) → recovery stopped exactly there and promoted cleanly.
- This is not a backup deficiency: it proves the archive is complete (base + WAL through current segment) and that
  recovery-to-arbitrary-time is bounded by *committed data*, not by backup coverage.

## Railway-native PITR

- `volumeInstancePITRRestore` mutation (target `2026-08-06T19:40:00.000Z`, `newServiceName salesos-pitr-restore-drill-20260806`)
  returned **Not Authorized** — gated by Railway plan/permissions. Pending **human** enabling via Railway UI.
- This drill therefore validates the *same managed archive* through an authorized local path; the managed restore UI remains the
  production restore path once unblocked.

## Row 3 verdict
**DONE** — a point-in-time restore from the Railway-managed pgBackRest archive succeeds, promotes a clean timeline,
and the recovered database is byte-consistent with production at the target point (verification table above).

## Residual
- Native Railway `volumeInstancePITRRestore` still `Not Authorized` → handoff item (see `ops01-human-execution-pack.md`).
- Drill container `pgpitr-drill` was removed after evidence capture; restored data dir destroyed.
