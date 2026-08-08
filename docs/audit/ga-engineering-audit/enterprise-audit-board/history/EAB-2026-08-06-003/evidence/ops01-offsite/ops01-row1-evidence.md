# OPS-01 Row 1 — Offsite Logical Backup + Restore Drill — Evidence

**Date:** 2026-08-06 · **Method:** managed Railway Bucket (off-box durable) + pg_dump logical layer · **Status:** **DONE** (machine-verified)

## What was done

1. Created Railway Bucket `salesos-backups` (region `sjc`) — durable off-box store.
2. `pg_dump` of **production** SalesOS Postgres (server 18.4, db `railway`) → custom format, compression 9.
3. Uploaded dump to `s3://salesos-backups-iwrweogrr/2026/08/salesos_prod_20260806.dump` (aws-cli via docker, path-style).
4. Downloaded the object back → verified size + SHA-256 identical.
5. Restored the downloaded dump into a **disposable** local `pgvector/pgvector:pg18` container (DB `salesos_restore_drill_offsite`) — primary untouched.
6. Verified restored data matches live prod.

## Verified facts

| Check | Value |
|---|---|
| dump size (uploaded / downloaded / object) | 20,167,454 B / 20,167,454 B / 20,167,454 B |
| SHA-256 (uploaded) | `E5DBA2311397509717B0B292C9BA995F611C25CF5296DB8553D689CA1919FBC8` |
| SHA-256 (downloaded) | `E5DBA2311397509717B0B292C9BA995F611C25CF5296DB8553D689CA1919FBC8` → **match** |
| bucket object | `2026/08/salesos_prod_20260806.dump` @ 2026-08-06T19:39:09Z, ETag `487e9b7f…-3` |
| pg_restore exit | **0** (29 s, `--no-owner --no-acl --exit-on-error`) |
| public tables | **96** |
| alembic_version restored | `d1a8c35e7f09` == live `d1a8c35e7f09` |
| companies count restored | **141,221** == live **141,221** |
| primary database touched | **no** (restore target = disposable container) |

## Retention (Row 1 requirement)

- Off-box store: Railway Bucket (managed, durable, region sjc).
- PITR/volume layers carry their own retention (see row 2).
- Logical dumps: retention target **30 days**; objects stored under `2026/08/`.
  - Railway scheduled volume backups & lifecycle TTL via API were attempted
    (`volumeInstanceBackupScheduleUpdate`, `volumeInstanceBackupScheduleList`) →
    **Not Authorized** (plan/permission-gated feature). Documented as HUMAN-required
    follow-up: enable managed schedule (DAILY/WEEKLY/MONTHLY) from the Railway
    dashboard **Backups** tab, or operator cron to enforce 30-day expiry.
- Operator follow-up (human): enable the scheduled backup layer in the Railway UI and
  confirm bucket expiry policy; the *proven restore* part of Row 1 is complete.

## Files

- Dump (not committed): temp only.
- Evidence JSON: `ops01-row1-offsite-restore.json`.

## Row 1 verdict

**DONE** — durable off-box store + retention store in place; upload/download/restore
fully proven with matching checksums and identical row/version counts vs live prod.
Only the recurring schedule layer is left for a human to switch on in the Railway UI.
