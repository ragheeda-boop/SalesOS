# 129 — run_initial_sync(): the same GUC-pinning bug report 84 fixed, in a separate live call path (the real OAuth callback)

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container (`sweep-pg9`) migrated to head `f2e3d4c5b6a7`, torn down after use. No write to `salesos_test` or production.

## 1. Reachability — live, and more directly reachable than report 84's finding

`app/modules/communication_hub/initial_sync.py::run_initial_sync()` is fired by `schedule_initial_sync()`, called directly from `app/modules/communication_hub/router.py`'s real, mounted Google OAuth callback route (`GET .../oauth/callback` region, confirmed via source read at `router.py:117-119`) immediately after a user completes Google OAuth connect. Unlike report 84's `tasks.py` Celery tasks — explicitly disclosed there as "code-ready but not currently executed... no worker service provisioned" — this code path requires no worker at all; it fires as a fire-and-forget `asyncio` task on the same event loop as the request that just handled the OAuth callback.

## 2. Bug — same root cause as report 84, missed because it lives in a different file

`google_accounts` has RLS + FORCE RLS. `GmailSyncService.sync()`/`CalendarSyncService.sync()`'s first call is `self.repo.get_by_user(self.tenant_id, self.user_id)`. Neither `GmailSyncService` nor `CalendarSyncService` pins the tenant GUC internally — report 84 already established this: the pin is applied only at the *call site*, inside `tasks.py`'s per-account loop. `run_initial_sync()` constructs both services directly against a bare `async_session()`, with no pin anywhere — a separate, unaudited call path into the exact same two service classes report 84 already fixed one caller of.

Confirmed directly: under an unpinned session against the restricted `salesos_app` role, `get_by_user()` for a real, just-created account returns `None` regardless of the account genuinely existing — `sync()` raises `GmailSyncError`/`CalendarSyncError` ("No active Google account connected"), caught by `run_initial_sync()`'s own broad `except (GmailSyncError, Exception)`, logged as `initial_sync.gmail.failed`/`initial_sync.calendar.failed`, and silently appended to `results["errors"]`. The OAuth redirect still succeeds (by this module's own design — "Failures are logged; they never fail the OAuth redirect") but the promised behavior in the file's own docstring — "Emp360/Comm Hub populate without a manual Sync click" — has never worked for any real user completing this flow, on the very same account the same request just connected.

**Fix**: `apply_tenant_guc(db, str(tenant_id))` added immediately after opening each of the two fresh sessions, before constructing the corresponding sync service — matching `tasks.py`'s established pattern exactly.

## 3. A significant environment-methodology correction, disclosed in full

While building the verification container for this finding, the first attempt (`docker run ... pgvector/pgvector:pg16` connected as `postgres:postgres`) produced a test that passed **even with the fix reverted** — a false green. Investigating directly (per this session's standing discipline of never accepting an unexplained result) found the root cause: `postgres` is a Postgres **superuser**, which unconditionally bypasses RLS regardless of `FORCE ROW LEVEL SECURITY` — confirmed by re-running report 84's own, previously-established test file against the same connection, which **also failed** for the same reason (`assert account is None` → found a real `GoogleAccount` object instead).

The correct setup, used throughout this session's *other* prior verifications but skipped when standing up this session's two newest containers (`sweep-pg8`, `sweep-pg9`), is to additionally apply `infra/docker/postgres/init/02-app-role.sql` (creates the restricted, `NOSUPERUSER NOBYPASSRLS` role `salesos_app`) and connect the actual test run as `salesos_app`, not the bootstrap superuser. Applied via `docker exec -i sweep-pg9 psql -U postgres -d salesos_test < 02-app-role.sql`, then reconnected as `salesos_app:salesos_app_dev_password` — report 84's test immediately passed correctly, and this report's new test correctly failed with the fix reverted and passed once restored.

This does **not** invalidate this session's earlier fixes in the same segment (Contract/Forecast/Decision/Recommendation, reports 123/125-127): those bugs are pure Python `AttributeError`/`TypeError`s from domain/DB-model field mismatches, which fire identically regardless of which Postgres role executes the underlying query — RLS enforcement was never the mechanism under test there. It matters only for bugs whose entire premise is row-visibility under RLS, which this finding is, and which several of this session's earlier reports (68-93 range) already were — those used the correct role-switch discipline throughout (confirmed by their own report text explicitly naming "the restricted, non-superuser, non-BYPASSRLS role"). Flagging this explicitly as a one-off setup gap on this segment's two newest containers, now corrected, rather than silently fixing it without disclosure.

## 4. Verification — genuine red→green, using the corrected setup

New `tests/integration/test_initial_sync_guc_db.py` (1 test) seeds a real account, patches only `_ensure_provider` on both service classes to raise a distinguishable marker exception (avoiding any need for real Google API access), and asserts `run_initial_sync()`'s `errors` list contains the marker text — proving `get_by_user()` found the real account and execution advanced past the lookup — rather than the pre-fix "No active Google account connected" message.

Reverting exactly the fixed file (scoped `git stash push -- app/modules/communication_hub/initial_sync.py`), reconnected as `salesos_app`: `['gmail: No active Google account connected', 'calendar: No active Google account connected']` — the exact predicted failure. Restored: test PASSES.

Regression (all reconnected as `salesos_app`): this new test + report 84's own 2-test file + the existing 3 mocked unit tests in `app/modules/communication_hub/tests/test_initial_sync.py`: **6/6 PASS**. Ruff (`E4,E7,E9,F,I`) on both changed files: 0 findings. `compileall` and `git diff --check` clean.

## 5. Scope and safety

- Files changed: `salesos/backend/app/modules/communication_hub/initial_sync.py` (2 `apply_tenant_guc` calls added), `salesos/backend/tests/integration/test_initial_sync_guc_db.py` (new).
- `salesos_test` and production: untouched. Only the disposable container was written to.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. With `postgres_repositories.py` fully swept (report 128), this session has moved to Phase 2 of the roadmap: broad triage outside that one file, starting with the SQL EXPLAIN sweep tool (report 98) re-run — which surfaced only one finding, a documented tool limitation (an `expanding=True` bind, not a real bug) — followed by a targeted GUC/RLS-pinning audit across every non-test file that opens its own `async_session()` directly (the exact technique that found this report's bug, and the majority of reports 68-93's findings). Remaining candidates from that grep, not yet checked: `app/modules/relationships/store.py`, `domains/commercial/quote/engine/service.py`, `runtime/agent_runtime/dispatcher.py`, `runtime/agent_runtime/tasks.py`, `app/modules/signal_actions/hitl_router.py`, `app/modules/signal_actions/router.py`.
