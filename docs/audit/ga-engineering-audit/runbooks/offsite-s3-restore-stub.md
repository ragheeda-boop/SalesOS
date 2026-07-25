# Offsite / S3 backup restore path (STUB — OPEN)

**Status:** **OPEN** — no MinIO/S3 service or credentials exercised on local compose  
**Classification:** Runbook stub only — **not validated** off-box restore  
**Related:** [DR_RUNBOOK.md](../../../ops/DR_RUNBOOK.md) §2 / §5, [backup-restore-drill.md](./backup-restore-drill.md), `salesos/infra/scripts/backup-db.sh` (`S3_BUCKET`), Wave 10 progress docs  
**Checked:** 2026-07-22 (Wave 10 DR-gaps close-as-far-as-local-allows pass)

---

## Honest local state (2026-07-22)

| Check | Result |
|-------|--------|
| `salesos/docker-compose.yml` MinIO service | **Absent** (grep: no `minio` / `MINIO`) |
| Compose profiles available | `backup`, `observability` (+ others) — **no** MinIO/S3 profile |
| `docker-compose.prod.yml` / staging / test | **No** MinIO service found |
| `backup` service `S3_BUCKET` | `""` (empty) in compose |
| AWS / rclone credentials in drill env | **Not present / not used** |
| Dump location | Docker volume `salesos_backup_data` only (`/backups/*.dump`) |
| Off-box copy evidence | **None** |

**Conclusion:** Cannot start MinIO “via compose profile without secrets” — the service is not defined. Durability remains **single-host Docker volume** until an external bucket or an added (non-committed-secret) MinIO profile exists.

---

## Operator checklist to close (when ready)

Do **not** commit secrets. Prefer env files outside git / secret manager.

- [ ] **Choose target:** staging MinIO **or** real S3/Spaces bucket (document endpoint; no keys in repo)
- [ ] **Add or enable** MinIO via a **dedicated compose profile** (e.g. `objectstore`) **or** use external endpoint — if adding MinIO locally, use disposable root user via `.env` (gitignored), never hardcode
- [ ] Set `S3_BUCKET` / endpoint / region for `backup` service **without** committing `.env`
- [ ] Ensure backup image has `aws` **or** `rclone` (rebuild if missing)
- [ ] **Upload drill:** copy a dated dump (or tiny probe object) → record object key + size in `evidence/wave10-dr/` (no secrets)
- [ ] **Download drill:** pull object back → checksum / size match
- [ ] **Restore drill:** `pg_restore` / hardened `restore-db` into **disposable** DB only (`salesos_restore_drill`) — never primary without `--force` + wipe window
- [ ] Update [PROGRESS-WAVE10-DR-GAPS.md](../PROGRESS-WAVE10-DR-GAPS.md) offsite row — still ≠ production GO / CRR

### Intended production path (documented target — unproven here)

1. Daily `pg_dump` (and Neo4j dump when scheduled) land under `/backups`  
2. `backup-db.sh` uploads when `S3_BUCKET` is set  
3. Optional WAL archive to `s3://…-wal-archives/` (requires `archive_mode` — see [wal-pitr-local-drill.md](./wal-pitr-local-drill.md))  
4. Cross-region replication / DR region — see `DR_RUNBOOK.md` §4  

### Restore from S3 (operator stub)

```bash
# Preconditions (ALL currently OPEN locally):
# - AWS credentials with read on backup bucket
# - Network to S3 endpoint
# - Disposable restore DB (never wipe primary by accident)

export AWS_PROFILE=...          # or key env — do not commit secrets
aws s3 ls s3://salesos-backups/ # verify listing

aws s3 cp s3://salesos-backups/YYYY/MM/salesos_YYYYMMDD_HHMMSS.dump ./

# restore-db ./salesos_YYYYMMDD_HHMMSS.dump --db salesos_restore_drill
```

**Forbidden without approved wipe window:** restore over production primary; claiming RTO ~2h without timed staging evidence.

---

**Current label:** **not validated** (offsite). Local volume dump/restore + Neo4j load-drill remain **light validated**.
