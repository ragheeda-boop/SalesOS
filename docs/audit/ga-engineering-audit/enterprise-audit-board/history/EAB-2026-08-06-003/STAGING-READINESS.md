# Staging Readiness Checklist — OPS-01 (honesty)

**Date:** 2026-08-07 (update)  
**Parent:** [OPS-01-ADVANCEMENT.md](./OPS-01-ADVANCEMENT.md)  
**Does not close:** OPS-01 row 4 (staging soak) or Production GO

---

## 2026-08-07 UPDATE — Railway staging now production-parity (EXECUTE + VERIFY)

Machine-verified parity with the prod baseline snapshot after execution:

| Fact | Value |
|------|-------|
| Staging env | `5ce7864a-27c5-43c7-847d-667aecfbf773` · `https://salesos-staging.up.railway.app` |
| Source | **`4750038c`** (prod baseline) — deployed from clean worktree |
| Code schema | `/openapi.json` **881,643 B — byte-identical to prod** |
| DB | migrated to **repo head `e5f9a32b0c08`**; RLS 71/71; extensions present |
| Config | `DEBUG=false`; `FRONTEND_URL` set; `FEATURE_HTTPONLY_ACCESS_COOKIE=false`; `GOOGLE_REDIRECT_URI` staging-scoped |
| Secrets | **`JWT_SECRET_KEY` / `SECRET_KEY` NEW and distinct from prod** (isolation fixed) |
| Neo4j | connected (prod also repaired — no inversion) |
| Workers | celery-worker + celery-beat redeployed to `4750038c` (`Dockerfile.railway`) |
| CI | `RAILWAY_STAGING_SERVICE_ID` + `RAILWAY_STAGING_ENVIRONMENT_ID` repo secrets set; `deploy-staging.yml` hard-fails when absent; YAML validated (5 jobs) |
| Postgres | connection saturation **cleared** (active=12/100); `max_connections=100` vs prod 500 (capacity gap) |
| /health | 200, `database`/`redis`/`graph` all connected |

**Conclusion:** staging is now a **production-parity replica at the code/config/secret level** and is **soak-capable with conditions**. Remaining before an unqualified soak: (1) **human task** staging Google OAuth app → `SSO_GOOGLE_CLIENT_ID/SECRET`; (2) accept or close staging WAL/offsite-backup gap; (3) decide on staging `max_connections` (100 vs 500) if load realism matters. **Soak itself has NOT started** — evidence must run ≥48h.

---

## Two tracks (do not conflate)

| Track | What it is | Closes cloud staging? | Closes OPS-01 #4? |
|-------|------------|----------------------|-------------------|
| **Virtual staging** | Local compose stand-in / tabletop using staging overlay shape | **No** | **No** |
| **Real staging** | Reachable non-prod host + GH Environment + deploy/rollback + soak | **Yes (this is the path)** | Required (with 48–72h evidence) |

---

## Real staging — gates status (2026-08-07)

| # | Gate | Status |
|---|------|--------|
| S1 | Staging host identity (Railway env `5ce7864a-…`) | **DONE** |
| S2 | GH Environment `staging` + `RAILWAY_STAGING_HEALTH_URL` | **DONE** |
| S3 | Repo secrets `RAILWAY_STAGING_SERVICE_ID` / `RAILWAY_STAGING_ENVIRONMENT_ID` | **DONE** |
| S4 | Deploy workflow discoverable (repo-root `.github/workflows/`) + validated | **DONE** (YAML parses; 5 jobs) |
| S5 | `.env.staging` placeholders off-git (Railway env vars) | **DONE** (DEBUG=false, secrets distinct) |
| S6 | Deploy + rollback tabletop on real host with evidence | PARTIAL — deploy done via CLI; scripted rollback not yet exercised |
| S7 | Staging soak ≥48h (prefer 72h) + TL review | **OPEN** — not started |

## Operator order (remaining)

1. Create staging Google OAuth app → set `SSO_GOOGLE_CLIENT_ID/SECRET` on staging.
2. Accept or close staging WAL/offsite-backup gap (parity with prod rows 1–3).
3. Optionally raise staging `max_connections` to match prod (500) or seed sanitized data.
4. Start soak per [SOAK-GATE-CHECKLIST.md](./SOAK-GATE-CHECKLIST.md) with dated UTC window; collect evidence.
5. TL review, then update `soak_complete_claim` and OPS-01 Row 4 → DONE.

**Honesty:** Completing parity ≠ staging soak complete. The 48–72h soak with dated evidence + TL review is still required.
