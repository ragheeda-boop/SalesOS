# Pre-Production Migration Risk Assessment

**Date:** 2026-08-07  
**Product:** SalesOS  
**Range:** `d1a8c35e7f09` → `e5f9a32b0c08` (revisions **after** current, **including** target)  
**Method:** Static review of Alembic scripts under `salesos/backend/app/alembic/versions/`  
**Migrations executed:** **NONE**  
**Production / staging DB writes:** **NONE**  
**Validation label:** **not validated** against prod DB (no live schema probe; no `alembic upgrade`)  
**Production GA:** still **NO-GO**

> AI assists. Humans decide. Evidence governs.  
> Do **not** treat this document as approval to run migrations.

**Related prep (older head pin):** [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) — Wave 12 / PROD-W1 migrate **PREP DONE / EXECUTION BLOCKED** (historically pinned toward `0040`; this assessment covers a **later** tip range).  
**Policy:** Prefer forward-fix over Alembic downgrade ([runbooks/deploy-rollback.md](./runbooks/deploy-rollback.md)).

---

## Final verdict

### **REQUIRES MAINTENANCE WINDOW**

Not **SAFE TO EXECUTE** online without a write-quiet window: the path includes **37 non-`CONCURRENTLY` index creates** on live hot tables (`companies`, `contacts`, `emails`, `meetings`, …), multiple **DML backfills**, **FORCE RLS** on new Integration Hub tables, and a **RANGE-partitioned** `sync_runs` parent with 25 child partitions. No broken chain / multi-head in this range; no upgrade-path column drops. DBA spot-check of `a4f7c29e1b80` (index lock budget) is strongly recommended before the window, but the overall class is maintenance-window rather than “blocked pending unknown DDL.”

---

## Scope & chain integrity

| Item | Finding |
|------|---------|
| Current (exclusive start) | `d1a8c35e7f09` — DB-05 Slice 4 deferred-8 RLS |
| Target (inclusive end) | `e5f9a32b0c08` — STORY-08-06 conflict_resolution_policies |
| Chain length | **15** revisions |
| Topology | **Linear** — single child of `d1a8c35e7f09` is `e2b9d46f8a10`; each subsequent revision has exactly one `down_revision` predecessor in this path |
| Merge heads / multiple heads in range | **None detected** (static `down_revision` walk) |
| Broken chain | **No** |

---

## 1. Ordered migration chain

| # | Revision | Filename | Short title |
|--:|----------|----------|-------------|
| 1 | `e2b9d46f8a10` | `e2b9d46f8a10_db05_slice5c_create_admin_global_trio.py` | DB-05 Slice 5c: CREATE admin_plans / admin_feature_flags / admin_health_snapshots |
| 2 | `a4f7c29e1b80` | `a4f7c29e1b80_db05_slice5d_indexes_types_nullable.py` | DB-05 Slice 5d: 37 additive indexes + contacts VARCHAR widen |
| 3 | `f6b2e84c1a90` | `f6b2e84c1a90_story_04_01_tenant_owner_platform_fields.py` | STORY-04-01: tenants owner/platform columns + provisioning backfill |
| 4 | `c3a9f12d4e80` | `c3a9f12d4e80_story_05_01_subscriptions_table.py` | STORY-05-01: CREATE subscriptions |
| 5 | `d4b0e23f5a91` | `d4b0e23f5a91_story_04_04_tenant_deleted_at.py` | STORY-04-04: tenants.deleted_at + settings backfill |
| 6 | `e5c1f34a6b02` | `e5c1f34a6b02_story_05_02_stripe_webhook_ledger.py` | STORY-05-02: Stripe webhook ledger + subscription Stripe ids |
| 7 | `f6d2a45b7c03` | `f6d2a45b7c03_story_05_02_portal_invoices_catalog.py` | STORY-05-02b: plan Stripe price ids + platform_billing_invoices |
| 8 | `a7e3b56c8d04` | `a7e3b56c8d04_story_05_03_usage_meters.py` | STORY-05-03: usage_meter_events + usage_meters |
| 9 | `b8f4c67d9e15` | `b8f4c67d9e15_story_05_04_dunning_cases.py` | STORY-05-04: dunning_cases |
| 10 | `c9e5d78a0f26` | `c9e5d78a0f26_story_05_05_pending_plan_change.py` | STORY-05-05: subscriptions pending plan columns |
| 11 | `d0f6e89b1a37` | `d0f6e89b1a37_story_06_01_plan_entitlements.py` | STORY-06-01: admin_plans.entitlements JSONB + Python tier backfill |
| 12 | `e1a7b68c2d05` | `e1a7b68c2d05_story_08_02_external_system_connections.py` | STORY-08-02: external_system_connections + FORCE RLS |
| 13 | `f2b8c79d3e06` | `f2b8c79d3e06_story_08_03_field_mapping_configs.py` | STORY-08-03: field_mapping_configs + FORCE RLS |
| 14 | `c4d8e21a9f07` | `c4d8e21a9f07_story_08_05_sync_runs.py` | STORY-08-05: sync_runs RANGE partitions + FORCE RLS |
| 15 | `e5f9a32b0c08` | `e5f9a32b0c08_story_08_06_conflict_resolution_policies.py` | STORY-08-06: conflict_resolution_policies + FORCE RLS |

---

## 2. Risk level per migration

| # | Revision | Risk | Rationale (ops found in file) |
|--:|----------|:----:|-------------------------------|
| 1 | `e2b9d46f8a10` | **LOW** | Idempotent `CREATE TABLE` for three empty/global admin tables + one index. No DML. Downgrade drops tables (data loss if populated later). |
| 2 | `a4f7c29e1b80` | **HIGH** | Up to **37** `op.create_index` calls **without** `CONCURRENTLY` on existing tables (`companies`, `contacts`, `emails`, `meetings`, commercial_*, etc.) → `ShareLock` write blocking for build duration. Also `ALTER COLUMN … TYPE VARCHAR(500)` widen on `contacts.name` / `name_ar` (PG widen usually metadata-only; still DDL). Downgrade narrows to VARCHAR(255) — can fail or truncate if values >255. |
| 3 | `f6b2e84c1a90` | **MEDIUM** | Additive columns on `tenants`; one NOT NULL + `server_default`; then `UPDATE tenants SET provisioning_status='active' WHERE …`. Small table expected, but exclusive-ish DDL + DML in same revision. Downgrade drops columns (irreversible for app state). |
| 4 | `c3a9f12d4e80` | **LOW** | Idempotent `CREATE TABLE subscriptions` + indexes. No RLS/DML. |
| 5 | `d4b0e23f5a91` | **LOW** | Nullable `deleted_at` + index + conditional `UPDATE` from `settings` JSON. Tenants-scale DML. |
| 6 | `e5c1f34a6b02` | **LOW** | Additive nullable Stripe columns + `CREATE INDEX IF NOT EXISTS` + new `stripe_webhook_events` table. |
| 7 | `f6d2a45b7c03` | **LOW** | Additive nullable price-id columns on `admin_plans` + new `platform_billing_invoices` + unique constraint on stripe id. |
| 8 | `a7e3b56c8d04` | **LOW** | Two new Owner-plane usage tables + indexes. Empty at create. |
| 9 | `b8f4c67d9e15` | **LOW** | New `dunning_cases` + indexes. Empty at create. |
| 10 | `c9e5d78a0f26` | **SAFE** | Two nullable additive columns on `subscriptions` only. No DML/indexes. |
| 11 | `d0f6e89b1a37` | **MEDIUM** | Adds `entitlements` JSONB with server default, then **Python row loop** importing `app.modules.admin.entitlements` and issuing per-row `UPDATE`. Plans table usually tiny, but migrate depends on app package + image layout; failure mid-loop is partial backfill risk. |
| 12 | `e1a7b68c2d05` | **MEDIUM** | New tenant table + FKs + indexes, then `generate_policy_sql` → `ENABLE`/`FORCE ROW LEVEL SECURITY` + `CREATE POLICY`. New table so lock blast radius is low; **FORCE RLS** is operationally sensitive if runtime `app.tenant_id` / DEC-085 path is wrong (app correctness, not lock). Requires `scripts.generate_rls_policies` importable in migrate image. |
| 13 | `f2b8c79d3e06` | **MEDIUM** | Same pattern as #12 for `field_mapping_configs` (FK to connections + unique constraint + FORCE RLS). |
| 14 | `c4d8e21a9f07` | **MEDIUM** | Creates **RANGE-partitioned** `sync_runs` (composite PK `id, started_at`), **24 monthly partitions (2026–2027) + DEFAULT**, indexes, then FORCE RLS. Many DDL statements; partition DDL is fine on empty parent but is non-trivial ops surface (future months beyond 2027 need ops care). |
| 15 | `e5f9a32b0c08` | **MEDIUM** | New `conflict_resolution_policies` + unique on `connection_id` + FORCE RLS (same Integration Hub / script dependency pattern). |

**Highest risk level seen:** **HIGH** (`a4f7c29e1b80`).

---

## 3. Detect & flag matrix

Legend: Y = present in upgrade path of that revision.

| Revision | Schema | Data/DML | Locks note | Index rebuild / create | Table rewrite | Long txn risk | Col drop (upgrade) | Constraints | Triggers | Irreversible / weak downgrade |
|----------|:------:|:--------:|------------|:----------------------:|:-------------:|:-------------:|:------------------:|:-----------:|:--------:|-------------------------------|
| `e2b9…` | Y | — | Catalog DDL on new tables | Y (1 idx) | — | Low | — | PK | — | Downgrade DROP TABLE |
| `a4f7…` | Y | — | **ShareLock** on many live tables during non-concurrent index builds; ALTER TYPE | **Y (≤37)** | Unlikely (varchar widen) | **Medium–High** if large tables | — | — | — | Downgrade VARCHAR shrink **unsafe** |
| `f6b2…` | Y | **Y UPDATE** | ADD COLUMN on `tenants` | — | Unlikely (defaults) | Low–Med | — | — | — | DROP columns |
| `c3a9…` | Y | — | New table | Y | — | Low | — | UNIQUE tenant_id | — | DROP TABLE |
| `d4b0…` | Y | **Y UPDATE** | ADD COLUMN + index | Y | — | Low | — | — | — | DROP column |
| `e5c1…` | Y | — | ADD COLUMN + indexes + CREATE | Y | — | Low | — | PK on events | — | DROP cols/table |
| `f6d2…` | Y | — | ADD COLUMN + CREATE + UNIQUE | Y | — | Low | — | UNIQUE stripe_invoice_id | — | DROP |
| `a7e3…` | Y | — | CREATE | Y | — | Low | — | UNIQUE meter period | — | DROP |
| `b8f4…` | Y | — | CREATE | Y | — | Low | — | — | — | DROP |
| `c9e5…` | Y | — | ADD COLUMN nullable | — | — | Low | — | — | — | DROP cols |
| `d0f6…` | Y | **Y Python UPDATEs** | ADD COLUMN | — | — | Low (small N) / Med if many plans | — | — | — | DROP entitlements |
| `e1a7…` | Y | — | CREATE + **FORCE RLS** | Y | — | Low | — | FK tenants | — | DROP policy/table |
| `f2b8…` | Y | — | CREATE + **FORCE RLS** | Y | — | Low | — | FK + UNIQUE | — | DROP |
| `c4d8…` | Y | — | Partitioned CREATE + **many partition DDLs** + FORCE RLS | Y | — (new empty) | Med (DDL volume) | — | Composite PK + FKs | — | DROP parent CASCADE |
| `e5f9…` | Y | — | CREATE + FORCE RLS | Y | — | Low | — | FK + UNIQUE | — | DROP |

### Summary flags (range)

| Flag | Status |
|------|--------|
| Schema changes | **Yes** — throughout (CREATE TABLE / ADD COLUMN / indexes / partitions / RLS) |
| Data migrations | **Yes** — `f6b2e84c1a90`, `d4b0e23f5a91`, `d0f6e89b1a37` |
| Dangerous locks | **Yes** — non-concurrent indexes in `a4f7c29e1b80` (write blocking); RLS ENABLE/FORCE is AccessExclusive-class DDL but on **new** tables |
| Index rebuilds | **Creates** (not REINDEX) — especially `a4f7c29e1b80` |
| Table rewrites | **Not expected** for varchar widen; no `USING` casts / type-downsizes in upgrade |
| Long transactions | **Possible** if all 15 run in one Alembic session while index builds hold locks — keep window write-quiet |
| Column drops (upgrade) | **None** |
| Constraint changes | **Yes** — new UNIQUE/PK/FK on new tables; no ALTER of legacy FKs observed |
| Trigger changes | **None** observed |
| Irreversible | No empty/`pass`-only / `NotImplemented` downgrades; several downgrades are **destructive** (DROP TABLE/COLUMN) or **unsafe** (`a4f7` varchar shrink). Prefer restore-from-backup over downgrade. |

---

## 4. Estimates (honest ranges)

**Assumptions**

- Prod row counts / table sizes **unknown** in this review.
- Local / audit evidence such as small `pg_dump` sizes (e.g. ~22MB in Wave docs) is **not** production size.
- Indexes created with default (non-concurrent) Alembic `create_index`.
- Deploy image includes `scripts/generate_rls_policies.py` (required by STORY-08-* revisions).
- Single `alembic upgrade e5f9a32b0c08` transaction/session semantics as Alembic default (per-revision commits depending on env — still sequential lock exposure).

| Estimate | Range | Notes |
|----------|-------|-------|
| **Downtime / write impact** | **5–45+ minutes** write degradation or planned freeze | Dominated by `a4f7c29e1b80` ShareLock index builds on hot tables. Empty/new-table revisions: seconds each. If prod tables are large, use upper bound or split window. |
| **Execution time** | **~2–30+ minutes** wall clock | Lower bound: small DB / indexes already exist (idempotent skips). Upper: large `companies`/`emails`/`meetings` index builds + 25 partition DDLs. |
| **Rollback complexity** | **HIGH** | Alembic downgrade of 15 steps is **not** the preferred recovery ([Wave 12 prep](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md)). Several downgrades DROP tables/columns; `a4f7` reverse ALTER can fail. **Restore from pre-migrate backup** is the honest rollback path. |

---

## 5. Preconditions before any approved execution

Align with [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) (still **EXECUTION BLOCKED** until human gates close):

1. Verified backup + restore drill for **target** env  
2. Staging upgrade of this same range to `e5f9a32b0c08` with smoke  
3. Confirm migrate runtime can `import scripts.generate_rls_policies`  
4. Maintenance window sized for non-concurrent indexes  
5. Explicit human approval — **this document is not approval**  
6. Prefer forward-fix + backup restore over multi-step downgrade  

---

## Evidence — files read

All under `salesos/backend/app/alembic/versions/`:

1. `e2b9d46f8a10_db05_slice5c_create_admin_global_trio.py`  
2. `a4f7c29e1b80_db05_slice5d_indexes_types_nullable.py`  
3. `f6b2e84c1a90_story_04_01_tenant_owner_platform_fields.py`  
4. `c3a9f12d4e80_story_05_01_subscriptions_table.py`  
5. `d4b0e23f5a91_story_04_04_tenant_deleted_at.py`  
6. `e5c1f34a6b02_story_05_02_stripe_webhook_ledger.py`  
7. `f6d2a45b7c03_story_05_02_portal_invoices_catalog.py`  
8. `a7e3b56c8d04_story_05_03_usage_meters.py`  
9. `b8f4c67d9e15_story_05_04_dunning_cases.py`  
10. `c9e5d78a0f26_story_05_05_pending_plan_change.py`  
11. `d0f6e89b1a37_story_06_01_plan_entitlements.py`  
12. `e1a7b68c2d05_story_08_02_external_system_connections.py`  
13. `f2b8c79d3e06_story_08_03_field_mapping_configs.py`  
14. `c4d8e21a9f07_story_08_05_sync_runs.py`  
15. `e5f9a32b0c08_story_08_06_conflict_resolution_policies.py`  

Also referenced (policy generator, not a revision): `salesos/backend/scripts/generate_rls_policies.py` (ENABLE/FORCE RLS + CREATE POLICY).

**Commands run:** filesystem Glob/Grep/Read only; temporary chain parser deleted; **no** `alembic upgrade` / `downgrade`; **no** prod/staging DB connection for migrate.

**Commit:** none (documentation deliverable only; not committed by this assessment).

---

## Cross-links

| Doc | Role |
|-----|------|
| [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) | Wave 12 prod migrate prep / execution blocked |
| [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md) | Wave 12 deploy/rollback program |
| [runbooks/deploy-rollback.md](./runbooks/deploy-rollback.md) | Forward-fix preference |
| [RELEASE-BACKLOG-2026-08-06.md](./RELEASE-BACKLOG-2026-08-06.md) | Ops backlog (staging/prod gates) |
| [README.md](./README.md) | GA audit index |
