# 153 — Final exhaustive pass: the `app.state` wiring methodology (reports 148-152) is now conclusively closed

**Read-only in scope of production/salesos_test.** Pure source-code review; no database container needed.

## 1. Scope — widening the reader extraction one more time

Reports 148-152 checked `app.state.X` readers/writers across `app/routers/`, `app/modules/`, `domains/`, `runtime/`. This report widens the same extraction to also include `intelligence/`, `sdk/`, and `mcp_server/`, to be fully exhaustive before closing the methodology. 11 additional candidate attributes surfaced beyond the original 39: `_fs_repo_session`, `company_intelligence_engine`, `marketplace_permission_gate`, `marketplace_registry`, `object_viewer`, `revenue_brain`, `signal_bridge`, `signal_engine`, `signal_marketplace_service`, `signal_task_mapper`, `timeline_repo`.

## 2. Nine of the eleven — a false alarm from dead code referencing itself

`_fs_repo_session`, `company_intelligence_engine`, `object_viewer`, `revenue_brain`, `signal_bridge`, `signal_engine`, `signal_marketplace_service`, `signal_task_mapper`, `timeline_repo` all resolve to exactly one writer each — and in every case, that writer is `app/startup.py` (the file confirmed dead in reports 132/139/140/148: never imported anywhere in the repository). Checking for readers of each **outside** `app/startup.py` returns **zero matches for all nine** — both the write and the apparent "read" my wide grep picked up are internal cross-references within the same dead file (one boot phase's output feeding a later phase, entirely within code nothing ever executes). None of these are live; none require action.

## 3. The remaining two — a different, legitimate pattern, not the report 148/151 bug

`marketplace_registry` and `marketplace_permission_gate` are both assigned in `domains/marketplace/router.py` itself (genuinely live — mounted at `/api/v1/marketplace` per `app/boot/routers.py:248,256`), via a lazy-singleton helper:

```python
def _get_registry():
    from app.main import app
    from domains.marketplace.registry import PluginRegistry
    if not hasattr(app.state, "marketplace_registry"):
        app.state.marketplace_registry = PluginRegistry()
    return app.state.marketplace_registry
```

This is structurally different from report 148's copilot bug (which constructed a **fresh** object on **every** call) and from report 151's NBA bug (which had **no** assignment path at all): here, the object is created **once**, on the first call, via a direct import of the live global `app` singleton (`from app.main import app`) — not through per-request `Request` injection — and every subsequent call reuses the same cached instance from `app.state`. `PluginRegistry()`/`PermissionGate()` take no constructor arguments (pure in-memory state), so this lazy pattern is functionally correct, if unconventional compared to the `_init_*`-at-boot pattern used elsewhere in this codebase. Not a bug.

## 4. Conclusion — the methodology is exhausted

Combined with reports 148-152's earlier findings, every `app.state.X` reference in the live application (across `app/`, `domains/`, `runtime/`, `intelligence/`, `sdk/`, `mcp_server/`) has now been checked in both directions (assigned-but-unread, and read-but-unassigned). Final tally for this entire investigation family:

- **2 real, severe bugs found and fixed**: `approval_service` (report 148), `nba_engine` (report 151) — both "correctly built component, never actually connected to the live app" defects that had gone undetected through unit tests exercising the component in isolation.
- **1 genuine architecture gap documented, not fixed**: `workflow_service` (report 152) — live, silently degraded, and confirmed to require a schema/product decision rather than a code fix.
- **1 dead router confirmed**: `timeline_service`'s reader (`domains/timeline/router.py`, itself unmounted).
- **Everything else**: confirmed clean, either correctly wired, intentional keep-alive handles, harmless redundant storage, dead-code self-reference, or a legitimate alternate wiring pattern.

No further candidates remain under this methodology.

## 5. Scope and safety

- No files changed. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes the `app.state` wiring investigation (reports 148-153) as fully exhaustive. Pivoting to a fresh methodology for the next tick.
