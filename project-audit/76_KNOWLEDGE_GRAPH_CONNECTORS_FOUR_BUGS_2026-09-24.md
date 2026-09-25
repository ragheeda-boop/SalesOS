# 76 — Data Fabric Connectors (CRM/ERP/MarketFeed): 4 independent bugs, `store()` never worked (2026-09-24)

## Summary

`runtime/knowledge_graph_runtime/connectors.py` defines `CrmConnector`,
`ErpConnector`, and `MarketFeedConnector` — a "Data Fabric" pipeline
(authenticate → fetch → transform → store) meant to sync external company
data into `companies`. **Dead code**: confirmed via repo-wide grep that these
three classes are referenced only by their own test file
(`runtime/knowledge_graph_runtime/tests.py`), which exercises `transform()`,
`authenticate()`, `_mock_fetch()`, and `sync()`-without-auth, but **never**
calls `store()` against a real database — so its SQL had never actually been
executed by any test, ever. Every one of the 3 `store()` methods had the
same 3 of 4 bugs; `ErpConnector`/`MarketFeedConnector` had a 4th.

## Bugs found (all confirmed via direct reproduction against the real schema before any fix)

1. **INSERT referenced a `source` column that does not exist on `companies`.**
   Confirmed via `\d companies` and a direct INSERT:
   ```
   ERROR:  column "source" of relation "companies" does not exist
   ```
   All 3 connectors' `store()` methods hardcoded a literal `'crm'`/`'erp'`/
   `'market_feed'` into this non-existent column. Fixed by using the model's
   actual `source_ids` JSONB column instead (a JSON array containing the
   connector type string) — an existing column whose evident purpose
   (list of contributing sources) matches what the code was trying to do.

2. **External source ids bound directly to the `uuid` primary key `id`.**
   `record.source_id` (values like `"crm-001"`, `"erp-001"`, `"mkt-001"`)
   was passed straight as `:id`. Confirmed via direct INSERT:
   ```
   ERROR:  invalid input syntax for type uuid: "crm-001"
   ```
   Fixed by deriving a deterministic `uuid5` from
   `(tenant_id, connector_type, source_id)` via a new
   `_derive_company_id()` helper — this preserves the file's intended
   idempotent `ON CONFLICT (id) DO UPDATE` upsert semantics (the same
   external id always maps to the same row on re-sync) without requiring a
   schema change for a raw external-id column.

3. **No tenant GUC pinning anywhere in any `store()` method.** `companies`
   has RLS + FORCE RLS (confirmed via `pg_class.relrowsecurity`/
   `relforcerowsecurity`); every real write would fail its `WITH CHECK` even
   after fixing bugs 1 and 2. `apply_tenant_guc()` added to all 3 `store()`
   methods, matching the DEC-085 canonical pattern used everywhere else in
   this codebase.

4. **`ErpConnector` and `MarketFeedConnector` never supplied `name_ar`**,
   which is `NOT NULL` on `companies` with no default. Confirmed via direct
   INSERT:
   ```
   ERROR:  null value in column "name_ar" of relation "companies" violates not-null constraint
   ```
   (`CrmConnector` was unaffected — it already included `name_ar` in its
   transform/insert.) Fixed by falling back to the English name for both
   connectors, matching `CrmConnector.transform()`'s own existing
   `name_ar` fallback pattern (`raw.get("name_ar", raw.get("name", ""))`).

Net effect before this fix: every real `store()` call, for all 3 connector
types, would have raised on its very first INSERT attempt (bug 1), and even
past that would have failed on bug 2, bug 3 (RLS), and — for ERP/MarketFeed —
bug 4. This connector pipeline could never have persisted a single row.

## Fixes

**`runtime/knowledge_graph_runtime/connectors.py`**:
- Added `import json`, `import uuid`, `from app.database import apply_tenant_guc`.
- Added `_CONNECTOR_UUID_NAMESPACE` constant and `_derive_company_id()` helper.
- `CrmConnector.store()`, `ErpConnector.store()`, `MarketFeedConnector.store()`:
  - Pin `app.tenant_id` once per `store()` call (before the per-record loop).
  - Replace the non-existent `source` column with `source_ids` (JSONB array).
  - Replace `record.source_id` as `:id` with `_derive_company_id(...)`.
  - `ErpConnector`/`MarketFeedConnector` additionally now supply `name_ar`
    (falling back to `name_en`).

## Verification

Fresh ephemeral `pgvector/pgvector:pg16` container, `salesos_app` restricted
role (non-superuser, `NOBYPASSRLS`).

**New file**: `tests/integration/test_knowledge_graph_connectors_store_db.py`
(2 tests):
- `test_crm_connector_store_persists_and_is_idempotent_and_tenant_scoped` —
  first sync persists and is invisible to a different tenant (RLS); a
  second sync with the same external id updates the same row rather than
  duplicating it (proves the derived-UUID upsert key preserves idempotency).
- `test_erp_and_market_feed_connectors_store_persists` — both connectors
  persist a row each under the same tenant.

**Genuine red→green, all 4 bugs isolated independently**:
- Bugs 1 and 2 were each independently confirmed via direct raw-SQL
  reproduction against the real schema (`psql`, exact error text captured
  above) *before* any code fix was written — the same evidentiary standard
  as a code-level revert-and-rerun.
- Bug 3 (GUC pin): removed only the `apply_tenant_guc()` call from
  `CrmConnector.store()`, re-ran the CRM test — confirmed it failed exactly
  as predicted (`assert 0 == 1`). Restored, re-confirmed passing.
- Bug 4 (`name_ar`): reverted only the `ErpConnector` INSERT to omit
  `name_ar`, re-ran the ERP/MarketFeed test — confirmed it failed exactly as
  predicted (`assert 0 == 1`). Restored, re-confirmed passing.

**Existing unit regression** (`runtime/knowledge_graph_runtime/tests.py`,
the mocked `transform`/`authenticate`/`_mock_fetch`/`sync` tests for all 3
connectors): **13/13 PASS**, unaffected by these changes.

**Combined session regression** (all integration tests from reports
68/70–76 run together in the same container): **33/33 PASS**, no cross-fix
regressions.

**Full local unit suite** (`tests/unit/`): **3766 passed, 0 failed** (4
skipped, 7 xfailed, 3 xpassed — all pre-existing categories) — clean
baseline reconfirmed.

## Production / Phase 7

These classes are not wired into any router, boot sequence, or scheduled
job — fixed ahead of any future wiring decision, same posture as reports
73/74. No production or `salesos_test` write; only a disposable, ephemeral
Postgres container was used, destroyed after verification. Phase 7 remains
BLOCKED; production remains **NOT APPROVED**.
