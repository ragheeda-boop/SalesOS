# 143 — domains/employee/postgres_repo.py: metadata silently discarded on every write, live; a false-positive existing test corrected

**Ephemeral, disposable Postgres container only (`sweep-pg16`, `pgvector/pgvector:pg16`, destroyed after use).** No `salesos_test` or production contact.

## 1. Scope — fifth file in the `domains/*/postgres_repo.py` sweep

`domains/employee/postgres_repo.py` (213 lines, `PostgresEmployeeSignalRepository`) checked against `domains/employee/db_models.py`'s `EmployeeSignalModel`/`EmployeeScoreModel` and `domains/employee/models.py`'s `EmployeeSignal`/`EmployeeScore` dataclasses.

## 2. The bug — a deliberate column-rename collided with SQLAlchemy's reserved class attribute

`EmployeeSignalModel` deliberately renames its Python attribute away from the DB column name:

```python
signal_metadata = Column("metadata", JSONB, nullable=True, default=dict)
```

This is necessary because every SQLAlchemy declarative model class already has a reserved class-level `metadata` attribute (the schema's `MetaData` registry) — you cannot map a column to a plain `metadata` Python attribute name at all.

`save()`/`save_many()` nonetheless constructed the model with `EmployeeSignalModel(..., metadata=signal.metadata, ...)` — using the wrong keyword. SQLAlchemy's declarative `__init__` does **not** reject an unmapped keyword named `metadata`: it silently sets an **instance** attribute that shadows the class-level `MetaData` descriptor for that one object. The real, mapped `signal_metadata` attribute — the one that actually gets INSERTed — was never touched, so every signal's real metadata was silently discarded on every save, forever, landing in the database as the column's own `default=dict` (`{}`).

Independently, on the read side, `get_by_employee()`/`get_summary()` reconstructed `EmployeeSignal(..., metadata=r.metadata or {}, ...)`. `r.metadata` on a row loaded via a genuine `SELECT` is the class-level `MetaData()` singleton (never `None`), which is **truthy** — so the `or {}` fallback never triggers. Every `EmployeeSignal` ever reconstructed from a real database row therefore had its `.metadata` field silently set to a SQLAlchemy internal `MetaData` object, not a dict — a second, independent defect.

## 3. Why the existing test suite never caught this

`domains/employee/tests/test_postgres_repo.py::TestDatabaseIntegrity::test_signal_has_all_required_fields` already asserted `row.metadata == {"deal_id": "123"}` — but `row` is fetched via `select(EmployeeSignalModel).where(EmployeeSignalModel.id == signal.id)` on the **same session** that performed the `save()`. SQLAlchemy's identity map returns the **exact same in-memory Python object** for a matching primary key within one session — not a fresh row from the database — so the test was unknowingly reading back the poisoned *instance* attribute the buggy constructor call had just set, not a genuine database round trip. The test passed by accident, on the bug it should have caught.

## 4. Reachability — genuinely live, 3 independent construction sites

`grep -rn "PostgresEmployeeSignalRepository("` finds real construction (outside tests) at `app/modules/employee_360/router.py:24`, `domains/employee/router.py:41`, and `domains/employee/tasks.py:452`. Both `employee_signals` and `employee_scores` are confirmed present in `app/alembic/lib/rls.py`'s tenant-table registry.

## 5. Fix

All 4 occurrences corrected: `signal_metadata=signal.metadata` / `signal_metadata=s.metadata` on write (`save()`, `save_many()`); `metadata=r.signal_metadata or {}` on read (`get_by_employee()`, `get_summary()`). `save_score()`/`get_latest_score()` (a separate, flat, non-renamed model with no equivalent issue) were checked and confirmed already correct.

The pre-existing test's assertion was corrected in the same edit — `row.metadata` → `row.signal_metadata` — since leaving it unfixed would have turned a silent false-positive into a straightforward, correctly-failing assertion the moment the real bug was fixed (confirmed: with the fix applied but the test unfixed, it failed with `AssertionError: assert MetaData() == {'deal_id': '123'}`, definitively proving the test had always been checking the wrong attribute).

## 6. Verification — genuine red→green, empirically reproduced twice (raw SQL and repo-level)

Reproduced directly before writing any fix: constructing `EmployeeSignalModel(metadata={"foo": "bar"})` in isolation showed `m.signal_metadata is None` while `m.metadata` held the dict — confirming the exact mechanism. Then reproduced through the real repository against a fresh, disposable, fully-migrated container using **two separate sessions** (eliminating the identity-map shortcut): the raw INSERT log showed `'{}'` bound for `metadata`, a raw `SELECT metadata FROM employee_signals` confirmed `{}` at the database level, and the repo-reconstructed `EmployeeSignal.metadata` came back as `MetaData()` — a SQLAlchemy internal object, not a dict.

New `tests/integration/test_employee_signal_metadata_column_bug_db.py` (2 tests, using two separate sessions per test to avoid the identity-map trap) proves the real, persisted metadata round-trips for both `save()` and `save_many()`. Reverting exactly `domains/employee/postgres_repo.py` (scoped `git stash`): both new tests fail with the exact predicted symptom (raw INSERT log showing `'{}'` for every row). Restored: both PASS.

Regression: `domains/employee/tests/test_postgres_repo.py` (12 tests, including the now-corrected assertion) + `tests/integration/test_performance_engine.py` (6 tests, a separate consumer of this same repository) + the 2 new tests: **18/18 PASS**. Ruff (`E4,E7,E9,F,I`): 5 pre-existing, unrelated findings (`I001`/`F401`) across the 2 changed files, identical before and after (confirmed via scoped stash/pop) — 0 new; the new test file is Ruff-clean. `compileall` and `git diff --check` clean.

## 7. Scope and safety

- Files changed: `salesos/backend/domains/employee/postgres_repo.py` (4-site fix), `salesos/backend/domains/employee/tests/test_postgres_repo.py` (1-line assertion correction), `salesos/backend/tests/integration/test_employee_signal_metadata_column_bug_db.py` (new).
- One disposable, ephemeral Postgres container (`sweep-pg16`) used for verification; destroyed after (`docker rm -f`). No `salesos_test` or production contact.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes the planned `domains/*/postgres_repo.py` sweep from report 138's next-candidates list: `decision_center` (139, clean), `feature_store` (140, clean), `workflow` (141, clean), `timeline` (142, bug fixed), `notifications` (checked clean this session, no dedicated report — flat dataclass, no nested objects, correct field mapping, correct tenant/user DI throughout its live router), `employee` (this report, bug fixed). Net: 2 genuine, live, previously-undetected bugs found and fixed across 6 files, plus one existing test corrected from a false positive to a genuine assertion.
