# Work Order WO-401 — Phase 4: Company360

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 3 (Companies) ✅
> **Priority**: P1

---

## Scope

Build unified Company 360 view integrating Knowledge Graph, Timeline, and Decision Platform.

## Tasks

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Company 360 page** — tabbed layout: Overview, Hierarchy, Financial, Activity, Insights | 3d |
| F-2 | **Knowledge Graph panel** — company relationships (competitors, partners, subsidiaries) | 2d |
| F-3 | **Activity timeline** — filterable event stream per company | 2d |
| F-4 | **Decision Platform panel** — 3+ recommendation types for the company | 2d |

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Company 360 aggregation endpoint** — single endpoint joining Companies + KG + Timeline + Enrichment | 2d |
| B-2 | **KG company insights API** — relationships, market position, hierarchy | 1d |
| B-3 | **Timeline filter API** — filter by event type, date range, domain | 1d |

## Assigned Engineer

`frontend-engineer` (F-1, F-2, F-3, F-4)
`backend-engineer` (B-1, B-2, B-3)

## Deliverables

- Unified Company 360 page
- `SPRINT4_COMPANY360_REPORT.md`

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-4.1 | 360 page shows: Companies, CRM, Timeline, Enrichment, Entity Resolution, KG data |
| G-4.2 | Timeline loads < 200ms p95 |
| G-4.3 | KG insights are company-specific |
| G-4.4 | Decision Platform provides ≥ 3 recommendation types |
| G-4.5 | All existing tests pass |

---

**Engineering OS**: ✅ Approved
