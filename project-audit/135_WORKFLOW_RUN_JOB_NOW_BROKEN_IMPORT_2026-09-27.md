# 135 — WorkflowService.run_job_now(): a dead, broken import made every call silently fail

**Read-only in scope of production/salesos_test.** Pure in-memory-repository test; no database container needed for this fix.

## 1. Context — mypy sweep resumed after the encoding-blocker fix (report 134)

Re-ran the full-tree mypy sweep (filtered to `[attr-defined]`/`[call-arg]`/`[arg-type]`, the same technique from reports 64-67) now that `runtime/` is reachable for the first time this session: 189 findings, up from the ~46 previously seen when `runtime/` was permanently blocked by the corrupted-byte files. Triaging this larger list from the top.

## 2. False positive investigated first — `domains/workflow/service.py:99-103`, `"WorkflowStep" has no attribute "get"`

Traced in full before concluding it was benign, since it looked plausible at first: `WorkflowService.create()`'s `if template: ... elif steps: ...` branches each bind a loop variable named `s` to a different type (`WorkflowStep` from `for s in tmpl.steps:`, then `dict[str, Any]` from `for i, s in enumerate(steps):`). Confirmed both branches are independently correct by reading `Workflow.steps: list[WorkflowStep]` (the template branch's attribute access is genuine) and every real caller of `create(steps=...)` (all pass plain dicts, matching the dict branch's `.get()` calls). This is mypy's documented default no-implicit-redefinition behavior misattributing the first loop's inferred type to the second, unrelated loop — a known limitation, not a real bug. No fix needed or made.

## 3. The real bug — `run_job_now()`, line 347

`from domains.workflow.templates import log_message` — `log_message` does not exist anywhere in `templates.py` (confirmed via direct grep: zero matches). The imported name is never referenced anywhere in the function body afterward — a vestigial, dead import. Python evaluates `from X import Y` eagerly: this line raises `ImportError` on every single invocation, regardless of whether `log_message` is ever used. The very next lines (marking the execution `status="completed"`, updating job stats) never execute, because the import fails first — but the surrounding `try/except Exception` (line 346) catches the `ImportError` (a subclass of `Exception`) and reports it as a generic job failure: `execution.status = "failed"`, `execution.error = str(exc)`. `run_job_now()` has never once succeeded.

## 4. Reachability — unreached today, fixed ahead of wiring per established precedent

Grepped `app/routers/workflows.py` for a "run job now" endpoint: only `POST /jobs`, `GET /jobs`, `GET /jobs/{job_id}`, `PUT /jobs/{job_id}`, `DELETE /jobs/{job_id}`, `GET /jobs/{job_id}/executions` exist — no `POST /jobs/{job_id}/run` or equivalent. `run_job_now` has zero callers anywhere outside its own definition. Fixed anyway, matching the "correct dead code ahead of any future wiring decision" precedent from reports 121/123/126/127/130/131, since the failure is unconditional and would surface instantly the moment such an endpoint is added.

## 5. Fix

Deleted the single dead import line. No other change — the rest of the method's logic (marking completion, updating `job.run_count`/`retry_count`/`last_run_at`) was already correct and now actually executes.

## 6. Verification — genuine red→green

New `domains/workflow/tests/test_service.py::TestWorkflowService::test_run_job_now_succeeds` (in-memory repository, no database needed) creates a real job via `WorkflowService.create_job()`, calls `run_job_now()`, and asserts `execution.status == "completed"`, `execution.error is None`, and the job's `run_count`/`retry_count` update correctly.

Reverting exactly the fixed file (scoped `git stash push -- domains/workflow/service.py`): `AssertionError: assert 'failed' == 'completed'` — the exact predicted failure. Restored: PASS.

Regression: full `domains/workflow/tests/` suite: **145/145 PASS** (144 pre-existing + 1 new), no regression. Ruff (`E4,E7,E9,F,I`) on both changed files: 10 findings before (including the `log_message imported but unused` this fix removes) → 9 after — net improvement of 1, 0 new. `compileall` and `git diff --check` clean.

## 7. Scope and safety

- Files changed: `salesos/backend/domains/workflow/service.py` (1 line removed), `salesos/backend/domains/workflow/tests/test_service.py` (1 new test).
- No database, container, or migration involved — pure in-memory-repository unit test.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. Resuming the mypy triage of the remaining ~188 filtered findings from the same sweep; most match established benign shapes already documented in reports 64/66/110/112 (`Column[T]`-vs-`T` ORM narrowing, `Result[Any]` missing `rowcount`, heterogeneous dict/list-literal value-type widening) but several genuinely new candidates remain unexamined, including `runtime/data_fabric_runtime/__init__.py`'s `PipelineMetrics` missing-attribute errors, `runtime/odoo/__init__.py`'s `FromClause.insert()` calls, `app/modules/facts/{service,apply_service}.py`'s `type[BaseModel]` attribute errors, and `runtime/agent_runtime/tasks.py`'s `Result`/`object` attribute errors on a file not yet examined this session.
