# Work Order WO-801 — Phase 8: Revenue

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 7 ✅
> **Priority**: P0

---

## Scope

Revenue domain completion: forecasting, quota management, territory planning, revenue dashboard.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Revenue forecasting** — ML-backed (time-series + pipeline-based), by-rep/region/product/total | 3d |
| B-2 | **Quota management** — CRUD, assignment, tracking attainment %, forecast attainment | 2d |
| B-3 | **Territory planning** — assign accounts to reps, coverage gap analysis, load balancing | 2d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Revenue dashboard** — ARR, NRR, churn, expansion metrics + trend charts | 2d |
| F-2 | **Quota management UI** — set quotas, track attainment bar, forecast indicator | 2d |
| F-3 | **Territory map** — account assignment, rep coverage visualization | 2d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-8.1 | Forecasting: by-rep, by-region, by-product, total |
| G-8.2 | Quota: set, track attainment %, forecast attainment |
| G-8.3 | Territory: assign accounts, coverage gap analysis |
| G-8.4 | Dashboard refreshes < 500ms p95 |

---

**Engineering OS**: ✅ Approved
