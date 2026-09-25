# 77 — HybridRetriever: wrong pgvector column name + missing GUC pinning in both search paths (2026-09-24)

## Summary

`runtime/knowledge_graph_runtime/hybrid_retrieval.py`'s `HybridRetriever`
combines pgvector cosine-similarity search and Postgres full-text (BM25-style)
search via Reciprocal Rank Fusion. **Dead code**: confirmed via repo-wide
grep that `HybridRetriever` is referenced only by its own test file, which
exercises `_reciprocal_rank_fusion()` and metrics with in-memory fixtures —
never `_vector_search()`/`_bm25_search()` against a real database. Two
independent bugs meant neither method could ever return a real result:

1. **`_vector_search()` referenced a nonexistent `embedding` column.**
   `companies`' real pgvector column is `embedding_vector` (confirmed via
   `\d companies` and a direct query attempt:
   `ERROR: column "embedding" does not exist`). Because `_vector_search()`
   wraps its query in a `try/except` that logs and returns `[]` on any
   failure, this error was always silently swallowed — the method would
   simply return no results forever, never raise.
2. **Neither `_vector_search()` nor `_bm25_search()` ever pinned
   `app.tenant_id`.** `companies` has RLS + FORCE RLS; without the GUC
   pinned, `current_setting('app.tenant_id', true)` returns NULL, so the
   `tenant_id = :tid` predicate the policy checks is never satisfied and the
   SELECT silently returns 0 rows — confirmed directly: a genuinely-seeded
   company row is invisible to an unpinned session
   (`count(*) = 0` against real data). This is a *second*, independent
   failure mode from bug 1 — fixing the column name alone would still leave
   both methods returning nothing.

Net effect before this fix: `HybridRetriever.retrieve()` would always
degrade to its own "vector failed → BM25-only fallback" path (bug 1 forces
this), and even that BM25-only fallback would always return `[]` (bug 2) —
so the entire retrieval pipeline could never surface a single result,
silently, with no error ever raised or logged as fatal.

## Fixes

**`runtime/knowledge_graph_runtime/hybrid_retrieval.py`**:
- Added `from app.database import apply_tenant_guc`.
- `_vector_search()`: `embedding` → `embedding_vector` (3 occurrences: the
  `<=>` projection, the `IS NOT NULL` filter, and the `ORDER BY`). Added
  `apply_tenant_guc()` pin before the query.
- `_bm25_search()`: added `apply_tenant_guc()` pin before the query.

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app` restricted
role (non-superuser, `NOBYPASSRLS`).

**New file**: `tests/integration/test_hybrid_retrieval_db.py` (2 tests):
- `test_bm25_search_finds_the_seeded_company_and_is_tenant_scoped` — seeds
  one company under tenant A, confirms `_bm25_search()` finds it by name,
  and confirms tenant B (RLS) sees nothing.
- `test_vector_search_finds_the_seeded_company` — seeds a company with a
  real 3072-dim `embedding_vector`, confirms `_vector_search()` (via a fake
  embedding service) finds it and returns a similarity score.

**Genuine red→green, both bugs isolated independently**:
1. Reverted only `embedding_vector` → `embedding` (bug 1): re-ran the vector
   test, confirmed it failed exactly as predicted (`assert 0 == 1`, silently
   caught by the method's own `except`). Restored, re-confirmed passing.
2. Reverted only the `apply_tenant_guc()` call in `_bm25_search()` (bug 2):
   re-ran the BM25 test, confirmed it failed exactly as predicted
   (`assert 0 == 1`). Restored, re-confirmed passing.

**Existing unit regression** (`runtime/knowledge_graph_runtime/tests.py`,
`TestHybridRetriever`): **3/3 PASS**, unaffected.

**Combined session regression** (all integration tests from reports
68/70–77 run together in the same container): **35/35 PASS**, no cross-fix
regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

`HybridRetriever` is not wired into any router, boot sequence, or scheduled
job — fixed ahead of any future wiring decision, same posture as reports
73/74/76. No production or `salesos_test` write; only a disposable,
ephemeral Postgres container was used, destroyed after verification. Phase
7 remains BLOCKED; production remains **NOT APPROVED**.
