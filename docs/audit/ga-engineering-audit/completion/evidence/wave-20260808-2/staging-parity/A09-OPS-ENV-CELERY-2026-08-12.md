# A-09 ops pass — 2026-08-12 (ENV mislabel + celery-worker + celery-beat)

**Validation:** **light validated** (Railway CLI + live staging `/health` + worker/beat logs)  
**Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false`  
**AI flag:** `feature_ai_copilot` / `FEATURE_AI_COPILOT` remain **false**  
**No prod alembic head.** · **No `RAILWAY_TOKEN` invent.**

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
| Staging celery-beat offline | Root cause: **no GitHub source** + missing `APP_POSTGRES_*` + GitHub tip `3af6e656` `railway.json` still uvicorn-only (overwrote beat startCommand) |
| Beat source + `APP_POSTGRES_*` | Connected `ragheeda-boop/SalesOS` `@master`; `APP_POSTGRES_USER=salesos_app` + password via `${{SalesOS.APP_POSTGRES_PASSWORD}}` (presence only) |
| Beat redeploy | CLI `railway up` with local branching `railway.json` → deploy `81de263f` **SUCCESS** |
| Beat scheduler | Logs: `beat: Starting…` + `Scheduler: Sending due task agent-dispatch-every-1m (agent_dispatch_all)` |
| Worker still healthy after beat | Deploy `3c9de5f4` still **SUCCESS**; receives `agent_dispatch_all` |

## Still blocked / human

| Item | Notes |
|------|-------|
| Rotate `RAILWAY_TOKEN` for GH Environment `staging` | Prior run Unauthorized; no token available in agent env to invent/update |
| End-to-end `deploy-staging.yml` SUCCESS | Re-dispatch after token rotate |
| Push A-09 SHA `6cbcf9f` to `origin/master` | Local master **ahead 1**; remote tip `3af6e656` still has uvicorn-only `railway.json` — GitHub auto-deploy of beat would regress to uvicorn until push |
| Dashboard Config-as-Code path | Prod uses `/railway.worker.json` + `/railway.beat.json`; staging celery still `/railway.json` service-name branch (CLI up) |
| Neo4j on staging agent_dispatch | Task succeeds with `Connect call failed …:6432` errors (pre-existing Neo4j reachability; not beat offline) |
| User-supplied env UUIDs | Confirm origin (other workspace/project?) or discard |
| Google OAuth / WAL-PITR / rollback tabletop / Wave 11 soak | Human gates unchanged |

## Rotate `RAILWAY_TOKEN` (exact steps)

1. Railway dashboard → Account → Tokens → create project token for `responsible-comfort` (or regenerate existing).
2. GitHub → `ragheeda-boop/SalesOS` → Settings → Environments → **staging** → Secrets → set `RAILWAY_TOKEN` to the new value (also update repo-level `RAILWAY_TOKEN` if staging env inherits/overrides incorrectly).
3. Confirm secrets present: `RAILWAY_TOKEN`, `RAILWAY_PROJECT_ID`, `RAILWAY_STAGING_SERVICE_ID`, `RAILWAY_STAGING_ENVIRONMENT_ID` (= `5ce7864a-…`).
4. Actions → **Deploy Staging** → Run workflow → `confirm_staging=CONFIRM-STAGING-DEPLOY` on branch `staging` (or intended ref).
5. Expect: gate SUCCESS → Railway up SUCCESS → health gate HTTP 200.

Do **not** paste token values into chat, commits, or evidence docs.
