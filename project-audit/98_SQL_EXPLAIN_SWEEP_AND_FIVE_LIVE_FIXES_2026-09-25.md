# 98 — Repository-wide SQL EXPLAIN sweep; 5 live defects fixed (2026-09-25)

## Method

Reports 70–95 found SQL defects one file at a time. I generalised that into
a single mechanical check, now saved as
`scripts/audit_sql_explain_sweep.py`:

- It parses every static `text("…")` / `sa_text("…")` literal in `app/`,
  `runtime/`, `domains/`, `intelligence/` and `sdk/`, excluding tests and
  migrations.
- It replaces bind parameters with `NULL` and runs `EXPLAIN` on each
  statement, inside a rolled-back transaction, against the disposable
  `loop4h-pg` database migrated to head.
- `EXPLAIN` plans without executing. A planning failure therefore means the
  statement can never run: a missing table or column, a type mismatch, or a
  syntax error.

**Coverage:** 378 statements across 77 files. 369 planned cleanly on the
first run.

## The 9 failures, triaged

| # | location | classification |
|---|---|---|
| 1 | `entity_resolution/er_router.py:451` — unmerge `uuid = varchar` | **NEW, fixed** (below) |
| 2 | `knowledge_graph_runtime/router.py:220` — `varchar = uuid` | **NEW, fixed** |
| 3 | `data_fabric_runtime/__init__.py:647` — `companies.embedding` | **NEW, fixed**, together with a larger pinning defect found while verifying it |
| 4–5 | `intelligence/grounding.py:90,106` — `is_decision_maker`, `amount` | **NEW detail in a known file, fixed** |
| 6–7 | `grounding.py:139,156` — `buying_signals`, `timeline_events` | Known (report 71). The right source is a product decision. Left unchanged. |
| 8 | `nba_engine/__init__.py:330` — `nba_feedback.nba_id` | Known (report 92, finding 4). Needs an architecture decision. Left unchanged. |
| 9 | `gtm/evidence_router.py:63` | **False positive**: an expanding bind (`IN :ids`) became `IN NULL`. The real code is fine. |

After the fixes, the saved script reports 6 failures: #6–#9 above (one of
which is the false positive), each already classified.

## Fixes

### A. Manual ER merge and unmerge always failed (`POST /api/v1/er/merge`, `/er/unmerge`)

These are human-invoked operations behind the `entity-resolution:CREATE`
permission. They are not automatic merges.

- **Merge:** the history insert bound a Python list (`[source_id]`) and a
  dict (`details`) raw into `jsonb` columns. asyncpg's jsonb encoder expects
  a string, so every call raised `DataError: 'list' object has no attribute
  'encode'` and the whole merge rolled back. **Fixed** with `json.dumps` +
  `CAST(... AS jsonb)`.
- **Unmerge:** the same jsonb defect, plus `md_source_rows.id` (uuid)
  compared with `md_entity_matches.source_a_id`. That column has been
  `varchar` since migration `q9r0s1t2u3v4`, which notes that source IDs are
  "not necessarily UUIDs." **Fixed** with `id::text IN (...)`, preserving
  the intended meaning (a non-UUID ID matches no row).
- **Checked, not a problem:** the source-immutability trigger permits
  updating `global_entity_id`, so the merge's row transfer is allowed by
  design.

### B. `GET /graph/query/companies-without-activity` always failed

Three correlated subqueries compared `activity_records.entity_id`
(varchar) with `companies.id` (uuid). This is the same class as report 72,
in the same router. **Fixed** with `c.id::text`.

### C. Data Fabric ingestion never ingested anything (`POST /api/v1/data-fabric/ingest`)

Verifying the embedding-column finding by actually running the pipeline
exposed the larger defect:

- **No session in `DataFabricPipeline` pinned `app.tenant_id`.**
  `golden_records` and `companies` are FORCE-RLS, so entity resolution's
  first insert failed `WITH CHECK`.
- The endpoint still returned **201** with `golden_records_created: 0` and
  the error buried in `errors`. Nothing was ever ingested.
- **Fixed:** the tenant is pinned in all 5 session sites (batch, audit,
  DLQ, DLQ retry outer and inner), and re-pinned after the batch session's
  internal `commit()`. Stage 8 reads `golden_records` on that same session
  after the commit (the report 83 pattern).
- **Embedding stage:** it wrote to `companies.embedding`, which does not
  exist (the real column is `embedding_vector`), and bound a raw list.
  **Fixed** with `embedding_vector = CAST(:emb AS vector)` and
  `json.dumps`. The configured model is `text-embedding-3-large`, which
  matches `vector(3072)`.

### D. Agent grounding context was always empty for contacts and opportunities

`GroundingService` is live: `agent_runtime` builds it with a tenant-pinned
session factory. Its failures were swallowed (`except Exception: return
[]`).
- **Contacts:** the query selected and ordered by `is_decision_maker`, which
  `contacts` does not have. **Fixed** to order by the real `is_primary`.
  No consumer reads the old key.
- **Opportunities:** the query read the `opportunities` table, which is
  marked `_deprecated`, has no writer, and lacks the `amount` and
  `probability` columns. **Fixed** to read the canonical
  `commercial_opportunities` (AGENTS.md §12), aliased (`name AS title`,
  `value AS amount`) so consumers keep their keys.

## Verification

New tests, all on the disposable database with the restricted
`salesos_app` role:

| test | proves | red (fix reverted) |
|---|---|---|
| `test_er_manual_merge_unmerge_db.py` | merge → unmerge round trip; history JSON, status and rollback flags | merge: `DataError 'list' … encode`; with only the unmerge cast reverted: `UndefinedFunctionError uuid = varchar` |
| `test_knowledge_graph_inactive_companies_db.py` | 60-day-idle company returned, 1-day-active one not | `UndefinedFunctionError varchar = uuid` |
| `test_data_fabric_ingest_db.py` | golden record + company + stored embedding; other tenant sees none | pins reverted: entity-resolution error; embedding reverted: embedding-stage error |
| `test_grounding_service_db.py` | context holds the real contact and opportunity; prompt includes the amount | original file: `assert [] == ['Primary Person']` |

**Regression:**
- Combined integration regression (reports 68/70–98): **63/63**.
- Adjacent unit suites (data fabric, ER, KG, grounding, agent runtime) pass.
- A first combined run showed 3 setup timeouts in `test_dec157`. The cause
  was my new KG test returning an unclosed session from a dependency
  override. I fixed it with a generator override and pool disposal; the
  `dec157` file passes 9/9 alone and in combination.

## Observed, not changed

- `runtime/knowledge_graph_runtime/tests.py`: 4 connector tests call
  `asyncio.get_event_loop()` from synchronous tests and fail only when run
  after async suites. This is pre-existing test design, not a product
  defect.
- `intelligence/company/__init__.py::search_from_db` is unpinned against
  FORCE-RLS `companies`, but it has no caller, and `app/startup.py` (a
  legacy boot module) is not imported anywhere. It is dead code.

## Deliberate non-claims

- The sweep covers **static** SQL only. f-string SQL and ORM queries are not
  planned.
- A statement that plans can still be semantically wrong. That is what the
  per-file review and red→green tests are for.
- Data Fabric ingestion was proven with a synthetic record, not with a real
  scraper payload or live Neo4j / feature store.
- `grounding.py`'s `buying_signals` / `timeline_events` and `nba_feedback`
  remain open by design (product/architecture decisions).
- Only the disposable container was written. Production is **NOT
  APPROVED**.
