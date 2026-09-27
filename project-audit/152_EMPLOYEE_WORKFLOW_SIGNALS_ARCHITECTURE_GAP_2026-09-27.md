# 152 — `workflow_service` (report 151's deferred candidate): genuinely live, silently degraded, and unfixable without a schema/architecture decision

**Read-only in scope of production/salesos_test.** Pure source-code review; no database container needed.

## 1. Scope — completing report 151's deferred investigation

Report 151 found `app.state.workflow_service` read once (`domains/employee/router.py:54`) with no corresponding assignment anywhere, and deferred a closer look. This report completes that investigation.

## 2. Confirmed live, unlike `timeline_service`

`domains/employee/router.py` (unlike `domains/timeline/router.py`, report 151's other deferred candidate) **is** genuinely mounted at boot — confirmed in `app/boot/routers.py:55,80`, under `/api/v1`, real auth dependencies. `_get_pipeline()` constructs a real `SignalPipeline(repository=..., activity_runtime=getattr(...), timeline_recorder=getattr(...), workflow_service=getattr(request.app.state, "workflow_service", None), logger=getattr(...))` — `activity_runtime`/`timeline_recorder` are both genuinely wired (confirmed elsewhere this session), but `workflow_service` is always `None` in the real running application (zero assignments anywhere, confirmed via repo-wide grep for `app.state.workflow_service\s*=`).

## 3. Unlike reports 148/151, this degrades silently rather than crashing

`domains/employee/signals.py::_collect_workflow_signals()` (the one method that uses `self._workflow_service`, the same file report 112 already fixed a real bug in) guards correctly: `if not self._workflow_service: return signals` — an empty list, no exception, no 503. `_collect_workflow_signals()` is one of several `_collect_X_signals()` methods (alongside timeline/CRM sources) feeding a broader multi-source Employee 360 signal-aggregation pipeline — so the practical effect today is that the `WORKFLOW_COMPLETED` employee-signal type has **never once contributed a real signal to any employee's score**, silently, since this router went live, while the other signal sources (timeline, CRM) continue to function normally.

## 4. Why a naive wiring fix would make things worse, not better

Checked whether wiring `app.state.workflow_service` to a real `domains.workflow.service.WorkflowService` instance (the same class already thoroughly swept for bugs in report 141, confirmed clean) would actually work if connected: **it would not.** `_collect_workflow_signals()` calls `self._workflow_service.get_executions_by_actor(actor=employee_id, tenant_id=tenant_id, limit=100)` — confirmed via `grep` that **no method named `get_executions_by_actor` exists anywhere on `WorkflowService`** (its real execution-listing method is `list_executions(tenant_id, workflow_id=None)`, filtered only by workflow, not by who triggered it).

More fundamentally: `WorkflowExecution` (`domains/workflow/models.py`, read in full during report 141's sweep) has **no field at all** representing "which employee/actor triggered this execution" — only `trigger_event: str = "manual"` (a trigger-type label like `"manual"`/`"scheduled"`, not a specific user identifier). The underlying data this signal source would need was never captured in the first place. This is not a method-rename fix; it would require either (a) adding an `actor`/`triggered_by` column to `WorkflowExecutionModel` plus a migration and a decision on how existing/future executions populate it, or (b) a product decision that this signal source is not supportable and should be removed from `_collect_workflow_signals()` entirely. Naively wiring `app.state.workflow_service` today, without also fixing the method-name/schema mismatch, would turn a silent, harmless empty-list degradation into a live `AttributeError` on every employee-signal collection that happens to reach this code path — a strictly worse outcome than the current state.

## 5. Not fixed — documented, matching established precedent

This matches report 135's `NBAEngine.record_feedback()` finding exactly ("a genuine schema/architecture gap, not a one-line fix, intentionally left unpatched") and reports 130/148 §3's precedent for genuinely ambiguous, product-level gaps this session does not resolve unilaterally. No files changed.

## 6. Scope and safety

- No files changed. No database or container needed (pure source-code cross-reference, reusing report 141's already-verified reading of `domains/workflow/models.py`/`service.py`).
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 7. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes report 151's deferred investigation (`nba_engine` fixed in report 151; `timeline_service` confirmed dead code; `workflow_service` confirmed live-but-architecturally-blocked, documented here). The "component built and tested in isolation but never actually wired to `app.state`" failure mode (reports 148, 151) has now been checked exhaustively against every live reader in the application — no further instances remain to investigate under this specific methodology.
