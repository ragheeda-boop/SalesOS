# DEC-137 — ADR-033/034 index↔file status honesty (Phase 0 criterion 6.3)

> **Status:** **Accepted** — Cursor implementation **COMPLETE** · Criterion **6.3 READY FOR REVIEW** (Arch/Val PENDING)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / ADR Drift (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **6.3** · ADR Drift status conflict (index Accepted vs file Proposed)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §6.3 · DEC-136a “Architecture next” (prefer **6.3**) · ARB review protocol  
> **Out of scope this land:** ADR-032 naming (6.4) · ADR-036 multi-index (6.5) · inventing Accepted without ARB evidence · advancing ADR bodies to Accepted · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · VERIFIED/CLOSED

---

## 1. Decision

Resolve criterion **6.3** by **aligning the canonical index to file header status** (checklist: “Index status matches file header status”) — not by inventing Accepted on ADR-033/034 without ARB acceptance evidence.

| Pin | Value |
|---|---|
| Evidence required | Index status matches file header status |
| Observation | `docs/adr/index.md` claimed ✅ Accepted for ADR-033/034; file headers are `**Status**: Proposed` |
| Disposition | Index → **📝 Proposed**; dates → file headers (`2026-07-17`); ADR bodies unchanged |
| Files | `docs/adr/0033-decision-engine-lifecycle.md` · `docs/adr/0034-repository-pattern-compliance.md` |
| Criterion state | **READY FOR REVIEW** (Orchestrator VERIFIED/CLOSED only after Arch+Val PASS) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| ADR-033 file header Status = Proposed | **Yes** |
| ADR-034 file header Status = Proposed | **Yes** |
| `docs/adr/index.md` Status for 033/034 matches file headers | **Yes** (after this land) |
| No invented Accepted without ARB evidence | **Yes** |
| ADR file bodies not rewritten to force Accepted | **Yes** |
| `.engineering/27_ADR_INDEX.md` re-pin | **Residual** — tree untracked (criterion **4.5**); non-blocking for 6.3 |

**Not claimed this land:** Production GO · CI GREEN · VERIFIED/CLOSED · Phase 0 exit · closing 6.4–6.5 · ADR-033/034 Accepted.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Flip file headers to Accepted to match index | Rejected — no ARB acceptance evidence; invents binding Accepted |
| (b) Leave mismatch | Rejected — fails 6.3 |
| (c) Remove index rows until Accepted | Rejected — files exist; Proposed is valid lifecycle state |
| (d) Align index Status (+ dates) to file headers | **Approved** — honesty without inventing acceptance |

---

## 3. Validation

| Check | Result |
|---|---|
| `docs/adr/0033-decision-engine-lifecycle.md` exists · Status Proposed | **Yes** |
| `docs/adr/0034-repository-pattern-compliance.md` exists · Status Proposed | **Yes** |
| Index File column paths match disk (`Test-Path`) | **Yes** |
| Index Status for ADR-033/034 = Proposed | **Yes** (this land) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (filesystem + index/file status match; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met. VERIFIED/CLOSED not claimed** (Arch/Val PENDING).

---

## 4. Records

- Phase 0 criterion **6.3** → **READY FOR REVIEW**
- Phase 0 remains **31/54** until Orchestrator CLOSE
- ADR Drift Complete remains **2/5** / Open **3** until CLOSE
- ADR Drift residual after CLOSE target: **6.4** (032 naming), **6.5** (036 all indexes)
- EOS **4.5** / `.engineering/` re-pin of `27_ADR_INDEX.md` = follow-on
- **Not claimed:** Production GO · CI GREEN · VERIFIED/CLOSED · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | ADR-033 file (Status Proposed) | `docs/adr/0033-decision-engine-lifecycle.md` |
| EV-002 | ADR-034 file (Status Proposed) | `docs/adr/0034-repository-pattern-compliance.md` |
| EV-003 | Index alignment | `docs/adr/index.md` |
| EV-004 | This DEC | `docs/program/decisions/DEC-137-CRITERION-6-3-ADR-033-034-STATUS.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (index status/dates + DEC-137 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 6.3 returns OPEN (index Accepted vs file Proposed mismatch) |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Readers assume 033/034 are binding Accepted | LOW after land | Index now Proposed; matches files |
| Future silent flip to Accepted without ARB | MEDIUM residual | Lifecycle requires ARB; not this land |
| Overclaim VERIFIED/CLOSED | LOW | Land is READY FOR REVIEW only |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 6.3? | **After** Arch PASS + Validation PASS (light: index Status == file header for 033/034; no Accepted-without-evidence) → Orchestrator DEC-137a |
| Next PARALLEL | **6.4** (032 naming) — docs-only; **6.5** after ADR-036 + `27_ADR_INDEX` |
| Do not | Invent Accepted · claim Production GO / CI GREEN · close 6.4–6.5 in this land |
