# 149 — Sweep for report 148's exact anti-pattern: no further live occurrences found

**Read-only in scope of production/salesos_test.** Pure source-code review; no database container needed.

## 1. Scope

Following report 148's fix (the copilot's Recommend-mode HITL gate constructing a fresh, disposable `InMemoryApprovalRepository()` on every single call instead of using the real, shared, persistent service): grepped every `InMemory*Repository(` construction across `app/routers/` and `app/modules/` to check for further live instances of the same shape (a per-request handler silently falling back to a throwaway in-memory store where a real, persistent one exists and should be used).

## 2. Every candidate checked — none share the bug

- **`app/routers/notifications.py`**'s `create_and_notify()`/`broadcast_notification()` helpers (`repo or _inmemory_repo`): confirmed dead code — zero callers anywhere in `app/`, `domains/`, or `runtime/` outside their own module. `_inmemory_repo` is also a module-level singleton (constructed once at import time), not re-created per call, so even if it had a caller this would not share the copilot bug's "destroyed every request" shape.
- **`app/modules/signal_marketplace/router.py`**'s `get_signal_service()` (`if not settings.feature_signal_marketplace_postgres: return SignalMarketplaceService()` else the real Postgres-backed one): a **deliberate, explicit, feature-flag-gated** degraded-mode fallback, not an oversight. Report 26's own history confirms the flag is configured `True` in real deployment, so the in-memory branch is intentionally unreachable outside an explicit flag flip — a fundamentally different shape from the copilot bug, which had no flag and never had a real alternative reachable at all.
- **`app/modules/webhooks/service.py`**'s `WebhookService.__init__` — already correctly hardened by an **earlier session**: an explicit `SALESOS_TESTING` environment check raises `ValueError("WebhookService requires Postgres repositories outside tests (refuse InMemory default)")` unless both repos are supplied, with the code's own comment reading "Fail closed outside tests — InMemory default was a reaudit residual." This confirms the underlying anti-pattern is a real, recurring risk in this codebase, and that this specific instance was already found and fixed previously.
- **`app/modules/audit/service.py`**, **`app/modules/telemetry/service.py`**: false-positive grep matches — both are `class InMemoryXRepository(...):` *definitions*, not instantiation call sites.

## 3. Conclusion

Report 148's fix closes the only live, unguarded instance of this specific anti-pattern found in the request-handling code (`app/routers/`, `app/modules/`). This sweep is conclusive, not a lead for later.

## 4. Scope and safety

- No files changed. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 5. Loop status

Continuing the standing 24-hour continuous-loop authorization. Five systematic methodologies have now independently reached conclusive/saturated results this session (SQL EXPLAIN sweep, RLS/GUC census, mypy triage, ON-CONFLICT-nullability sweep, and now this in-memory-fallback sweep). Pivoting to a fresh angle: reviewing the remaining not-yet-checked `_init_*` functions in `app/boot/startup.py` for the same "constructed but never actually wired/read" shape that report 148 found for `_init_approval` (before it existed) — specifically checking every `app.state.X` assignment in that file against a corresponding real reader elsewhere in the codebase, the mirror image of report 148's investigation.
