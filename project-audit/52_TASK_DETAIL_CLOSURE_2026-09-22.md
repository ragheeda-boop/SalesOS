# Task Detail Closure — 2026-09-22

## Scope

Closed a V3 Revenue Execution gap. The task-detail page read the full task list
and searched it locally because the backend had no `GET /tasks/{id}` endpoint.
This could produce a false “not found” result when the needed row was not in a
returned list and made the details page depend on list behavior.

## Implementation

- Added `RevenueService.get_task(task_id, tenant_id)` with both values in its
  database predicate.
- Added authenticated, permission-gated `GET /api/v1/tasks/{task_id}` which
  returns 404 when no task belongs to the current tenant.
- Added `due_date` to the task response contract and reads so the detail page
  can display it consistently.
- Added `getTask()` to the typed frontend API client.
- Changed `/v3/tasks/[id]` to fetch its task directly under a detail query key;
  the page no longer downloads the list as a detail lookup workaround.
- Updated the source-level frontend test for the direct request. It remains
  unexecuted because the local frontend dependency tree is unavailable.

## Verification

An isolated temporary PostgreSQL 16 database was migrated through current head
and removed after the test. No shared test or production database was changed.

1. `tests/unit/test_revenue_service.py`: **22/22 PASS**.
2. `tests/integration/test_revenue_task_detail_rls.py`: **1/1 PASS** with a
   non-superuser runtime role. The owning tenant reads its row; another tenant
   and a session with no tenant scope get no row.
3. Python compilation passed for the changed service, router, schema, and test.
4. Route registration inspection confirmed `GET /api/v1/tasks/{task_id}`.

## Roadmap effect

This closes one code-scope Revenue Execution capability: direct, tenant-scoped
task detail. The capability census moves from **87/113 to 88/113 = 77.9%**.
Phase 7 and Production GO remain unchanged.
