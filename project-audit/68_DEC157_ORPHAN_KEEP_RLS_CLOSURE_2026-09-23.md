# 68 — DEC-157 Closure: Tenant GUC Pinning + RLS for the 14 Live Orphan-Keep Tables (2026-09-23)

> **Scope:** Executes all 4 steps of DEC-157 (Accepted — CLOSED this session):
> semantics rulings, GUC pinning at 5 call sites, regression proof, and the
> RLS/FORCE RLS migration for 14 tables. Read-only/ephemeral-DB verification
> only — **no write to `salesos_test` or any shared/persistent database.**
> Full ruling text lives in
> [`docs/program/decisions/DEC-157-ORPHAN-KEEP-TENANT-GUC-RLS-REMEDIATION.md`](../docs/program/decisions/DEC-157-ORPHAN-KEEP-TENANT-GUC-RLS-REMEDIATION.md);
> this report is the closure evidence.

## 1. What this closes

Report 59 found 14 tables — governed by DEC-130f's "no DROP without a
dedicated DEC" orphan-keep register — that are live (read/written by five
routed runtime engines via raw SQL) but had **zero** database-level tenant
isolation, relying entirely on hand-written `WHERE tenant_id = :tid` clauses.
DEC-157 proposed a 4-step remediation and left it **Proposed — not
Accepted**, pending two semantics rulings. This session ruled on both,
implemented all 4 steps, and closed the DEC.

## 2. Semantics rulings

1. **`activity_records.tenant_id` nullability** — exhaustive grep of every
   production caller of `ActivityRuntime.query()` / `get_by_entity()` /
   `get_by_actor()` / `get_by_action()` shows all 4 call sites
   (`app/modules/company/service.py`, `app/modules/employee_360/service.py`,
   `app/modules/work_intelligence/service.py`,
   `domains/employee/signals.py`) pass a concrete `tenant_id` from the
   authenticated router boundary. Zero legitimate cross-tenant/tenant-less
   read use case. **Ruling: no carve-out** — standard fail-closed RLS,
   matching the already-accepted `admin_ai_costs`/`admin_jobs` precedent
   (migration `d1a8c35e7f09`) and `b7e2f65a3f07`'s explicit rejection of an
   `OR tenant_id IS NULL` bypass.
2. **`domain_events.read_by_type()` cross-tenant read** — exhaustive grep
   (`grep -rn "read_stream\|read_by_type"`, whole repo, tests included)
   finds **zero callers** of either `EventStore` read method anywhere.
   **Ruling: dead code, not intentional** — `sdk/events/base.py`'s abstract
   signatures now require `tenant_id: str` on both; `PostgresEventStore`
   pins the GUC and filters by tenant on every read. Same no-carve-out
   policy as `activity_records`.

## 3. Code changes

| File | Change |
|---|---|
| `sdk/events/base.py` | `read_stream()`/`read_by_type()` now require `tenant_id: str` (was optional/absent from any real contract) |
| `sdk/events/store.py` | Added local `_pin_tenant_guc()` helper (duplicated from `app.database.apply_tenant_guc`, **not imported** — importing `app.database` here creates a circular import: `sdk.events.store` → `app.database` → `app.common.models` → `sdk.database` → `sdk.events`, discovered via a failing `pytest` run and fixed by duplication instead). Pinned before `append()`'s INSERT and both read methods' SELECTs |
| `runtime/feature_store/features.py` | GUC pin added to `FundingScoreComputer`, `HiringScoreComputer`, `IntentScoreComputer`, `ExpansionScoreComputer`, `RevenueScoreComputer` (5 sites, covering all 9 Feature Store orphan-keep tables) |
| `runtime/policy_runtime/__init__.py` | GUC pin added to `PolicyEngine.evaluate()` (covers `company_policies`) |
| `runtime/decision_runtime/feedback_loop.py` | GUC pin added to `DecisionFeedbackLoop.record_feedback()` (covers `decision_feedback_loop`) |
| `runtime/activity_runtime/__init__.py` | GUC pin added to `ingest()`, `ingest_batch()`, `query()`, `get_stats()` (4 sites, covers `activity_records`) |
| `runtime/activity_runtime/router.py` | **Side-effect security fix**: `ingest-batch`'s `enriched = [{**r, "tenant_id": r.get("tenant_id", tenant_id)} for r in records]` let a client-supplied `tenant_id` in the request body override the authenticated caller's tenant — a real cross-tenant injection vulnerability, independent of RLS. Fixed to `{**r, "tenant_id": tenant_id}` — the authenticated tenant always wins |
| `app/alembic/lib/rls.py` | Added `DEC_157_ORPHAN_KEEP_TENANT_TABLES` (14-table list) |
| `app/alembic/versions/e1d1c1225d00_dec157_orphan_keep_rls.py` | New migration (head, was `70193187420d`): `ENABLE`/`FORCE ROW LEVEL SECURITY` + canonical `tenant_isolation_<table>` policy on all 14 tables via `generate_policy_sql()` |

## 4. Test changes

| File | Change |
|---|---|
| `tests/unit/test_event_runtime_subscriber_bounds.py` | `test_postgres_event_store_append_uses_json_dumps_binds` updated: `session.execute.await_count` 1→2 (GUC pin + INSERT), plus an explicit assertion the first call is the `set_config` pin with the correct tenant. Verified genuine red (failed with `assert 2 == 1`) before the fix, green after |
| `tests/unit/test_activity_runtime_router_tenant_injection.py` | **New**, 2 tests. Proves the authenticated tenant always wins over a body-supplied `tenant_id`, including when the body omits it entirely. Verified genuine red (reverted the fix, re-ran, got `AssertionError: assert 'tenant-b-victim' == 'tenant-a'`) before restoring the fix |
| `tests/integration/test_dec157_orphan_keep_rls_db.py` | **New**, 9 tests, run on a fresh ephemeral `pgvector/pgvector:pg16` container built from current source. Covers every one of the 14 tables through its real GUC-pinned application code path (not just `pg_class` inspection): RLS/FORCE/policy shape check; `FundingScoreComputer`/`HiringScoreComputer` (funding events + job postings) and `ExpansionScoreComputer`/`RevenueScoreComputer` (products, deals, payments) each see only their own tenant on a same-`company_id` cross-tenant probe; `PolicyEngine.evaluate()` isolates `company_policies`; `DecisionFeedbackLoop.record_feedback()` isolates `decision_feedback_loop`; `decisions` isolates via GUC-pinned raw-SQL read; `ActivityRuntime` isolates `activity_records` **and** proves a NULL-tenant insert is rejected outright by `WITH CHECK` (fail-closed, no `OR tenant_id IS NULL` bypass — ruling 1); `PostgresEventStore.append/read_stream/read_by_type` isolates `domain_events` |

## 5. Verification

| Check | Result |
|---|---|
| Local unit regression (no DB, mocked) | `tests/unit/`: **3763 passed**, 4 skipped, 7 xfailed, 3 xpassed, **1 pre-existing unrelated failure** — `test_db05_slice4_deferred_8_rls_authority.py::test_deferred_8_not_folded_into_category_a_47` asserts `len(ALL_TENANT_TABLES) == 55`, actual is 66 (drift accumulated across many prior sessions adding new RLS tables without bumping this one stale assertion). Confirmed pre-existing and unrelated to this DEC — this session never touched `app/alembic/lib/rls.py`'s `ALL_TENANT_TABLES` list or this test file's assertion. Flagged, not fixed; out of scope for DEC-157 |
| Zero callers of `read_stream`/`read_by_type` | Confirmed via repo-wide grep before changing the interface — no production or test caller anywhere |
| Alembic single head | Confirmed before (`70193187420d`) and after (`e1d1c1225d00`) this migration |
| Fresh ephemeral Postgres, full migration chain from zero | **PASS** — `docker build` from current source (not a stale image; bind-mount path mangling under git-bash makes this the only reliable way to get current source into a container), `alembic upgrade head` ran clean end to end, 111 migrations applied, terminating at `e1d1c1225d00` |
| RLS/FORCE/policy shape, all 14 tables | **PASS** — `relrowsecurity=t`, `relforcerowsecurity=t`, exactly 1 `tenant_isolation_<table>` policy each |
| Downgrade → upgrade round trip | **PASS** — `alembic downgrade -1` removed RLS/FORCE/policy from all 14 tables (verified via `pg_class`/`pg_policy`); `alembic upgrade head` restored identical state |
| Cross-tenant isolation via restricted role | **PASS** — `salesos_app` (confirmed `rolsuper=false`, `rolbypassrls=false`) via the new 9-test integration suite; every one of the 14 tables proven isolated through its real application code path, not just schema inspection |
| Fail-closed NULL-tenant proof | **PASS** — an `ActivityRuntime.ingest(tenant_id=None, ...)` call is rejected by Postgres's `WITH CHECK` (raises `DBAPIError`); tenant A's own subsequent data is unaffected |
| Adjacent suite regression | **PASS**, same ephemeral container — `test_effectiveness_force_rls.py` (1 test), `test_relationships_rls.py` (7 tests), `test_feature_store_licenses_table_db.py` (2 tests): all 10 pass, no change in behavior from adding RLS to these 14 tables |
| Test collection sanity | **PASS** — `tests/unit/` + all touched `tests/integration/` files: 3795 tests collected, 0 collection errors |
| Cleanup | All ephemeral Docker resources (`dec157-pg`, `dec157-runner`, `dec157-net`, `dec157-backend:latest` image) removed after verification |

## 6. What this does not claim

- No production or staging migration. `salesos_test` and any shared/persistent
  database were never written to — verification used only a disposable
  `pgvector/pgvector:pg16` container created and destroyed within this
  session.
- Does not fix the pre-existing `test_db05_slice4_deferred_8_rls_authority.py`
  stale-count failure (§5) — that predates this session and is unrelated to
  any of the 5 modules or 14 tables this DEC touches.
- Does not reopen or affect DEC-130f (no table dropped, renamed, or
  reshaped — RLS is not a schema-shape change) or DEC-156 (a separate,
  still-unaccepted proposal about `MetaData()` island location, not RLS).
- Does not claim or move the capability census. This closure is a security/
  correctness fix to already-existing, already-counted runtime engines, not
  a new capability.

## 7. Files changed this session (DEC-157 scope only)

- `sdk/events/base.py`
- `sdk/events/store.py`
- `runtime/feature_store/features.py`
- `runtime/policy_runtime/__init__.py`
- `runtime/decision_runtime/feedback_loop.py`
- `runtime/activity_runtime/__init__.py`
- `runtime/activity_runtime/router.py`
- `app/alembic/lib/rls.py`
- `app/alembic/versions/e1d1c1225d00_dec157_orphan_keep_rls.py` (new)
- `tests/unit/test_event_runtime_subscriber_bounds.py`
- `tests/unit/test_activity_runtime_router_tenant_injection.py` (new)
- `tests/integration/test_dec157_orphan_keep_rls_db.py` (new)
- `docs/program/decisions/DEC-157-ORPHAN-KEEP-TENANT-GUC-RLS-REMEDIATION.md`
- `docs/program/DECISION_LOG.md`
