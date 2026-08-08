# DEC-151 — Phase 0 Governance Freeze

> **Status:** **Accepted**  
> **Date:** 2026-08-02  
> **Board:** Execution Orchestrator / Chief Architect (SalesOS) — program/governance scribe land  
> **Story / risk:** Phase 0 program governance · residual hard OPEN **3.7**, **3.9**, **4.1**, **4.8**  
> **Authority:** User directive **Phase 0 Governance Freeze** · tip after DEC-150 Option B @ `a734853` · aligns Architecture = FROZEN (EEC-001 / checklist Operating State) · AI org baseline / runtime deferred (ARB-003 / DEC-145 / DEC-146) · DEC-149 / DEC-149a · DEC-150 B  
> **Out of scope this land:** closing any Phase 0 criterion · inventing EOS **4.1/4.8** ARB PASS · Production GO · full CI GREEN · Phase 0 COMPLETE · app/backend/frontend code · workflow topology changes · superseding DEC-149 / DEC-150  
> **In scope:** Formal freeze of Phase 0 organizational redesign, deployment-topology DECs, and criterion rewrites; crumbs on checklist / board / DAG

---

## 1. Decision

**Accept** a **Phase 0 Governance Freeze** effective immediately at tip after DEC-150 Option B.

Phase 0 remains **48/54 NO-GO**. Canonical deploy remains **Backend → Railway + Frontend → Vercel** (DEC-149 / DEC-149a). Stage 6 GHCR remains **retired as a Phase 0 gate** (DEC-150 Option B); CI-08 remains **GOVERNANCE COMPLETED**.

This freeze does **not** declare Phase 0 exit, Production GO, or CI GREEN.

---

## 2. What is frozen

| Surface | Freeze meaning |
|---|---|
| **Organizational redesign** | No new org charts, role-registry redesigns, swarm-model rewrites, or `.ai/` org baseline expansion beyond bugfix / evidence crumbs |
| **Deployment-topology DECs** | No new DEC proposing alternate live deploy planes (VPS, K8s-as-primary, GHCR-as-primary, multi-cloud forks, etc.) that supersede DEC-149 |
| **Criterion rewrites** | No redefinition, renumbering, or supersession of Phase 0 exit criteria except as allowed in §3 |
| **Architecture layers** | Remains FROZEN per EEC-001 / ADR-036 / checklist Operating State — no new architectural layers |
| **AI Runtime** | Remains DEFERRED (DEC-146); org baseline ≠ live Agent OS |

Cross-align:

```text
STATE = EXECUTION
Architecture = FROZEN          (prior — EEC-001 / ARB-2026-08-01)
Governance = FROZEN            (this DEC — DEC-151)
Program = ACTIVE               (execution of allowed residual work only)
Engineering = STABILIZING
AI Runtime = DEFERRED          (DEC-146 / ARB-003 org baseline)
```

---

## 3. What remains allowed

Work that **does not** change architecture, supersede DEC-149/150, or invent ARB PASS:

1. **Field evidence** toward hard OPEN exit criteria only:
   - **3.7** — Stage 7 E2E with real backend services (not fake local green)
   - **3.9** — CI GREEN under DEC-149 topology (Stages 1–5 same-run + retained Railway/Vercel deploy evidence; no Stage 6 GHCR requirement)
   - **4.1** — Independent ARB re-audit of B1–B7 (ARB only)
   - **4.8** — Independent ARB re-audit PASS report (ARB only)
2. **Bugfixes** that unblock the above without topology or org redesign
3. **Evidence crumbs** (checklist / board / DAG / decision-log notes) that record field results honestly
4. **Conditional residual field-verify** already disclosed (e.g. tip Stages 1–5 for 3.8 residual; Security Scan pip-audit post-align) — does **not** rewrite criteria

---

## 4. What is forbidden (without formal ARB reverse)

| Forbidden | Notes |
|---|---|
| **New deploy topology DEC** | Must not supersede DEC-149 Railway+Vercel without ARB reverse of DEC-149 / DEC-151 |
| **Reopening GHCR as Phase 0 gate** | Must not reverse DEC-150 Option B without ARB reverse; residual GHCR 403 stays legacy/non-blocking |
| **Organizational redesign** | New agent org models, role ceilings redesign, or claiming live Agent OS |
| **Inventing ARB PASS** on **4.1** / **4.8** | Cursor / Orchestrator must not self-close EOS ARB criteria |
| **Criterion rewrite / invent COMPLETE** | No silent rewrites of OPEN rows; no claim Phase 0 COMPLETE / Production GO / CI GREEN / VERIFIED for 4.1/4.8 without ARB evidence |
| **Architecture Freeze break** except EEC-001 Rule 4 | Bug blocking a Phase 0 criterion, or formal new ARB decision |

---

## 5. Hard OPEN inventory (unchanged by this DEC)

| # | Criterion | Block class |
|---|-----------|-------------|
| **3.7** | Stage 7 E2E green | E2E services |
| **3.9** | CI GREEN (DEC-149 topology) | tip field-verify |
| **4.1** | B1–B7 findings resolved | ARB |
| **4.8** | Independent ARB re-audit = PASS | ARB |

Scoreboard pin remains **48/54 NO-GO**. This DEC does **not** change Complete/Open counts.

---

## 6. Explicit non-claims

1. Do **not** claim Phase 0 COMPLETE / Phase 0 GO.  
2. Do **not** claim Production GO / full CI GREEN.  
3. Do **not** claim VERIFIED / CLOSED for **4.1** or **4.8**.  
4. Do **not** claim field GHCR green or reopen CI-08 as ops Phase 0 gate.  
5. Validation level this land: **governance freeze documentation only**.

---

## 7. Artifacts updated with this land

| Artifact | Change |
|---|---|
| `PHASE_0_EXIT_CHECKLIST.md` | Operating State → `Governance = FROZEN`; header pointer to DEC-151 |
| `SPRINT_05_DELIVERY_BOARD.md` | Progress crumb **GOVERNANCE FROZEN** |
| `EXECUTION_DAG.md` | Freeze crumb + pointer |
| `DECISION_LOG.md` | DEC-151 Accepted entry |

---

## 8. Reverse / thaw

Thaw requires a **new Accepted DEC** (or ARB reverse explicitly naming DEC-151) authorizing one of: organizational redesign, deployment-topology change superseding DEC-149, reopening GHCR as Phase 0 gate, or criterion rewrite. Completing **3.7 / 3.9 / 4.1 / 4.8** with honest evidence does **not** require thawing this freeze.
