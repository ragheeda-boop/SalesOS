# Workflow Parallel-Branch CancelledError Leak — Closure — 2026-09-23

## Purpose

Follow up on report 64's two flagged-but-uninvestigated mypy leads. One
(`domains/decision_center/service.py:305`) turned out to be a false
positive; the other (`domains/workflow/engine.py:395`) is a real bug, now
fixed.

## Investigation

**`decision_center/service.py:305`** — `create_template(d["name"], d["type"], d["config"], tenant_id)`.
Checked `create_template`'s actual signature
(`name: str, template_type: str, config: dict[str, Any], tenant_id: str`)
against the call: the positional order is correct. mypy's complaint
(`Collection[str]` where `str`/`dict` expected) is the same dict-literal
value-type-widening artifact already seen in report 64's
`muhide_adapter.py` finding — `defaults` is a `list[dict]` with
heterogeneous per-key value types (`name`/`type` are `str`, `config` is
`dict`), so mypy widens every `d[...]` lookup to the union of all possible
values in the list rather than narrowing per-key. **Not a bug. Not fixed.**

**`domains/workflow/engine.py:395`** (`WorkflowEngine._handle_parallel`) —
real bug, confirmed by reading the surrounding `asyncio.gather` call.

## The bug

```python
tasks = [_run_branch(branch, idx) for idx, branch in enumerate(branches)]
branch_results = await asyncio.gather(*tasks, return_exceptions=True)

results: list[dict[str, Any]] = []
for idx, res in enumerate(branch_results):
    if isinstance(res, Exception):
        results.append({"branch_index": idx, "error": str(res), "status": "failed"})
    else:
        results.append(res)
```

`asyncio.gather(..., return_exceptions=True)` can return **any**
`BaseException` for a task that raised — not only `Exception` subclasses.
`asyncio.CancelledError` is a direct `BaseException` subclass in Python
3.8+, specifically **not** an `Exception`. `_run_branch`'s own inner
`except Exception as exc:` (used per-step, one level in) has the identical
gap, so a step handler that raises `CancelledError` (a real branch task
cancellation, a timeout-driven cancel, or any handler that explicitly
propagates it) is never caught internally, reaches `gather`, and — because
`isinstance(res, Exception)` is `False` for it — fell through to the `else`
branch. The raw `CancelledError` object was appended directly into
`results`, a list every caller expects to contain only
`{"branch_index", "error"/"result", "status"}` dicts. Any caller iterating
`results` expecting dict access (`r["status"]`), or serializing the parallel
step's output to JSON for storage/API return, would break or silently
corrupt the workflow execution record the moment a branch was ever
cancelled.

## Fix

```python
if isinstance(res, BaseException):
    results.append({"branch_index": idx, "error": str(res), "status": "failed"})
else:
    results.append(res)
```

`BaseException` covers `Exception` and everything else (`CancelledError`,
`KeyboardInterrupt`-adjacent cases in async contexts, etc.) that
`return_exceptions=True` can hand back — every entry in `results` is now
guaranteed to be a well-formed dict.

## Verification

- New test, `domains/workflow/tests/test_phase13.py::test_parallel_handles_cancelled_branch_without_leaking_raw_exception`:
  registers a step handler that raises `asyncio.CancelledError`, runs it as
  one of two parallel branches, asserts the result is a dict with
  `status == "failed"` (not a raw exception object). Genuine red→green
  proof, not asserted: temporarily reverted the fix
  (`isinstance(res, Exception)`), re-ran the test locally, watched it fail
  exactly as predicted (`AssertionError: ... isinstance(CancelledError(''), dict)`),
  restored the fix, re-ran — full suite green again.
- This test run (and the full-suite regression below) executed directly
  with the local Python interpreter (`python -m pytest ...`), not Docker —
  `pytest`/`pytest-asyncio` are present in this host's Python and this
  suite needs no database, unlike most of this session's other
  verification work.
- One incidental finding while writing the test: `asyncio` internally
  discards a cancelled task's original exception message once the task is
  marked cancelled (a raised `CancelledError("msg")` surfaces as an empty
  message through `gather`) — a documented asyncio quirk, not something
  this fix controls; the test asserts dict-shape and status, not the exact
  message text.
- Full regression: `domains/workflow/tests/test_phase13.py` **56/56 PASS**
  (was 55; +1 new test). `tests/unit/test_workflow_engine.py` **52/52
  PASS**, unaffected.
- `python -m py_compile` clean on both changed files. Pre-existing,
  unrelated Ruff findings in `test_phase13.py` (unused imports predating
  this change) were left untouched — out of this fix's scope.
- Docker image/container removed after verification.

## Deliberate non-claims

- Does not audit every other `asyncio.gather(..., return_exceptions=True)`
  call site in the codebase for the same `isinstance(..., Exception)` gap —
  this fix is scoped to the one call site mypy's sweep (report 64) actually
  flagged.
- Does not change `_run_branch`'s own per-step
  `except Exception as exc:` — that still won't catch a `CancelledError`
  raised by an individual step handler *inside* `_run_branch`, but that is
  the correct, standard behavior (a step handler cancellation should
  propagate and cancel its own branch task, which is exactly what reaches
  `gather` and is now handled correctly one level up). No change needed
  there.
- No database, migration, deployment, commit, or push occurred.
- Phase 7 remains **BLOCKED**; production remains **NOT APPROVED**. Pure
  correctness fix to the Tenant Studio Workflow Builder's parallel-branch
  step, unrelated to Master Data or production-readiness gates.

## Report 64 mypy sweep — status update

Of the two findings flagged for a closer look: one fixed (this report), one
confirmed false positive (decision_center). The remaining ~50 filtered
findings from report 64 (mostly the recurring ORM-Optional-into-required
pattern) remain open and uninvestigated individually.
