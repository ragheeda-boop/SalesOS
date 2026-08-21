# Production Migration Runbook — 2026-08-21

**Purpose:** Execute pending Alembic migrations on production Railway database to resolve P0 schema drift.  
**Current State:** Production DB at revision `f4aee055fd6e`; repo HEAD at `g1h2i3j4k5l6` (13 migrations pending).  
**Impact:** `/api/v1/companies` returns 500 for all authenticated users (`UndefinedColumnError: column companies.owner_id does not exist`).  
**Risk Level:** HIGH — production data modification, 141,221 company rows.

---

## Prerequisites

| Item | Owner | Status |
|------|-------|--------|
| Railway CLI installed | DevOps | ⏳ Verify |
| Access to Railway project `responsible-comfort` | DevOps | ⏳ Verify |
| Production environment credentials | DevOps | ⏳ Verify |
| Fresh database backup evidence | DevOps | ⏳ Verify |
| Zero blocking transactions on target tables | DevOps | ⏳ Verify |

---

## Pre-Flight Checklist

```bash
# 1. Verify current revision (expect: f4aee055fd6e)
railway run --environment production -- poetry run alembic current

# 2. Check for blocking transactions
railway run --environment production -- psql -c "SELECT pid, state, query FROM pg_stat_activity WHERE state = 'active' AND query NOT ILIKE '%pg_stat_activity%';"

# 3. Verify backup exists (PITR or pg_dump within last 1h)
# Check Railway dashboard → Backups tab for latest backup timestamp

# 4. Record pre-migration table structure
railway run --environment production -- psql -c "\d companies" > /tmp/pre_companies_schema.txt
railway run --environment production -- psql -c "SELECT COUNT(*) FROM companies;" > /tmp/pre_companies_count.txt
```

---

## Migration Execution

```bash
# Execute all pending migrations (f4aee055fd6e → g1h2i3j4k5l6)
railway run --environment production -- poetry run alembic upgrade head
```

**Expected duration:** 1-5 minutes (depends on table sizes; `companies` has 141,221 rows).

**Migration chain (13 migrations):**
1. `f4aee055fd6e` → `m5b0a1c2d3e4` (merge point)
2. `m5b0a1c2d3e4` → `ec0e98ec106b`
3. `ec0e98ec106b` → `b0d0e0f0a0d0`
4. `b0d0e0f0a0d0` → `c1d2e3f4a5b6`
5. `c1d2e3f4a5b6` → `f8b3d4e5f6a7`
6. `f8b3d4e5f6a7` → `a1b2c3d4e5f6` ← **CRITICAL: adds `companies.owner_id` + `companies.segment`**
7. `a1b2c3d4e5f6` → `b2c3d4e5f6a7`
8. `b2c3d4e5f6a7` → `c3d4e5f6a7b8`
9. `c3d4e5f6a7b8` → `d4e5f6a7b8c9`
10. `d4e5f6a7b8c9` → `e5f6a7b8c9d0`
11. `e5f6a7b8c9d0` → `f6a7b8c9d0e1`
12. `f6a7b8c9d0e1` → `g1h2i3j4k5l6` (HEAD)

**Key migration details:**
- `a1b2c3d4e5f6`: `ALTER TABLE companies ADD COLUMN owner_id UUID; ALTER TABLE companies ADD COLUMN segment VARCHAR(50);` + 3 indexes
- `f8b3d4e5f6a7`: Creates `llm_cost_entries` + `tenant_llm_budgets` tables
- `e5f6a7b8c9d0`: Creates `commercial_insights` + `commercial_evidence_items` tables
- `f6a7b8c9d0e1`: Creates `approval_requests` table

---

## Post-Migration Verification

```bash
# 1. Verify current revision matches repo HEAD (expect: g1h2i3j4k5l6)
railway run --environment production -- poetry run alembic current

# 2. Verify companies table schema
railway run --environment production -- psql -c "\d companies"
# Expected: owner_id (uuid), segment (character varying(50)) columns present

# 3. Verify row count unchanged (expect: 141,221 ± 0)
railway run --environment production -- psql -c "SELECT COUNT(*) FROM companies;"

# 4. Verify new tables exist
railway run --environment production -- psql -c "\dt" | grep -E "llm_cost|approval|commercial"

# 5. Test API endpoint (requires valid auth token)
curl -H "Authorization: Bearer <TOKEN>" https://salesos-production-96c0.up.railway.app/api/v1/companies
# Expected: 200 OK with company list

# 6. Check version endpoint
curl https://salesos-production-96c0.up.railway.app/api/v1/version
# Expected: schema_version = g1h2i3j4k5l6
```

---

## Rollback Plan (If Needed)

If migration causes issues:

```bash
# Option 1: Downgrade to previous revision
railway run --environment production -- poetry run alembic downgrade f4aee055fd6e

# Option 2: Restore from backup (if PITR available)
# Use Railway dashboard → Backups → Restore to timestamp
```

**WARNING:** `alembic downgrade` for `a1b2c3d4e5f6` will DROP `owner_id` and `segment` columns (data loss). Ensure no application code depends on these columns before downgrading.

---

## Success Criteria

| Check | Expected Result | Status |
|-------|-----------------|--------|
| `alembic current` | `g1h2i3j4k5l6` | ⏳ |
| `companies.owner_id` exists | Column present | ⏳ |
| `companies.segment` exists | Column present | ⏳ |
| Row count unchanged | 141,221 | ⏳ |
| `/api/v1/companies` | 200 OK (authenticated) | ⏳ |
| `/api/v1/version` schema_version | `g1h2i3j4k5l6` | ⏳ |

---

## Timeline

| Step | Duration | Owner |
|------|----------|-------|
| Pre-flight checks | 5 min | DevOps |
| Migration execution | 1-5 min | DevOps |
| Post-migration verification | 5 min | DevOps |
| API smoke test | 2 min | DevOps |
| **Total** | **13-17 min** | |

---

## Communication

**Before migration:**
- Notify team: "Executing production database migration to resolve P0 500 error on /companies endpoint. Expected downtime: <5 minutes."

**After migration:**
- Notify team: "Production migration complete. `/api/v1/companies` now returns 200. Schema drift resolved. All 13 pending migrations applied."

---

## Evidence Collection

After successful execution, record:
1. Screenshot of `alembic current` output
2. Screenshot of `\d companies` showing new columns
3. Screenshot of API 200 response
4. Timestamp of completion
5. Save to `evidence/ops/migrations/2026-08-21-production-migration.json`

---

## References

- `FINAL_GO_NOGO_ASSESSMENT.md` §9 — Schema drift root cause
- `docs/audit/star-audit/B03-production-migration/` — Previous migration process
- `salesos/backend/app/alembic/versions/a1b2c3d4e5f6_phase1_product_core_domain.py` — Critical migration
- `docs/ops/DR-GA-GAPS-CHECKLIST.md` — DR gate context
