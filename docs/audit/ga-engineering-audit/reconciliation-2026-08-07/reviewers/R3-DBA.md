# R3 — DBA | Enterprise Reconciliation Audit

## Role / Date

**Role:** DBA (Alembic, migration risk, OPS-01 Rows 1–3 backup/WAL/PITR, Neo4j data durability)  
**Date:** 2026-08-07  
**Mode:** READ ONLY — governance claims vs executable evidence  
**Did not modify:** GA_STATUS, SIGN_HERE, OPS checklists, run reports, history  
**Validation:** light validated (no live SQL/`alembic` this review)

---

## Claims examined (quote + path)

| ID | Quote / claim | Path |
|----|---------------|------|
| B1 | “Backup DR — offsite + WAL + PITR **DONE 2026-08-06** (… pg_dump→S3 … pgBackRest … PITR restore-to-timestamp…)” | `GA_STATUS.md` #7 |
| B2 | “OPS01-01 … DONE\*”; “OPS01-02 … DONE\*”; “OPS01-03 … DONE\*” | `OPS-01-CHECKLIST.md` |
| B3 | “Production WAL archive + PITR restore proven \| **OPEN**”; “Offsite … \| **OPEN**” | `DR-GA-GAPS-CHECKLIST.md` |
| B4 | “Offsite / WAL / PITR / staging soak \| **NOT done** — do not claim”; “Primary `archive_mode` \| Still **off**” | `DR-GA-GAPS-CHECKLIST.md` EAB-003 block |
| B5 | “offsite S3/MinIO **OPEN**; primary `archive_mode=off`” | `SIGN_HERE.md` #7 |
| B6 | “rows 1–5 **OPEN**”; “Local drills ≠ offsite / WAL / staging soak” | `DR_RUNBOOK.md` banner |
| B7 | “no WAL/offsite/staging soak this run”; Still Deferred | `EAB-2026-08-06-003/FINDINGS-RECHECK.md` (OPS-01) |
| B8 | “rows 1–5 still OPEN” (OPS-01 Deferred) | `REMEDIATION-PROGRAM-STATUS.md` |
| B9 | “`alembic_version` \| `d1a8c35e7f09`”; companies 141,221 | `PRODUCTION-VERIFICATION.md`; offsite/PITR JSON |
| B10 | “Muhide prod: … Alembic **0051**” | `GA_STATUS.md` |
| B11 | “Alembic head **0040**” | `SIGN_HERE.md` B16 / TL notes |
| B12 | Range `d1a8c35e7f09` → `e5f9a32b0c08`; “Migrations executed: **NONE**”; “**REQUIRES MAINTENANCE WINDOW**” | `PROD-MIGRATION-RISK.md` |
| B13 | “Measured window … **~60.6 s** … dress rehearsal”; “PREPARED — NOT EXECUTED” | `PRODUCTION-CUTOVER-PACKAGE.md` |
| B14 | Downtime estimate “**5–45+ minutes**” | `PROD-MIGRATION-RISK.md` §4 |
| B15 | “Prod Neo4j repaired … `graph=connected`”; “**no persistent volume**” | `ROOTCAUSE-NEO4J.md`; `OPS01-ROW4-STATUS.md` |
| B16 | “`graph\":\"unavailable\"`”; Neo4j OFFLINE | `PRODUCTION-VERIFICATION.md`; `GA_STATUS.md` #10 |
| B17 | “OPS01-06 Neo4j … PARTIAL … prod policy OPEN” | `OPS-01-CHECKLIST.md` |
| B18 | Production GA **NO-GO** | Multiple; cutover/risk packages |
| B19 | “READY with conditions — NOT GO”; Progress ~**96%** | `OPS01-ROW4-STATUS.md` |
| B20 | Local restore `closes_ops01_rows_1_to_5: false` / local archive off | `ops01-local-backup-20260806.json` (via advancement narrative) |

---

## Evidence found / NOT VERIFIED

| Artifact | Present? | Key facts |
|----------|:--------:|-----------|
| `evidence/ops01-offsite/ops01-row1-offsite-restore.json` | Yes | Dump size/SHA; restore exit 0; alembic `d1a8c35e7f09`; companies 141221 |
| `evidence/ops01-offsite/ops01-row1-evidence.md` | Yes | Object key `2026/08/salesos_prod_20260806.dump`; schedule human |
| `evidence/ops01-pitr/ops01-row2-wal-archiver.json` | Yes | archive_mode on; failed_count 0; base `20260806-192926F` |
| `evidence/ops01-pitr/ops01-row3-pitr-restore.json` | Yes | restore exit 0; promote timeline 2; consistency vs live |
| `evidence/ops01-staging/migration-dress-rehearsal.json` | Yes | Scratch CLEAN PASS ~60.6s → tip `e5f9a32b0c08` |
| `evidence/ops01-staging/prod-index-probe.json` | Yes | Prod alembic `d1a8c35e7f09`; 0/37 target indexes |
| Post-repair prod `/health` JSON (`graph=connected`) under evidence/ | **No** | Connected claim **NOT VERIFIED** as durable artifact |
| Prod migration execution log for 15 revisions | **No** | `PROD-MIGRATION-RISK`: migrations **NONE** — consistent |
| Human checklist CLOSED + `signed_off_by` for rows 1–3 | **No** | DONE\* without ink |

---

## Contradictions only (Claim A vs Claim B, P0/P1/P2/P3)

### P0

| ID | Claim A | Claim B |
|----|---------|---------|
| **DB-P0-1** | `GA_STATUS` #7 + OPS-01: Rows 1–3 **DONE** / DONE\* | `DR-GA-GAPS-CHECKLIST` rows 1–3 **OPEN**; EAB-003 “**NOT done**”; `SIGN_HERE` / `DR_RUNBOOK` / PROGRAM-STATUS / FINDINGS-RECHECK still OPEN/Deferred |
| **DB-P0-2** | Checklist EAB-003: `archive_mode` **Still off**; offsite **NOT done** | Linked OPS-01 evidence: production WAL on + offsite restore proven |
| **DB-P0-3** | DR row 1 requires **automated** offsite + retention; row 3 native managed PITR | Status **DONE\*** with schedule / `volumeInstancePITRRestore` **BLOCKED-HUMAN** and empty sign-off — “manual proven” ≠ “requirement CLOSED” |

### P1

| ID | Claim A | Claim B |
|----|---------|---------|
| **DB-P1-1** | Neo4j repaired / `graph=connected` (`ROOTCAUSE`, ROW4) | Neo4j OFFLINE / `graph=unavailable` (`PRODUCTION-VERIFICATION`, `GA_STATUS` #10); post-repair health JSON **NOT VERIFIED**; no volume + OPS01-06 OPEN |
| **DB-P1-2** | Prod Alembic **0051** (`GA_STATUS`); head **0040** (`SIGN_HERE`) | Evidence/probe/risk: **`d1a8c35e7f09`** current, tip **`e5f9a32b0c08`** |
| **DB-P1-3** | “READY with conditions” / ~**96%** (`OPS01-ROW4`) | Audit **production no-go** / Readiness **38** (and EAB ~53) — vocabulary conflict |
| **DB-P1-4** | EAB FINDINGS/CEO: OPS-01 as no WAL/offsite this run | OPS-01 machine table DONE\* with JSON on same EAB-003 tree |

### P2

| ID | Claim A | Claim B |
|----|---------|---------|
| **DB-P2-1** | Risk doc downtime **5–45+ min**, validation **not validated** | Dress rehearsal ~**60.6 s** / a4f7 ≈20 s measured — estimate SoT drift |
| **DB-P2-2** | Advancement object path `2026/08/06/…` | Evidence path `2026/08/…` |
| **DB-P2-3** | `STAGING-VERIFICATION` staging alembic `b7e2f65a3f07` (2026-08-06) | Later ROW4/DIFF: staging `e5f9a32b0c08` without supersession banner |
| **DB-P2-4** | PITR JSON size fields labeled inconsistently (MB vs bytes naming) | Metadata-only inconsistency |

### P3

| ID | Claim A | Claim B |
|----|---------|---------|
| **DB-P3-1** | Offsite restore ~96 public tables | Local restore ~134 tables — env difference; mis-citation risk |
| **DB-P3-2** | Wave10 DR gaps still OPEN (local) | GA_STATUS DONE (prod path) — scope confusion if unlabeled |

---

## Topic → candidate authoritative source

| Topic | Candidate SoT | Deprioritize |
|-------|---------------|--------------|
| Offsite/WAL/PITR **facts** | `evidence/ops01-offsite/*`, `evidence/ops01-pitr/*` | Wave10 local alone |
| Offsite/WAL/PITR **cutover CLOSED?** | `DR-GA-GAPS-CHECKLIST.md` + ink | `GA_STATUS` DONE; OPS DONE\* until gate updated |
| Prod Alembic current | `prod-index-probe.json` / restore JSON / PRODUCTION-VERIFICATION → `d1a8c35e7f09` | `0051`, `0040` |
| Migration risk class | `PROD-MIGRATION-RISK.md` (**REQUIRES MAINTENANCE WINDOW**) | Treating rehearsal as prod executed |
| Measured migrate timing | `migration-dress-rehearsal.json` + cutover package | Unupdated 45+ min as sole estimate |
| Neo4j availability | Dated `/health` evidence artifact | Stale OFFLINE vs unreplicated “connected” |
| Neo4j DR | OPS01-06 + ROOTCAUSE residual (no volume) | “repaired” alone |
| Production GA | `SIGN_HERE` + audit **production no-go** | READY/~96% |

---

## Summary counts by severity

| Severity | Count |
|----------|------:|
| P0 | 3 |
| P1 | 4 |
| P2 | 4 |
| P3 | 2 |
| **Total contradictions** | **13** |

**Production NO-GO:** **Agreed.**  
**GA_STATUS DONE vs DR OPEN:** **CRITICAL (DB-P0-1).**  
**Evidence JSON for rows 1–3:** present and supportive of **manual** drills — contradiction is governance CLOSED vs OPEN, not missing JSON.

---

*R3-DBA — reconciliation-2026-08-07 — contradictions only*
