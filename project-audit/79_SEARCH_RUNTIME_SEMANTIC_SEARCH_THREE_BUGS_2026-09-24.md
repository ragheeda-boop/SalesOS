# 79 — SearchRuntime semantic search: live, unregistered 500 on GET /api/v1/search/similar/{id} (2026-09-24)

## Summary

`runtime/search_runtime/__init__.py`'s `SearchRuntime` is **genuinely live**:
registered at boot (`app/boot/startup.py`) and mounted as real REST
endpoints via `runtime/search_runtime/router.py`, including
`GET /api/v1/search/similar/{company_id}`, `GET /api/v1/search?strategy=semantic`,
and the default hybrid strategy's semantic-boost step. This is the second
genuinely-live finding this session (after report 75's `PersistentDeadLetterQueue`),
and by far the most directly user-facing: **every real call to
`GET /api/v1/search/similar/{company_id}` with an embedding service
configured would crash with an unhandled 500** — there is no exception
handling at either the router or `similar_to()` method level, unlike the
other two call paths which happen to swallow the same bug behind a broad
`except Exception` and silently degrade instead.

Three independent bugs, all in the semantic-search path:

1. **`companies.c.embedding` does not exist.** The lightweight
   `sqlalchemy.table()` query stub at the top of the file declared
   `column("embedding", String)`, but the real pgvector column is
   `embedding_vector` (confirmed via `\d companies`). Both `similar_to()`
   and `_semantic_search()` used it for the `<->` distance operator.
2. **Even after renaming to `embedding_vector`, the column was still typed
   as a bare `String`.** SQLAlchemy then compiled the `<->` operator's bind
   parameter with an explicit `::VARCHAR` cast, which Postgres rejects:
   `UndefinedFunctionError: operator does not exist: vector <-> character
   varying` — an explicit cast blocks the implicit unknown-type-to-vector
   cast that would otherwise apply. Fixed by adding a small
   `_PgVectorColType(UserDefinedType)` (`vector(3072)`), mirroring
   `app.modules.company.models._PgVector` without importing that ORM model
   (keeping this file's stated "avoid private MetaData island" design).
3. **Even with the correct type, asyncpg had no codec for a raw Python
   `list` bind value** — `DataError: invalid input for query argument $3:
   [...] (expected str, got list)`. Fixed by giving the new type a
   `bind_processor` that serializes the embedding list to pgvector's own
   text literal format (`"[0.02,0.02,...]"`), which Postgres implicitly
   casts to `vector` since the parameter carries no explicit `::cast`.

A fourth, independent bug found in the same file: **the `"activity"` filter
field pointed at a second, separate, nonexistent `activity` column** — the
stub already had a correct `activity_description` column declared further
down, so the file had two declarations for what should be one field. Fixed
by removing the duplicate stub and renaming the public
`ALLOWED_FILTER_FIELDS` entry from `"activity"` to `"activity_description"`
(matching the `"activity": "activity_description"` alias already used
elsewhere in this codebase, e.g. `runtime/data_fabric_runtime/__init__.py`).
Not independently reachable from the live router today (which only exposes
city/region/industry/status filters), so fixed ahead of any future caller.

## Fixes

**`runtime/search_runtime/__init__.py`**:
- Added `from sqlalchemy.types import UserDefinedType` and a new
  `_PgVectorColType` class (`get_col_spec` → `"vector(3072)"`,
  `bind_processor` → serializes a Python list to pgvector's text literal).
- Table stub: `column("embedding", String)` → `column("embedding_vector",
  _PgVectorColType())`; removed the duplicate/nonexistent
  `column("activity", String)` (the correct `activity_description` column
  was already declared separately).
- `similar_to()` and `_semantic_search()`: `companies.c.embedding` →
  `companies.c.embedding_vector` (4 occurrences total).
- `ALLOWED_FILTER_FIELDS`: `"activity"` → `"activity_description"`.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app` restricted
role (non-superuser, `NOBYPASSRLS`).

**New file**: `tests/integration/test_search_runtime_semantic_db.py`
(3 tests):
- `test_similar_to_finds_a_neighbor_via_real_embedding_column` — seeds two
  companies with real 3072-dim embeddings, confirms `similar_to()` finds the
  neighbor (this is the exact code path the unprotected
  `GET /api/v1/search/similar/{company_id}` endpoint calls).
- `test_semantic_search_finds_the_seeded_company` — confirms
  `_semantic_search()` finds a real seeded company via its embedding.
- `test_activity_description_is_a_valid_filter_field_end_to_end` — confirms
  the renamed filter field works and the old broken name is gone from
  `ALLOWED_FILTER_FIELDS`.

**Genuine red→green**:
- Bugs 2 and 3 (vector type cast, then list serialization) were each hit
  organically during development in strict sequence — fixing the column
  name alone surfaced `UndefinedFunctionError: vector <-> character
  varying`; adding the `UserDefinedType` alone (before its `bind_processor`)
  surfaced `DataError: ... expected str, got list`; both are captured
  directly in this session's tool transcript, not fabricated.
- Bug 1 (column name) was independently isolated afterward: reverted just
  `similar_to()`'s two `companies.c.embedding_vector` references back to
  `companies.c.embedding`, re-ran, confirmed
  `AttributeError: embedding` (the stub no longer declares that name at
  all — an even stronger failure than the original run's DB-level
  `UndefinedColumnError`, since the column had already been renamed).
  Restored, re-confirmed passing.

**Existing unit regression** (`tests/unit/test_search_runtime.py`):
**12/12 PASS**, unaffected (all mock `embedding_service=None` or don't
exercise real SQL).

**Combined session regression** (all integration tests from reports
68/70–79 run together in the same container): **40/40 PASS**, no
cross-fix regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

This is a live, currently-reachable bug fix: `GET /api/v1/search/similar/{company_id}`
was crashing with an unhandled 500 on every real call (given a configured
embedding service), and `strategy=semantic`/hybrid's semantic boost were
silently degrading to fulltext-only on every real call. No production or
`salesos_test` write; only a disposable, ephemeral Postgres container was
used, destroyed after verification. Phase 7 remains BLOCKED; production
remains **NOT APPROVED**.
