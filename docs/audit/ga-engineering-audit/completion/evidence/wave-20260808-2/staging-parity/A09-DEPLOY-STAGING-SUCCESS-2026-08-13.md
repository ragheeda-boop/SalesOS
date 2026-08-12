# A-09 steps 1–2 — Deploy Staging SUCCESS (2026-08-13)

**Validation:** **light validated** (GitHub Actions conclusion + independent `/health` probe)  
**Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false`  
**Constraints:** No `feature_ai_copilot` flip · No secret dumps · No forge CLOSE

---

## Result

| Step | Result |
|------|:------:|
| 1. `RAILWAY_TOKEN` (Environment `staging`) | **PASS** — `railway up` authenticated |
| 2. `deploy-staging.yml` | **SUCCESS** |

**Run:** https://github.com/ragheeda-boop/SalesOS/actions/runs/31649846410  
**Ref:** `master` · `workflow_dispatch` · `CONFIRM-STAGING-DEPLOY`

| Job | Conclusion |
|-----|:----------:|
| Staging Availability Gate | success (~5s) |
| Deploy Backend (Railway Staging) | success (~1m36s) — `railway up` |
| Frontend (Vercel) | success (Git primary; CLI skipped) |
| Staging Health Gate | success — probe `/health` |
| Deploy Notification | success |

## Independent probe (post-run)

`GET https://salesos-staging.up.railway.app/health` → **200**

```json
{"status":"ok","version":"5.1.0-rc1","database":"connected","cache":"connected","graph":"connected","kafka":"in_memory","redis":"connected","rate_limiter":"active"}
```

`uptime_seconds` ≈ 71 at probe time (consistent with a fresh deploy).  
`GET /version` → **200** (`api_version=5.1.0-rc1`; `backend_commit` empty in this image).

## Residual (A-09 still OPEN)

- Human-Gate step 7: OAuth / PITR / WAL / `max_connections` / rollback ink  
- Soak claim stays **false** (step 9)  
- Final parity **CONDITIONAL / OPEN** (step 10)
