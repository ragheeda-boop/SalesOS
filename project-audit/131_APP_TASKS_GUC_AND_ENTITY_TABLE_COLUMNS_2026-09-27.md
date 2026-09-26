# 131 — app/tasks.py: 2 fixable GUC-pin gaps (one reachable from the report 130 GraphQL fix), a shared table stub broken on both tables, and a documented architecture gap

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container (`sweep-pg11`) migrated to head `f2e3d4c5b6a7`, with the restricted `salesos_app` role provisioned, torn down after use. No write to `salesos_test` or production.

## 1. Reachability — one directly reachable via report 130's own fix, one an independent Celery task

`_run_enrichment_pipeline()` is the async body of `enrich_company_task` (`@celery_app.task`), which is `.delay()`-called by `app/graphql/mutation.py::_enrich_company()` — the same `enrichCompany` GraphQL mutation whose GUC-pinning gap this session already fixed in report 130. `sync_notion_database` is a separate, independent `@celery_app.task`.

## 2. Bug 1 (both functions) — no GUC pin despite already knowing `tenant_id`

Unlike `_get_entity_tenant()` (below), both functions receive `tenant_id` as a plain parameter — the straightforward case this session has fixed repeatedly (reports 84/129/130). `companies` has FORCE RLS; `_run_enrichment_pipeline()`'s own `WHERE tbl.c.id == company_id, tbl.c.tenant_id == tenant_id` app-layer filter was already correct, but with no pin, RLS silently returned zero rows regardless — every real call returned `{"error": "company_not_found", ...}`, including for the account that had just been created by the same GraphQL request report 130 fixed. `NotionSyncService.import_companies()` writes to the same FORCE-RLS `companies` table with no internal pinning either.

**Fix**: `apply_tenant_guc(session, tenant_id)` added to both. Also added to `_generate_embedding()`'s inner session (gated behind bug 3 below, but correct once that gap is ever resolved — matching the "fix ahead of the day it's reachable" precedent from reports 121/123/126/127/130).

## 3. Bug 2 (both real tables) — `_entity_table()`'s single shared stub matched neither table's real schema

`companies` and `contacts` have genuinely different schemas, but one `table()`/`column()` stub was used for both. Confirmed directly against the schema:
- `companies` has no `embedding` column at all — the real column is `embedding_vector` (`vector(3072)`).
- `contacts` has none of `name_en`/`activity_description`/`city`/`industry`/`embedding` — real columns are `id`/`tenant_id`/`company_id`/`name`/`name_ar`/`email`/`phone`/`mobile`/`position`/`position_ar`/`department`/`is_primary`/`source`/`confidence_score`/`tags`/`metadata`.

Every whole-row `select(tbl)` through the old stub — in `_load_company_record()` and `_run_enrichment_pipeline()` (companies) and `_generate_embedding()` (both) — would raise `UndefinedColumnError` the instant a real row became visible (i.e., the instant bug 1's fix let RLS stop hiding it). `_generate_embedding()`'s `update(tbl).values(embedding=str(embedding))` would independently raise a second `UndefinedColumnError` writing to a column that was never real on either table.

**Fix**: split into two schema-correct stubs (companies: `id`/`tenant_id`/`name_ar`/`name_en`/`activity_description`/`city`/`industry`; contacts: `id`/`tenant_id`/`name_ar`/`position`/`department` — the subset both existing callers actually need), excluding the embedding column entirely from the shared stub since no caller of `_entity_table()` reads its value. `_generate_embedding()`'s write now targets `companies.embedding_vector` directly via a raw parameterized `UPDATE ... SET embedding_vector = CAST(:vec AS vector)` (this session's established pattern for pgvector binds, reports 74/75/79/82/95), and the `contacts` branch — which has no embedding-storage column at all — now logs and returns rather than raising or inventing a migration for a column no caller has ever asked for (same "no schema home" posture as report 122's Proposal.sections, report 127's Recommendation.context_id).

## 4. Bug 3 (found, NOT fixed — architecture gap, matching the report 84/104 precedent) — `_get_entity_tenant()` cannot look up a tenant it doesn't yet know

`_sync_to_graph()` and `_generate_embedding()` are both queued with only `entity_id`/`entity_type` (no `tenant_id`), so they call `_get_entity_tenant()` to discover it — an inherent cross-tenant lookup-by-ID-alone. Under the restricted, non-BYPASSRLS `salesos_app` role, this can never work: pinning a tenant GUC *before* knowing which tenant owns the row is a chicken-and-egg problem no per-call fix resolves. Every real call to `_sync_to_graph()`/`_generate_embedding()` today logs "no tenant found" and silently no-ops. Fixing this properly needs a deliberate RLS-bypass connection (e.g., `owner_engine`) or a producer-side change to always pass `tenant_id` at enqueue time — a genuine architecture/product decision, not made unilaterally here, matching the exact posture already established for `communication_hub`'s cross-tenant account enumeration (reports 84/104).

## 5. Verification — genuine red→green, environment-methodology followed correctly

Two test files (isolation rationale below). `tests/integration/test_tasks_guc_and_column_db.py` (3 async tests, `salesos_app` role): `_load_company_record()` no longer references the phantom `embedding` column; `_run_enrichment_pipeline()` finds a real, just-seeded company instead of `company_not_found`; `_entity_table("contacts")` round-trips real seeded columns and excludes every phantom one. `tests/integration/test_sync_notion_guc_db.py` (1 sync test, isolated into its own process): patches `NotionSyncService` to capture the session it receives and asserts `current_setting('app.tenant_id', true)` genuinely equals the seeded tenant.

`sync_notion_database` is a bound Celery task whose body calls `asyncio.run()` internally; nesting that inside pytest-asyncio's own running loop raises `RuntimeError`, and the shared `app.database.engine`'s connection pool is loop-bound (asyncpg) — reusing it after any prior async test in the same process raised `attached to a different loop` on every subsequent statement (reproduced directly, not guessed at). Isolating this one test into its own file/process, matching this session's own `_run_async()` docstring's documented caveat, resolved it cleanly.

Reverting exactly `app/tasks.py` (scoped `git stash`): all 3 tests in the first file failed with the exact predicted `UndefinedColumnError: column contacts.name_en does not exist`; the isolated notion test failed with the exact predicted `assert None == '<tenant_id>'`. Restored: all 4 PASS.

Regression: `tests/unit/test_celery_async_engine_dispose.py` (7, unaffected). Ruff (`E4,E7,E9,F,I`) on all 3 files: 0 findings. `compileall` and `git diff --check` clean.

## 6. A test-authoring note, disclosed

Mid-investigation, one of this report's own draft tests initially failed for a reason unrelated to the fix under test: `set_config(..., true)` is transaction-local, and the test's own `commit()` between its seed insert and its assertion query silently reset the pin before the SELECT ran — the exact bug class report 83 found in production code (`signal_persistence.py`), reproduced here in test code instead. Fixed by re-pinning after the commit, same as report 83's fix.

## 7. Scope and safety

- Files changed: `salesos/backend/app/tasks.py` (`_entity_table()` split; GUC pins added to `_run_enrichment_pipeline`, `sync_notion_database`, `_generate_embedding`; `_generate_embedding`'s embedding write corrected; unused `update` import removed), `salesos/backend/tests/integration/test_tasks_guc_and_column_db.py` (new), `salesos/backend/tests/integration/test_sync_notion_guc_db.py` (new).
- `_get_entity_tenant()`/`_sync_to_graph()`: unchanged, documented only.
- `salesos_test` and production: untouched. Only the disposable container was written to.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 8. Loop status

Continuing the standing 24-hour continuous-loop authorization. This is the 4th consecutive report in the GUC/RLS-pinning sweep (129 communication_hub, 130 GraphQL, 131 this file) plus the 2nd genuinely-clean-code architecture gap deliberately left undecided (104 communication_hub's `list_active()`, now this file's `_get_entity_tenant()`). Remaining unchecked from the original grep: `app/main.py`, `app/startup.py`, `app/modules/signal_marketplace/seeding.py` (all likely boot-time/platform-scope). Given the GUC/RLS-pinning technique's yield has now covered `postgres_repositories.py` (report 128), `communication_hub` (129), the entire GraphQL layer (130), and this file (131) — the next tick will assess whether to continue this specific methodology on the 3 remaining low-priority files or pivot to a fresh systematic pass (e.g., a repeat of the SQL EXPLAIN sweep on files touched since report 98, or the broader mypy-findings triage from the original 24-hour roadmap's Phase 2).
