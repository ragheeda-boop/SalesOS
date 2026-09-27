# 150 — Mirror-image sweep of report 148: every `app.state.X` assignment in the live boot module checked for a real reader; no further orphans found

**Read-only in scope of production/salesos_test.** Pure source-code review; no database container needed.

## 1. Scope

Report 148 found `app.state.approval_service` assigned nowhere while being read in 2 places. This report checks the mirror direction: every one of the 39 distinct `app.state.X` attributes actually assigned in the live `app/boot/startup.py`, checked for whether anything outside that file ever reads it — the same shape as report 139's earlier, narrower finding for `decision_center_service` ("correctly built, unreached code").

## 2. Method and a methodology correction mid-investigation

A first pass grepping the literal pattern `app\.state\.X` reported `approval_service: 0 readers` and `db_session_factory: 0 readers` — both **false negatives**: `app/routers/approval.py` and `app/routers/copilot.py` read `approval_service` via `getattr(request.app.state, "approval_service", ...)`, and 3 middleware files read `db_session_factory` the same way. Neither matches a literal `app.state.X` substring. Widened the pattern to also catch `getattr(state, "X", ...)`-style access before drawing any conclusion — a direct instance of this session's own recurring lesson (reports 71/72/74/85/142/143 etc.) that a narrow textual check can silently produce a false clean/false orphan result.

## 3. Every genuinely zero-external-reader candidate, checked individually

After the corrected sweep, 7 attributes had zero readers outside `app/boot/startup.py` and outside tests:

- **`_embedding_service`, `_sdk_cache_service`, `_sdk_redis_client`**: all three ARE read — just later in the same `startup.py` file (a different boot phase consuming an earlier phase's result), which the sweep had deliberately excluded to focus on *external* consumers. Confirmed via direct line-level inspection (lines 331, 494, 517, 922) — legitimate internal use, not orphaned.
- **`agent_task_trigger_subscriber`, `signal_detection_bridge`, `workflow_subscriber`**: all three are deliberate **keep-alive handles**. Each is a bound callback/bridge object already registered with the event system via `event_runtime.register(...)` in the same function, immediately before the `app.state.X = ...` assignment — the actual work happens through that event subscription, not through anyone reading `app.state.X` afterward. Storing the reference on `app.state` is the standard Python idiom to prevent premature garbage collection of a closure that only the event system otherwise holds. Not a bug.
- **`llm_cost_tracker`**: `init_cost_tracker(async_session)` sets a **module-level global** (`intelligence/providers/cost_tracker.py`'s `_cost_tracker`), and every real consumer calls `get_cost_tracker()` to read that global — not `app.state.llm_cost_tracker`. The `app.state` assignment is genuinely redundant (the actual wiring works through the global, independent of it) but harmless — removing it would change nothing observable, and it isn't causing any incorrect behavior. Not the same shape as report 148's finding (where the *only* path to the service was through the never-set `app.state` attribute).

## 4. Conclusion

Report 148's `approval_service` was a genuinely isolated defect, not one instance of a systemic "wired but orphaned" pattern in this boot module. No further action taken.

## 5. Scope and safety

- No files changed. No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes the mirror-image check prompted by report 148. Six systematic methodologies have now independently reached conclusive/saturated results this session (SQL EXPLAIN sweep, RLS/GUC census, mypy triage, ON-CONFLICT-nullability sweep, in-memory-fallback sweep, and now this app.state reader sweep). Given the substantial ground covered across this segment (reports 139-150: 4 real live bugs fixed — timeline metadata collision, employee signal metadata loss, and the two-part Approval/HITL wiring gap — plus new test coverage added to the canonical CRM-write boundary, and 6 independent sweeps each run to a conclusive close), this is a natural point to report progress and take direction on where to focus next.
