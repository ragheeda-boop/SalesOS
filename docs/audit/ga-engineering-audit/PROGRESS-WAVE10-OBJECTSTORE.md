# Progress — Wave 10 primary DR + offsite (2026-07-28)

**Classification:** prep only — **not validated** primary PITR / offsite restore  
**Production GO:** **false**

## Done in repo

1. Optional MinIO service under compose profile `objectstore` (`salesos/docker-compose.yml`)
2. Offsite checklist remains [runbooks/offsite-s3-restore-stub.md](./runbooks/offsite-s3-restore-stub.md) — operators can now start local MinIO without inventing a missing service
3. RPO acceptance remains **UNSIGNED** in [SIGN_HERE.md](./SIGN_HERE.md) — do not forge

## Still BLOCKED (requires human / infra)

| Item | Blocker |
|------|---------|
| Primary `archive_mode=on` + restart | Explicit ops approval; may interrupt local primary |
| `pg_basebackup` / PITR restore drill | Needs archive_mode + replication HBA |
| Offsite upload/download drill | Needs `MINIO_*` / `S3_*` secrets outside git |
| CTO RPO sign-off (24h vs WAL) | Human signature |

## Operator next commands (local disposable only)

```powershell
cd salesos
docker compose --profile objectstore up -d minio
# Configure backup S3 endpoint to http://minio:9000 via env — never commit keys
# Then follow offsite-s3-restore-stub.md upload/download/restore into salesos_restore_drill
```

**Honesty:** Adding MinIO profile ≠ DR closed. Primary WAL/PITR still OPEN.
