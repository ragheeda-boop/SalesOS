# OPS-01 Signature Pack — Rows 1-3, 8 (2026-08-22)

**Finding:** EAB-001-P0-OPS-01  
**Prepared by:** Engineering Agent (automated — human signatures required)  
**Depends on:** OPS-01-CHECKLIST.md, OPS01-ROW4-STATUS.md, SOAK-RCA-2026-08-22.md

---

## Summary of Rows Requiring Signature

| Row | Requirement | Machine Status | Human Status |
|-----|-------------|---------------|--------------|
| OPS01-01 | Offsite backup + retention | **DONE*** (pg_dump to S3, SHA256 verified) | **UNSIGNED** |
| OPS01-02 | WAL archive on primary | **DONE*** (archive_mode=on, archived_count=1240+) | **UNSIGNED** |
| OPS01-03 | PITR restore to named timestamp | **DONE*** (pgBackRest restore, timeline 2) | **UNSIGNED** |
| OPS01-08 | RPO/RTO signed acceptance | **BLOCKED-HUMAN** (DR_RUNBOOK.md §1) | **UNSIGNED** |

*BLOCKED-HUMAN = scheduled automation blocked (Railway backup-schedule API not authorized)

---

## Row 1: Offsite Backup

**Machine evidence:** `evidence/ops01-offsite/ops01-row1-offsite-restore.json`
- pg_dump executed, uploaded to S3 bucket `salesos-backups-iwrweogrr`
- Download + SHA256 verification passed
- Disposable restore: 96 tables, companies 141,221 == live
- **Scheduled automation:** BLOCKED-HUMAN (Railway Owner/Admin required)

### PO Signature Required

```
Status:     [ ] VERIFIED    [ ] NOT VERIFIED
Name:       _______________
Title:      Project Owner
Date:       _______________
I confirm:  Evidence reviewed (ops01-row1-offsite-restore.json)
            Backup exists, verified, and downloadable from S3.
_________________________________________________
Signature:  _______________
```

---

## Row 2: WAL Archive

**Machine evidence:** `evidence/ops01-pitr/ops01-row2-wal-archiver.json`
- Primary: `archive_mode=on`
- pgBackRest push wrapper configured
- `archived_count=1240+` (grew from 6 to 1240+ since drill)
- `failed=0`
- Base backup: `20260806-192926F` in bucket `salesos-pitr-w-857q3fjjrr`
- **Managed schedule:** BLOCKED-HUMAN (Railway Owner/Admin required)

### PO Signature Required

```
Status:     [ ] VERIFIED    [ ] NOT VERIFIED
Name:       _______________
Title:      Project Owner
Date:       _______________
I confirm:  Evidence reviewed (ops01-row2-wal-archiver.json)
            WAL archiving active, zero failures, base backup exists.
_________________________________________________
Signature:  _______________
```

---

## Row 3: PITR Restore

**Machine evidence:** `evidence/ops01-pitr/ops01-row3-pitr-restore.json`
- pgBackRest 2.59.0 restore to 19:29:50 UTC
- Timeline promoted to 2
- Exact consistency vs live confirmed
- **Native `volumeInstancePITRRestore`:** BLOCKED-HUMAN

### PO Signature Required

```
Status:     [ ] VERIFIED    [ ] NOT VERIFIED
Name:       _______________
Title:      Project Owner
Date:       _______________
I confirm:  Evidence reviewed (ops01-row3-pitr-restore.json)
            PITR restore drill successful, data consistent.
_________________________________________________
Signature:  _______________
```

---

## Row 8: RPO/RTO Acceptance

**Reference:** DR_RUNBOOK.md §1  
**Status:** UNSIGNED (BLOCKED-HUMAN)

### RPO/RTO Claims

| Dependency | RPO | RTO | Current Capability |
|------------|-----|-----|-------------------|
| PostgreSQL | < 1h | < 4h | pg_dump + WAL archive; manual restore |
| Redis | None (ephemeral) | None | Data reconstructable from Postgres |
| Neo4j | N/A | N/A | Offline per ADR-108 |

### PO Signature Required

```
Status:     [ ] ACCEPTED    [ ] NOT ACCEPTED
Name:       _______________
Title:      Project Owner
Date:       _______________
I confirm:  DR_RUNBOOK.md §1 reviewed
            RPO < 1h (PostgreSQL), RTO < 4h (PostgreSQL) accepted
            Redis: no RPO/RTO obligation (ephemeral cache)
            Neo4j: not in scope (ADR-108, offline v1.0)
_________________________________________________
Signature:  _______________
```

---

## How to Sign

1. Open each Row section above
2. Fill in your name, title, date
3. Check the box (VERIFIED / ACCEPTED)
4. Sign on the Signature line
5. Return to engineering agent for evidence file update

**Or:** Edit the relevant evidence JSON files directly (ops01-row1-offsite-restore.json, etc.) and add `signed_by` + `signed_at` fields.

---

## After All Signatures Complete

1. Update `OPS-01-CHECKLIST.md` rows 1-3 status from `DONE*` to `DONE` (remove asterisk)
2. Update row 8 from `BLOCKED-HUMAN` to `DONE`
3. Update `HUMAN-GATE-CLOSURE-SUMMARY-2026-08-21.md` — OPS-01 rows status
4. Update `FINAL_GO_NOGO_ASSESSMENT.md` — remaining human-blocked items

---

*This document is a signature preparation template. All signatures must be executed by the Project Owner (رغيد المدني) before OPS-01 can be closed.*
