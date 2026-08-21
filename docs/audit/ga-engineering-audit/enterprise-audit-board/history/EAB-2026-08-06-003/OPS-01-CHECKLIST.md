# OPS-01 Checklist — machine-readable table

**Finding:** EAB-001-P0-OPS-01  
**Run:** EAB-2026-08-06-003  
**Updated:** 2026-08-20 (governance reconciliation — OPS01-06 N/A, OPS01-08 scoped to in-scope deps)  
**Disposition:** Deferred (launch blocker — soak/residual evidence still OPEN; OPS01-06 reclassified per ADR-108)  
**Authority narrative:** [OPS-01-ADVANCEMENT.md](./OPS-01-ADVANCEMENT.md) · [DR-GA-GAPS-CHECKLIST.md](../../../../../ops/DR-GA-GAPS-CHECKLIST.md) · [HUMAN-GO-DECLARATION-2026-08-08.md](../../../reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md)

Status vocabulary: `DONE` | `PARTIAL` | `OPEN` | `BLOCKED-HUMAN` | `UNSIGNED` | `HUMAN-GO-INK`

| id | requirement | status | launch_blocker | owner | evidence |
|----|-------------|--------|----------------|-------|----------|
| OPS01-01 | Offsite backup to durable off-box store + retention | DONE* | yes | ops | evidence/ops01-offsite/ops01-row1-offsite-restore.json + .md (pg_dump→S3 `salesos-backups-iwrweogrr`, upload/download SHA256 verified, disposable restore=96 tables, companies 141221==live). \*Scheduled automation BLOCKED-HUMAN (Railway backup-schedule API Not Authorized) |
| OPS01-02 | WAL archive on primary (or managed equivalent) to offsite | DONE* | yes | ops | evidence/ops01-pitr/ops01-row2-wal-archiver.json + .md (primary archive_mode=on, pgBackRest push wrapper, archived_count=6/failed=0, base 20260806-192926F → bucket `salesos-pitr-w-857q3fjjrr`). \*Managed schedule BLOCKED-HUMAN |
| OPS01-03 | PITR restore to named timestamp with evidence | DONE* | yes | ops | evidence/ops01-pitr/ops01-row3-pitr-restore.json + .md (pgBackRest 2.59.0 restore to 19:29:50 UTC from managed archive, promote timeline 2, exact consistency vs live). \*Native `volumeInstancePITRRestore` BLOCKED-HUMAN |
| OPS01-04 | Staging soak 48–72h (staging parity, not local-only) | OPEN | yes | ops | PROGRESS-WAVE11-SOAK*.md; soak_complete_claim=false; PROGRESS-WAVE12-STAGING.md; 2026-08-06 verified Railway staging exists but NOT parity (409 commits behind, empty DB, DEBUG=true, no CI wiring, shared JWT/SECRET_KEY) — see STAGING-VERIFICATION.md + SOAK-READINESS.md + OPS01-ROW4-STATUS.md; parity fixes require human approval, then ≥48h soak |
| OPS01-05 | Go-live signatures Project Owner | HUMAN-GO-INK | yes | leadership | SIGN_HERE.md — CTO+TL **SIGNED GO** 2026-08-08 (رغيد المدني; dual-role same person = P1); prior NO-GO 2026-08-06 preserved; **human-declared GO** ≠ evidence close of OPS01-04; [HUMAN-GO-DECLARATION-2026-08-08.md](../../../reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md); GO-LIVE-SIGNATURE-PACKET.md |
| OPS01-06 | Neo4j staging/prod backup-restore policy | NOT APPLICABLE | no | ops | **Reclassified per ADR-108** (2026-08-07, ACCEPTED): "Keep Neo4j offline in v1.0. Do not activate." Neo4j has no production dependency obligation. Local neo4j-admin dump/load drills remain as development convenience. Neo4j DR obligation deferred to v2.0 per ADR-108 §What moves to v2.0. **Governance gap note:** Railway `neo4j-prod` service exists with `graph=connected` — deployment artifact, not production data path (no traffic flows through Neo4j; Activity Intelligence uses PG; Company 360 is optional; Graph API has SQL fallback). See NEO4J_GOVERNANCE_GAP.md. |
| OPS01-07 | Compose SoT for target env (no root cutover) | DONE | no | ops | docs/ops/COMPOSE-SOURCE-OF-TRUTH.md |
| OPS01-08 | RPO/RTO signed acceptance vs capability | BLOCKED-HUMAN | related | Project Owner | DR_RUNBOOK.md §1; SIGN_HERE RPO item UNSIGNED |
| OPS01-LOCAL-PG | Local pg_dump → disposable restore | DONE | no | eng | evidence/ops01-local-backup-20260806.json; PROGRESS-WAVE10-BACKUP.md |

## Counts

| Scope | DONE | PARTIAL | OPEN | BLOCKED-HUMAN | NOT APPLICABLE | HUMAN-GO-INK / other |
|-------|-----:|--------:|-----:|--------------:|---------------:|----------------------:|
| Rows OPS01-01…08 | 4 | 0 | 1 | 1 | 1 (OPS01-06) | 1* (OPS01-05 HUMAN-GO-INK) |
| Launch blockers (01–05) | 3 | 0 | 1 (OPS01-04) | 0 | 0 | 1* (OPS01-05 HUMAN-GO-INK) |

\*OPS01-05 = human GO ink on SIGN_HERE (2026-08-08); **not** engineering DONE — OPS01-04 soak still OPEN. Vocabulary extended: `HUMAN-GO-INK` = human Decision=GO recorded; evidence residuals remain.

## Close rule

All of `OPS01-01`…`OPS01-05` must be `DONE` with linked executable evidence **and** human signatures where required before any **evidence-based** Production GO / cutover claim. `HUMAN-GO-INK` on OPS01-05 records human Decision=GO on SIGN_HERE but does **not** by itself close OPS01-04 or invent soak/DR. Local `OPS01-LOCAL-PG` alone never closes the finding. `NOT APPLICABLE` (OPS01-06) means the requirement is outside v1.0 production scope per ADR-108 — no obligation to close.
