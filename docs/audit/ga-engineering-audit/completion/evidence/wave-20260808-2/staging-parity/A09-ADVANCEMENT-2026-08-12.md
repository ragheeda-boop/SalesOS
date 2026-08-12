# A-09 advancement evidence — 2026-08-12

**Validation:** **light validated** (host health + DB seed counts + CI diagnosis)  
**Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false`

---

## Closed by agent this pass

| Item | Evidence |
|------|----------|
| Staging host live | `GET https://salesos-staging.up.railway.app/health` → **200** (`database/cache/redis/graph` connected; `FEATURE_AI_COPILOT=false` on service) |
| Staging git branch strategy | [staging-branch-strategy.md](../../../../runbooks/staging-branch-strategy.md) + remote `staging` branch |
| CI path safe wire | `.github/workflows/deploy-staging.yml` uses `--environment staging` (name) after 2026-08-09 UUID “Environment not found” failures |
| Minimal Decision seed | Idempotent muhide tenant + 5 companies via `seed_staging_decision_minimal.py` (staging public DB only). Post-seed: `muhide_tenant=1`, muhide `companies_total=5`, staging totals `companies=22` / `tenants=18` |
| GH Environment inventory | Environment `staging` exists; secrets `RAILWAY_*` bound; var `RAILWAY_STAGING_HEALTH_URL` set |

## Still human / OPEN

| Item | Notes |
|------|-------|
| End-to-end `deploy-staging.yml` SUCCESS | Prior runs failed (env UUID). Re-exercise after this wire; human confirms green run URL |
| `ENV=production` on staging service | Mislabel (`RAILWAY_ENVIRONMENT_NAME=staging` but `ENV=production`) — fix in Railway vars |
| Google OAuth staging app | Human-Gate |
| WAL / PITR / offsite | Human-Gate |
| `max_connections` 100 vs 500 | Accept or raise |
| Rollback tabletop | Dated notes still missing |
| Wave 11 soak claim | 72h harness had failures; do not flip |
| Staging celery-worker | Observed **Deploy failed** on staging status snapshot |

## Seed credentials (ops only — not secrets in git)

- Email: `ragheed.a@muhide.com`
- Default password set by script constant — **rotate on first login**; prefer `MUHIDE_ADMIN_PASSWORD` on re-seed
- Login round-trip against staging API: **not validated** in this pass (JWT/Settings path separate)

## Commands (redacted)

```text
# health
Invoke-WebRequest https://salesos-staging.up.railway.app/health

# seed (requires CONFIRM_STAGING_SEED=1 + staging DATABASE_PUBLIC_URL as DATABASE_URL)
python salesos/backend/scripts/seed_staging_decision_minimal.py
```

No prod alembic head. No `feature_ai_copilot` flip. No secret dumps.
