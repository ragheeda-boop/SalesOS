# 125 — Forecast: line metadata silently lost on every reload (live); kpis() returned a fake look-alike object, not the real dataclass

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container migrated to head, torn down after use. No write to `salesos_test` or production.

## 1. Core CRUD is correct — second clean class, same as Contract

`PostgresForecastRepository.save()`/`get()`/`_to_domain()`'s mapping of `ForecastSnapshot`/`ForecastLine`/`ForecastExplanation` fields against `ForecastSnapshotModel` was checked field-by-field and found correct. The two bugs below were found by tracing what the domain layer actually does with the data (`ForecastSnapshot.by_dimension()`) and by comparing `kpis()`'s output against the in-memory reference repository — not from a field-name mismatch.

## 2. Bug 1 — live: `ForecastLine.metadata` was never persisted or reloaded

`domains/revenue/forecast/engine.py`'s `ForecastEngine.predict()` — the real forecasting logic behind `POST /forecast/run` — populates `ForecastLine.metadata` with `rep_id`/`region`/`product` for every line it produces. `ForecastSnapshot.by_dimension(dimension, value)` is a real method that filters lines using exactly this metadata. `PostgresForecastRepository.save()`'s JSON serialization of each line never included a `metadata` key, and `_to_domain()`'s reconstruction never read one back — so any forecast reloaded through this repository (via `ForecastService.finalize()`, `get_latest()`, or `list_snapshots()`, all of which round-trip through `_to_domain()`) had every line's `metadata` silently reset to `{}`, making `by_dimension()` always return `[]` regardless of what the engine originally computed.

`commercial_forecast_snapshots.lines` is a schema-flexible JSON column (like Quote's lines fix, unlike Proposal's sections gap) — no migration needed. **Fixed** by adding `"metadata": l.metadata` to the serialization dict in `save()` and `metadata=ld.get("metadata", {})` to the `ForecastLine(...)` reconstruction in `_to_domain()`.

## 3. Bug 2 — `kpis()` returned a fake look-alike object, not the real `ForecastKPIs`

`domains/revenue/forecast/repo.py` defines a real `ForecastKPIs` dataclass with fields `total_snapshots`, `latest_expected_revenue`, `latest_weighted_revenue`, `latest_confidence`, `forecast_accuracy`, `forecast_bias`. The Postgres repository's `kpis()` instead built a dynamically-created class via `type("ForecastKPIs", (), {...})()` — an object that merely *prints* the same class name but **is not an instance of the real dataclass** (`isinstance()` returns `False`, confirmed directly) — with entirely different field names (`total_expected`, `total_weighted`, `confidence`, `risk`) that match none of the real dataclass's fields.

Checked reachability: **zero live router endpoints and zero tests** call `ForecastService.kpis()`/`PostgresForecastRepository.kpis()` at all (confirmed via grep — the 3 forecast-related router endpoints all read `get_latest()`'s properties directly, never calling `kpis()`). Fixed anyway, mirroring the in-memory reference repository's exact formula, consistent with reports 121/122/123's precedent for zero-caller `kpis`/`revenue_kpis` methods, and because unlike those three, this one had **no existing test coverage at all** — the new test closes that gap too.

## 4. Verification — genuine red→green, both bugs independently

New `tests/integration/test_forecast_repository_persistence_db.py` (2 tests) drives the real `ForecastService`→`PostgresForecastRepository` flow through the real `ForecastEngine`, against a fresh, fully-migrated, RLS-enforced disposable database.

- `test_line_metadata_round_trips_and_by_dimension_finds_it_after_reload`: creates a forecast from a `CommercialInput` with `rep_id="rep-42"`, confirms the engine really populated `metadata` before any save (sanity check), then reloads via `service.get()` and asserts `by_dimension("rep_id", "rep-42")` finds every line.
- `test_kpis_returns_the_real_dataclass_with_correct_fields`: creates 2 forecasts, asserts `isinstance(kpis, ForecastKPIs)` and every field value against the second (latest) snapshot's real properties.

Reverting exactly the 1 changed file (scoped `git stash`): `assert None == 'rep-42'` (metadata lost) and `assert False` (not an instance of the real `ForecastKPIs`) — both exact predicted failures. Restored: both PASS.

Regression: `domains/revenue/forecast/tests/test_forecast.py` + both new tests: **26/26 PASS**. Ruff (`E4,E7,E9,F,I`): confirmed via scoped stash/pop that the file's finding count dropped from 26 to 25 (removed the now-unused local `from dataclasses import dataclass` inside the old `kpis()` body; 0 new). New test file Ruff-clean on its own. `compileall` and `git diff --check` clean.

## 5. Scope and safety

- Files changed: `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py` (`save()`/`kpis()`/`_to_domain()` + `ForecastKPIs` import), `salesos/backend/tests/integration/test_forecast_repository_persistence_db.py` (new, includes the report 118/121 `current_database()` safety guard from the outset).
- `salesos_test` and production: untouched. Only the disposable container was written to; every env-var export was kept in the same Bash call as the command needing it.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization ("stop only on completion, or something requiring heavy-weight human intervention"). Remaining unreviewed classes in this file: `Analytics`, `Decision`, `Recommendation`, `Meeting`, `Email`, `OpportunityContact`, `Review`, `Quota`, `Territory`. Not every one will necessarily have a bug — Contract and Forecast's core CRUD were both clean; each is checked on its own merits, not assumed.
