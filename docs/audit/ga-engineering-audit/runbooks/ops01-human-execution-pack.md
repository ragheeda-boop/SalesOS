# OPS-01 Human Execution Pack — Rows 1–5 (launch blockers)

**ID:** PROD-OPS01-HUMAN-001  
**Date:** 2026-08-06  
**Status:** **PARTIAL-EXECUTED** — rows 1–3 **DONE**; Row 5 **HUMAN-GO-INK** (SIGNED GO 2026-08-08 on SIGN_HERE); Row 4 (staging soak) **still OPEN**.  
**Production decision:** **human-declared GO** on SIGN_HERE — **engineering residual** until Row 4 (+ evidence close rule) — see [HUMAN-GO-DECLARATION-2026-08-08.md](../reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md).  
**Authority:** [DR-GA-GAPS-CHECKLIST.md](../../../ops/DR-GA-GAPS-CHECKLIST.md) (cutover gate) · [OPS-01-ADVANCEMENT.md](../enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md) · [OPS-01-CHECKLIST.md](../enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md)  
**Release/ops backlog:** [RELEASE-BACKLOG-2026-08-06.md](../RELEASE-BACKLOG-2026-08-06.md)  
**Validation label:** rows 1–3 **machine verified**; Row 5 human ink recorded; Row 4 **not validated**.

> **Principle:** AI assists. Humans decide. Evidence governs.  
> Local drills ≠ staging/prod. Human GO ink ≠ soak/DR evidence closure.  
> **Do not commit secrets.** All credentials via `.env` (gitignored) or GitHub Environment secrets.

---

## How to use (one pass, in order)

| Order | Row | Minimum time | Prerequisite |
|------:|-----|--------------|--------------|
| 1 | Row 1 — Offsite backup | ~1–2 h | A bucket (S3/Spaces/approved object store) |
| 2 | Row 2 — WAL archive | ~1 h (self-managed) or platform confirm | Offsite store from Row 1; approved Postgres restart window (non-prod) |
| 3 | Row 3 — PITR restore drill | ~1–2 h | Row 2 WAL source; disposable target DB |
| 4 | Row 4 — Staging soak 48–72h | **48–72 h wall-clock** | Real staging host (see §4.0) |
| 5 | Row 5 — Signatures | ~30 min | Rows 1–4 evidence reviewed |

Run sequentially. Do **not** start Row 4 soak until a real staging host exists (virtual/local does not count).

---

## Executed 2026-08-06 (opsai — full operator authorization)

Rows **1–3** were executed against **production** on 2026-08-06 with recorded command evidence. Managed Railway automation is
**Not Authorized** for the agent (GraphQL returns `Not Authorized`) and remains a **human** handoff. Summary + evidence:

| Row | What was proven | Evidence |
|-----|-----------------|----------|
| 1 | `pg_dump` production → bucket **`salesos-backups-iwrweogrr`** (region `sjc`), upload/download + SHA256 re-verified, disposable restore `salesos-restore-drill-pg18` = 96 tables, alembic `d1a8c35e7f09`, companies `141221` == live | `evidence/ops01-offsite/ops01-row1-offsite-restore.json` + `.md` |
| 2 | Primary `archive_mode=on` via official `postgres-ssl:18` pgBackRest wrapper → bucket **`salesos-pitr-w-857q3fjjrr`**; `archived_count=6` `failed_count=0`; base backup `20260806-192926F` (367.8 MB, 1949 files) | `evidence/ops01-pitr/ops01-row2-wal-archiver.json` + `.md` |
| 3 | pgBackRest 2.59.0 restore against the **same managed archive** → `2026-08-06 19:29:50 UTC`, promote **timeline 2**, exact consistency vs live (companies 141221, audit_logs 683, tenants 57) | `evidence/ops01-pitr/ops01-row3-pitr-restore.json` + `.md` |

**Remaining human handoffs** (agent cannot execute):
- Enable Railway managed **backup schedule** (`volumeInstanceBackupScheduleUpdate/List` → Not Authorized).
- Run native Railway **PITR restore** (`volumeInstancePITRRestore` → Not Authorized) — agent fallback already proved the same archive restores.
- **Row 4** staging soak 48–72h on a real staging host + TL review.
- **Row 5** CTO + Tech Lead — **HUMAN-GO-INK** (SIGNED GO 2026-08-08, رغيد المدني; prior NO-GO 2026-08-06 preserved).

Evidence files: `../enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/` and `.../ops01-pitr/`.

---

## Row 1 — Offsite backup (durable off-box store + retention)

**Checklist row:** OPS01-01 · **Owner:** ops · **Status:** **DONE\*** (agent-executed 2026-08-06; \*retention lifecycle rule + managed schedule = human)

### 1.0 Preconditions (human supplies, off-git)

- [ ] Target bucket name + endpoint + region chosen (e.g. S3 `salesos-backups`, or MinIO on staging host).
- [ ] IAM/API key **with write+read on that bucket only** (least privilege).
- [ ] `.env` (gitignored) on the backup host contains (names only — never paste values into this repo):
  ```
  S3_BUCKET=s3://salesos-backups
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_DEFAULT_REGION=...
  RETENTION_DAYS=30
  ```

### 1.1 Upload drill

```bash
cd salesos
docker compose --profile backup run --rm backup backup-db
# expect: "Backup complete: salesos_YYYYMMDD_HHMMSS.dump (NMB, ...)" then "Uploaded to S3: s3://.../YYYY/MM/..."
```

- [ ] Dump created under `/backups` **and** object exists in the bucket (record `s3://…/YYYY/MM/<file>.dump`, size, checksum).

### 1.2 Download drill

```bash
aws s3 ls s3://salesos-backups/YYYY/MM/
aws s3 cp s3://salesos-backups/YYYY/MM/salesos_YYYYMMDD_HHMMSS.dump ./
sha256sum ./salesos_YYYYMMDD_HHMMSS.dump   # must match upload checksum
```

- [ ] Downloaded object size + checksum == uploaded object.

### 1.3 Restore drill (disposable target — never primary)

```bash
docker exec salesos-postgres-1 psql -U salesos -d postgres \
  -c "CREATE DATABASE salesos_restore_drill_offsite OWNER salesos;"
DB_NAME=salesos_restore_drill_offsite restore-db.sh ./salesos_YYYYMMDD_HHMMSS.dump
```

- [ ] `pg_restore` exit 0; table count matches source; `alembic_version` matches source head.

### 1.4 Retention

- [ ] Bucket lifecycle rule set (e.g. 30 days) **and** `RETENTION_DAYS` on backup host consistent.

### 1.5 Evidence (write under `docs/audit/ga-engineering-audit/evidence/ops01-offsite-YYYYMMDD/`)

```json
{
  "row": 1,
  "date": "YYYY-MM-DD",
  "bucket": "salesos-backups",
  "dump": "s3://salesos-backups/YYYY/MM/salesos_YYYYMMDD_HHMMSS.dump",
  "size_bytes": 0,
  "upload_ok": true,
  "download_checksum_match": true,
  "restore_exit": 0,
  "restore_target": "salesos_restore_drill_offsite",
  "table_count_match": true,
  "retention_days": 30,
  "signed_off_by": ""
}
```

**Closes when:** upload + download + disposable restore all succeed with evidence. MinIO local profile alone **does not** close it (not durable off-box).

---

## Row 2 — WAL archive on primary (or managed equivalent)

**Checklist row:** OPS01-02 · **Owner:** ops + DBA · **Status:** **DONE\*** (managed path, agent-executed 2026-08-06; \*managed base-backup schedule = human)

### 2.0 Decide path

- [ ] **Managed (recommended for Railway prod):** confirm Railway Postgres platform backups / PITR availability and retention. If the platform provides PITR, document it as the managed equivalent and prove it in Row 3 using the platform restore UI. **No `archive_mode` editing needed on managed.**
- [ ] **Self-managed (local/staging compose):** continue §2.1.

### 2.1 Self-managed compose change (non-prod only — requires Postgres restart)

```yaml
# salesos/docker-compose.yml → postgres service (approved window on NON-PROD)
command:
  - postgres
  - -c
  - wal_level=replica
  - -c
  - archive_mode=on
  - -c
  - "archive_command=test ! -f /wal_archive/%f && cp %p /wal_archive/%f"
  - -c
  - archive_timeout=60
volumes:
  - pgdata:/var/lib/postgresql/data
  - wal_archive_data:/wal_archive
```

For **offsite** WAL archive (replaces the `cp` command once credentials exist):
```yaml
  - -c
  - "archive_command=aws s3 cp %p s3://salesos-wal-archives/%f"
```

- [ ] Restart postgres; run `CHECKPOINT; SELECT pg_switch_wal();`.
- [ ] `SELECT * FROM pg_stat_archiver;` → `archived_count` **> 0**, `last_archived_wal` populated.

### 2.2 Evidence

```json
{
  "row": 2,
  "date": "YYYY-MM-DD",
  "path": "managed",
  "platform_confirm": "Railway Postgres PITR availability + retention documented",
  "archive_mode": "on",
  "archived_count": 0,
  "last_archived_wal": "",
  "offsite_destination": "s3://salesos-wal-archives/",
  "signed_off_by": ""
}
```

**Closes when:** continuous archive producing files to a durable destination (or managed equivalent confirmed) with `archived_count` evidence.

---

## Row 3 — PITR restore drill (named timestamp)

**Checklist row:** OPS01-03 · **Owner:** ops · **Status:** **DONE\*** (agent-executed 2026-08-06 against the managed archive; \*native `volumeInstancePITRRestore` = human)

### 3.0 Preconditions

- [ ] WAL source from Row 2 (managed platform restore OR self-managed archive).
- [ ] Disposable target (never restore over primary).
- [ ] Known target timestamp (e.g. a known row's `created_at`).

### 3.1 Self-managed drill

```bash
# Base backup (requires pg_hba replication entry + TLS for the client)
pg_basebackup -h $DB_HOST -U salesos_repl -D /tmp/pg_restore -X stream -P

# Recovery config (PG16: postgresql.conf + recovery.signal)
echo "restore_command = 'aws s3 cp s3://salesos-wal-archives/%f %p'" >> /tmp/pg_restore/postgresql.conf
echo "recovery_target_time = 'YYYY-MM-DD HH:MM:SS UTC'" >> /tmp/pg_restore/postgresql.conf
touch /tmp/pg_restore/recovery.signal

pg_ctl -D /tmp/pg_restore start
# wait for replay to reach target; verify:
psql -d salesos -c "SELECT NOW() - pg_last_xact_replay_timestamp() AS lag;"
pg_ctl -D /tmp/pg_restore promote
```

- [ ] Data at the timestamp matches known source value; replay stops at target; promote succeeds.

### 3.2 Managed-platform drill (if Row 2 = managed)

- [ ] Use platform restore-to-timestamp into a **new disposable instance/DB**; verify same checks.

### 3.3 Evidence

```json
{
  "row": 3,
  "date": "YYYY-MM-DD",
  "target_timestamp": "YYYY-MM-DD HH:MM:SS UTC",
  "base_backup": "",
  "wal_replayed_ok": true,
  "promote_ok": true,
  "verify_sql": "SELECT COUNT(*) FROM ...",
  "verify_expected": "",
  "verify_actual": "",
  "signed_off_by": ""
}
```

**Closes when:** a named-timestamp restore is proven on a disposable target with linked evidence.

---

## Row 4 — Staging soak 48–72h (staging parity, not local-only)

**Checklist row:** OPS01-04 · **Owner:** ops + TL · **Status:** BLOCKED-HUMAN

### 4.0 Prerequisite — real staging host (BLOCKED-HUMAN until done)

Complete [STAGING-READINESS.md](../enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-READINESS.md) S1–S7 first:

| # | Gate | Evidence |
|---|------|----------|
| S1 | Staging host identity (`STAGING_HOST`) | host reachable |
| S2 | `STAGING_USER` / `STAGING_SSH_KEY` on GH Environment `staging` | GH secret set |
| S3 | GitHub Environment named exactly `staging` | `gh api repos/…/environments` lists it |
| S4 | Deploy workflow published (`deploy-staging.yml`) | Actions run URL |
| S5 | `.env.staging` filled off-git | no `CHANGE_ME` |
| S6 | Deploy + rollback tabletop on real host | `evidence/wave12-staging/` |
| S7 | → soak (this row) | — |

### 4.1 Parity checklist (fill against real staging)

| Dimension | Staging | Production | Match |
|-----------|---------|------------|-------|
| Backend image digest | GHCR tag/SHA | same SHA | ☐ |
| Frontend image digest | same | same | ☐ |
| Alembic `current` | == heads | == heads | ☐ |
| `demo_mode` / `feature_ai_copilot` | False / False | False / False | ☐ |
| Redis / Neo4j / Kafka | per signed degraded matrix | same | ☐ |
| Secrets source | `.env.staging` / GH env | GH env `production` | ☐ |

### 4.2 Run the 72h gate loop (staging API/FE only)

```bash
python salesos/scripts/wave11-soak-gate.py \
  --api "$STAGING_API" --fe "$STAGING_FE" --compose-dir salesos \
  --evidence-dir docs/audit/ga-engineering-audit/evidence/wave11-soak-72h \
  --loop --interval 300 --duration-hours 72 --fail-soft
```

- [ ] ≥48h (prefer 72h) continuous evidence; `soak_complete_claim` stays **false** until TL review.
- [ ] No new P0; no sustained `/health` failure; no alembic drift; flags stay False.

### 4.3 Soak report (file before flipping claim)

```markdown
# Soak Report — YYYY-MM-DD
- Environment:
- Image digests:
- Duration:
- Incidents (P0/P1/P2):
- Error rate summary:
- Decision: CONTINUE / FAIL / EXTEND
- TL review: NAME + DATE + ACK
```

**Closes when:** duration elapsed **and** TL signs the report **and** `soak_complete_claim=true` only then.

---

## Row 5 — Go-live signatures (CTO + Tech Lead)

**Checklist row:** OPS01-05 · **Owner:** leadership · **Status:** HUMAN-GO-INK (SIGNED GO 2026-08-08 on [SIGN_HERE.md](../SIGN_HERE.md); dual-role رغيد المدني)

### 5.0 Review before signing (humans only — agents must not fill names/dates/Decision)

- [ ] Rows 1–4 evidence read + linked in [OPS-01-CHECKLIST.md](../enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md).
- [ ] [go-live-checklist.md](./go-live-checklist.md) T-7/T-3/T-1/T-0 boxes re-checked.
- [ ] `soak_complete_claim` true (only after Row 4 TL review).
- [ ] RPO/RTO decision (related row 8): accept snapshot-class (24h) **or** require WAL/PITR before GA.

### 5.1 Ink

- CTO: fill the CTO block in [SIGN_HERE.md](../SIGN_HERE.md) — Status / Name / Date / **Decision: GO / NO-GO / CONDITIONAL** + conditions. **→ SIGNED GO 2026-08-08 (رغيد المدني)** — [HUMAN-GO-DECLARATION-2026-08-08.md](../reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md)
- Tech Lead: same + "Confirms evidence reviewed: [ ] Yes" checkbox. **→ SIGNED GO 2026-08-08 (same person — dual-role P1)**
- If CONDITIONAL: list conditions; scoreboard keeps engineering residual until conditions close.
- Optional witnesses: DevOps (rollback authority + on-call roster), Security (scans + residual SSRF/KG policy).

### 5.2 Update scoreboard

- [x] Record human Decision=GO on [GA_STATUS.md](../GA_STATUS.md) as **human-declared GO**; do **not** wipe OPS-01 engineering residuals (soak etc.).

---

## Evidence ledger (append one entry per completed row)

| Row | Date | Operator | Evidence path | Verdict (OPEN/PARTIAL/DONE) |
|----:|------|----------|---------------|-----------------------------|
| 1 | 2026-08-06 | opsai | `../enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/ops01-row1-offsite-restore.json` + `.md` | **DONE** |
| 2 | 2026-08-06 | opsai | `../enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row2-wal-archiver.json` + `.md` | **DONE** |
| 3 | 2026-08-06 | opsai | `../enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row3-pitr-restore.json` + `.md` | **DONE** |
| 4 | | | | OPEN (human) |
| 5 | 2026-08-08 | رغيد المدني | `../SIGN_HERE.md` + `../reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md` | **HUMAN-GO-INK** (not engineering DONE) |

## Non-claims (never write these here)

| Claim | Status |
|-------|--------|
| evidence-based Production GO (all rows 1–5 DONE) | **FALSE** — Row 4 OPEN; Row 5 is human ink only |
| human-declared GO on SIGN_HERE | **TRUE** (2026-08-08) |
| Offsite restore proven | **TRUE** (2026-08-06, production dump → S3 → disposable restore, SHA256 verified) |
| WAL/PITR proven | **TRUE** (2026-08-06, managed pgBackRest archive + restore-to-timestamp, promoted, consistency verified) |
| Managed-schedule automation (backup cadence / native PITR UI) | **FALSE** — Not Authorized for agent; human handoff |
| Staging 48–72h soak complete | **FALSE** until Row 4 closes + honest claim |
| Signatures | CTO + Tech Lead **SIGNED GO** 2026-08-08 (رغيد المدني; dual-role); prior CTO **NO-GO** 2026-08-06 preserved |

## Close rule

All of **OPS01-01 … OPS01-05** must be `DONE` with linked executable evidence **and** human signatures where required before any Production GO / cutover claim. Local drills alone never close this finding.

---

*OPS-01 Human Execution Pack — 2026-08-06 rows 1–3 machine verified; 2026-08-08 Row 5 HUMAN-GO-INK on SIGN_HERE; Row 4 still OPEN — human-declared GO ≠ evidence-based close — no commit of secrets.*
