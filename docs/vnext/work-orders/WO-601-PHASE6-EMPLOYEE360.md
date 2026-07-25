# Work Order WO-601 — Phase 6: Employee360

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 5 ✅
> **Priority**: P1

---

## Scope

Complete Employee360 view: unified profile, signals, scoring, activity timeline, performance insights.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Employee360 aggregation endpoint** — `GET /employees/{id}/360` combining profile + signals + scoring + timeline + performance | 2d |
| B-2 | **Employee timeline filter API** — `GET /employees/{id}/timeline?source=&type=&from=&to=&cursor=` | 1d |
| B-3 | **Performance insights** — trend analysis (score over time), peer comparison (vs department avg), risk flags (declining signals, low engagement) | 2d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Employee360 page** — 5 tabs: Overview, Signals, Scoring, Timeline, Performance | 2d |
| F-2 | **Overview tab** — profile card, quick stats (signals, score, tenure), recent activity feed | 1d |
| F-3 | **Timeline tab** — infinite scroll timeline with source/type filters, keyset cursor | 1.5d |
| F-4 | **Performance tab** — trend chart, peer comparison bar, risk flag badges | 1.5d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-6.1 | Employee360 shows: profile, signals, scoring, timeline, performance |
| G-6.2 | Timeline loads < 200ms p95 |
| G-6.3 | Performance includes: trend analysis, peer comparison, risk flags |

---

**Engineering OS**: ✅ Approved
