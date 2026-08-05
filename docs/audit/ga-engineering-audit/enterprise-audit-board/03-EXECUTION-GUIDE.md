# 03 — Execution Guide | دليل التنفيذ

**Pack:** Enterprise Audit Board v2.1  
**Role:** How to open and run a board without reinventing methodology  
**Status:** Framework — run not opened until approved

---

## 1. Preconditions (human approval)

Before any run:

| Gate | Required |
|------|----------|
| Scope | SalesOS paths, optional extras (e.g. `data/` lineage) |
| Workstreams | Which of §3 are in / deferred |
| Evidence budget | What may be run (grep-only vs approved narrow tests) |
| Low-load exceptions | Explicit list if any heavy commands allowed |
| Output path | Dated run file from [09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md) |

**Board run still awaits approval** until these are signed off.

---

## 2. Input reading order

1. This pack hub — [README.md](./README.md)  
2. [01-CHARTER.md](./01-CHARTER.md) + [04-EVIDENCE-STANDARD.md](./04-EVIDENCE-STANDARD.md)  
3. [PRODUCTION_PLAN.md](../PRODUCTION_PLAN.md) — Waves 0–14 DoD  
4. [AI_HONESTY.md](../AI_HONESTY.md) — AI stub / flag rules  
5. [00-EXECUTIVE-SUMMARY.md](../00-EXECUTIVE-SUMMARY.md) — baseline NO-GO  
6. [PRINCIPAL-AUDIT-BOARD-2026-08-06.md](../PRINCIPAL-AUDIT-BOARD-2026-08-06.md) — v1 scorecard (results sibling)  
7. [GA_STATUS.md](../GA_STATUS.md) — live scoreboard  
8. [APPENDIX-C-FINDINGS-REGISTER.md](../APPENDIX-C-FINDINGS-REGISTER.md) — historical findings seed  
9. [`docs/PROJECT_BIBLE.md`](../../../PROJECT_BIBLE.md) — if present  
10. `docs/program/decisions/` — DEC series  
11. `docs/adr/` + SES / Notion docs under `docs/` if present  
12. SalesOS module map — `salesos/backend/app/`, `salesos/frontend/`, compose files  
13. Then execute axes per [02-METHODOLOGY.md](./02-METHODOLOGY.md)

---

## 3. Recommended workstream split

| Workstream | Primary axes | Agents |
|------------|--------------|--------|
| **Business + Domain** | 02, 06, 07, 20, 21 | 1–2 explore |
| **ADR + SES + Docs + Traceability** | 01, 08, 09, 10, 29, **40** | 1 explore |
| **Drift + Fitness + Debt** | 23–28, 24, **41** | 1 explore + optional static scripts |
| **Engineering Economics** | **42** (+ 23 inputs) | 1 explore / principal |
| **AI + Knowledge + AI Governance** | 12, 13, 14, **43** | 1 explore (honesty-first) |
| **Data Lineage** | 16, 17, 18, 19 | 1–2 explore |
| **Runtime** | 05, 11, 15 | 1 explore |
| **Product Journey** | 03, 04, 20, 22 | 1 explore |
| **Security + Ops + Scorecards** | 30, 31, 32, 33, 34 | 1–2 explore (**do not weaken controls**) |
| **Executive synthesis** | 35–39 | Principal only |

Prefer ≥2–3 parallel READY workstreams (DEC-107 spirit). Do not pause the whole board solely because one ops/CI item is BLOCKED.

**Agent ownership:** Avoid conflicting edits on parallel-owned surfaces (e.g. `TenantList` / security P0 endpoints) unless assigned.

---

## 4. Low-load rules

Without **explicit** user approval, do **not**:

- Full `npm run build` / lint / test suites  
- Package installs (`npm` / `pnpm` / `yarn`)  
- Prisma generate/migrate (SalesOS core uses Alembic)  
- Production Alembic migrate / restore / deploy  
- Full pytest outside a narrow approved path  
- Secret or `.env` edits that weaken security  

**Prefer:** Grep/Read, static import graphs, Docker `alembic current` when already available, documented prior wave evidence.

Static explore → at most **light validated**. Heavy suites → only if approved → may reach **build validated**.

---

## 5. How to open a run

1. Confirm human approval (section 1).  
2. Copy [09-AUDIT-RUN-TEMPLATE.md](./09-AUDIT-RUN-TEMPLATE.md) to e.g.  
   `docs/audit/ga-engineering-audit/ENTERPRISE-AUDIT-BOARD-RUN-YYYY-MM-DD.md`  
3. Fill metadata; leave scores/findings empty until evidence exists.  
4. Dispatch workstreams; collect findings per [06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md).  
5. Score per [07-SCORING-MODEL.md](./07-SCORING-MODEL.md); report per [08-REPORTING-STANDARD.md](./08-REPORTING-STANDARD.md).  
6. Attach evidence appendix (commands, agent IDs, what was **not** run).  
7. Verdict defaults to **production no-go** until synthesis rules and evidence say otherwise.

Do **not** invent the dated run file until a real run starts.

---

## 6. Required run outputs

| Deliverable | Standard |
|-------------|----------|
| Findings register | [06-FINDINGS-SCHEMA.md](./06-FINDINGS-SCHEMA.md) |
| Axis scorecard | [07-SCORING-MODEL.md](./07-SCORING-MODEL.md) |
| Decision Traceability Matrix | [08-REPORTING-STANDARD.md](./08-REPORTING-STANDARD.md) §DTM |
| CEO / CTO / 30-60-90 / 12-mo | [08-REPORTING-STANDARD.md](./08-REPORTING-STANDARD.md) |
| GO / NO-GO | Explicit; no GO without evidence |
| Evidence appendix | Commands + gaps |

---

*Execution Guide — Enterprise Audit Board v2.1*
