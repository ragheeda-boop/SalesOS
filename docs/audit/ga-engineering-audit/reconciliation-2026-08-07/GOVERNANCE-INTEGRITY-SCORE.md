# Governance Integrity Score

**Pack:** Enterprise Reconciliation Audit — 2026-08-07  
**Method:** Four scores 0–100 from evidence-backed reconciliation only. No invented pass rates.  
**Inputs:** Seven reviewer reports + Chair merge (`DOCUMENT-CONTRADICTIONS.md`) + spot re-read of evidence JSON.

---

## Scorecard

| Dimension | Score (0–100) | Band |
|-----------|--------------:|------|
| **Consensus Score** | **84** | High agreement on critical forks |
| **Evidence Confidence** | **71** | Strong for Rows 1–3 drills + soak progress; gaps on Neo4j durability artifact & gate ink |
| **Documentation Integrity** | **36** | Critical DONE/OPEN fork; multi-score shopping; stale present-tense |
| **Governance Consistency** | **32** | Statusboard ≠ cutover gate ≠ signature packet ≠ board disposition text |

**Composite (unweighted mean):** **55.75 → 56**  
**Interpretation:** Governance pack is **usable for NO-GO enforcement** but **not integrity-clean** for any Production GO narrative.

---

## 1. Consensus Score — **84**

**Basis**
- All seven reviewers independently flagged **RC-P0-01** (GA_STATUS/OPS DONE vs DR/SIGN_HERE/EAB OPEN) as CRITICAL.
- All ops-facing reviewers (R2/R3/R6/R7) flagged checklist **self-inconsistency** with linked WAL/offsite evidence (**RC-P0-02**).
- Production **NO-GO** agreement: unanimous across reviewers and source set (non-contradiction).
- Severity disagreements were narrow (e.g., DONE\* vs automation: R3=P0 vs R1/R2=P2 → Chair P0 for CLOSED semantics only).

**Deductions (−16)**
- Reviewer raw contradiction inventories overlap but are not identical (11–14 each) → some topic scoping variance.
- Security score elevation (R4 P0 vs others P1) required Chair judgment.

---

## 2. Evidence Confidence — **71**

**Present and re-checked (raises score)**
- `ops01-row1-offsite-restore.json` — dump SHA, S3 upload/download match, restore path recorded.
- `ops01-row2-wal-archiver.json` / `ops01-row3-pitr-restore.json` — WAL/PITR drill artifacts present.
- `ops01-staging/loop-*.json` — **24** loop files observed; sample i00022 shows staging `/health` 200 with `graph=connected`, `kafka=in_memory`, gate_pass true.
- `migration-dress-rehearsal.json` / `prod-index-probe.json` — migration prep evidence present.
- EAB-001/002/003 SCORECARD/CEO/RUN-REPORT exist and align on NO-GO within each run’s score tables.

**Missing / weak (lowers score) → NOT VERIFIED**
- Post-repair **production** `/health` JSON claiming `graph=connected` under evidence/ — **absent**.
- Human `signed_off_by` / DR checklist CLOSE for rows 1–3 — **absent**.
- Managed schedule / native PITR API authorization — **BLOCKED-HUMAN** per OPS pack.
- Full 48–72h soak completion artifact / `soak_complete_claim: true` — **absent** (in progress only).
- Single supersession banner updating `GA_STATUS` / `SIGN_HERE` DR language — **absent**.

---

## 3. Documentation Integrity — **36**

**Basis for low score**
- Same launch-blocker topic published as **DONE** and **OPEN** simultaneously (**RC-P0-01**).
- Board-linked DR checklist denies facts recorded in linked evidence (**RC-P0-02**).
- Multiple concurrent Security / PR “current” numbers without supersession chain (**RC-P0-03**).
- Signature packet suite census (**1548**) vs EAB Verification Run (**2009/2492**) without date fence (**RC-P1-04**).
- Intra-document ROW4 “soak not started” vs “soak started” (**RC-P1-02**).
- Soft “READY / 96% / 100% / 98%” language adjacent to mandatory production no-go (**RC-P1-05**).

**What keeps score above ~20**
- Explicit NO-GO language still widespread; cutover package correctly **PREPARED — NOT EXECUTED**.
- Evidence folders exist and are linkable; problem is **doc layering**, not total absence of artifacts.

---

## 4. Governance Consistency — **32**

**Measured as agreement across governance layers**

| Layer | Stated posture on Rows 1–3 | Consistent? |
|-------|----------------------------|:-----------:|
| Evidence JSON | Drills recorded | — |
| OPS-01 checklist/advancement | DONE\* | vs gate |
| GA_STATUS | DONE | vs gate |
| DR-GA-GAPS-CHECKLIST | OPEN / NOT done | vs OPS/GA |
| SIGN_HERE | OPEN | vs OPS/GA |
| EAB CEO/RUN/FINDINGS/PROGRAM | OPS-01 open / Deferred / 1–5 OPEN | vs OPS DONE\* |
| RELEASE-BACKLOG | Backup DR PARTIAL | vs GA DONE |

**Also inconsistent**
- Neo4j OFFLINE verification doc vs repaired narrative without artifact bridge.
- Staging parity present-tense on GA_STATUS vs 2026-08-07 ROW4.
- Alembic identity: 0051 / 0040 / `d1a8c35e7f09`.

**Consistent (positive)**
- Production GA = **NO-GO** across SIGN_HERE CTO, GA_STATUS header, all EAB CEO summaries.
- Row 4 status value **OPEN** while soak incomplete.
- Tech Lead **UNSIGNED**.

---

## Honesty labels for this scoring exercise

| Label | Application |
|-------|-------------|
| **light validated** | This reconciliation (doc/evidence cross-read; no new live prod probes executed by Chair this session beyond reading checked-in JSON) |
| **not validated** | Any claim that post-repair prod Neo4j is durably healthy |
| **production no-go** | Unchanged recommendation posture |

---

## Score movement conditions (human actions — not executed here)

| To raise Documentation Integrity / Consistency above 70 | Required |
|---------------------------------------------------------|----------|
| Reconcile RC-P0-01/02 | Either CLOSE DR checklist rows 1–3 with ink + update SIGN_HERE/EAB disposition **or** revert GA_STATUS/OPS DONE\* if automation/sign-off bar unmet — **not both** |
| Reconcile RC-P0-03 | Publish one supersession: EAB-003 Security/PR onto GA_STATUS; fence **48** as historical |
| Reconcile Neo4j | Deposit post-repair prod health JSON or keep OFFLINE as SoT |
| Reconcile soak SoT | Point SIGN_HERE open soak to `ops01-staging` + K1–K6; remove dual 140-loop confusion |
| Complete Row 4/5 | 48–72h claim true + TL signature |

---

*Chair synthesis — GOVERNANCE-INTEGRITY-SCORE — reconciliation-2026-08-07*
