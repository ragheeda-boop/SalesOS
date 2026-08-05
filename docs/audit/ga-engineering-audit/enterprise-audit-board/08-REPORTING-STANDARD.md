# 08 — Reporting Standard | معيار التقارير

**Pack:** Enterprise Audit Board v2.1  
**Role:** Required sections for every executed run report  
**Status:** Template rules — content filled only during a run

---

## 1. Required report sections

Every dated Enterprise Audit Board **run** document must include:

| # | Section | Source axes / notes |
|---|---------|---------------------|
| 1 | **Metadata** | Run ID, date, scope, approver, pack version v2.1 |
| 2 | **CEO Executive Summary** | Axis 36 — one page, non-technical |
| 3 | **CTO Readiness** | Axis 35 — why NO-GO / what changes mind |
| 4 | **Scorecard** | All 43 axes + Security vs AI Governance split ([07-SCORING-MODEL.md](./07-SCORING-MODEL.md)) |
| 5 | **Decision Traceability Matrix** | Axis 40 — table §2 below |
| 6 | **Architectural Drift** | Axis 41 — metrics + formula inputs |
| 7 | **Engineering Economics** | Axis 42 — six cost bands |
| 8 | **AI Governance Scorecard** | Axis 43 — ten sub-factors + honesty gates |
| 9 | **Findings register** | [06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md) |
| 10 | **30 / 60 / 90 Day Recovery** | Axis 37 |
| 11 | **12-Month Architecture Roadmap** | Axis 38 |
| 12 | **GO / NO-GO Synthesis** | Axis 39 — explicit classification |
| 13 | **Evidence appendix** | [04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md) |
| 14 | **Relation to Principal Board** | Cite [PRINCIPAL-AUDIT-BOARD-2026-08-06.md](../PRINCIPAL-AUDIT-BOARD-2026-08-06.md) as results sibling; do not silently overwrite |

Omit-none rule: if a section has no data, write **`NOT EXECUTED` / `not validated`** — never omit the heading to hide gaps.

---

## 2. Decision Traceability Matrix (DTM) template

**Audit question:** Can every decision be traced to execution?

Fill one row per sampled decision (ADR, DEC, or capability-level decision). Mark each hop: `✓` present path | `△` partial | `✗` missing | `STUB` honesty stub | `n/a`.

| Decision ID | Vision | Product Bible | Capability | ADR | Implementation | API | UI | Tests | Runtime | Monitoring | Break notes | Finding IDs |
|-------------|--------|---------------|------------|-----|----------------|-----|----|-------|---------|------------|-------------|-------------|
| e.g. ADR-xxx / DEC-xxx | | | | | | | | | | | | |
| | | | | | | | | | | | | |
| | | | | | | | | | | | | |

**Chain (canonical):**  
Vision → Product Bible → Capability → ADR → Implementation → API → UI → Tests → Runtime → Monitoring

Sampling guidance: ≥10 material Accepted decisions **or** all P0-related decisions — state sample method in the run.

---

## 3. CEO summary rules

- One sentence: what SalesOS **is** / **is not**.  
- Business risk of shipping now.  
- Ask for 30/60/90.  
- Explicit: no Production GO without evidence.  
- No axis score dumps; no AI marketing overclaim.

---

## 4. CTO readiness rules

- P0 list with evidence status.  
- Residual risks + owners.  
- Unsigned gates called out.  
- Economics Extremes + drift baseline.  
- AI Governance vs Security as separate bullets.  
- “What would change the verdict” checklist.

---

## 5. 30 / 60 / 90 and 12-month

| Horizon | Must answer |
|---------|-------------|
| 30 days | What closes to unblock internal pilot **conditions** (not fake GA)? |
| 60 days | Structural debt (compose, MetaData, decision surface, DTM breaks)? |
| 90 days | Staging/DR/evidence bar? |
| 12 months | Fitness CI, lineage, single compose, AI honesty path, Core extraction defer/plan? |

Tie items to finding IDs. No wishful milestones without owners.

---

## 6. Naming dated runs

Suggested path:

`docs/audit/ga-engineering-audit/ENTERPRISE-AUDIT-BOARD-RUN-YYYY-MM-DD.md`

Start from [09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md). Do not create until a run is approved and opened.

---

*Reporting Standard — Enterprise Audit Board v2.1*
