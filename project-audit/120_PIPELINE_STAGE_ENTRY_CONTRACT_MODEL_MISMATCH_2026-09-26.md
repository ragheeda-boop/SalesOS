# 120 — PostgresPipelineRepository's stage-entry methods: guaranteed crash on every real call (2 independent bugs)

**Read-only in scope of production/salesos_test.** All reproduction and verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container migrated to the current Alembic head, torn down after use. No write to `salesos_test` or production. No provider call.

## 1. Reachability — live, not dead code

`domains/commercial/infrastructure/postgres_repositories.py`'s `PostgresPipelineRepository` is instantiated by `app/routers/commercial.py`'s `_get_pipe(db)` factory (`PipelineService(PostgresPipelineRepository(db))`), used by real, mounted router endpoints, and also referenced by `app/graphql/query.py`. This is not dead code awaiting a wiring decision (unlike several earlier findings this session) — every real call to `PipelineService.enter_stage()` / `exit_stage()` through this router would have crashed.

## 2. Bug 1 — the domain contract and the DB model use structurally different field names, in both directions

The `StageEntry` domain contract (`domains/commercial/pipeline/contracts/models.py`) models "one stay in one stage": `id, pipeline_id, opportunity_id, stage_name, entered_at, exited_at, exit_reason`, with no `tenant_id` and no `from_stage`/`to_stage`/`duration_hours`.

The DB model (`StageEntryModel`, table `commercial_stage_entries`, RLS+FORCE RLS, in `ALL_TENANT_TABLES`) models "one stage transition": `id, tenant_id, opportunity_id, pipeline_id, from_stage, to_stage, entered_at, exited_at, duration_hours` — a materially different shape, with no `exit_reason` column at all.

`PostgresPipelineRepository` bridged these incorrectly on both sides:
- `save_stage_entry(entry: StageEntry)` read `entry.from_stage` / `entry.to_stage` — fields that do not exist on the real contract. **`AttributeError` on every call**, confirmed as the actual crash mode in the red-proof below.
- `get_active_stage_entry()` / `get_stage_history()` constructed `StageEntry(from_stage=..., to_stage=..., duration_hours=...)` — keyword arguments the contract's constructor does not accept. **`TypeError` on every call** that got this far (masked behind the first bug once it's hit first in the write path, but independently reachable from a read-only history query).
- `tenant_id` was defensively defaulted to `""` (`entry.tenant_id if hasattr(entry, 'tenant_id') else ""`) — even with the field-name bugs fixed, an empty `tenant_id` on the INSERT would fail RLS's `WITH CHECK` against the real GUC-pinned tenant, since `commercial_stage_entries` is a FORCE-RLS tenant table. The defensive `hasattr` check (present nowhere else in this file's other methods) strongly suggests the field was expected to exist on `StageEntry` at some point and never was.

## 3. Bug 2 — found while fixing bug 1: unconditional INSERT would violate the primary key on every stage transition

`save_stage_entry()`'s original body always did `self.session.add(model)` — an unconditional INSERT. `PipelineService.enter_stage()`'s "close the previous entry" step re-fetches the still-open entry (`get_active_stage_entry`), mutates `exited_at`/`exit_reason` on it, and calls `save_stage_entry(prev)` again with the **same id** it was originally created with. Even with bug 1's field names fixed, this second call would raise a primary-key violation on every real stage transition after the very first stage entry for a given opportunity.

## 4. Fix

- `StageEntry` (contract): added `tenant_id: str = ""` and `from_stage: str = ""` — both additive, defaulted, appended after existing fields. Verified every construction call site in the repo (`test_pipeline.py`, `service.py`, `postgres_repositories.py`) uses keyword arguments only, so no positional-argument call site could break.
- `PipelineService.enter_stage()`: populates the new fields at the one place that has the needed information — `pipeline.tenant_id` (already fetched via `get_definition()`) and `prev.stage_name if prev else from_stage` (the caller-supplied `from_stage` parameter already existed on this method's signature but was never threaded through to persistence).
- `PostgresPipelineRepository.save_stage_entry()`: now upserts by id (`session.get(StageEntryModel, entry.id)` then either update the closing fields or insert a new row), maps `entry.stage_name → to_stage` and `entry.from_stage → from_stage` correctly, and computes `duration_hours` from `exited_at - entered_at` via a small shared helper (matching the persisted column's actual purpose).
- `get_active_stage_entry()` / `get_stage_history()`: both now reconstruct through one shared `_to_contract()` helper using the contract's real field names (`stage_name=model.to_stage`, `from_stage=model.from_stage`, `tenant_id=model.tenant_id`); `duration_hours` is no longer fed into the constructor (the contract computes `duration_days` as a property from `entered_at`/`exited_at` and never accepted this field).

## 5. Scope decisions — not fixed, disclosed

- **`exit_reason` is still not persisted** — `commercial_stage_entries` has no such column. Setting `entry.exit_reason` before a save is silently lost on the next read-back. This is a genuine, separate, lower-severity gap (silent loss of a diagnostic string, not a crash) that would need a new nullable column + migration to close properly; out of scope for this fix, which is narrowly targeted at the guaranteed-crash bugs. Not worked around by inventing a value.
- **`save_definition()`'s stage serialization is lossy** — it stores only `name`/`name_ar`/`order`/`default_probability`/`is_terminal` per stage, silently dropping `entry_criteria`/`exit_criteria`/`sla_days`/`is_reopen_target`/`description`. `get_definition()`'s `StageDefinition(**s)` deserialization then falls back to empty-list defaults for the criteria fields, meaning entry/exit criteria enforcement is silently disabled for any pipeline saved through this repository (found as a side-effect while tracing `enter_stage()`'s criteria-check path; does not crash, so out of scope for this fix). Documented here for a future dedicated pass, not touched.

## 6. Verification

- **Genuine red→green, both bugs together**: a new `tests/integration/test_pipeline_stage_entry_persistence_db.py` drives the real service-level flow (`PipelineService(PostgresPipelineRepository(session)).enter_stage()` called twice, transitioning `prospecting → qualification`) against a fresh, fully-migrated, RLS-enforced disposable database. With the fix reverted (scoped `git stash` of exactly the 3 changed files, not a blanket stash): `AttributeError: 'StageEntry' object has no attribute 'from_stage'` at `postgres_repositories.py:241` — the exact predicted failure. Restored: PASS.
- The test also asserts, directly against the raw table, that exactly 2 rows exist for the opportunity (proving the upsert-by-id fix prevents a duplicate/PK-violating row on the second `save_stage_entry` call), that the closed row's `to_stage`/`from_stage`/`duration_hours`/`tenant_id` are all correctly persisted, and that the second entry's `from_stage` correctly reflects the first entry's `stage_name`.
- Regression: `domains/commercial/pipeline/tests/test_pipeline.py` + `tests/unit/test_pipeline_analytics.py` + `tests/integration/test_pipeline_analytics_score_deal_db.py` (report 117's fix, same table) + this new file: **50/50 PASS**.
- Ruff (`E4,E7,E9,F,I`): 54 findings both before and after this change (confirmed via a scoped `git stash`/`pop` diff) — all pre-existing in this 1,700+ line file, none introduced by this fix. The new test file alone: clean. `compileall`: clean.
- `git diff --check`: clean.

## 7. Scope and safety

- Files changed: `salesos/backend/domains/commercial/infrastructure/postgres_repositories.py`, `salesos/backend/domains/commercial/pipeline/contracts/models.py`, `salesos/backend/domains/commercial/pipeline/engine/service.py`, `salesos/backend/tests/integration/test_pipeline_stage_entry_persistence_db.py` (new).
- `salesos_test` and production: untouched. Only the disposable container (destroyed after use) was written to.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 8. Loop status

Continuing the standing "6 hours, all approvals" authorization. Next: continue the systematic sweep (mypy findings still have entries left to triage; `domains/commercial/infrastructure/postgres_repositories.py`'s remaining `Quote`/`QuoteRevenueKPIs` field-mismatch findings from the same mypy batch look like the same class of bug and are a natural next target).
