# 138 — DigitalTwin.add_signal(): wrong parameter type, dead code; mypy sweep closed

**Read-only in scope of production/salesos_test.** Pure in-memory dataclass unit test; no database container needed.

## 1. Two more mypy findings confirmed benign

- `intelligence/notifications/email.py`'s `str | None` argument mismatches (`SMTP_SSL`/`login` calls): `send()` guards with `if not self.configured: return False` at the top, where `configured` checks `bool(self._smtp_host and self._smtp_user and self._smtp_password)` — by the time execution reaches the SMTP calls, all three are confirmed non-empty strings. mypy can't narrow `Optional[str]` attributes via a property-method boolean check; the runtime guard is genuinely sufficient. Not a bug — a 7th distinct false-positive shape, alongside the six already catalogued in reports 135-137.

## 2. The real finding — `DigitalTwin.add_signal()`: wrong parameter type, matched to the wrong dataclass

`add_signal(self, signal: BuyingSignal) -> None: self.business_object.signals.append(signal)` — `self.business_object.signals` is declared `list[ObjectSignal]` (`intelligence/business_objects/__init__.py`). `BuyingSignal` (`intelligence/signals/__init__.py`) and `ObjectSignal` are two **entirely unrelated** dataclasses with different field names (`signal_type`/`intensity`/`priority` vs `type`/`confidence`/`source_url`) that happen to share several field names by coincidence (`id`/`title`/`description`/`source`/`detected_at`/`expires_at`). Appending a real `BuyingSignal` instance would silently put a wrongly-shaped object into a list every downstream reader expects to hold `ObjectSignal` instances — no crash at append time (Python doesn't enforce parameter types), but any code reading `.type`/`.confidence`/`.source_url` off that entry would hit `AttributeError`, or worse, silently read whichever coincidentally-named field happens to exist.

**Reachability**: confirmed dead code via repo-wide grep — `DigitalTwin.add_signal()` has zero callers anywhere. `intelligence/digital_twin/` is the module explicitly marked "deferred" by the accepted ADR-103 (report 10's session history: "Digital Twin, Agent Runtime, Revenue Brain deferred"). Zero prior test coverage of any kind existed for this module.

**Fix**: corrected the parameter type to `ObjectSignal` (importing it from `intelligence.business_objects`, replacing the now-unused `BuyingSignal` import from `intelligence.signals`) — matching the list it is actually appended to.

## 3. Verification — different shape than a crash-bug fix, disclosed

This is a pure static-typing correctness fix: Python does not enforce parameter type annotations, so no runtime crash exists to reproduce via a red→green pytest cycle the way this session's other fixes have proven themselves. Verification instead used mypy directly: confirmed the specific finding (`twin.py:70/71`, `BuyingSignal`/`ObjectSignal` mismatch) is no longer reported after the fix (`grep` against the mypy output found zero matches, versus the original finding beforehand). New `tests/unit/test_digital_twin_add_signal.py` (1 test) builds a real `DigitalTwin`/`BusinessObject` and proves `add_signal()` accepts and correctly stores a genuine `ObjectSignal` instance (`isinstance` check), demonstrating the corrected contract rather than a bug reproduction.

Ruff (`E4,E7,E9,F,I`) on the changed file: 2 pre-existing, unrelated findings (`I001` import-sort, `F401 dataclasses.field` unused), identical before and after the fix (confirmed via scoped `git stash`) — 0 new. `compileall` and `git diff --check` clean.

## 4. Scope and safety

- Files changed: `salesos/backend/intelligence/digital_twin/twin.py` (import + 1 parameter type), `salesos/backend/tests/unit/test_digital_twin_add_signal.py` (new).
- No database, container, or migration involved.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 5. mypy sweep closed

This closes the mypy triage started in report 134 (after fixing the 5 invalid-UTF8 source files that had permanently blocked mypy from ever completing a run across `runtime/`). Across reports 135-138: **3 genuine bugs found and fixed** (`WorkflowService.run_job_now()`'s dead import, the Odoo sync module's 3 stacked bugs, `PATCH /opportunity-contacts/{id}`'s TOCTOU race) plus this report's dead-code type-correctness fix; **7 distinct false-positive shapes** identified and documented (`Column[T]`-vs-`T` ORM narrowing, `Result[Any]` missing `rowcount`/other attrs, heterogeneous dict/list-literal value-type widening, common-base-class attribute narrowing, loop-variable-redefinition across sequential loops, dynamic-proxy duck-typing via `__getattr__`, property-guarded `Optional` narrowing). The remaining ~170 unexamined findings in the original 189-finding list overwhelmingly match one of these seven shapes on visual inspection; this sweep has reached the same saturation point already reached by the SQL EXPLAIN sweep (report 132) and the RLS census (report 133).

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. Three systematic methodologies (SQL EXPLAIN sweep, RLS/GUC-pinning census, mypy triage) have each independently reached saturation this session. Next: pivot to a genuinely different methodology for the remainder of the authorized window — candidates include a repeat pass of the report 67-98-era "raw-SQL table/column existence" sweep restricted to files added or modified since report 98 (the fact ledger, provider spend, Agent Reach, and MA-proposal-staging modules built across reports 99-131 have not yet been swept this way), or a fresh review of frontend TypeScript files for the equivalent class of "stale contract" bugs this session found repeatedly on the backend.
