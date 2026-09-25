# 95 — RAG retrieval (`/api/v1/rag/*`) never persisted or retrieved anything from PostgreSQL (2026-09-24)

## Summary

`intelligence/rag/retrieval.py::RetrievalService` backs the live, boot-mounted
RAG router (`app/boot/routers.py:644`, which covers `/rag/ask`, `/rag/ingest`,
`/rag/documents`). It is the last file in the repository that still used the
`:name::type` bind form.

SQLAlchemy's `text()` does not recognise a bind name immediately followed by
`::`. This is the same quirk found in reports 74, 75 and 82. As a result,
every statement below was a syntax error:
- the document insert: `:metadata::jsonb`
- the chunk insert: `:embedding::vector`, `:metadata::jsonb`
- the vector search: `:vector::vector`, 3 occurrences
- the hybrid search: 2 occurrences

This was silent. `store_document_chunks()` and `_retrieve_pgvector()` both
catch the exception and fall back to a per-instance in-memory dict, and the
router builds a new `RetrievalService` for every request:

- `/rag/ingest` returned `status: ingested` while writing nothing durable.
- `/rag/ask` could never find a stored chunk.

A repository-wide grep (excluding tests and migrations) found no other
remaining occurrence of the pattern.

## Fix

All 9 occurrences replaced with `CAST(:name AS vector)` / `CAST(:name AS jsonb)`,
matching the established fix from reports 74 and 82. No other logic changed.

Checked, not changed:
- The request-scoped session is already tenant-pinned by `get_db`.
- The `commit()` in `store_document_chunks()` is not followed by further
  queries in `/rag/ingest`.
- The configured embedding model (`text-embedding-3-large`, 3072 dimensions)
  matches the `vector(3072)` column.

## Verification

Disposable `loop4h-pg` database, restricted `salesos_app` role, session
pinned exactly as `get_db` pins it.

**New file:** `tests/integration/test_rag_retrieval_persistence_db.py` (1 test):
- ingests one document with a one-hot 3072-dimension chunk;
- in a fresh session, confirms exactly 1 persisted chunk row;
- confirms vector retrieval returns it with score ≈ 1.0;
- confirms another tenant retrieves nothing.

**Red→green:**
- Run against the original code first: failed with `assert 0 == 1` (no
  chunk persisted).
- After the fix: PASS.

**Regression:**
- `tests/unit/test_rag_pipeline.py` + `test_rag_rls.py`: 60/60 PASS.
- Full local unit suite, run after the report 93 changes and before this
  fix: 3766 passed, 0 failed.
- `salesos_test` counts unchanged afterwards (296,746 companies, 54,185
  candidates, 1,114 link proposals).

## Deliberate non-claims

- Not exercised end-to-end over HTTP with a real embedding provider. The
  dev provider may not serve embeddings, in which case chunks are skipped
  (`if chunk.embedding:`). That is provider availability, not this bug.
- `retrieve_hybrid()` received the same mechanical fix but has no dedicated
  test.
- The silent in-memory fallback is still in place. It now only triggers on
  real errors, but it still hides them from the caller. Whether ingestion
  should fail loudly is a design choice left unchanged.
- The 5 pilot documents from AGENTS.md §30 were seeded by a separate script,
  not through this path.
- No production write. Production is **NOT APPROVED**.
