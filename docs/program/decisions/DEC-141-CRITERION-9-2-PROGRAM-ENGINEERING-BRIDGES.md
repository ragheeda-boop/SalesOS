# DEC-141 — Program ↔ Engineering layer bridges (Phase 0 criterion 9.2)

> **Status:** **VERIFIED/CLOSED** via DEC-141a (Arch PASS + Validation PASS light @ `7b618da`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / ADR-036 Applied (SalesOS / AQLIYA) — Orchestrator CLOSE  
> **Story / risk:** Phase 0 Exit Criterion **9.2** · `docs/program/` ↔ `.engineering/` bidirectional references  
> **Authority:** PHASE_0_EXIT_CHECKLIST §9.2 · ADR-036 Phase 2 · DEC-140 residual · DEC-141a  
> **Out of scope this land:** fingerprint re-measure (4.2/4.7) · EvidenceLevel upgrade (4.4) · ARB re-audit (4.1/4.8) · Eng Stability 8.1–8.3 · inventing SoT · merging layers · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · Phase 0 exit

---

## 1. Decision

Resolve criterion **9.2** by adding **thin bidirectional bridge files** that point across layers without copying catalogs, counts, or sprint state.

| Pin | Value |
|---|---|
| Evidence required | Cross-references exist; no data duplication |
| Observation | ADR-036 Accepted (9.1); `.engineering/` committed (4.5); ARB noted coordination gap; no dedicated program↔engineering bridge pair |
| Disposition | Add program bridge + EOS bridge; wire Related / Agent Bootstrap / constitution §8 / ADR-036 Related; no catalog body copy |
| Files | `docs/program/ENGINEERING_LAYER_BRIDGE.md` · `.engineering/33_PROGRAM_LAYER_BRIDGE.md` · crumbs · this DEC |
| Criterion state | **VERIFIED/CLOSED** (DEC-141a) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| Program → Engineering bridge exists | **Yes** — `docs/program/ENGINEERING_LAYER_BRIDGE.md` |
| Engineering → Program bridge exists | **Yes** — `.engineering/33_PROGRAM_LAYER_BRIDGE.md` |
| Bridges link reciprocally | **Yes** |
| No duplication of EOS catalogs / sprint tables into the other layer | **Yes** — pointers only |
| ADR-036 / constitution / checklist Related wired | **Yes** (this land) |
| DEC-085 / auth untouched | **Yes** |
| Fingerprint re-pin / ARB PASS | **No** — residuals **4.2/4.7/4.1/4.8** |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · closing 4.x / 8.x.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Merge `.engineering/` into `docs/program/` | Rejected — contradicts ADR-036 |
| (b) Duplicate fingerprint / board tables across layers | Rejected — data duplication forbidden |
| (c) Docs-only checklist note without files | Rejected — no executable cross-ref surface |
| (d) Claim VERIFIED/CLOSED in this land | Rejected — Arch+Val + Orchestrator gate |
| (e) Thin bidirectional bridges + Related wiring | **Approved** |

---

## 3. Validation

| Check | Result |
|---|---|
| Both bridge paths exist | **Yes** (this land) |
| Reciprocal links present | **Yes** |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (filesystem + link presence; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.** Closed via DEC-141a after Arch+Val PASS.

---

## 4. Records

- Phase 0 criterion **9.2** → **VERIFIED/CLOSED** (DEC-141a)
- Phase 0 **35/54 → 36/54**; ADR-036 Applied Complete **2 → 3**
- Residuals (non-blocking for 9.2): EOS **4.1/4.2/4.4/4.7/4.8** · Eng Stability **8.1–8.3**
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Program → Engineering bridge | `docs/program/ENGINEERING_LAYER_BRIDGE.md` |
| EV-002 | Engineering → Program bridge | `.engineering/33_PROGRAM_LAYER_BRIDGE.md` |
| EV-003 | This DEC | `docs/program/decisions/DEC-141-CRITERION-9-2-PROGRAM-ENGINEERING-BRIDGES.md` |
| EV-004 | Checklist / board / DAG crumbs | `PHASE_0_EXIT_CHECKLIST.md` · `SPRINT_05_DELIVERY_BOARD.md` · `EXECUTION_DAG.md` · `DECISION_LOG.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (bridges + Related wiring + DEC-141 crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 9.2 returns OPEN |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Bridge drift if paths rename | LOW | Thin pointers; future CI gate noted in ADR-036 trade-offs |
| New EOS file without fingerprint re-pin | LOW | Honest; 4.2/4.7 remain OPEN; pin preserved |
| Overclaim Production GO / CI GREEN | LOW | READY FOR REVIEW only |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 9.2? | **After** Arch PASS + Validation PASS (light: both bridges exist, reciprocal, no duplication) → Orchestrator DEC-141a |
| Next PARALLEL | EOS **4.2/4.7** fingerprint · **4.1/4.8** ARB · Eng Stability **8.1–8.3** |
| Do not | Merge layers · copy catalogs · claim Production GO / CI GREEN · claim Phase 0 exit |
