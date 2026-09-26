# 134 — 5 source files with invalid UTF-8 bytes, blocking static analysis (not a runtime bug)

**Read-only in scope of production/salesos_test.** Pure source-file text fixes; no database, no container.

## 1. Discovery

Attempting to run mypy across `app/`, `sdk/`, `domains/`, `runtime/`, `intelligence/` (the original 24-hour roadmap's Phase 2, last touched in reports 64-67) crashed immediately: `mypy: can't decode file 'runtime\execution_runtime\__init__.py': 'utf-8' codec can't decode byte 0x97 in position 18: invalid start byte`. A full repository scan (every `.py` file, explicit `bytes.decode('utf-8')`) found 5 affected files.

## 2. The bug — cp1252 characters typed in a Windows editor, saved without UTF-8 conversion

Same root cause as report 20's earlier, single-instance fix (`test_il1c_runtime_proof.py`): a Windows-1252 em-dash (`\x97`) or an unassigned cp1252 control byte (`\x9d`, likely from a similar copy-paste chain) landed in the raw file bytes instead of being encoded as UTF-8's 3-byte em-dash sequence.

- `runtime/execution_runtime/__init__.py`, `runtime/scheduler_runtime/__init__.py`, `runtime/simulation_runtime/__init__.py`, `runtime/workflow_runtime/__init__.py`: four **identical** one-line placeholder files, each containing only `# PLANNED FOR RT3 \x97 see ROADMAP.md`.
- `tests/unit/test_il2a_task_trigger.py`: two separate bad bytes in two different comments (`\x9d` and, once that one was fixed and decoding could proceed further, a second, previously-masked `\x97`) — `.decode('utf-8')` stops at the first invalid byte, so the scan only reports one at a time per file.

**Not a live runtime bug**: confirmed directly — `import runtime.execution_runtime` succeeds with no error, and `python -m py_compile` passes on all 5 files both before and after the fix. CPython's own source-file handling tolerates a stray invalid byte inside a comment in a way a strict `bytes.decode('utf-8')` call (which is what `mypy` and my scan both use) does not. It only ever blocked static-analysis tooling, not execution.

## 3. Fix

Replaced every occurrence of the offending byte with a proper UTF-8-encoded em-dash (`—`, `\xe2\x80\x94`) in all 5 files. Content is otherwise byte-for-byte unchanged.

## 4. Verification

- All 5 files: `bytes.decode('utf-8')` now succeeds (confirmed via the same repo-wide scan, re-run after the fix: 0 files remaining).
- All 5 files: `python -m py_compile` passes (unchanged from before — confirms this was never a compile-blocking issue).
- `tests/unit/test_il2a_task_trigger.py`: full existing suite re-run, **40/40 PASS**, unaffected — the two fixed bytes were both inside comments, never inside a string literal or identifier the tests could exercise.
- `python -m mypy app/ sdk/ domains/ runtime/ intelligence/` now proceeds past the file it previously crashed on entirely (result reported separately once the run completes — it takes several minutes across this many packages).

## 5. Scope and safety

- Files changed: the 5 files named above — comment-byte fix only, no logic touched.
- No database, container, or migration involved.
- No gate closed by this report.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. This was a pure tooling-blocker fix, found while pivoting to the original roadmap's Phase 2 (mypy triage) after the SQL EXPLAIN sweep and RLS census methodologies both reached saturation (reports 132/133). The mypy run itself is in progress; its findings will be triaged in the next report.
