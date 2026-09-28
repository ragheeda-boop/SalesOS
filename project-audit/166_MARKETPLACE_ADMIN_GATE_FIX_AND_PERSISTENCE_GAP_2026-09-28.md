# 166 — `domains/marketplace`: the entire plugin REST API required only `verify_token` (any authenticated user, any tenant) for install/uninstall/enable/disable/config; fixed. Its full persistence layer is dead, in-memory-only — documented, not fixed.

**Read-only in scope of production/salesos_test.** Pure unit-level fix (in-process `TestClient`, no database); no database container needed.

## 1. Scope

Continuing the `domains/` sweep. `domains/marketplace` (1,287 lines: `db_models.py`, `registry.py`, `manifest_schema.py`, `sandbox.py`, `lifecycle.py`, `router.py`, `plugins/slack.py`, `plugins/salesforce.py`).

## 2. The severe finding — router-level authorization gap

`domains/marketplace/router.py` mounts a full plugin-management REST API at `/api/v1/marketplace` — `GET`/list, `GET {id}`, `POST install`, `POST {id}/uninstall`, `POST {id}/enable`, `POST {id}/disable`, `GET {id}/history`, `POST {id}/config`, `GET {id}/config`, `POST {id}/permissions/approve`, `DELETE {id}/permissions/{permission}`, `GET {id}/permissions` — 12 endpoints total, gated at the router level by a single `dependencies=[Depends(verify_token)]`: **any authenticated user, regardless of role, could install, uninstall, enable, disable, or reconfigure any plugin.**

This is materially worse than an ordinary per-tenant authorization gap: `_get_registry()`/`_get_permission_gate()` cache a **single, process-wide** `PluginRegistry`/`PermissionGate` on `app.state` (confirmed in report 153 as a legitimate lazy-singleton pattern for *that* mechanism — but that report did not examine this router's authorization level). Neither `PluginModel`/`PluginLifecycleEventModel` (the DB schema) nor `PluginRegistry`/`PluginLifecycle`/`PermissionGate` (the actual live logic) carry a `tenant_id` anywhere. Every real caller of every one of these 12 endpoints operates on the exact same, undifferentiated, platform-wide plugin state — a regular, non-admin user of any single tenant could install or uninstall plugins on behalf of every other tenant on the same deployment.

## 3. Fix — matches an already-ratified precedent for the identical shape of gap

DEC-159 (report 115) already ruled on this exact pattern for `/api/v1/cache/*`: a broad-blast-radius, effectively-platform-wide admin API gated by mere authentication rather than a role check, tightened to `require_role_dep("admin")` at the router level — "matches the existing pattern already used by `metrics.py`/`benchmarks.py`." Confirmed the identical mechanism is used there (`APIRouter(..., dependencies=[Depends(require_role_dep("admin"))])`) and applied the same fix here: `verify_token` → `require_role_dep("admin")` at the router's single, shared dependency list, uniformly gating all 12 endpoints (matching DEC-159's own choice not to split reads from writes).

**Deliberately not resolved**: whether "admin" here should mean the caller's own tenant's admin (`require_role_dep`, what was applied) or a true platform-wide owner (`require_owner_role_dep`, used elsewhere for genuinely platform-scoped operations like the billing tables in DEC-158/report 106) depends on whether plugin management is *intended* to be a platform-wide, single-operator feature or an unfinished, should-have-been-tenant-scoped one — a real product question this session does not resolve unilaterally. Either interpretation agrees that a non-admin end user having this power was wrong, which is the narrow, unambiguous improvement made here.

## 4. The persistence architecture gap — documented, not fixed

Confirmed `PluginModel`/`PluginLifecycleEventModel` (`db_models.py`) have **zero references anywhere in the codebase outside their own definition file** — fully dead ORM models with real migrations behind them, never queried or written to. The actual live logic (`PluginRegistry`, `PluginLifecycle`, `PermissionGate` — all confirmed live via the router) is **100% in-memory** (plain Python dicts). Every installed plugin, its lifecycle history, and its approved permissions are lost on every process restart and are not shared across replicas in a multi-worker deployment.

Matches this session's established "genuine architecture gap requiring a product decision, not a narrow code bug" pattern (reports 130/157): wiring the existing dead tables up would require deciding real design questions this session should not answer unilaterally — should plugin state be tenant-scoped at all (the schema currently has no `tenant_id` column to support that), what are the transactional semantics for lifecycle-event logging alongside plugin state changes, and is the in-memory design perhaps intentional (e.g., for a not-yet-launched or single-operator-managed feature)? Documented here for a deliberate decision, not resolved.

## 5. `WidgetSandbox`/`BackendPluginSandbox` — dead code, not touched

`grep -rln "WidgetSandbox\|render_widget\|BackendPluginSandbox"` (excluding the module itself): only the module's own test file. Zero live callers anywhere. `render_widget()`'s raw embedding of `plugin_code` into a `<script>` block is inherent to its sandboxing design (isolation via CSP `script-src 'self'`/`connect-src 'none'`/`frame-src 'none'` plus `postMessage`, not string-escaping — plugin code is meant to execute), not a narrow bug to fix; whether the overall sandbox design is sufficiently robust is a broader security-architecture question out of scope for a single dead-code review, and not pursued further here.

## 6. Verification — genuine red→green

New `tests/unit/test_marketplace_router_admin_gate.py` (3 tests, following the exact established pattern from report 115's `test_cache_admin_router.py`): a non-admin (`"user"`) role is rejected with 403 on every one of the 8 sampled endpoints; a `"manager"` role is also rejected (admin-only, not merely elevated); an admin role can genuinely install a plugin and see it in the list (proving the gate doesn't just fail-closed everything).

Scoped `git stash push -- salesos/backend/domains/marketplace/router.py` (reverting only the fix): all 3 tests failed — the reverted router requires only `verify_token`, so the test harness's real-JWT-free `TestClient` calls return 401 (no token supplied) rather than passing through to the vulnerable behavior directly, but this still proves the tests genuinely depend on the fix being present (they cannot pass against the unfixed router by any path). `git stash pop` restored the fix; all 3 re-confirmed PASS.

## 7. Regression

New test file: 3/3 PASS. Ruff (`--select E4,E7,E9,F,I`): 0 findings on both files. `python -m py_compile` and `git diff --check`: clean. No pre-existing test file for this router existed to regress.

## 8. Scope and safety

- Two files touched: `salesos/backend/domains/marketplace/router.py` (fix + explanatory comment), `salesos/backend/tests/unit/test_marketplace_router_admin_gate.py` (new).
- No database or container needed — the fix and its verification are both pure in-process HTTP-level checks.
- No production/`salesos_test` write. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted. The persistence/tenant-scoping architecture gap is explicitly left open for a deliberate product decision, not resolved unilaterally.

## 9. Loop status

Continuing the standing 24-hour continuous-loop authorization. Remaining `domains/` candidates: `domains/ai`, `domains/copilot`, `domains/rag` (`domains/ubom` deferred, explicitly marked DEPRECATED).
