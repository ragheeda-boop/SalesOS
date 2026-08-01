# DEC-139 — ADR-036 multi-index registration (Phase 0 criterion 6.5)

> **Status:** **Accepted** — Criterion **6.5 READY FOR REVIEW** (Cursor COMPLETE; awaiting Arch+Val + Orchestrator DEC-139a)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / ADR Drift (SalesOS / AQLIYA) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **6.5** · ADR-036 present in all ADR indexes  
> **Authority:** PHASE_0_EXIT_CHECKLIST §6.5 · ADR-036 body · criterion 9.1 (Accepted already checked)  
> **Out of scope this land:** inventing Accepted without file/ARB evidence · advancing ADR-032/033/034 to Accepted · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · VERIFIED/CLOSED · Phase 0 exit · criterion 9.2 cross-refs

---

## 1. Decision

Resolve criterion **6.5** by registering **ADR-036** in both required indexes — checklist evidence: `docs/adr/index.md` + `.engineering/27_ADR_INDEX.md`.

| Pin | Value |
|---|---|
| Evidence required | ADR-036 registered in `docs/adr/index.md` + `27_ADR_INDEX.md` |
| Observation | Body @ `docs/adr/0036-engineering-organization-layer-separation.md` (untracked); header **Status: Accepted** (CTO / ARB); criterion **9.1** already ✅; Active ADRs table + `.engineering/27` lacked ADR-036 |
| Disposition | Add index rows; Status **✅ Accepted** matches file header + 9.1 (not invented); engineering-os has no separate ADR index (files only) |
| Files | ADR body · `docs/adr/index.md` · `.engineering/27_ADR_INDEX.md` · this DEC |
| Criterion state | **READY FOR REVIEW** (not VERIFIED/CLOSED) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| ADR-036 body path exists | **Yes** — `docs/adr/0036-engineering-organization-layer-separation.md` |
| `docs/adr/index.md` Active ADRs row for ADR-036 | **Yes** |
| `.engineering/27_ADR_INDEX.md` master table row for ADR-036 | **Yes** |
| Index Status matches file header (**Accepted**) | **Yes** — file header + criterion 9.1; not invented |
| engineering-os separate index | **N/A** — no `engineering-os/adr/index.md`; submodule is ADR files only |
| DEC-085 / auth untouched | **Yes** |
| `.engineering/27` committed for 6.5 evidence | **Yes** — broader EOS tree re-pin remains **4.5** |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · VERIFIED/CLOSED · closing 9.2.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Register as Proposed despite file Accepted | Rejected — invents status conflict; contradicts header + 9.1 |
| (b) Leave `.engineering/27` untracked for 4.5 only | Rejected — checklist evidence requires both indexes |
| (c) Duplicate ADR-036 under `engineering-os/adr/` | Rejected — no separate index; body already product-root |
| (d) Claim VERIFIED/CLOSED in this land | Rejected — Arch+Val + Orchestrator gate |
| (e) Multi-index registration + Status Accepted from file/9.1 | **Approved** |

---

## 3. Validation

| Check | Result |
|---|---|
| Body exists · Status Accepted · Date 2026-08-01 | **Yes** |
| `docs/adr/index.md` ID ADR-036 · Status Accepted · File → body | **Yes** (this land) |
| `.engineering/27_ADR_INDEX.md` ADR-036 row + conflict #13 RESOLVED | **Yes** (this land) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (filesystem + dual-index row presence; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.** Awaiting Arch+Val + Orchestrator DEC-139a for CLOSE.

---

## 4. Records

- Phase 0 criterion **6.5** → **READY FOR REVIEW**
- Phase 0 remains **33/54** until Orchestrator CLOSE
- ADR Drift Complete remains **4/5** / Open **1** until CLOSE
- Residual after CLOSE (expected): ADR Drift cluster COMPLETE; EOS **4.5** broader `.engineering/` re-pin; **9.2** OPEN
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit · VERIFIED/CLOSED

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | ADR-036 body (Status Accepted) | `docs/adr/0036-engineering-organization-layer-separation.md` |
| EV-002 | Product-root index row | `docs/adr/index.md` |
| EV-003 | EOS ADR index row | `.engineering/27_ADR_INDEX.md` |
| EV-004 | This DEC | `docs/program/decisions/DEC-139-CRITERION-6-5-ADR-036-MULTI-INDEX.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (body + indexes + DEC-139 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 6.5 returns OPEN (ADR-036 missing from indexes) |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Accepted without separate ARB minutes in-repo | LOW | File header cites CTO/ARB; criterion 9.1 already ✅ |
| Committing `.engineering/27` before full EOS 4.5 | LOW | Required for 6.5 evidence; other `.engineering/` files still **4.5** |
| Overclaim Production GO / CI GREEN | LOW | READY FOR REVIEW only |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 6.5? | **Arch review + Validation (light)** → Orchestrator DEC-139a |
| Next PARALLEL | EOS Audit **4.x** (incl. broader `.engineering/` re-pin **4.5**); Engineering Stability **8.1–8.3**; ADR-036 Applied **9.2** (program↔engineering cross-refs) |
| Do not | Invent Accepted for other ADRs · claim Production GO / CI GREEN · claim VERIFIED/CLOSED without Arch+Val |
