# 136 — runtime/odoo: 3 independent, stacked bugs — the scheduled Odoo sync has never once run successfully

**Read-only in scope of production/salesos_test.** Pure unit tests with mocked I/O; no database container needed for this fix.

## 1. Reachability — live, scheduled in Celery Beat

`odoo_sync_all` (a `@shared_task`) is registered in `app/celery_schedule.py`'s beat schedule — intended to run automatically once a Celery worker/beat process is provisioned, same category as report 130's communication_hub tasks ("code-ready, worker not yet wired") but on the CORRECT wiring path this time, not dead code. `runtime/odoo/__init__.py` had **zero prior test coverage** — confirmed by grepping every existing `test_odoo_*.py` file (7 of them) for any reference to `runtime.odoo`, `OdooJsonRpcClient`, or `OdooSyncService`: none found. Those existing tests cover a separate Odoo translation/ACL layer, not this sync orchestration module.

## 2. Bug 1 (would fire first, outermost) — `settings` was never imported

`odoo_sync_all()`'s very first executable line, `if not settings.odoo_url:`, and `_run_odoo_sync()`'s `OdooConfig(url=settings.odoo_url, ...)` all reference a name that does not exist anywhere in this module's namespace — confirmed directly (`hasattr(module, "settings")` → `False`) and independently by Ruff (`F821 Undefined name 'settings'`, 5 occurrences). `odoo_sync_all()` would raise `NameError` on its very first line, before any of the logic below it ever executes. **Fixed**: `from app.config import settings` added at module level (confirmed zero circular-import risk — `app.config` imports only `pydantic`/`pydantic_settings`).

## 3. Bug 2 (masks bug 3 entirely, fires second) — nested `asyncio.run()`

`_run_odoo_sync()` was a plain `def` that called `asyncio.run(_sync())` internally to bridge into async code — a correct pattern for a top-level entry point. But its **sole caller**, `odoo_sync_all()`'s own `_run()` coroutine, is *already running inside an event loop* via the outer `asyncio.run(_run())`. Calling `asyncio.run()` from within a running loop raises `RuntimeError: asyncio.run() cannot be called from a running event loop` — reproduced first in complete isolation (a minimal 2-function repro) before attributing it to this file, then confirmed live in the actual code. This fires on every real per-tenant sync attempt inside `odoo_sync_all()`, independent of bug 1 (once bug 1 is fixed) and ahead of bug 3 (masking it entirely). **Fixed**: `_run_odoo_sync` converted to a real `async def` (confirmed its only caller is this one `_run()` coroutine, and it is not itself a separate `@shared_task` — safe to remove the internal event-loop bridge entirely); the caller now `await`s it directly instead of wrapping it a second time.

## 4. Bug 3 (the deepest, masked by bugs 1 and 2 until they're fixed) — sync methods awaited as if async

`OdooClientProtocol` declares `search_read`/`count`/`read` as `async def`, matching every `OdooSyncService` call site's `await self._client.search_read(...)` (3 sites). `OdooJsonRpcClient`'s actual implementations were plain `def` (blocking `urllib.request` calls) returning real values directly, not coroutines — `await <list>` raises `TypeError: object list can't be used in 'await' expression`. The class's own docstring already documented the correct fix ("Uses requests for synchronous calls; wrap in asyncio.to_thread for async") but it was never actually wired. **Fixed**: the original blocking implementations renamed to `_search_read_sync`/`_count_sync`/`_read_sync`; new `async def search_read`/`count`/`read` wrappers delegate via `asyncio.to_thread`, matching the documented intent exactly. `authenticate()` (called internally from within the now-thread-wrapped methods) stays synchronous — it isn't part of `OdooClientProtocol` and runs correctly inside the executor thread.

## 5. Net effect

All three bugs sit on the single reachable path (`odoo_sync_all` → `_run()` → `_run_odoo_sync()` → `OdooSyncService.run_full_sync()` → `search_read`/`count`/`read`). Before this fix, the scheduled Odoo sync task has never once completed successfully for any tenant, for three independent, stacked reasons, each masking the next.

## 6. Verification — genuine red→green, all three bugs together

New `tests/unit/test_odoo_json_rpc_client_async.py` (4 tests, mocked I/O, no database): `search_read`/`count`/`read` are genuinely awaitable and return the blocking implementation's real result; `_run_odoo_sync()` can be awaited from inside an already-running event loop (reproducing `odoo_sync_all()`'s exact call shape) without raising, using a patched `OdooSyncService.run_full_sync` and a mocked `settings`.

Reverting exactly the fixed file (scoped `git stash push -- runtime/odoo/__init__.py`): all 4 tests fail with the exact predicted errors — `TypeError: object list can't be used in 'await' expression` (bugs 3, ×3 tests) and `AttributeError: <module 'runtime.odoo'>... does not have the attribute 'settings'` (bug 1, confirming the patch itself fails against the unfixed module). Restored: all 4 PASS.

One test-authoring correction made during verification, disclosed: the first mock for `search_read`/`read` returned the same canned value for every call to `_call`, including the *internal* `authenticate()` call, which then failed on `result.get("uid", 0)` since the mocked value was a list, not a dict — a mock-setup gap in the test, not a code bug. Fixed by pre-setting `client._uid` to skip the internal round-trip.

Regression: all 7 pre-existing `test_odoo_*.py` files (unrelated Odoo translation/ACL layer, confirmed unaffected) + the new file: **35/35 PASS**. Ruff (`E4,E7,E9,F,I`) on the fixed file: 12 findings before (including `F821 Undefined name 'settings'` ×5 and `F821 Undefined name 'asyncio'`, independently confirming both critical bugs) → 6 after (all pre-existing import-sort/unused-import style issues) — net improvement of 6, 0 new. `compileall` and `git diff --check` clean.

## 7. Scope and safety

- Files changed: `salesos/backend/runtime/odoo/__init__.py` (module-level `asyncio`/`settings` imports added; `_search_read_sync`/`_count_sync`/`_read_sync` + async wrappers; `_run_odoo_sync` converted to `async def`; caller updated to `await` it), `salesos/backend/tests/unit/test_odoo_json_rpc_client_async.py` (new).
- No database, container, or migration involved. No real Odoo instance or network call made.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. Resuming the mypy triage from report 135's remaining candidate list: `app/modules/facts/{service,apply_service}.py`'s `type[BaseModel]` attribute errors, `runtime/agent_runtime/tasks.py` (a file not yet examined this session, with multiple `Result`/`object` attribute findings), and `app/boot/startup.py`'s `FactoryBoundRepository` type-mismatch findings.
