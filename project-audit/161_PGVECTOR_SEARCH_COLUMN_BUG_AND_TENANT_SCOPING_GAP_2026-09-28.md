# 161 — `sdk/search.py::PgVectorSearch`: same wrong-column-name/type bug found 3 times before (reports 77/79/81/82), plus a deeper, undecided tenant-scoping gap discovered while proving the fix

**Read-only in scope of production/salesos_test.** Fresh, disposable `pgvector/pgvector:pg16` container migrated to head and destroyed after verification; no production/`salesos_test` write.

## 1. Scope

Continuing the unreviewed-`sdk/` sweep from report 160. `sdk/search.py` (`FullTextSearch`/`VectorSearch` abstractions, `PgVectorSearch` implementation) had 5 raw-SQL/DB indicator hits from the initial scan.

## 2. The bug — 4th occurrence of an established pattern

`_embedding_table()`'s stub declared `column("embedding", String)`. Verified directly against a fresh, fully-migrated schema:

```
companies.embedding_vector   USER-DEFINED (vector)   -- the real column
companies.embedding          -- does not exist at all
```

This is the exact same defect shape already found and fixed 3 times this session in sibling files (`runtime/search_runtime/__init__.py` report 79, `domains/search/engine/hybrid_search.py` report 82, `domains/search/engine/postgres_repo.py` report 81's sibling): wrong column name, and a bare `String` type that makes the `<=>` distance operator's bind parameter compile as `::VARCHAR`, which Postgres has no `vector <=> varchar` operator for.

## 3. Scope of the fix — only 1 of 8 "supported" collections has any real backing storage

`ALLOWED_COLLECTIONS`/`PgVectorSearch._TABLE_MAP` list 8 entries. Checked all 8 directly against the migrated schema:

| Collection | Real state |
|---|---|
| `companies` | **Real, fixable** — has `embedding_vector` (type `vector`) |
| `contacts`, `licenses`, `branches`, `opportunities` | Table exists, but **no embedding column of any kind** |
| `company_embeddings`, `contact_embeddings`, `document_embeddings` | **Table does not exist at all** |

Only `companies` is genuinely fixable by a column-name/type correction. The other 7 are non-functional by a missing-schema gap this session cannot responsibly resolve (would require either adding columns/creating tables — a real schema decision — or narrowing the allowlist, which risks removing entries someone may intend to build out later). Left as-is, documented here, matching report 157's established precedent for undecided architecture gaps.

## 4. Fix (for `companies`)

Added a local `_PgVectorColType(UserDefinedType)` (mirroring `runtime/search_runtime/__init__.py`'s already-fixed, identical class rather than importing it cross-module, matching that file's own stated "avoid private MetaData island" rationale). Renamed the stub column to `embedding_vector`; changed `id`'s stub type from `String` to `PGUUID(as_uuid=True)` (matching every real table's actual `id` column type, confirmed `uuid` on all 5 existing collections). Updated `search()`'s and `upsert()`'s column references and `on_conflict_do_update()`'s `set_` clause accordingly. Also fixed the call sites that pre-stringified the vector (`str(vector)`) before passing it as the bind value — the new `_PgVectorColType.bind_processor()` does that serialization itself; pre-stringifying would double-encode it and crash the processor's own `float(x)` conversion on individual characters of the string.

## 5. A second, deeper gap found while proving the fix — documented, NOT fixed

Writing the verification test surfaced a second, independent, more severe defect: **`PgVectorSearch`'s entire public API (`search`/`upsert`/`delete`) has no `tenant_id` parameter anywhere**, and `_embedding_table()`'s stub never included a `tenant_id` column. `companies` (and every other real, existing collection) has `tenant_id NOT NULL`. Reproduced directly, in order of increasing severity:

1. Under the restricted, real application role (`salesos_app`, FORCE RLS on `companies`): `upsert()` fails with `InsufficientPrivilegeError: new row violates row-level security policy` — expected, since nothing pins the tenant GUC.
2. **Under the unrestricted owner/superuser connection (bypassing RLS entirely)**: `upsert()` *still* fails, this time with a plain `NotNullViolationError: null value in column "tenant_id"` — proving this has nothing to do with RLS at all. `PgVectorSearch` cannot write to `companies` (or any of the other 4 real tenant-scoped tables) under **any** role, because it never supplies `tenant_id` in the first place.

This is a genuine, undecided API/architecture gap — should `search`/`upsert`/`delete` take an explicit `tenant_id` argument? Should every collection's stub include one and pin the GUC internally? These are real design choices this session should not make unilaterally, matching the established precedent (reports 85/87/147/152/157). **Not fixed.**

## 6. A third finding, documented only

`delete(collection, document_id)` issues an unconditional `DELETE FROM <table> WHERE id = ...`. For the 3 (non-existent) dedicated embedding tables this would be the correct semantic (the row exists only to hold an embedding). For the 5 shared-entity collections (`companies`, `contacts`, etc.) this would **delete the entire business record**, not merely remove a search-index entry — almost certainly not the intended behavior for any future "remove this document from the index" caller. Not touched; flagged for whoever eventually designs the tenant-scoping fix above, since both questions likely need resolving together.

## 7. Reachability

`grep -rln "PgVectorSearch(" app/ domains/ runtime/ intelligence/ mcp_server/` (excluding the module itself): zero matches. Dead code, matching this session's established "correctly-designed-but-unwired, genuine internal defect" pattern for the narrow embedding-column fix (reports 121/123/126/127/130/131/135/156/158/160) — fixed ahead of any future wiring. The deeper tenant-scoping gap is a separate, larger question independent of reachability.

## 8. Verification — genuine red→green

Two new tests in `tests/integration/test_pgvector_search_db.py` against a fresh, fully-migrated, disposable `pgvector/pgvector:pg16` container (`salesos_app` restricted role provisioned via `infra/docker/postgres/init/02-app-role.sql`):

- `test_upsert_and_search_round_trip_through_real_embedding_vector_column`: isolates the embedding_vector fix using a scratch table shaped exactly like the stub (no `tenant_id`, so the separate gap above can't interfere) — a real `upsert()` → `search()` round trip through the actual `<=>` cosine-distance operator, asserting a perfect `1.0` similarity score for a vector against itself, plus a second upsert proving the `ON CONFLICT DO UPDATE` path doesn't duplicate rows.
- `test_upsert_has_no_tenant_scoping_and_cannot_write_companies_at_all`: reproduces the deeper gap directly — even the unrestricted owner connection cannot `upsert()` into `companies` at all (`NotNullViolationError` on `tenant_id`).

Scoped `git stash push -- salesos/backend/sdk/search.py` (reverting only the fix): both tests failed as predicted — the first with `UndefinedColumnError: column "embedding" of relation "companies" does not exist` (the scratch table is shaped for the fixed code, so the reverted code's reference to the wrong column name fails this way, still a genuine reproduction of the original bug), the second for the same underlying reason (execution never reaches the tenant_id check because the column-name bug fails first). `git stash pop` restored the fix; both tests re-confirmed PASS.

## 9. Regression

New test file: 2/2 PASS. Ruff (`--select E4,E7,E9,F,I`): 0 findings on both files. `python -m py_compile` and `git diff --check`: clean. No pre-existing test file for `sdk/search.py` existed to regress.

## 10. Scope and safety

- Two files touched: `salesos/backend/sdk/search.py` (fix + explanatory comments), `salesos/backend/tests/integration/test_pgvector_search_db.py` (new).
- Only a disposable, ephemeral `pgvector/pgvector:pg16` container was used, migrated to head via Alembic and destroyed (`docker rm -f`) after verification. No production/`salesos_test` write.
- No gate closed. No auto-merge, auto-resolution, or cluster-certify attempted. The tenant-scoping and `delete()` findings are explicitly left as open architecture questions, not resolved unilaterally.

## 11. Loop status

Continuing the standing 24-hour continuous-loop authorization. Remaining unreviewed `sdk/` root files from report 160's list (`sdk/queue.py`, `sdk/vector.py`, `sdk/telemetry.py`) showed no DB-touching indicators in the initial scan; lower priority. Given `sdk/` root is now largely swept, the next tick should either check these three for completeness or pivot to a fresh file family — candidates: `sdk/agent_sdk/`, `sdk/backend_sdk/`, `sdk/company_sdk/`, `sdk/integration_sdk/`, `sdk/plugin_sdk/` (all unreviewed this session).
