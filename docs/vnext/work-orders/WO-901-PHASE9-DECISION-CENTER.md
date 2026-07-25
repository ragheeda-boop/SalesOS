# Work Order WO-901 — Phase 9: Decision Center

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 0 ✅, Phase 3-8 ✅
> **Priority**: P0

---

## Scope

Decision Center UI: unified interface, audit trail, feedback, templates, multi-provider ensemble.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Decision Center aggregation** — `GET /decisions` combining decisions from all domains (pipeline, employee, company, revenue) | 2d |
| B-2 | **Audit trail** — `GET /decisions/{id}/audit` returning full reasoning chain, confidence, provider, alternatives | 1d |
| B-3 | **Feedback mechanism** — `POST /decisions/{id}/feedback` (thumbs up/down + comment), track for evaluation | 1d |
| B-4 | **Decision templates** — lead qualification, deal progression, renewal risk, pricing (4 templates) | 2d |
| B-5 | **Multi-provider ensemble** — for deals >$100K, invoke 2+ providers, vote on decision | 1d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Decision Center page** — unified table of all decisions across domains | 2d |
| F-2 | **Audit trail panel** — expandable per decision: reasoning chain, confidence, provider, alternatives | 1.5d |
| F-3 | **Feedback UI** — thumbs up/down + comment on each decision | 1d |
| F-4 | **Templates management** — view/edit/use decision templates | 1.5d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-9.1 | Shows decisions across all domains |
| G-9.2 | Audit trail: input context, reasoning, confidence, provider, alternatives |
| G-9.3 | Feedback tracked for evaluation |
| G-9.4 | 4+ templates operational |
| G-9.5 | Ensemble mode for >$100K deals |

---

**Engineering OS**: ✅ Approved
