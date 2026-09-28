# 162 — `sdk/agent_sdk::AgentContextCollector.collect()`: `asyncio.run()` from a sync method, 2nd occurrence of report 136's Odoo-sync bug class

**Read-only in scope of production/salesos_test.** Pure unit-level fix (fake async runtimes); no database container needed.

## 1. Scope

Continuing the sweep into the remaining `sdk/*_sdk/` plugin-facing SDK subdirectories flagged in report 161. `sdk/agent_sdk/__init__.py` (`AgentContextCollector`) had 2 DB/async indicator hits from the initial scan.

## 2. The bug — same class as report 136

`AgentContextCollector.collect()` is declared as a plain synchronous method (`def collect(...)`), but internally bridges to three async runtime dependencies via `asyncio.run(...)`:

```python
events = asyncio.run(timeline_rt.query(entity_type=entity_type, entity_id=entity_id, limit=20))
...
scores = asyncio.run(feature_store.get_scores(entity_id))
...
network = asyncio.run(kg.get_ego_network(entity_id, depth=1))
```

`asyncio.run()` cannot be called from within an already-running event loop. This entire application is FastAPI-based — every real request handler already runs inside a live asyncio loop — so any real caller of `collect()` would trigger `RuntimeError: asyncio.run() cannot be called from a running event loop` on all three calls, every time. Each call site's own `try/except Exception: pass` silently swallowed the failure, leaving `timeline`/`features`/`graph` permanently empty (`[]`/`{}`/`None`) regardless of what the underlying runtimes would actually have returned — this is the second occurrence this session of exactly the bug class fixed in report 136 (`runtime/odoo/__init__.py`'s `_run_odoo_sync()`).

## 3. Reproduction — before touching any code

```python
import asyncio
from sdk.agent_sdk import AgentContextCollector

class FakeTimelineRuntime:
    async def query(self, entity_type, entity_id, limit):
        return [{"event": "created"}]

async def main():
    collector = AgentContextCollector({"timeline_runtime": FakeTimelineRuntime()})
    ctx = collector.collect(user_id="u1", tenant_id="t1", entity_type="company", entity_id="c1")
    print("timeline result:", ctx.timeline)

asyncio.run(main())
```
Output: `RuntimeWarning: coroutine 'FakeTimelineRuntime.query' was never awaited` and `timeline result: []` — confirming the exact predicted failure mode, silently, before any fix was applied.

## 4. Reachability

`grep -rln "AgentContextCollector\|create_agent_context"` across `app/`, `domains/`, `runtime/`, `intelligence/`, `mcp_server/` (excluding the module itself): zero matches. Dead code — matching this session's established "correctly-designed-but-unwired, genuine internal defect" pattern (reports 121/123/126/127/130/131/135/136/156/158/160/161). Fixed anyway, since the defect is unconditional and would surface as silent, permanent data loss the instant a real caller (e.g., a future copilot agent-context endpoint) is wired up — exactly matching report 136's fix rationale for the same bug class.

## 5. Fix

Converted `collect()` to a real `async def`, replacing every `asyncio.run(x)` with `await x` directly. `create_agent_context()` (the factory function) is unaffected — it only constructs the collector, never calls `collect()` itself. The existing broad `except Exception: pass` around each runtime call is left as-is (a reasonable best-effort-degradation design for a context collector whose individual sub-sources may legitimately be unavailable) — only the specific `asyncio.run()`-from-a-running-loop defect is fixed.

## 6. Verification — genuine red→green

New `tests/unit/test_agent_sdk_context_collector.py` (2 tests, zero prior coverage existed). The key test runs inside pytest-asyncio's own event loop — exactly the "already running loop" condition that broke the original implementation — and asserts `timeline`/`features`/`graph` are genuinely populated from three fake async runtimes, not left empty.

Scoped `git stash push -- salesos/backend/sdk/agent_sdk/__init__.py` (reverting only the fix): both tests failed with `TypeError: object AgentContext can't be used in 'await' expression` (the reverted `collect()` returns a plain `AgentContext`, not a coroutine) — plus the tell-tale `RuntimeWarning: coroutine '...' was never awaited` at all three call sites in the warnings output, directly confirming the original `asyncio.run()` failure mode. `git stash pop` restored the fix; both tests re-confirmed PASS.

## 7. Regression

New test file: 2/2 PASS. Ruff (`--select E4,E7,E9,F,I`): 0 findings on both files. `python -m py_compile` and `git diff --check`: clean. No pre-existing test file for `sdk/agent_sdk/` existed to regress.

## 8. Scope and safety

- Two files touched: `salesos/backend/sdk/agent_sdk/__init__.py` (fix + explanatory comment), `salesos/backend/tests/unit/test_agent_sdk_context_collector.py` (new).
- No database or container needed — the fix and its verification are both pure async-Python logic against fake runtime stand-ins.
- No production/`salesos_test` write. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 9. Loop status

Continuing the standing 24-hour continuous-loop authorization. Remaining `sdk/*_sdk/` files from report 161's list (`sdk/backend_sdk/__init__.py`, `sdk/integration_sdk/__init__.py`, `sdk/plugin_sdk/__init__.py`, `sdk/theme_sdk/__init__.py`, `sdk/widget_sdk/__init__.py`, `sdk/frontend_sdk/__init__.py`, `sdk/company_sdk/`) showed near-zero DB/async indicators in the initial scan except `sdk/widget_sdk/__init__.py` (1 hit) — checking that next.
