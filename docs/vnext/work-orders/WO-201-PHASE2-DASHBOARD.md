# Work Order WO-201 — Phase 2: Dashboard Polish

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 0 (Security + Performance) ✅, Phase 1 (Design System V2) ✅
> **Priority**: P0

---

## Scope

Polish dashboard widgets: loading, empty, error states. Fix NBA feed N+1.

## Tasks

| # | Task | Type | Effort |
|---|------|------|--------|
| 1 | **Dashboard loading audit** — apply `<Skeleton>` to all 8 widget Containers | Frontend | 2d |
| 2 | **Dashboard empty states** — apply `<EmptyState>` to all 8 widget Views | Frontend | 2d |
| 3 | **Dashboard error states** — apply `<ErrorBoundary>` + Toast patterns | Frontend | 1d |
| 4 | **NBA feed N+1** — implement `batch_get_or_compute()` in NBA engine | Backend | 2d |
| 5 | **Widget compatibility** — verify all widgets consume SDK correctly | Frontend | 1d |

## Assigned Engineer

`frontend-engineer` (tasks 1-3, 5)
`backend-engineer` (task 4)

## Deliverables

- All 8 widgets: Skeleton loading, EmptyState, error handling
- NBA feed with true O(1) batch evaluation
- `SPRINT2_DASHBOARD_REPORT.md`

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-2.1 | All widgets show `<Skeleton>` during loading |
| G-2.2 | All empty states use `<EmptyState>` component |
| G-2.3 | Widget errors show error boundary + retry |
| G-2.4 | NBA feed runs O(1) database queries |
| G-2.5 | All 103 widget contract tests pass |

---

**Engineering OS**: ✅ Approved
