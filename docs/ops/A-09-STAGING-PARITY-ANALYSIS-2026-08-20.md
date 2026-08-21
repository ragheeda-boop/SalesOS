# A-09 Staging Parity Analysis — Current State (2026-08-20)

**Classification:** INFRASTRUCTURE AUDIT — Light Validated
**Supersedes:** `A09_STAGING_PARITY.md` (2026-08-13) for current gap metrics

---

## Executive Summary

| Metric | Previous (2026-08-13) | Current (2026-08-20) | Status |
|--------|----------------------|----------------------|--------|
| **Staging host** | `salesos-staging.up.railway.app` | `salesos-staging.up.railway.app` | ✅ Exists |
| **Staging branch** | `staging` (remote) | `staging` (local + remote) | ✅ Exists |
| **Commit gap** | 409 behind (stale claim) | **47 behind master** | ✅ Reduced |
| **CI deploy workflow** | `deploy-staging.yml` SUCCESS [31649846410] | Same workflow, untested since | ⚠️ Needs re-run |
| **Business data seed** | muhide + 5 companies (2026-08-12) | Same seed, untested since | ⚠️ Stale |
| **Human-Gate items** | 8 open (OAuth, PITR, max_conn, rollback, soak, etc.) | **8 still open** | ❌ Unchanged |
| **Soak claim** | `soak_complete_claim=false` | `soak_complete_claim=false` | ❌ Unchanged |

**Verdict:** **CONDITIONAL / OPEN** — Gap reduced from 409→47 commits, but all Human-Gate residuals remain.

---

## 1. Commit Gap Analysis

```bash
# Current state (2026-08-20)
git log --oneline staging..master | wc -l
# → 47 commits

git log --oneline master..staging | wc -l
# → 0 commits (staging has no unique commits)
```

**Interpretation:** Staging is a strict subset of master (47 commits behind). No divergent history on staging.

**Key commits on master since staging:**

| Commit | Date | Summary |
|--------|------|---------|
| `ac79861` | 2026-08-20 | fix-CSP-script-src-for-Next.js-RSC-hydration |
| `c8b473f` | 2026-08-20 | chore: gitignore soak evidence loop JSONs (582 files) |
| `fd93d68` | 2026-08-19 | fix(tests): resolve 38 pre-existing failures (2388 pass, 10 xfail) |
| `5183c61` | 2026-08-19 | test: update remaining test files for Phase 1-4 compatibility |
| `4f9fc0b` | 2026-08-19 | fix: chaos resilience + DR drill + load SLO + marketplace wiring |
| ... | ... | ... (47 total) |

**Risk:** The CSP fix (`ac79861`) is deployed to production (Vercel) but **not to staging**. Staging FE may still have CSP hydration issues.

---

## 2. Deploy Plan to Close Gap

### Option A: Fast-forward staging to master (Recommended)

```bash
# 1. Push master to staging branch
git push origin master:staging --force

# 2. Trigger deploy-staging.yml manually
# GitHub Actions → Deploy Staging → confirm_staging=CONFIRM-STAGING-DEPLOY

# 3. Verify staging health
curl https://salesos-staging.up.railway.app/health
# → 200 OK

# 4. Re-seed Decision data (if DB was reset)
railway run --project $PROJECT_ID --environment $STAGING_ENV_ID --service $STAGING_SERVICE_ID -- \
  python seed_staging_decision_minimal.py
```

**Risk:** Force-push rewrites staging history. Acceptable since staging has no unique commits.

### Option B: Merge master into staging (Safer)

```bash
git checkout staging
git merge master --no-ff
git push origin staging
# Then trigger deploy-staging.yml
```

**Risk:** Creates merge commit. No functional difference for deploy.

### Option C: Deploy master directly to staging env (No branch change)

The `deploy-staging.yml` uses `--environment staging` which targets the Railway staging environment, not the git branch. Could deploy from any commit:

```yaml
# In deploy-staging.yml, add:
#   ref:
#     description: "Git ref to deploy (default: staging branch)"
#     required: false
#     type: string
#     default: staging
```

Then trigger with `ref=master`.

---

## 3. Human-Gate Residuals (Unchanged Since 2026-08-13)

| # | Item | Status | Blocker |
|---|------|--------|---------|
| 1 | Google OAuth staging app | **OPEN** | Requires Google Cloud Console setup |
| 2 | WAL/PITR/offsite posture acceptance | **OPEN** | Requires Platform sign-off |
| 3 | Postgres `max_connections` 100→500 | **OPEN** | Requires Railway support or acceptance |
| 4 | Rollback tabletop dated notes | **OPEN** | Template exists; needs human execution |
| 5 | Wave 11 soak claim unlock (U1–U5) | **OPEN** | Requires TL/DevOps review of 72h triage |
| 5 | Reconcile Railway env UUIDs | **OPEN** | User-supplied UUIDs not in CLI workspace |
| 6 | Local WIP (entrypoint/Dockerfile/celery_app) | **OPEN** | Uncommitted changes after df5028c |
| 7 | Neo4j `:6432` on dispatch | **CLOSED** (was Postgres misconfig) | — |

**Note:** The 72h soak (Wave 11) failed at 97.6% due to DB outage. Triage done (`ae76dae`). Claim cannot advance without human review of triage.

---

## 4. Schema Drift on Staging (New Risk)

**Production schema drift confirmed:** Migration `a1b2c3d4e5f6` (adds `companies.owner_id`) missing on production DB.

**Staging likely has same drift** — if staging DB was never migrated after the migration was added to repo.

**Action:** Run schema drift check on staging before/after deploy:

```bash
railway run --project $PROJECT_ID --environment $STAGING_ENV_ID --service $STAGING_SERVICE_ID -- \
  alembic current --verbose
# Compare stamp to repo HEAD (g1h2i3j4k5l6)
```

If staging is also at `f4aee055fd6e`, it will hit the same `UndefinedColumnError` on `/api/v1/companies`.

---

## 5. Recommended Next Steps (Priority Order)

| Priority | Action | Owner | Estimated Effort |
|----------|--------|-------|------------------|
| **P0** | Fast-forward staging to master (`git push origin master:staging --force`) | DevOps | 5 min |
| **P0** | Run `deploy-staging.yml` with `confirm_staging=CONFIRM-STAGING-DEPLOY` | DevOps | 10 min |
| **P0** | Verify staging `/health` + `/api/v1/companies` (schema drift check) | DevOps | 5 min |
| **P0** | Re-seed Decision data if DB reset | Backend | 5 min |
| **P1** | Close Human-Gate #1: Google OAuth staging app | DevOps | 30 min |
| **P1** | Close Human-Gate #2: WAL/PITR/offsite acceptance | Platform | 1 hr |
| **P1** | Close Human-Gate #3: max_connections acceptance | DevOps/Platform | 15 min |
| **P1** | Close Human-Gate #4: Rollback tabletop execution | DevOps | 1 hr |
| **P1** | Close Human-Gate #5: Wave 11 soak claim unlock review | TL/DevOps | 30 min |
| **P2** | Reconcile Railway UUIDs (user vs CLI) | DevOps | 15 min |
| **P2** | Commit or discard local WIP (entrypoint/Dockerfile/celery) | Backend | 30 min |

---

## 6. Evidence Links

| Artifact | Link |
|----------|------|
| A-09 Parity Checklist (2026-08-13) | `docs/audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md` |
| Human-Gate Prep (2026-08-13) | `docs/audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md` |
| Soak Claim Unlock (2026-08-13) | `docs/audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md` |
| Staging OAuth Setup Runbook | `docs/audit/ga-engineering-audit/runbooks/staging-oauth-setup.md` |
| Rollback Tabletop Template | `docs/audit/ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md` |
| Staging Branch Strategy | `docs/audit/ga-engineering-audit/runbooks/staging-branch-strategy.md` |
| 72h Failure Triage | `docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-72H-FAILURE-TRIAGE-2026-08-12.md` |

---

## 7. Definition of "Staging Parity Complete"

**All must be true:**

- [ ] `git log --oneline staging..master | wc -l` == 0
- [ ] `deploy-staging.yml` SUCCESS (green run)
- [ ] Staging `/health` → 200
- [ ] Staging `/api/v1/companies` → 200 (no schema drift)
- [ ] Staging login + Decision evaluate smoke PASS
- [ ] Human-Gate items 1–4 signed/accepted
- [ ] Wave 11 soak claim reviewed + explicit decision (accept/reject)
- [ ] `soak_complete_claim` explicitly set (true/false with rationale)
- [ ] Railway env UUIDs reconciled

**Current state:** 1/9 met (staging host exists).

---

*Generated 2026-08-20. Evidence governs. Do not claim parity complete until all 9 criteria met.*