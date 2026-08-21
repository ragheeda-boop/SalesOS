# OPS-01 DR Sign-off Checklist — 2026-08-20

**Status:** OPEN / Human-Gate  
**Classification:** Production Go/No-Go Gate  
**Authority:** DR-RUNBOOK.md + DR-GA-GAPS-CHECKLIST.md + FINAL_GO_NOGO_ASSESSMENT.md

---

## Executive Summary

| Row | Requirement | Machine Drill | Human Sign-off | Status |
|-----|-------------|---------------|----------------|--------|
| 1 | Offsite backup (durable store + retention) | **DONE\*** (`ops01-row1-offsite-restore.json`) | **UNSIGNED** | OPEN |
| 2 | WAL archive (continuous + offsite) | **DONE\*** (`prod-live-wal-archive-reverify-2026-08-07.json`) | **UNSIGNED** | OPEN |
| 3 | PITR restore drill (timestamp evidence) | **DONE\*** (`ops01-row3-pitr-restore.json`) | **UNSIGNED** | OPEN |
| 4 | Staging soak (≥48–72h, `soak_complete_claim`) | Drills done; 72h **failed** (97.6%) | **UNSIGNED** | OPEN |
| 5 | Go-live signatures (CTO + Tech Lead) | N/A | **HUMAN-GO-INK** (2026-08-08) | SIGNED GO ≠ DR CLOSE |
| 6 | Neo4j backup/restore policy | N/A (deferred v2.0) | **NOT APPLICABLE** | ADR-108 |
| 7 | Compose SoT for target env | **DOC FIXED** | N/A | CLOSED |
| 8 | RPO/RTO signed acceptance | N/A | **UNSIGNED** | OPEN |

**Key Distinction:** `DONE*` = machine drill evidenced (JSON exists). **Human CLOSE still required** for all cutover rows. Agent docs cannot forge human sign-off.

---

## Row-by-Row Sign-off Criteria

### Row 1: Offsite Backup
**Evidence:** `ops01-row1-offsite-restore.json` (EAB-003 evidence)
**Drill:** `pg_dump` custom format → S3 (`s3://salesos-backups`) → disposable restore verified
**Human CLOSE requires:**
- [ ] Offsite S3 bucket `salesos-backups` exists in me-south-1
- [ ] Cross-region replication to `salesos-backups-dr` (eu-central-1) enabled
- [ ] Retention policy: 7 days local + 30 days S3 (documented + enforced)
- [ ] Automated schedule: Daily 03:00 UTC (cron or managed)
- [ ] Project Owner signs: "Offsite backup meets RPO < 1h target"

**Blocker:** Automated schedule / retention policy **BLOCKED-HUMAN** (Railway managed backup schedule not enabled)

### Row 2: WAL Archive
**Evidence:** `prod-live-wal-archive-reverify-2026-08-07.json`
**Drill:** `archive_mode=on` + `archive_command='aws s3 cp %p s3://salesos-wal-archives/%f'` on production PostgreSQL
**Human CLOSE requires:**
- [ ] `archive_mode=on` confirmed on production PostgreSQL
- [ ] WAL files continuously streaming to `s3://salesos-wal-archives/`
- [ ] `pg_stat_archiver` shows `failed_count=0` (reverified 2026-08-07)
- [ ] Cross-region replication for WAL bucket enabled
- [ ] Project Owner signs: "WAL archive meets continuous offsite requirement"

**Blocker:** Compose-local `archive_mode` often off (scope ≠ prod); managed schedule **BLOCKED-HUMAN**

### Row 3: PITR Restore Drill
**Evidence:** `ops01-row3-pitr-restore.json`
**Drill:** Point-in-time restore to random timestamp via pgBackRest
**Human CLOSE requires:**
- [ ] PITR restore to arbitrary timestamp within retention window demonstrated
- [ ] Restore time measured: **~5–10 min** (meets RTO < 4h)
- [ ] Native Railway `volumeInstancePITRRestore` UI **not** used (drill-proven pgBackRest path)
- [ ] Project Owner signs: "PITR capability meets RTO target"

**Blocker:** Native Railway PITR UI authorization **BLOCKED-HUMAN**

### Row 4: Staging Soak (48–72h)
**Evidence:** 72h soak attempted 2026-08-10; triage `ae76dae` (97.6% failure = DB outage)
**Human CLOSE requires:**
- [ ] Staging soak ≥48h continuous WITHOUT critical DB outage
- [ ] `soak_complete_claim` explicitly set by TL/DevOps after review
- [ ] Failure triage reviewed and unlock criteria (U1–U5) satisfied
- [ ] Decision runtime smoke PASS throughout soak

**Current state:** Triage DONE, claim **false**, unlock criteria documented but not reviewed.

### Row 5: Go-live Signatures
**Status:** **HUMAN-GO-INK SIGNED** 2026-08-08 (رغيد المدني, dual-role P1)
**Note:** This is a **Product GO decision**, not a DR/soak closure. Prior NO-GO (2026-08-06) preserved.

### Row 6: Neo4j
**Status:** **NOT APPLICABLE** per ADR-108 (ACCEPTED 2026-08-07)
**ADR-108 Decision:** "Keep Neo4j offline in v1.0. Do not activate."
**Deferred to v2.0:** Neo4j activation + DR obligation

### Row 7: Compose Source of Truth
**Status:** **DOC FIXED** — `COMPOSE-SOURCE-OF-TRUTH.md` establishes `salesos/docker-compose.yml` as SoT

### Row 8: RPO/RTO Signed Acceptance
**Target:** RPO < 1h, RTO < 4h (PostgreSQL only — Redis not in prod per R-011)
**Current capability:** Minutes-class (PITR drill) / ~5–10 min (restore)
**Human CLOSE requires:**
- [ ] Project Owner reviews DR_RUNBOOK.md §1 capability table
- [ ] Project Owner signs: "RPO < 1h and RTO < 4h accepted for PostgreSQL"
- [ ] Acceptance covers: current minutes-class capability with pgBackRest path

---

## Required Signatures

| Role | Name | Row 1 | Row 2 | Row 3 | Row 4 | Row 8 | Date |
|------|------|-------|-------|-------|-------|-------|------|
| Project Owner | | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Tech Lead | | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Platform/DevOps Lead | | ☐ | ☐ | ☐ | ☐ | ☐ | |

**Note:** Row 5 (Go-live) already signed by رغيد المدني (2026-08-08). Row 6 = N/A per ADR-108. Row 7 = DOC FIXED.

---

## Pre-Sign-off Validation Checklist

Before collecting signatures, verify:

- [ ] `alembic current` on production == `alembic heads` (g1h2i3j4k5l6) — **CURRENTLY FAILS** (prod at f4aee055fd6e)
- [ ] Schema drift gate passes in CI (new `schema-drift-gate` job in `deploy.yml`)
- [ ] Staging deployed from master (0 commit gap) and `/api/v1/companies` → 200
- [ ] `pg_stat_archiver` on production shows `failed_count=0`
- [ ] S3 buckets `salesos-backups` and `salesos-wal-archives` exist and accessible
- [ ] Cross-region replication to eu-central-1 buckets verified
- [ ] 72h soak triage (`ae76dae`) reviewed by TL/DevOps
- [ ] `soak_complete_claim` explicitly set with rationale

---

## Sign-off Procedure

1. **Reviewer** validates all pre-sign-off checks above
2. **Project Owner** reviews DR_RUNBOOK.md §1 capability table
3. **Project Owner** signs Row 1, 2, 3, 8 (and Row 4 after soak review)
4. **Tech Lead** countersigns Row 1, 2, 3, 4, 8
5. **Platform/DevOps Lead** confirms Row 1–3 automation blockers resolved or accepted
6. **Document** signatures in this file (or linked SIGN_HERE.md)
7. **Update** DR-GA-GAPS-CHECKLIST.md rows 1–4, 8 from `OPEN` → `CLOSED`
8. **Update** FINAL_GO_NOGO_ASSESSMENT.md OPS-01 status

---

## Links to Evidence

| Evidence | Path |
|----------|------|
| Offsite restore drill JSON | EAB-003 `evidence/ops01-row1-offsite-restore.json` |
| WAL archive reverify JSON | EAB-003 `evidence/prod-live-wal-archive-reverify-2026-08-07.json` |
| PITR restore drill JSON | EAB-003 `evidence/ops01-row3-pitr-restore.json` |
| 72h soak triage | `docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-72H-FAILURE-TRIAGE-2026-08-12.md` |
| DR Runbook (capability table) | `docs/ops/DR_RUNBOOK.md` §1 |
| DR-GA-Gaps Checklist | `docs/ops/DR-GA-GAPS-CHECKLIST.md` |
| Final GO/NO-GO Assessment | `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` |
| Human GO Declaration | `docs/audit/ga-engineering-audit/reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md` |
| Sign Here Template | `docs/audit/ga-engineering-audit/SIGN_HERE.md` |

---

## Important Reminders

- **Do NOT claim** DR cutover CLOSED until all human signatures collected
- **Do NOT equate** HUMAN-GO-INK (Row 5) with DR/soak closure (Rows 1–4, 8)
- **Do NOT deny** machine drill facts (DONE*) — they exist; residual is human process
- **Schema drift is a blocker** — production must be at HEAD before any Production GO
- **Staging must be parity** before external pilot (A-09 dependency)

---

*Generated 2026-08-20. Evidence governs. Human ink required.*