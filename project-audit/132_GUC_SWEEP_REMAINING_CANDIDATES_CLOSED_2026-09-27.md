# 132 — GUC/RLS-pinning sweep: remaining 3 candidates closed clean; methodology retired for this pass

**Read-only.** Verification by direct source inspection; no container needed for these three.

## 1. `app/main.py` (4 `async_session()` sites) — clean

All four are pure health/diagnostics endpoints: three run `SELECT 1` to check DB connectivity, one reads `alembic_version.version_num` (a schema-metadata table, not tenant-scoped). None touch a FORCE-RLS table. No GUC pin needed.

## 2. `app/startup.py` — confirmed entirely dead code

Grep for `from app.startup import` / `from app import startup` / `import app.startup` across the whole repository: **zero matches**. This top-level file is never imported anywhere — the actual, live boot module is the separate `app/boot/startup.py`. A related observation, documented but not acted on: both files independently set `app.state.opportunity_service` and `app.state.timeline_recorder`, but grep for `.opportunity_service` across the entire codebase finds only these two write sites — nothing anywhere reads it. This looks like unused app-state wiring in the live boot file too, not something this report fixes (no observable behavior depends on it, so there is nothing to prove red→green against).

## 3. `app/modules/signal_marketplace/seeding.py` — clean

Writes only to `signal_catalog`, classified `GLOBAL_PLATFORM` per report 26 (no `tenant_id` column, no RLS policy) — confirmed still accurate. No pin needed.

## 4. Scope and safety

No files changed. No container used. No commit content beyond this report and its AGENTS.md entry.

## 5. Loop status

This closes report 131's remaining candidate list from the original `async_session()` grep — every file that grep surfaced (report 129: `initial_sync.py`; report 130: `app/graphql/{query,mutation}.py`; report 131: `app/tasks.py`; this report: the 3 low-priority remainders) has now been checked. Continuing the standing 24-hour continuous-loop authorization by pivoting methodology: re-running the SQL EXPLAIN sweep tool (report 98) against the current source tree, which has grown substantially since that report (fact ledger, provider spend, Agent Reach, and other modules added across reports 99-131) and may surface new static-SQL candidates the original sweep predates.
