# Enterprise Audit Board — Institutional Reference Pack | مجلس التدقيق المؤسسي

**Version:** v2.1 (pack)  
**Document type:** Framework / methodology (not an executed audit run)  
**Date authored:** 2026-08-06  
**Product in scope:** SalesOS (`salesos/`) under AQLIYA  
**Principle:** AI assists. Humans decide. Evidence governs.

> **Status:** **Framework ready / axes not executed.**  
> This pack defines how every future Enterprise Audit Board run must operate. It does **not** invent axis scores, Production GO, or a completed full-root audit.  
> **Board run still awaits human approval** (scope, workstreams, evidence budget, low-load exceptions).

---

## Purpose

Institutional reference for full-root enterprise governance audits of SalesOS under AQLIYA:

**Vision → architecture → docs → code → data → runtime → monitoring**, with checkable fitness, measured drift, engineering economics, and AI governance (separate from Security).

Each future audit run **executes this pack** — it does not reinvent methodology.

---

## Pack structure

```
Enterprise Audit Board
├── Charter
├── Methodology
├── Execution Guide
├── Evidence Standard
├── Fitness Catalog
├── Findings Schema
├── Scoring Model
├── Reporting Standard
└── Audit Run Template
```

| # | File | Role |
|---|------|------|
| — | [README.md](./README.md) | Hub index (this file) |
| 01 | [01-CHARTER.md](./01-CHARTER.md) | Purpose, scope, non-claims, authority |
| 02 | [02-METHODOLOGY.md](./02-METHODOLOGY.md) | Full axis catalog (43 axes; 4 × v2.1) |
| 03 | [03-EXECUTION-GUIDE.md](./03-EXECUTION-GUIDE.md) | Workstreams, agents, how to open a run |
| 04 | [04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md) | Validation labels, forbidden claims |
| 05 | [05-FITNESS-CATALOG.md](./05-FITNESS-CATALOG.md) | Fitness functions + drift metrics |
| 06 | [06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md) | Finding IDs, severity, evidence fields |
| 07 | [07-SCORING-MODEL.md](./07-SCORING-MODEL.md) | Scores, rollups, economics bands, GO rules |
| 08 | [08-REPORTING-STANDARD.md](./08-REPORTING-STANDARD.md) | Required report sections + DTM template |
| 09 | [09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md) | Blank run template — **NOT EXECUTED** |

---

## Version lineage | التسلسل

| Version | Artifact | Role |
|---------|----------|------|
| **v1** | [PRINCIPAL-AUDIT-BOARD-2026-08-06.md](../PRINCIPAL-AUDIT-BOARD-2026-08-06.md) | Engineering Pre-Launch Board — **current-state results** (Production GA **NO-GO**) |
| **v2** | Historical single-file charter (preserved as pointer: [ENTERPRISE-AUDIT-BOARD-V2.md](../ENTERPRISE-AUDIT-BOARD-V2.md)) | First full-root methodology (~39 axes) — charter only |
| **v2.1** | **This pack** (`enterprise-audit-board/`) | Institutional reference pack + 4 mandatory axes (Decision Traceability, Architectural Drift, Engineering Economics, AI Governance) |

**Results sibling (do not confuse with methodology):** Principal Board 2026-08-06 remains the authoritative **executed** pre-launch engineering verdict until a dated Enterprise Board **run** is approved and completed.

---

## Four v2.1 mandatory axes (summary)

| Axis | Name | Audit question |
|------|------|----------------|
| 40 | Decision Traceability Matrix | Can every decision be traced Vision → … → Monitoring? |
| 41 | Architectural Drift Detection | Is ADR↔code drift **measured** over time (not only discovered)? |
| 42 | Engineering Economics | What is the CTO cost of change (capability, locale, tenant, upgrade, DB, delete module)? |
| 43 | AI Governance Score | Separate from Security — safety, explainability, override, vendor lock-in, aligned with [AI_HONESTY.md](../AI_HONESTY.md) |

---

## Authority chain

Executable evidence → [ga-engineering-audit](../) → [`AGENTS.md`](../../../../AGENTS.md) → [`docs/PROJECT_BIBLE.md`](../../../PROJECT_BIBLE.md)

Audit wins over bible maturity claims for GO/NO-GO. Standing classification until a run changes it with evidence: **production no-go**.

---

## How to open a run

1. Human approves scope + workstreams + evidence budget ([03-EXECUTION-GUIDE.md](./03-EXECUTION-GUIDE.md)).  
2. Copy [09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md) → dated run file under `docs/audit/ga-engineering-audit/`.  
3. Execute axes per [02-METHODOLOGY.md](./02-METHODOLOGY.md); score per [07-SCORING-MODEL.md](./07-SCORING-MODEL.md); report per [08-REPORTING-STANDARD.md](./08-REPORTING-STANDARD.md).  
4. Do **not** claim Production GO without executable evidence ([04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md)).

---

*Enterprise Audit Board v2.1 — AQLIYA / SalesOS. Framework ready. Axes not executed. Board run awaits approval.*
