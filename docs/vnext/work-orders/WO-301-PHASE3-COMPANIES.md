# Work Order WO-301 — Phase 3: Companies

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 0-2 ✅
> **Priority**: P0

---

## Scope

Complete Companies domain: bulk operations, advanced filtering, keyset pagination.

Note: `search_by_filters` double-query was already fixed in Sprint 0 (PERF-08).

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Bulk operations API** — bulk edit (PATCH), bulk delete (DELETE), bulk export (GET /export) | 3d |
| B-2 | **Advanced filtering API** — filter by industry, size, region, created date range, status | 2d |
| B-3 | **Keyset pagination** — verify all company endpoints use cursor-based, not OFFSET | 1d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Bulk selection UI** — select-all-on-page, select-all-across-pages, count bar | 2d |
| F-2 | **Bulk action dialogs** — bulk edit modal, bulk delete confirmation, bulk export | 2d |
| F-3 | **Advanced filter component** — industry dropdown, size range, region, date range, status chips | 2d |

## Assigned Engineer

`backend-engineer` (B-1, B-2, B-3)
`frontend-engineer` (F-1, F-2, F-3)

## Deliverables

- Bulk operations (API + UI) for companies
- Advanced filter component
- Keyset pagination verified
- `SPRINT3_COMPANIES_REPORT.md`

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-3.1 | Bulk edit supports: industry, size, status, tags |
| G-3.2 | Bulk delete shows confirmation with count |
| G-3.3 | Bulk export produces CSV with selected fields |
| G-3.4 | Filters: industry, size, region, created date, status |
| G-3.5 | All company list endpoints use keyset pagination |
| G-3.6 | p95 < 100ms at 100k records |

---

**Engineering OS**: ✅ Approved
