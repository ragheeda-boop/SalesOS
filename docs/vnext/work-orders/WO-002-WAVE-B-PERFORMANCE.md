# Work Order WO-002 — Wave B: Backend Performance

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: WO-001 (Security) — ✅ Closed
> **Priority**: P0 — Critical

---

## Wave ID

WO-002 / WAVE-B

## Objective

Fix critical backend performance issues that block HTTP load testing, cause N+1 query degradation, and leave list endpoints unbounded. Wave B must be complete before AI or Frontend work can proceed.

## Scope

Strictly limited to backend performance fixes:

1. **PERF-01** — BodyCache middleware: buffer and restore request body (fixes POST body consumption bug)
2. **PERF-02** — N+1 workspace loop at `commercial.py:470-488`
3. **PERF-03** — N+1 NBA feed (find current location; Sprint 0 verification shows it may be at `runtime/nba_engine/api/`)
4. **PERF-04** — Pagination: add keyset/cursor pagination to remaining unbounded list endpoints
5. **PERF-08** — `search_by_filters` double-query pattern
6. **PERF-10** — Remove `print()` in `metrics.py:18`

## Assigned Engineer

`backend-engineer`

## Assigned Reviewer

`performance-reviewer`

## Expected Deliverables

| Deliverable | Description |
|-------------|-------------|
| BodyCache middleware | New middleware that reads request body once and caches it; all middlewares and handlers read cached copy |
| N+1 workspace fix | Workspace listing runs in O(1) queries |
| N+1 NBA fix | NBA recommendation feed runs in O(1) queries |
| Pagination on 4 endpoints | benchmarks, demo scenarios, RAG documents, pipelines |
| `search_by_filters` fix | Single query using `COUNT(*) OVER()` window function |
| `print()` removed | `metrics.py:18` uses structured logging instead |
| `SPRINT0_WAVE_B1_REPORT.md` | Final report documenting all changes |

## Quality Gates

| Gate | Criteria |
|------|----------|
| G-B.1 | POST endpoints receive intact request body (BodyCache verified) |
| G-B.2 | Workspace listing produces O(1) database queries (not O(N)) |
| G-B.3 | NBA feed produces O(1) database queries (not O(N)) |
| G-B.4 | 4 unbounded endpoints now use keyset/cursor pagination |
| G-B.5 | `search_by_filters` executes 1 query instead of 2 |
| G-B.6 | No `print()` in production code |
| G-B.7 | All existing tests pass |
| G-B.8 | Performance reviewer approves all changes |

## Stop Condition

Wave B is complete when:

- All deliverables are produced
- Quality gates G-B.1 through G-B.8 pass
- Performance reviewer approves
- `SPRINT0_WAVE_B1_REPORT.md` filed in `docs/vnext/reports/`
- This work order is marked **Closed** by Engineering OS

## Constraints

- Do NOT touch Agent Runtime
- Do NOT touch frontend code
- Do NOT implement new features beyond the listed fixes
- Do NOT refactor architecture (no splitting api.ts, main.py — that is Phase 2 scope)
- All fixes must maintain backward compatibility

## Dependencies

WO-001 (Security) — ✅ Closed. Wave A security fixes are in place.

---

**Engineering OS Authorization**: ✅ Approved
