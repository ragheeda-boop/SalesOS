# Staging Deploy Checklist — 2026-08-21

**Purpose:** Fast-forward staging to master and deploy to resolve staging parity gap.  
**Current State:** Staging branch 47 commits behind master; no divergent history.  
**Prerequisites:** Production migration must complete first (P0).

---

## Pre-Deploy Checklist

| Item | Owner | Status |
|------|-------|--------|
| Production migration complete (`alembic current` = `g1h2i3j4k5l6`) | DevOps | ⏳ Verify |
| `deploy-staging.yml` schema-drift-gate fixed (Python/Poetry setup added) | Engineering | ✅ Done |
| Staging Railway environment exists and is healthy | DevOps | ⏳ Verify |
| Staging secrets configured (DATABASE_URL, SECRET_KEY, etc.) | DevOps | ⏳ Verify |
| Staging OAuth credentials separate from production | DevOps | ⏳ OPEN (staging OAuth app not created) |

---

## Step 1: Fast-Forward Staging Branch

```bash
# Option A: Force-push (clean, linear history)
git push origin master:staging --force

# Option B: Merge (preserves history, creates merge commit)
git checkout staging
git merge master
git push origin staging
```

**Recommendation:** Option A (force-push) — staging has no unique commits, so force-push is clean and maintains linear history.

---

## Step 2: Trigger Staging Deploy

```bash
# Via GitHub Actions CLI
gh workflow run deploy-staging.yml \
  --field environment=staging \
  --field confirm_staging_deploy="CONFIRM-STAGING-DEPLOY" \
  --field skip_backend=false

# Via GitHub UI
# Go to Actions → Deploy (Staging) → Run workflow → Fill confirmation → Run
```

**Expected duration:** 5-10 minutes (backend build + deploy + health check).

---

## Step 3: Verify Staging Schema

```bash
# Check staging schema version
railway run --environment staging -- poetry run alembic current
# Expected: g1h2i3j4k5l6

# Verify companies table
railway run --environment staging -- psql -c "\d companies"
# Expected: owner_id, segment columns present
```

**Note:** If staging DB is empty/fresh, migrations will run automatically on first deploy (unlike production which has B03-B safety control).

---

## Step 4: Verify Staging API

```bash
# Health check
curl https://staging-salesos.up.railway.app/health
# Expected: {"status":"ok","database":"connected","redis":"connected"}

# Version check
curl https://staging-salesos.up.railway.app/api/v1/version
# Expected: schema_version = g1h2i3j4k5l6

# Companies endpoint (requires auth)
curl -H "Authorization: Bearer <STAGING_TOKEN>" https://staging-salesos.up.railway.app/api/v1/companies
# Expected: 200 OK
```

---

## Step 5: Configure Staging OAuth (If Needed)

If staging OAuth app doesn't exist yet:

1. Go to Google Cloud Console → Credentials → Create OAuth 2.0 Client ID
2. Set redirect URI to staging domain
3. Set `SSO_GOOGLE_CLIENT_ID` and `SSO_GOOGLE_CLIENT_SECRET` in Railway staging environment
4. Redeploy staging
5. Test SSO round-trip

---

## Step 6: Update Staging Documentation

After successful deploy, update:
- `docs/ops/A-09-STAGING-PARITY-ANALYSIS-2026-08-20.md` — mark staging parity as complete
- `docs/audit/ga-engineering-audit/OPS-01-CHECKLIST.md` — mark OPS01-04 as ready for soak

---

## Success Criteria

| Check | Expected Result | Status |
|-------|-----------------|--------|
| Staging branch | At same commit as master | ⏳ |
| `deploy-staging.yml` | Passes (schema-drift-gate + health-check) | ⏳ |
| Staging `alembic current` | `g1h2i3j4k5l6` | ⏳ |
| Staging `/health` | `{"status":"ok"}` | ⏳ |
| Staging `/api/v1/companies` | 200 OK (authenticated) | ⏳ |

---

## Timeline

| Step | Duration | Owner |
|------|----------|-------|
| Fast-forward staging branch | 1 min | DevOps |
| Trigger staging deploy | 2 min | DevOps |
| Wait for deploy | 5-10 min | Automated |
| Schema verification | 3 min | DevOps |
| API smoke test | 2 min | DevOps |
| OAuth setup (if needed) | 15-30 min | DevOps |
| **Total** | **23-48 min** | |

---

## Blockers

| Blocker | Resolution | Owner |
|---------|------------|-------|
| Production migration not complete | Complete P0 migration first | DevOps |
| Staging OAuth app not created | Create staging OAuth client | DevOps |
| Schema-drift-gate not validated | Trigger manual deploy to test | DevOps |

---

## References

- `docs/ops/A-09-STAGING-PARITY-ANALYSIS-2026-08-20.md` — Staging parity analysis
- `.github/workflows/deploy-staging.yml` — Staging deploy workflow
- `docs/ops/OPS-01-DR-SIGNOFF-CHECKLIST-2026-08-20.md` — DR sign-off context
