# 151 — Report 135's NBA fix was never actually reachable: `app.state.nba_engine` was never wired, matching report 148's exact defect shape

**Ephemeral, disposable Postgres container only (`sweep-pg20`, `pgvector/pgvector:pg16`, destroyed after use).** No `salesos_test` or production contact.

## 1. Method — the complementary direction of reports 148/150

Report 150 checked "every `app.state.X` *assigned* in the boot module — is it ever read?" and found nothing further wrong. This report checks the complementary direction: "every `app.state.X` *read* anywhere in the live application — is it ever assigned?" Extracted every distinct attribute read via `getattr(request.app.state, "X", ...)` or `app.state.X` across `app/routers/`, `app/modules/`, `domains/`, and `runtime/`, and diffed against the 39-attribute assignment list already compiled in report 150. Three attributes were read but never appeared in that assignment list: `nba_engine`, `timeline_service`, `workflow_service`.

## 2. `nba_engine` — the real finding: report 135's fix was never reachable

`app.state.nba_engine` is read in 3 places: `app/application/dashboard/router.py:176` and, critically, `runtime/nba_engine/api/router.py:81,104` — the live, mounted `GET /opportunities/{id}/nba` and `POST /opportunities/{id}/nba/refresh` endpoints. **These are the exact same endpoints report 135 fixed 3 internal `NBAEngine` bugs in** (missing GUC pinning, a nonexistent `activity_records.description` column, unserialized JSON in `_cache_result()`).

Confirmed via repo-wide grep for `app.state.nba_engine\s*=`: **zero matches anywhere in the codebase.** `NBAEngine` has exactly 2 construction sites — `mcp_server/salesos_client.py` (an unrelated standalone MCP client script, not part of the FastAPI boot sequence) and `runtime/nba_engine/subscribers/register_subscribers()` (itself never called from anywhere in the live app either, confirmed via a second grep). Neither ever touches `app.state`.

Both router endpoints begin with `engine = getattr(request.app.state, "nba_engine", None); if not engine: raise HTTPException(503, "NBA Engine not initialized")`. **This means every single real call to the NBA REST API has always returned 503 — before ever reaching the code report 135 fixed.** Report 135's own reachability claim ("Live, most severe finding this session — the router is mounted at boot") was correct about the router being mounted, but the report verified `NBAEngine`'s internal correctness through direct instantiation in its own tests, not through the actual `app.state`-mediated path the router uses — so this separate, prerequisite wiring gap went unnoticed at the time.

## 3. `timeline_service` and `workflow_service` — checked, genuinely unreached, lower priority

- **`timeline_service`**: read once, in `domains/timeline/router.py:39`. Zero assignments anywhere. However: `domains/timeline/router.py` itself is not registered in `app/boot/routers.py` (confirmed via grep) — the live timeline surface is `runtime/timeline_runtime`, wired separately (`app.state.timeline_runtime`, already confirmed correct). This is dead code behind a dead router, not a live-reachable defect; not fixed here.
- **`workflow_service`**: read once, in `domains/employee/router.py:54`, as an optional constructor argument (`workflow_service=getattr(request.app.state, "workflow_service", None)`) to a class that has other, non-optional real dependencies. Needs a closer read of `domains/employee/router.py`'s surrounding context to determine live reachability and whether the `None` default degrades gracefully or breaks a real employee-domain feature; deferred to a follow-up given this report's primary finding (`nba_engine`) is the higher-severity, confirmed-live one.

## 4. Fix

Added `_init_nba_engine()` to `app/boot/startup.py`, in Phase 3 ("Decision pipeline") alongside `_init_policy_engine`/`_init_recommendation_engine` — Phase 3 begins only after Phase 1 and Phase 2 fully complete (both `await asyncio.gather(...)` blocks, not fire-and-forget), guaranteeing `app.state.feature_store` and `app.state.event_runtime` (both set in Phase 1/2) are available before `NBAEngine` is constructed:

```python
async def _init_nba_engine(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.nba_engine import NBAEngine
    try:
        feature_store = getattr(app.state, "feature_store", None)
        event_runtime = getattr(app.state, "event_runtime", None)
        engine = NBAEngine(
            session_factory=async_session,
            feature_store=feature_store,
            event_runtime=event_runtime,
            logger=logger,
        )
        app.state.nba_engine = engine
        logger.info("  nba engine: ok")
    except Exception:
        logger.exception("  nba engine init failed")
```

**Deliberately not fixed**: the separate event-subscriber wiring gap (`register_subscribers()` in `runtime/nba_engine/subscribers/__init__.py`, which enables background auto-recomputation when an `opportunity.*` event fires) is a distinct feature (proactive background recompute vs. this fix's on-demand REST path) with its own separate never-called status — the on-demand REST API this fix restores does not depend on it. Documented, not fixed, matching this session's established practice for genuinely separate, additional gaps found alongside a primary fix (e.g., report 130's communication_hub enumeration gap).

## 5. Verification — genuine red→green

New `tests/integration/test_nba_engine_wiring_db.py` (2 tests) against a fresh, disposable, fully-migrated, RLS-enforced Postgres container:

- `test_init_nba_engine_wires_a_real_working_engine`: calls `_init_nba_engine()` directly against a bare `SimpleNamespace` stand-in for the app, confirms `nba_engine` is set and is a real `NBAEngine` instance.
- `test_router_lookup_pattern_finds_the_wired_engine_and_computes_a_real_nba`: reproduces the router's *exact* `getattr(request.app.state, "nba_engine", None)` lookup, then calls `engine.get_or_compute()` — the same call the live `GET /opportunities/{id}/nba` endpoint makes — against a genuinely seeded opportunity, proving the full path now works end to end (correctly exercising report 135's earlier internal fixes for the first time through this wiring).

Reverting exactly `app/boot/startup.py` (scoped `git stash`): `ImportError: cannot import name '_init_nba_engine' from 'app.boot.startup'` — the exact predicted failure (the function didn't exist before this fix). Restored: both PASS.

Regression: combined with report 135's existing `test_nba_engine_rls_db.py` (3 tests): **5/5 PASS**, no change to any existing behavior. Ruff (`E4,E7,E9,F,I`): 4 pre-existing import-sort findings on `startup.py`, identical count before/after (confirmed via scoped stash/pop, just shifted line numbers) — 0 new; the new test file is Ruff-clean. `compileall` and `git diff --check` clean.

## 6. Scope and safety

- Files changed: `salesos/backend/app/boot/startup.py` (new `_init_nba_engine()` function + Phase 3 registration), `salesos/backend/tests/integration/test_nba_engine_wiring_db.py` (new).
- One disposable, ephemeral Postgres container (`sweep-pg20`) used for verification; destroyed after (`docker rm -f`). No `salesos_test` or production contact.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.
- Noted, not touched: a parallel local session made 3 commits (`445e40a8`, `4b315615`, `546e2602`, all `fix(tests): ...`) to `conftest.py`/`tests/integration/conftest.py`/`test_rls_policy_generation.py` during this investigation — confirmed via `git diff --stat` to touch entirely disjoint files from this fix, no conflict.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization. This is the second time this session a feature previously "fixed" at the component level (report 135's internal `NBAEngine` bugs) turned out to have a separate, prerequisite wiring gap making the fix unreachable in practice (the first being report 148's Approval Service) — suggesting this specific failure mode (component correctly built and tested in isolation, but never actually connected to `app.state`) may be worth one more targeted pass across any remaining `runtime/*_engine`/`*_runtime` classes with a REST router that reads `app.state.X`. Next: investigate `workflow_service` (§3 above) for the same shape.
