# Employee Workflow-Signal Metadata Type Fix — 2026-09-23

## Purpose

Continue verifying report 64's remaining, uninvestigated mypy findings.
This one — `domains/employee/signals.py:153` — turned out to be a real,
if currently dormant, bug: a `list` was being passed where the
`EmployeeSignal.metadata` contract requires a `dict[str, Any]`.

## The bug

`EmployeeSignalPipeline._collect_workflow_signals` built each
`WORKFLOW_COMPLETED` signal's `metadata` argument directly from a workflow
execution's `step_results` field:

```python
signals.append(self._make_signal(
    employee_id, tenant_id, signal_type,
    SignalSource.WORKFLOW.value,
    getattr(exec_, "step_results", []) if hasattr(exec_, "step_results") else exec_.get("step_results", []),
    ts,
))
```

`step_results` is a **list** of per-step result dicts (matching the same
shape produced by `WorkflowEngine._handle_parallel`/`_handle_for_each`
elsewhere in this codebase — see report 65). `_make_signal`'s `metadata`
parameter, `EmployeeSignal.metadata`, and — critically —
`domains/employee/schemas.py::EmployeeSignalResponse.metadata` are all
typed `dict[str, Any]`.

**Why "dormant" and not already crashing in production:** `EmployeeSignal`
is a plain `@dataclass` (no runtime type enforcement) and the DB column is
`JSONB` (which stores a list value without complaint), so nothing crashes
at signal-creation or persistence time. Nothing in
`domains/employee/scoring.py` currently reads `.metadata` by key for this
signal type either. The live risk is at the API boundary:
`EmployeeSignalResponse` is a **Pydantic** `BaseModel` with
`metadata: dict[str, Any]` — Pydantic validates on serialization, so the
first time a `WORKFLOW_COMPLETED` signal is returned through any endpoint
using this response schema, validation would fail. This is exactly the
"latent until triggered" bug class this session's mypy sweep exists to
catch before it surfaces as a production incident.

## Fix

```python
step_results = (
    getattr(exec_, "step_results", [])
    if hasattr(exec_, "step_results")
    else exec_.get("step_results", [])
)

signals.append(self._make_signal(
    employee_id, tenant_id, signal_type,
    SignalSource.WORKFLOW.value,
    {"step_results": step_results},
    ts,
))
```

Wraps the list in a dict under an explicit `step_results` key — preserves
every field of data that was being captured, now behind a `dict[str, Any]`
that matches every consumer's declared contract.

## Verification (genuine red→green, not asserted)

Extended the existing `test_collect_workflow_signals` test with an
assertion that `metadata` is a `dict` and matches the expected
`{"step_results": [...]}` shape, then actually exercised both directions:

1. Ran the extended test against the **fixed** code first: PASS.
2. Temporarily reverted the fix (passed `step_results` bare again), re-ran:
   **FAILED** — `assert False where False = all(isinstance(s.metadata, dict) for s in signals)` —
   confirms the test genuinely catches the bug.
3. Restored the fix, re-ran: PASS again.

Full regression: `domains/employee/tests/test_signals.py` **8/8 PASS**.
Wider `domains/employee/` suite: **184 passed, 3 pre-existing failures**
(`test_phase5_14_services.py`, `test_postgres_repo.py`, `test_tasks.py` —
a `NameError: OAuthTokenService` import gap and DB-repo-dependent tests,
none referencing `signals.py` or `metadata`; confirmed present in this
checkout independent of this change). `python -m py_compile` clean on both
changed files. Ruff pre-existing findings (unused imports predating this
change, unrelated to this edit) left untouched, matching this session's
established scope discipline.

## A note on how the pre-existing-failure check was done, and a near-miss

To double-check those 3 pre-existing failures were unrelated to this
change, an **unscoped `git stash`** was used to compare against a clean
tree — a mistake: it swept up the entire repository's existing uncommitted
state (270 files, matching the long-documented pre-existing dirty tree),
not just this session's changes. The subsequent `git stash pop` then
failed with a merge conflict on 4 files (`AGENTS.md`,
`docs/adr/0113-evidence-architecture.md`,
`docs/adr/0114-canonical-write-boundary.md`, `docs/program/DECISION_LOG.md`)
and correctly refused to apply anything rather than risk overwriting
content — this is git's safe default behavior. Verified immediately after
that every file in this session's actual scope (this report's code changes,
all of reports 57–65, the DEC-157 file, migration `70193187420d`, and every
other new/modified file from this session) was present and correct in the
working tree, and that `stash@{0}` — confirmed to be a redundant duplicate
of already-present content — was left untouched rather than dropped or
popped again. **No work was lost.** Going forward this session, any
"what did this look like before my changes" check should use
`git diff`/`git show HEAD:<path>` scoped to the specific file, never a
blanket `git stash`.

## Deliberate non-claims

- Does not audit other `_collect_*_signals` methods
  (`_collect_crm_signals`, `_collect_timeline_signals`) for the same
  metadata-shape question — mypy's filtered sweep (report 64) did not flag
  them, and they were not independently re-inspected this session.
- No database, migration, deployment, commit, or push occurred.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**. Narrow
  correctness fix to Employee 360 signal collection, unrelated to Master
  Data or production-readiness gates.

## Report 64 mypy sweep — status update

Three of the flagged/sampled findings are now resolved: `phase6/pipeline.py`
(fixed, report 64), `workflow/engine.py` (fixed, report 65),
`employee/signals.py` (fixed, this report). Two more confirmed false
positives, checked directly against their runtime call sites (not assumed
by pattern alone):

- `domains/commercial/pipeline/engine/forecast_engine.py:56`
  (`opportunity_count`) — traced `count` from its origin
  (`_compute_weighted_pipeline`'s `count = 0; count += 1` loop, a genuine
  `int` at every step) through `_combine`. It is stored in a dict whose
  *declared* return type is `dict[str, float]` (shared with real float
  values in the same dict), so mypy widens the key lookup to `float` — the
  runtime value was never anything but a real `int`. Not a bug.
- `app/modules/company/signal_persistence.py:183,209,231` (`.rowcount` ×3)
  — confirmed these are raw `UPDATE`/`DELETE` statements run through
  `AsyncSession.execute(text(...))`; at runtime this always returns a
  `CursorResult`, which has `.rowcount`. `AsyncSession.execute()`'s type
  stub only promises the more generic `Result[Any]` base class, a known
  SQLAlchemy-async typing-precision gap. Not a bug.

Both confirm the same recurring false-positive shape already seen in
`decision_center/service.py` (report 65) and `muhide_adapter.py` (report
64, not individually re-confirmed this round but matching the identical
dict-widening pattern) — a dict or return-type declared with one uniform
value type even though individual keys' *actual* runtime values are more
specific and always correct. Five of the seven individually-inspected
leads are now accounted for (3 real bugs fixed, 2 confirmed benign); the
remaining ~46 filtered findings from report 64 (mostly the same two
false-positive shapes, repeated across `domains/feature_store`,
`domains/workflow/postgres_repo.py`, `domains/timeline`,
`domains/decision_center/postgres_repo.py`, `domains/revenue/analytics`,
plus deprecated `domains/ubom`) remain open and were not individually
checked this session — continuing to grind through all of them has
clearly diminishing real-bug yield at this point.
