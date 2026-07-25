# Work Order WO-501 — Phase 5: Employees

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 0 ✅
> **Priority**: P1

---

## Scope

Complete Employees domain (70% → 100%): signals pipeline, Decision Platform integration, search, bulk ops.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Signals pipeline** — collect from 3+ sources (CRM activity, timeline events, workflow completions) | 3d |
| B-2 | **Employee scoring** — integrate with Decision Platform scoring engine | 2d |
| B-3 | **Employee search pagination** — keyset cursor on all list endpoints | 1d |
| B-4 | **Employee bulk operations** — edit, delete, export | 2d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Employee list page** — search, filter, pagination with DataTable | 2d |
| F-2 | **Employee signals dashboard** — signal types, counts, trends | 2d |
| F-3 | **Employee scoring display** — score gauge, trend, factors | 1d |
| F-4 | **Employee bulk operations UI** — selection, edit modal, delete confirm, export | 2d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-5.1 | Signals from 3+ sources |
| G-5.2 | Score integrated in Decision Platform |
| G-5.3 | Search p95 < 100ms |
| G-5.4 | All list endpoints paginated (keyset) |

---

**Engineering OS**: ✅ Approved
