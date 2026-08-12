# DR Rows 1–3 Close Packet — Project Owner Ink (RC-01 Option A)

**Packet ID:** DR-ROWS-1-3-CLOSE-PACKET  
**Date prepared:** 2026-08-12 (agent-authored packet — **no human CLOSE ink**)  
**Finding:** EAB-001-P0-OPS-01  
**Authority:** [CTO-REQUIRED-HUMAN-DECISIONS.md](../audit/ga-engineering-audit/CTO-REQUIRED-HUMAN-DECISIONS.md) **RC-01** (Option A recommended) · **RC-04** (managed backup / native PITR residual)  
**Cutover gate SoT:** [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md)  
**Machine row table:** [OPS-01-CHECKLIST.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md)  
**Evidence root:** `docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/`

> **Principle:** AI assists. Humans decide. Evidence governs.  
> Agents **must not** forge Name / Date / Decision CLOSE. This packet is blank ink until a Project Owner signs.  
> **Do NOT claim:** Production GO, cutover CLOSED, or “DR fully closed” from this file alone.

---

## Residual banner (mandatory — read before ink)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  RESIDUAL — BLOCKED-HUMAN / Not Authorized                                   ║
║                                                                              ║
║  Railway managed backup schedule                                             ║
║    mutations: volumeInstanceBackupScheduleUpdate / List                      ║
║    status: Not Authorized (plan/permission gating) → BLOCKED-HUMAN           ║
║                                                                              ║
║  Railway native PITR restore                                                 ║
║    mutation: volumeInstancePITRRestore                                       ║
║    status: Not Authorized (plan/permission gating) → BLOCKED-HUMAN           ║
║                                                                              ║
║  RC-01 Option A CLOSE = drill facts accepted with this residual labeled.     ║
║  RC-04 remains open for schedule enablement + native PITR + RPO/RTO ink.     ║
║  Agents cannot authorize Railway account scopes (see HG-04 runbook).         ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

Human follow-up runbook: [railway-managed-backup-schedule.md](../audit/ga-engineering-audit/runbooks/railway-managed-backup-schedule.md) (HG-04).

---

## RC-01 Option A — what this packet does / does not do

| Claim | Status after this packet (unsigned) | After human CLOSE ink |
|-------|-------------------------------------|------------------------|
| Rows 1–3 **machine drill facts** | **DONE\*** (already evidenced) | Still **DONE\*** |
| Rows 1–3 **cutover CLOSE** on [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md) | **OPEN / Human-Gate** | Human may mark **CLOSED with residuals** |
| Managed schedule + native `volumeInstancePITRRestore` | **BLOCKED-HUMAN** | Remains **BLOCKED-HUMAN** until HG-04 done |
| Production GO / evidence-based cutover | **NO-GO / blocked** | Still **not** invented by this packet — other gates (soak, etc.) apply |

**Option A meaning (CTO register):** CLOSE checklist rows 1–3 as *drill facts done*, with explicit residual banner for the not-yet-authorized native PITR / schedule path (RC-04). Human CLOSE is authoritative; agents recommend only.

---

## Machine facts — Rows 1–3 DONE\* (evidence links)

Base path (relative to repo root):

`docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/`

### Row 1 — Offsite backup + restore (OPS01-01) — DONE\*

| Field | Value |
|-------|--------|
| Status | **DONE\*** — scheduled automation **BLOCKED-HUMAN** |
| Store | Railway Bucket `salesos-backups` → physical `salesos-backups-iwrweogrr` (region `sjc`) |
| Proven | pg_dump → S3 upload/download SHA-256 match; disposable restore 96 tables; companies 141221 == live; alembic `d1a8c35e7f09` |
| Evidence | [ops01-offsite/ops01-row1-offsite-restore.json](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/ops01-row1-offsite-restore.json) · [ops01-row1-evidence.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/ops01-row1-evidence.md) |
| Residual | `volumeInstanceBackupScheduleUpdate` / `volumeInstanceBackupScheduleList` → **Not Authorized** |

### Row 2 — WAL archive offsite (OPS01-02) — DONE\*

| Field | Value |
|-------|--------|
| Status | **DONE\*** — managed schedule **BLOCKED-HUMAN** |
| Archive | Primary `archive_mode=on`; pgBackRest → bucket `salesos-pitr-w-857q3fjjrr`; base `20260806-192926F`; `failed_count=0` |
| Reverify | Live prod `archive_mode=on`, archived_count growth, failed=0 (2026-08-07) |
| Evidence | [ops01-pitr/ops01-row2-wal-archiver.json](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row2-wal-archiver.json) · [ops01-row2-evidence.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row2-evidence.md) · [prod-live-wal-archive-reverify-2026-08-07.json](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/prod-live-wal-archive-reverify-2026-08-07.json) |
| Residual | Managed base-backup cadence still human |

### Row 3 — PITR restore to timestamp (OPS01-03) — DONE\*

| Field | Value |
|-------|--------|
| Status | **DONE\*** — native Railway PITR UI **BLOCKED-HUMAN** |
| Proven | pgBackRest 2.59.0 restore to `2026-08-06 19:29:50 UTC`, promote timeline 2, exact consistency vs live |
| Evidence | [ops01-pitr/ops01-row3-pitr-restore.json](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row3-pitr-restore.json) · [ops01-row3-evidence.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row3-evidence.md) |
| Residual | `volumeInstancePITRRestore` → **Not Authorized** (fallback = same managed archive via pgBackRest) |

Cross-check machine table: [OPS-01-CHECKLIST.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) rows OPS01-01…03.

---

## Gate status (honest)

| Gate | Status |
|------|--------|
| DR cutover gate ([DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md)) | **OPEN** until human signs CLOSE below |
| Rows 1–3 machine facts | **DONE\*** |
| HG-04 Railway schedule / native PITR | **BLOCKED-HUMAN** |
| RC-04 RPO/RTO + managed backup acceptance | Awaiting human decision (separate ink on CTO register) |
| Production GO | **Not claimed** by this packet |

---

## Project Owner ink — RC-01 Option A

**Decision (choose one):**

- [ ] **CLOSE** — Accept Rows 1–3 as drill facts **DONE\***; update DR-GA-GAPS checklist rows 1–3 to human CLOSE **with residuals** (banner above remains true until HG-04 closes).
- [ ] **DEFER** — Leave cutover rows 1–3 OPEN; do not treat DONE\* as checklist CLOSE until further evidence / Option B reconsideration.

**Residual acceptance (required if Decision = CLOSE):**

- [ ] I accept that Railway **managed backup schedule** (`volumeInstanceBackupScheduleUpdate` / `List`) remains **BLOCKED-HUMAN / Not Authorized** and is **not** closed by this ink.
- [ ] I accept that native **`volumeInstancePITRRestore`** remains **BLOCKED-HUMAN / Not Authorized** and is tracked under **RC-04** / HG-04 — not “fully closed DR automation.”
- [ ] I understand CLOSE here ≠ Production GO and ≠ soak (OPS01-04) CLOSE.
- [ ] I have reviewed the evidence JSON/MD links for rows 1–3 above.

| Field | Ink (human only — leave blank until signed) |
|-------|-----------------------------------------------|
| Name | ________________________________ |
| Role | Project Owner / Ops owner |
| Date (UTC) | ________________________________ |
| Decision | □ CLOSE □ DEFER |
| Signature / initials | ________________________________ |

**Agent attestation:** This section was left **unsigned** at packet create time. No CLOSE or Production GO was invented.

---

## Post-ink checklist (human / ops, after CLOSE)

1. Update [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md) rows 1–3 status to reflect human CLOSE **with residual banner** (do not erase BLOCKED-HUMAN automation).
2. Align narrative on [OPS-01-CHECKLIST.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) / SIGN_HERE language to Partial / DONE-with-residuals (human authoritative).
3. Record RC-01 decision on [CTO-REQUIRED-HUMAN-DECISIONS.md](../audit/ga-engineering-audit/CTO-REQUIRED-HUMAN-DECISIONS.md) (Approve / Reject / Defer checkboxes — human only).
4. Execute or schedule HG-04: [railway-managed-backup-schedule.md](../audit/ga-engineering-audit/runbooks/railway-managed-backup-schedule.md).
5. Do **not** flip Production GO from this packet alone.

---

## Cross-links

| Doc | Role |
|-----|------|
| [DR-GA-GAPS-CHECKLIST.md](./DR-GA-GAPS-CHECKLIST.md) | Cutover gate — remains OPEN until CLOSE ink |
| [OPS-01-CHECKLIST.md](../audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) | Machine DONE\* rows 1–3 |
| [CTO-REQUIRED-HUMAN-DECISIONS.md](../audit/ga-engineering-audit/CTO-REQUIRED-HUMAN-DECISIONS.md) **RC-01** | Option A disposition register |
| [CTO-REQUIRED-HUMAN-DECISIONS.md](../audit/ga-engineering-audit/CTO-REQUIRED-HUMAN-DECISIONS.md) **RC-04** | RPO/RTO + managed backup / native PITR residual |
| [HUMAN-GATE-CARD.md](../audit/ga-engineering-audit/completion/HUMAN-GATE-CARD.md) HG-03 / HG-04 | Human gate cards |
| [ops01-human-execution-pack.md](../audit/ga-engineering-audit/runbooks/ops01-human-execution-pack.md) | Full OPS-01 human pack |
| [GOVERNANCE-LABEL-ALIGNMENT.md](../audit/ga-engineering-audit/completion/GOVERNANCE-LABEL-ALIGNMENT.md) | DONE\* vs gate CLOSED vocabulary |

---

**Validation label:** light validated (evidence paths cross-linked from EAB-003; ink fields empty).  
**Production classification:** production no-go unchanged by this unsigned packet.
