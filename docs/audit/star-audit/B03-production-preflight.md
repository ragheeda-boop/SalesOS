# B03 PRODUCTION PREFLIGHT

**Date:** 2026-08-09
**Environment:** Production (Railway `responsible-comfort` → `production`)
**Method:** Read-only SQL via public TCP proxy (`interchange.proxy.rlwy.net:13698`)
**Production modified:** NO

---

## PostgreSQL

- **Version:** PostgreSQL 18.4 (Debian 18.4-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
- **Major:** 18
- **PASS:** YES

## Current Schema

- **alembic_version:** d1a8c35e7f09
- **PASS:** YES

- **Tables:** 96
- **RLS policies:** 67
- **FORCE RLS:** 67

> Note: Production is at d1a8c35e7f09 (pre-migration). Target f7a1b82c3d09 adds 41 tables, 6 RLS policies, 5 FORCE RLS.

## Database Health

- **Connection:** SUCCESS (via `interchange.proxy.rlwy.net:13698`)
- **Database:** railway
- **Started at:** 2026-08-06 19:29:20.770918+00:00
- **Uptime:** 2 days, 3:05:13
- **Active transactions:** 1
- **Blocking transactions:** 0

## Backup

- **Latest usable backup/restore point:** pgBackRest WAL archiving active
- **Backup identifier:** `salesos-pitr-w-857q3fjjrr` (Railway-managed pgBackRest S3 bucket)
- **Archive/WAL status:** 2600+ WAL segments archived; `archive_mode=on`, `wal_level=replica`
- **Last full backup:** 2026-08-06 19:29:50 UTC
- **Restore capability evidence:** PITR restore drill proven (`ops01-row3-pitr-restore.json`)
- **Sufficient for migration:** YES

## Migration Chain

- **Current:** d1a8c35e7f09
- **Target:** f7a1b82c3d09
- **Pending:** 16 revisions
- **Chain verified:** YES (single linear chain, no branches, no merges)

```
d1a8c35e7f09
    ↓ e2b9d46f8a10 (db05_slice5c_create_admin_global_trio)
    ↓ a4f7c29e1b80 (db05_slice5d_indexes_types_nullable)
    ↓ f6b2e84c1a90 (story_04_01_tenant_owner_platform_fields)
    ↓ c3a9f12d4e80 (story_05_01_subscriptions_table)
    ↓ d4b0e23f5a91 (story_04_04_tenant_deleted_at)
    ↓ e5c1f34a6b02 (story_05_02_stripe_webhook_ledger)
    ↓ f6d2a45b7c03 (story_05_02_portal_invoices_catalog)
    ↓ a7e3b56c8d04 (story_05_03_usage_meters)
    ↓ b8f4c67d9e15 (story_05_04_dunning_cases)
    ↓ c9e5d78a0f26 (story_05_05_pending_plan_change)
    ↓ d0f6e89b1a37 (story_06_01_plan_entitlements)
    ↓ e1a7b68c2d05 (story_08_02_external_system_connections)
    ↓ f2b8c79d3e06 (story_08_03_field_mapping_configs)
    ↓ c4d8e21a9f07 (story_08_05_sync_runs)
    ↓ e5f9a32b0c08 (story_08_06_conflict_resolution_policies)
    ↓ f7a1b82c3d09 (phase2_tasks_opportunity_id_signals) ← HEAD
```

**PASS:** YES

## Backfill Preview

- **f6b2e84c1a90 (provisioning_status):** Column does not exist on `companies` — expected, added by this migration
- **d4b0e23f5a91 (deleted_at):** Column does not exist on `companies` — expected, added by this migration
- **d0f6e89b1a37 (admin_plans entitlements):** Table does not exist — expected, created by this migration

> All three backfill targets are in pending migrations. Row counts will be 0 on first application (idempotent). Confirmed by isolated PG18 testing.

## Read-Only Safety

- **Production schema modified:** NO
- **Production data modified:** NO
- **Migration executed:** NO
- **Deployment:** NO
- **Railway configuration modified:** NO
- **Restore executed:** NO

## Decision

**READY**

All conditions met:
1. PostgreSQL = 18.x ✓
2. alembic_version = d1a8c35e7f09 ✓
3. Database connectivity healthy ✓
4. No unexplained blocking transaction ✓
5. Backup/restore point is sufficient ✓
6. 16-revision chain confirmed ✓
7. Backfill preview understood ✓
8. No unexpected production drift discovered ✓

## Gate

- **B03 Production Reconciliation:** NOT EXECUTED
- **B05:** BLOCKED

> A successful preflight means: "Production is eligible for a separate migration authorization."
> It does NOT authorize the migration.
