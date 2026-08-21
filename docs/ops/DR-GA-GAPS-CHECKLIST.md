# DR / GA Gaps Checklist — REQUIRED before any cutover

**Date:** 2026-08-06 (honesty refresh **2026-08-20** — OPS01-06 reclassified per ADR-108; OPS01-08 scoped to in-scope deps)  
**Finding:** EAB-001-P0-OPS-01  
**Decision:** Cutover gate remains **OPEN / Human-Gate** until human CLOSE ink — even when machine drill JSON exists.  
**Do NOT claim:** DR cutover CLOSED, soak complete, or **evidence-based** production GO from agent docs alone.

> **SUPERSEDED LANGUAGE (EAB-003 block below):** Lines that say offsite/WAL/PITR are absolutely **“NOT done”** or prod `archive_mode` **“Still off”** are **Incorrect-as-current** when read as denial of EAB-003 evidence JSON.  
> **Role split (RC-P0-01):**  
> - **Drill facts** = DONE\* (machine) — see OPS-01 evidence + [GOVERNANCE-LABEL-ALIGNMENT.md](../audit/ga-engineering-audit/completion/GOVERNANCE-LABEL-ALIGNMENT.md)  
> - **This checklist CLOSED?** = still **OPEN** until Project Owner / ops **human CLOSE**  
> Human SIGN_HERE = **GO** (2026-08-08, HUMAN-GO-INK) ≠ this gate CLOSED. See [HUMAN-GO-DECLARATION-2026-08-08.md](../audit/ga-engineering-audit/reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md).

Cross-links:

- [DR_RUNBOOK.md](./DR_RUNBOOK.md) — procedure spine (RPO honesty refreshed 2026-08-12)
- [DR-ROWS-1-3-CLOSE-PACKET.md](./DR-ROWS-1-3-CLOSE-PACKET.md) — **unsigned** Project Owner CLOSE packet (RC-01 Option A) — ink here / there; agents do not forge
- [railway-managed-backup-schedule.md](../audit/ga-engineering-audit/runbooks/railway-managed-backup-schedule.md) — HG-04 managed schedule + native PITR human runbook
- [PROGRESS-WAVE10-DR-GAPS.md](../audit/ga-engineering-audit/PROGRESS-WAVE10-DR-GAPS.md) — local Wave 10 residual
- [go-live-checklist.md](../audit/ga-engineering-audit/runbooks/go-live-checklist.md) — prepare-only
- [SIGN_HERE.md](../audit/ga-engineering-audit/SIGN_HERE.md) — human-declared GO 2026-08-08 (ink ≠ evidence close)
- [COMPOSE-SOURCE-OF-TRUTH.md](./COMPOSE-SOURCE-OF-TRUTH.md) — compose SoT
- [OPS-01-CHECKLIST.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) — machine row table
- [COMPLETION-PROGRAM.md](../audit/ga-engineering-audit/COMPLETION-PROGRAM.md) — living program

**Validation class:** light validated (doc inventory + evidence cross-link). Local drills ≠ staging soak. Machine DONE\* ≠ human CLOSE.

---

## Verdict

| Claim | Status |
|-------|--------|
| DR **cutover gate CLOSED** | **FALSE / OPEN / Human-Gate** |
| Machine offsite + WAL + PITR drill facts (prod path) | **DONE\*** — EAB-003 evidence JSON (automation schedule still BLOCKED-HUMAN) |
| Local backup→disposable restore drills | Partial / historical Wave 10 + EAB re-verify |
| Staging soak 48–72h complete | **OPEN** |
| Go-live signatures (human Decision) | **HUMAN-GO-INK** (SIGNED GO 2026-08-08) — dual-role P1; ≠ soak/DR CLOSE |

---

## Checklist (cutover gate)

Status vocabulary: `OPEN` (gate not human-CLOSED) · `DONE*` (machine drill evidenced; CLOSE still human) · `HUMAN-GO-INK` · `BLOCKED-HUMAN` · `DOC FIXED` · `NOT APPLICABLE` (outside v1.0 scope per ADR-108)

| # | Requirement | Status | Owner | Blocker / notes |
|---|-------------|--------|-------|-----------------|
| 1 | **Offsite backup** — durable off-box store + retention; **human CLOSE** for cutover | **OPEN** (facts **DONE\***) | ops | Drill: `ops01-row1-offsite-restore.json`. Automated schedule / retention policy CLOSE = **BLOCKED-HUMAN**. Do not deny drill facts. |
| 2 | **WAL archive** — continuous archive offsite; **human CLOSE** | **OPEN** (facts **DONE\***) | ops | Prod evidence: `archive_mode=on` + `prod-live-wal-archive-reverify-2026-08-07.json`. Compose-local often **off** (scope ≠ prod). Managed schedule = **BLOCKED-HUMAN**. |
| 3 | **PITR restore drill** — timestamp restore evidence; **human CLOSE** | **OPEN** (facts **DONE\***) | ops | Drill: `ops01-row3-pitr-restore.json`. Native `volumeInstancePITRRestore` UI = **BLOCKED-HUMAN**. |
| 4 | **Staging soak** — ≥48–72h staging with `soak_complete_claim` | **OPEN / HUMAN** | ops | Loops ≠ complete; see SOAK-GATE-CHECKLIST + HUMAN-GATE-CARD |
| 5 | **Go-live signatures** — CTO + Tech Lead on SIGN_HERE | **HUMAN-GO-INK** | leadership | SIGNED GO 2026-08-08 (رغيد المدني; dual-role P1). Prior NO-GO 2026-08-06 preserved. Ink ≠ soak/DR CLOSE. |
| 6 | **Neo4j backup/restore policy** for staging/prod (not only local dump drill) | **NOT APPLICABLE** | ops | **Reclassified per ADR-108** (ACCEPTED 2026-08-07): "Keep Neo4j offline in v1.0. Do not activate." Neo4j is not a production dependency; DR obligation deferred to v2.0. See OPS-01-CHECKLIST.md + NEO4J_GOVERNANCE_GAP.md. |
| 7 | **Compose SoT used for target env** — no accidental root-compose cutover | **DOC FIXED** (ops honesty) | ops | See COMPOSE-SOURCE-OF-TRUTH.md; merge of dual compose still deferred |
| 8 | **RPO/RTO signed acceptance** vs current capability | **OPEN / HUMAN** | Project Owner | In-scope dependencies: PostgreSQL (primary) + Redis (ephemeral, no persistence obligation). Redis deployed per live `/health` endpoint. RPO < 1h target, current capability minutes-class (EAB-003 evidence). SIGN_HERE RPO item may remain UNSIGNED. See DR_RUNBOOK.md §1. |

---

## Explicit deferral (this wave)

Infrastructure to close #1–#5 is **out of scope** for EAB Stream D (docs/honesty). Disposition for **EAB-001-P0-OPS-01**:

- **Deferred** with DEC/checklist artifact (this file)
- Residual human blockers: offsite store provisioning, WAL enablement + PITR drill, staging access/soak, leadership signatures
- Full infra = **not** claimed complete

---

## EAB-2026-08-06-002 post-verify (docs only) — HISTORICAL SNAPSHOT

| Item | Status (as of 2026-08-06 post-verify; **superseded for facts by EAB-003 evidence**) |
|------|--------|
| Checklist rows 1–5 re-reviewed | Then OPEN / HUMAN / UNSIGNED |
| Offsite / WAL / PITR / staging soak | Then claimed NOT done — **Incorrect-as-current** if used to deny later DONE\* JSON |
| This file + DR_RUNBOOK cross-links | Progress = inventory honesty only |
| Production cutover | **Still blocked** (launch blocker) — unchanged |

Board packaging: [../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-002/REMEDIATION-POST-VERIFY.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-002/REMEDIATION-POST-VERIFY.md).

---

## EAB-2026-08-06-003 OPS-01 advancement (in-repo) — honesty refresh 2026-08-08

| Item | Status |
|------|--------|
| Rows 1–3 **cutover CLOSE** | Still **OPEN / Human-Gate** (await human CLOSE) |
| Rows 1–3 **machine drill facts** | **DONE\*** — see OPS-01 evidence JSON (not denied) |
| Row 4 soak | **OPEN** |
| Row 5 signatures | **HUMAN-GO-INK** (SIGNED GO 2026-08-08) — ≠ evidence CLOSE of soak/DR |
| Row 7 Compose SoT | **DOC FIXED** (unchanged) |
| Local `pg_dump` → disposable restore | Re-verified historically — does **not** alone CLOSE cutover |
| Primary `archive_mode` (**prod**) | Evidence **on** (`prod-live-wal-archive-reverify-2026-08-07.json`) |
| Primary `archive_mode` (**compose-local**) | Often **off** — do not conflate with prod |
| Automation schedule / native PITR UI | **BLOCKED-HUMAN** |
| Status pack | [OPS-01-ADVANCEMENT.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md) |
| Evidence-based Production GO / cutover | **Still blocked** until human accepts gates + evidence |

See also: [GOVERNANCE-LABEL-ALIGNMENT.md](../audit/ga-engineering-audit/completion/GOVERNANCE-LABEL-ALIGNMENT.md) · [HUMAN-GATE-CARD.md](../audit/ga-engineering-audit/completion/HUMAN-GATE-CARD.md)

---

## Related DEC stub

| Field | Value |
|-------|--------|
| ID | DEC-OPS-DR-GA-GAPS (informal companion to EAB-001-P0-OPS-01) |
| Decision | Refuse any **evidence-based** Production GO / cutover claim until checklist rows 1–4 CLOSED with evidence links + human CLOSE; row 5 human Decision is separate (HUMAN-GO-INK may exist while residuals remain) |
| Alternatives rejected | Treating Wave 10 local drills as production DR CLOSE; claiming PITR from docs alone; equating SIGN_HERE GO ink with soak/DR evidence CLOSE |
