# Work Order WO-1701 — Phase 17: Production Hardening

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: All preceding phases (0-16)
> **Priority**: P0

---

## Scope

Final production hardening: pagination compliance, test coverage, contract tests, performance, docs, security, debt.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Pagination compliance scan** — verify all list endpoints use keyset cursor | 1d |
| B-2 | **AI test coverage** — add tests to reach ≥ 85% on intelligence module | 2d |
| B-3 | **Contract tests** — provider tests for all API endpoints | 3d |
| B-4 | **Security sweep** — dependency audit, config audit, pentest | 2d |
| B-5 | **Technical debt review** — resolve P0/P1 items or defer with ADR | 1d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Consumer contract tests** — test API client functions against expected responses | 2d |
| F-2 | **Performance optimization** — lazy loading, code splitting, bundle analysis | 2d |
| F-3 | **Documentation** — API docs, user guide updates | 1d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-17.1 | 100% list endpoints use keyset pagination |
| G-17.2 | AI test coverage ≥ 85% |
| G-17.3 | Provider + consumer contract tests for all endpoints |
| G-17.4 | All endpoints within perf budget at 100k+ scale |
| G-17.5 | Documentation coverage complete |
| G-17.6 | Security: 0 critical, 0 high findings |
| G-17.7 | Tech debt: 0 P0, 0 P1 items |
| G-17.8 | Total tests ≥ 3,000 |

---

**Engineering OS**: ✅ Approved
