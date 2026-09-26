# 133 — graph_nodes: a real tenant_id column with zero RLS, missed by every prior census

**Read-only in scope of production/salesos_test.** Verification ran against a disposable, ephemeral `pgvector/pgvector:pg16` container (`sweep-pg12`) migrated to head, with the restricted `salesos_app` role provisioned, torn down after use. No write to `salesos_test` or production.

## 1. Discovery — a direct pg_class census, not the GUC-pinning grep

Pivoting methodology after the SQL EXPLAIN sweep re-run (report 98's tool) found zero new candidates against the current, much larger source tree — confirming that specific technique has reached saturation. Instead ran a direct `pg_class`/`information_schema` census (matching report 104's own methodology): every table with a `tenant_id` column but `relrowsecurity = false`. Found 32 rows: 6 already-decided owner-plane billing tables (DEC-158, report 60 — not a new finding), 25 monthly partition children of `sync_runs` (whose parent correctly has RLS+FORCE — Postgres partition RLS applies at the parent, not a gap), and **`graph_nodes`** — genuinely new, never previously considered.

## 2. Why this table exists and why it was missed

`graph_nodes` was created in `0004_knowledge_graph.py` (later re-asserted in `0040_ensure_graph_tables.py`) and is explicitly kept under DEC-130f's "no DROP without a dedicated DEC" orphan-keep register (`app/db05_orphan_keep.py`), the same governance decision that report 105 found covering 14 other tables — but `graph_nodes` was **not** among the 14 DEC-157 remediated (`company_*` ×9, `company_policies`, `decisions`, `decision_feedback_loop`, `activity_records`, `domain_events`) and was never added to `ALL_TENANT_TABLES` at creation time. It has a real, `NOT NULL`, `varchar(36)` `tenant_id` column and a `ix_graph_nodes_tenant_id` index — schema-ready for RLS, just never wired up.

Confirmed via exhaustive grep (14 files matching the substring "graph_nodes") that **zero application code anywhere references this table by name** — every hit is the unrelated `merge_graph_nodes()` method on the knowledge-graph runtime (an entity-resolution merge operation over `graph_edges`/`companies`, per `runtime/knowledge_graph_runtime/repository/sql_repository.py`'s own `Table()` definitions, which do not include `graph_nodes` at all). This makes the fix meaningfully lower-risk than DEC-157's: there is no live caller whose GUC-pinning needs fixing first, only a registry gap to close ahead of whichever future code eventually queries it directly.

## 3. Fix

- Added `"graph_nodes"` to `ALL_TENANT_TABLES` (`app/alembic/lib/rls.py`) — confirmed this is the single source of truth (`scripts/generate_rls_policies.py` imports it, not a separate duplicated list, contrary to report 104's note about needing to keep two lists in sync).
- New migration `a1b2c3d4e5f7` (new head): `ENABLE`/`FORCE ROW LEVEL SECURITY` + the canonical `tenant_isolation_graph_nodes` policy via `generate_policy_sql()`, matching every other Category A table's DDL shape exactly.
- Updated `tests/unit/test_db05_slice4_deferred_8_rls_authority.py`'s `len(ALL_TENANT_TABLES) == 66` assertion (verified correct as of report 116) to `67`.

## 4. Verification — genuine red→green

New `tests/integration/test_graph_nodes_rls_db.py` seeds two tenants' rows directly via SQL (no application code exists to exercise), then proves under the restricted `salesos_app` role: each tenant's pinned session sees only its own row; a session with no GUC pinned at all sees zero rows (fail-closed, not both tenants' data); and a cross-tenant `tenant_id` mismatch on INSERT is rejected by the policy's `WITH CHECK` clause.

`alembic downgrade -1` (removing the new policy) reproduced the exact predicted cross-tenant leak: tenant A's session returned rows belonging to other tenants instead of only its own (`assert ids == {node_a}` failed with a multi-tenant result set). `alembic upgrade head` restored it; test PASSES.

Regression: `test_db05_slice4_deferred_8_rls_authority.py` (4, count assertion updated) + the new test: **5/5 PASS**. Alembic: single head (`a1b2c3d4e5f7`) confirmed via `alembic heads`. Ruff (`E4,E7,E9,F,I`) on all 4 changed/new files: 0 findings. `compileall` and `git diff --check` clean.

## 5. Scope and safety

- Files changed: `salesos/backend/app/alembic/lib/rls.py` (registry addition), `salesos/backend/app/alembic/versions/a1b2c3d4e5f7_graph_nodes_rls.py` (new migration), `salesos/backend/tests/integration/test_graph_nodes_rls_db.py` (new), `salesos/backend/tests/unit/test_db05_slice4_deferred_8_rls_authority.py` (count updated, comment extended).
- Does not touch DEC-130f's KEEP-register posture — RLS is not a schema-shape change; `app/db05_orphan_keep.py`'s stubs and `alembic check`'s `remove_table` count are unaffected, matching DEC-157's own migration's explicit note on this point.
- `salesos_test` and production: untouched. Only the disposable container was written to.
- No gate closed by this report. No auto-merge, auto-resolution, or cluster-certify attempted.

## 6. Loop status

Continuing the standing 24-hour continuous-loop authorization. This closes the direct-census methodology's one genuinely new finding; the other 31 candidates from the same query are already governed (6 owner-plane, DEC-158) or non-issues (25 `sync_runs` partition children, correctly inheriting the parent's RLS). Next: broaden the census to check for any *other* schema-level gap class beyond "tenant_id present but RLS disabled" — e.g., a repeat of report 104's "enabled but not forced" check (already closed for `account_funnel`/`score_observations` in report 57/70193187420d) against the current, larger table set, in case any table added since then repeated that specific gap.
