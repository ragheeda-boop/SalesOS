# 137 — PATCH /opportunity-contacts/{id}: an unhandled TOCTOU race, plus 4 mypy findings confirmed benign

**Read-only in scope of production/salesos_test.** Pure mocked-repository unit tests; no database container needed for this fix.

## 1. mypy findings triaged and confirmed benign (no fix needed)

Continuing report 136's triage of the remaining ~180 filtered mypy findings:

- `app/modules/facts/{service,apply_service}.py` (`"type[BaseModel]" has no attribute "tenant_id"`): `target_model = Company if subject_type == "company" else Contact` narrows to the shared abstract base `sdk.database.BaseModel` (`Company`/`Contact` both subclass it), which declares only `id` — `tenant_id` is declared separately on each concrete subclass. mypy correctly can't see attributes that exist on every union member but not the common ancestor; at runtime `target_model.tenant_id` resolves correctly regardless of branch. Confirmed via direct class-hierarchy inspection.
- `runtime/agent_runtime/tasks.py` (6 findings: `"Result[Any]" has no attribute "get"` ×3, `"object" has no attribute "extend"/"append"` ×3): the same loop-variable-redefinition false positive already diagnosed in report 135 (`result` bound to `Result[Any]` on its first use, then genuinely rebound to `dict` — confirmed `dispatch_all()` returns `dict`) plus the same heterogeneous-dict-literal-widening false positive from reports 64/66/110/112 (`stats = {"tenants_processed": 0, ..., "errors": []}` mixes int/list values in one literal).
- `app/boot/startup.py` (5 `FactoryBoundRepository` findings): a deliberate dynamic proxy (`__getattr__`-based, documented in its own docstring: "Thin proxy... wrap once at startup") that mypy cannot verify against a concrete repository Protocol by design — confirmed by reading the class.

None of these needed a fix; none of this session's precedent-established false-positive shapes has yet produced a false negative.

## 2. The real bug — `PATCH /opportunity-contacts/{oc_id}`, a TOCTOU race with no guard

Live, mounted route (confirmed in `app/boot/routers.py`). `update_opportunity_contact()`:
1. Checks the row exists (`existing = await repo.get(oc_id); if not existing: raise 404`).
2. Runs the `UPDATE ... WHERE id = :oc_id` statement inside its own transaction.
3. Re-fetches the row (`result = await repo.get(oc_id)`) and passes it straight to `_to_response(result)` — which accesses `.id`/`.tenant_id`/etc. **unconditionally, with no None-check.**

A concurrent delete of the same row between steps 1 and 3 — the existence check does not hold a lock across the gap — leaves `result` as `None` at step 3, and `_to_response(None)` raises `AttributeError: 'NoneType' object has no attribute 'id'`: an unhandled 500 instead of a clean 404, for a genuine (if narrow) race window that real concurrent traffic can hit.

## 3. Fix

Added an explicit `None` check after the re-fetch, raising the same `HTTPException(status_code=404, ...)` already used for the pre-update existence check — matching this router's own established convention exactly.

## 4. Verification — genuine red→green

New `tests/unit/test_opportunity_contacts_update_race.py` (2 tests) calls the router's handler function directly with a mocked repository whose `get()` returns a real row on the first call (the pre-update check) and `None` on the second (the post-update re-fetch) — reproducing the race deterministically without needing actual concurrency or a database. A second test confirms the normal, non-race path still returns the updated row correctly.

Reverting exactly the fixed file (scoped `git stash push -- app/routers/opportunity_contacts.py`): the race test fails with the exact predicted `AttributeError: 'NoneType' object has no attribute 'id'`. Restored: both tests PASS.

Regression: existing `test_opportunity_contact_isolation.py` (5, pre-existing `xfail` per report 16's history, unaffected) + `test_opportunity_contact_repos.py` (8) + the new file (2): **10 passed, 5 xfailed**, no change. Ruff (`E4,E7,E9,F,I`): 1 pre-existing, unrelated `I001` finding, identical before and after (confirmed via scoped stash). `compileall` and `git diff --check` clean.

## 5. Scope and safety

- Files changed: `salesos/backend/app/routers/opportunity_contacts.py` (4 lines added), `salesos/backend/tests/unit/test_opportunity_contacts_update_race.py` (new).
- No database, container, or migration involved — pure mocked-repository unit tests.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. The mypy triage across `app/`, `sdk/`, `domains/`, `runtime/`, `intelligence/` has now covered every finding flagged as a genuine lead across reports 135-137: two real bugs fixed (workflow `run_job_now`, the Odoo triple-bug) plus this router race, and every other finding traced to one of six now-well-established false-positive shapes (`Column[T]`-vs-`T` ORM narrowing, `Result[Any]` missing `rowcount`/other attrs, heterogeneous dict/list-literal value-type widening, common-base-class attribute narrowing, loop-variable-redefinition, dynamic-proxy duck-typing). The mypy sweep has reached the same saturation point the SQL EXPLAIN sweep (report 132) and RLS census (report 133) each reached — remaining findings are overwhelmingly repeats of these six shapes rather than new leads. Next: a fresh methodology pass, or continuing to spot-check the handful of not-yet-individually-verified findings still in the raw list (e.g., `intelligence/notifications/email.py`'s `str | None` argument mismatches, `intelligence/digital_twin/twin.py`'s `BuyingSignal`/`ObjectSignal` list-append mismatch) if the standing authorization continues.
