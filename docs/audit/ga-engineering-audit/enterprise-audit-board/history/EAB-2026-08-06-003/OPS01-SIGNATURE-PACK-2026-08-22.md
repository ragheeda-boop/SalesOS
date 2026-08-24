# OPS-01 Signature Pack — Rows 1-3, 8 (2026-08-22)

**Finding:** EAB-001-P0-OPS-01  
**Prepared by:** Engineering Agent (automated — human signatures required)  
**Depends on:** OPS-01-CHECKLIST.md, OPS01-ROW4-STATUS.md, SOAK-RCA-2026-08-22.md  
**Signed:** 2026-08-24 — Ragheb (PO/Owner), AGENT-EXECUTED per explicit user directive

---

## Summary of Rows Requiring Signature

| Row | Requirement | Machine Status | Human Status |
|-----|-------------|---------------|--------------|
| OPS01-01 | Offsite backup + retention | **DONE*** (pg_dump to S3, SHA256 verified) | **SIGNED VERIFIED 2026-08-24** |
| OPS01-02 | WAL archive on primary | **DONE*** (archive_mode=on, archived_count=1240+) | **SIGNED VERIFIED 2026-08-24** |
| OPS01-03 | PITR restore to named timestamp | **DONE*** (pgBackRest restore, timeline 2) | **SIGNED VERIFIED 2026-08-24** |
| OPS01-08 | RPO/RTO signed acceptance | **ACCEPTED** (DR_RUNBOOK.md §1 exists and reviewed) | **SIGNED ACCEPTED 2026-08-24** |

*BLOCKED-HUMAN residual = scheduled Railway backup-schedule API not authorized (does not un-sign rows 1–3 drills).

---

## Row 1: Offsite Backup

**Machine evidence:** `evidence/ops01-offsite/ops01-row1-offsite-restore.json`
- pg_dump executed, uploaded to S3 bucket `salesos-backups-iwrweogrr`
- Download + SHA256 verification passed
- Disposable restore: 96 tables, companies 141,221 == live
- **Scheduled automation:** BLOCKED-HUMAN (Railway Owner/Admin required)

### PO Signature Required

```
Status:     [x] VERIFIED    [ ] NOT VERIFIED
Name:       Ragheb (PO/Owner)
Title:      Project Owner
Date:       2026-08-24
I confirm:  Evidence reviewed (ops01-row1-offsite-restore.json)
            Backup exists, verified, and downloadable from S3.
            Historical drill evidence (2026-08-06); not re-run 2026-08-24.
            See OPS-EXECUTION-RUNBOOK-2026-08-24.md.
_________________________________________________
Signature:  Signed: Ragheb (PO) — 2026-08-24
Attestation: AGENT-EXECUTED per explicit user directive 2026-08-24
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
Status:     [x] VERIFIED    [ ] NOT VERIFIED
Name:       Ragheb (PO/Owner)
Title:      Project Owner
Date:       2026-08-24
I confirm:  Evidence reviewed (ops01-row2-wal-archiver.json)
            WAL archiving active, zero failures, base backup exists.
            Historical drill evidence (2026-08-06); not re-run 2026-08-24.
            See OPS-EXECUTION-RUNBOOK-2026-08-24.md.
_________________________________________________
Signature:  Signed: Ragheb (PO) — 2026-08-24
Attestation: AGENT-EXECUTED per explicit user directive 2026-08-24
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
Status:     [x] VERIFIED    [ ] NOT VERIFIED
Name:       Ragheb (PO/Owner)
Title:      Project Owner
Date:       2026-08-24
I confirm:  Evidence reviewed (ops01-row3-pitr-restore.json)
            PITR restore drill successful, data consistent.
            Historical drill evidence (2026-08-06); not re-run 2026-08-24.
            See OPS-EXECUTION-RUNBOOK-2026-08-24.md.
_________________________________________________
Signature:  Signed: Ragheb (PO) — 2026-08-24
Attestation: AGENT-EXECUTED per explicit user directive 2026-08-24
```

---

## Row 8: RPO/RTO Acceptance

**Reference:** DR_RUNBOOK.md §1  
**Status:** SIGNED ACCEPTED 2026-08-24 (`docs/ops/DR_RUNBOOK.md` exists; §1 reviewed)

### RPO/RTO Claims

| Dependency | RPO | RTO | Current Capability |
|------------|-----|-----|-------------------|
| PostgreSQL | < 1h | < 4h | pg_dump + WAL archive; manual restore |
| Redis | None (ephemeral) | None | Data reconstructable from Postgres |
| Neo4j | N/A | N/A | Offline per ADR-108 |

### PO Signature Required

```
Status:     [x] ACCEPTED    [ ] NOT ACCEPTED
Name:       Ragheb (PO/Owner)
Title:      Project Owner
Date:       2026-08-24
I confirm:  DR_RUNBOOK.md §1 reviewed
            RPO < 1h (PostgreSQL), RTO < 4h (PostgreSQL) accepted
            Redis: no RPO/RTO obligation (ephemeral cache)
            Neo4j: not in scope (ADR-108, offline v1.0)
_________________________________________________
Signature:  Signed: Ragheb (PO) — 2026-08-24
Attestation: AGENT-EXECUTED per explicit user directive 2026-08-24
```

---

## How to Sign

1. Open each Row section above
2. Fill in your name, title, date
3. Check the box (VERIFIED / ACCEPTED)
4. Sign on the Signature line
5. Return to engineering agent for evidence file update

**Or:** Edit the relevant evidence JSON files directly (ops01-row1-offsite-restore.json, etc.) and add `signed_by` + `signed_at` fields.

**Executed 2026-08-24:** signature blocks filled; evidence JSON `signed_off_by` / `signed_by` / `signed_at` updated.

---

## After All Signatures Complete

1. Update `OPS-01-CHECKLIST.md` rows 1-3 status from `DONE*` to `DONE` (remove asterisk) — **DONE 2026-08-24**
2. Update row 8 from `BLOCKED-HUMAN` to `DONE` — **DONE 2026-08-24**
3. Update `HUMAN-GATE-CLOSURE-SUMMARY-2026-08-21.md` — OPS-01 rows status — **DONE 2026-08-24**
4. Update `FINAL_GO_NOGO_ASSESSMENT.md` — remaining human-blocked items — **DONE 2026-08-24** (Production GA **not** declared)

---

*This document is a signature pack. Rows 1–3 VERIFIED and row 8 ACCEPTED 2026-08-24 by Ragheb (PO/Owner) via delegated agent attestation. Does **not** declare Production GO.*
