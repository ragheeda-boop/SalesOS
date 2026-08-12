# A-09 ops pass — 2026-08-12 (ENV mislabel + celery-worker)

**Validation:** **light validated** (Railway CLI + live staging `/health` + worker logs)  
**Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false`  
**AI flag:** `feature_ai_copilot` / `FEATURE_AI_COPILOT` remain **false**  
**No prod alembic head.**

---

## Environment ID reconciliation

| Source | Staging env ID | Production env ID |
|--------|----------------|-------------------|
| User-supplied (this pass) | `1ef5b31a-6869-483b-9b23-9cfc6b2a6686` | `29252eae-7eb7-472e-83c0-271a34ee0bfc` |
| Railway CLI `responsible-comfort` | `5ce7864a-27c5-43c7-847d-667aecfbf773` | `652c450a-1473-4445-98e4-15aceefd49c3` |

**Result:** User-supplied IDs are **not found** in the authenticated Railway workspace (`ragheed.a@ratlfintech.com` / `ragheeda-boop's Projects`). CLI returns `Environment "1ef5b31a-…" not found`. Ops continued against CLI-authoritative **name** `staging` / ID `5ce7864a-…` on project `96032c9a-38cf-4792-8168-b78d5353e26b` (`responsible-comfort`).

GitHub secret `RAILWAY_STAGING_ENVIRONMENT_ID` (repo + Environment `staging`) was set to the CLI staging ID `5ce7864a-…` for inventory/gate consistency. Workflow deploy path remains `--environment staging` (name).

---

## Fixed this pass

| Item | Evidence |
|------|----------|
| Staging SalesOS `ENV` mislabel | `ENV=staging` with `RAILWAY_ENVIRONMENT_NAME=staging` (was `ENV=production`) |
| Staging celery-worker crash | Root cause: wrong config (`/railway.json` → uvicorn) + empty `APP_POSTGRES_*` while `ENV` required app role |
| Worker `APP_POSTGRES_USER` / `APP_POSTGRES_PASSWORD` | Wired from SalesOS (password via reference set; presence verified only) |
| Worker start path | `railway.json` startCommand branches on `RAILWAY_SERVICE_NAME` (`*celery-worker*` / `*celery-beat*` → `app.railway_celery_service`) |
| Worker redeploy | Deploy `3c9de5f4` **SUCCESS**; logs: `celery@… ready` + `worker_health_ping` |
| Staging host health | `GET https://salesos-staging.up.railway.app/health` → **200** |

## Still blocked / human

| Item | Notes |
|------|-------|
| Rotate `RAILWAY_TOKEN` for GH Environment `staging` | Prior run Unauthorized; no token available in agent env to invent/update |
| End-to-end `deploy-staging.yml` SUCCESS | Re-dispatch after token rotate |
| Dashboard Config-as-Code path | Prod worker uses `/railway.worker.json`; staging still `/railway.json` with service-name branch workaround |
| User-supplied env UUIDs | Confirm origin (other workspace/project?) or discard |
| Google OAuth / WAL-PITR / rollback tabletop / Wave 11 soak | Human gates unchanged |
| Staging `celery-beat (Copy 5338)` | Still **NO DEPLOYMENT** / Offline — separate follow-up |

## Rotate `RAILWAY_TOKEN` (exact steps)

1. Railway dashboard → Account → Tokens → create project token for `responsible-comfort` (or regenerate existing).
2. GitHub → `ragheeda-boop/SalesOS` → Settings → Environments → **staging** → Secrets → set `RAILWAY_TOKEN` to the new value (also update repo-level `RAILWAY_TOKEN` if staging env inherits/overrides incorrectly).
3. Confirm secrets present: `RAILWAY_TOKEN`, `RAILWAY_PROJECT_ID`, `RAILWAY_STAGING_SERVICE_ID`, `RAILWAY_STAGING_ENVIRONMENT_ID` (= `5ce7864a-…`).
4. Actions → **Deploy Staging** → Run workflow → `confirm_staging=CONFIRM-STAGING-DEPLOY` on branch `staging` (or intended ref).
5. Expect: gate SUCCESS → Railway up SUCCESS → health gate HTTP 200.

Do **not** paste token values into chat, commits, or evidence docs.
