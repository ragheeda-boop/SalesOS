# A-09 checklist step 6 — Neo4j / `:6432` dispatch residual — 2026-08-12

**Validation:** **light validated** (Railway CLI vars + service logs + staging `/health`)  
**Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false`  
**Constraints:** No `feature_ai_copilot` flip · No alembic head · No secret dumps · Auth not weakened

**Host:** `https://salesos-staging.up.railway.app`  
**CLI staging env:** `5ce7864a-27c5-43c7-847d-667aecfbf773`  
**Project:** `responsible-comfort` (`96032c9a-38cf-4792-8168-b78d5353e26b`)

---

## Verdict

| Item | Result |
|------|--------|
| Step 6 — resolve Neo4j / `:6432` on `agent_dispatch_all` | **PASS** (agent-closed misconfig) |
| Neo4j Bolt from SalesOS API | Already **connected** (not the failure) |
| Human Neo4j volume/password blocker? | **Not required for reachability** — password present; API graph OK. Volume still **detached** (persistence residual only) |

---

## Root cause (misdiagnosis corrected)

Prior residual labeled staging `agent_dispatch_all` `:6432` connect failures as **Neo4j**. Live evidence shows:

1. Error text: `Agent dispatch load tenants failed: … Connect call failed (…, 6432)` — this is the **Postgres** tenant load in `agent_dispatch_all`, not Bolt/Neo4j.
2. Config default `postgres_port=6432` (PgBouncer-era default in `app/config.py`). Runtime DB URL for app role is built from `POSTGRES_HOST` + `POSTGRES_PORT` when `APP_POSTGRES_PASSWORD` is set (`app_database_url`).
3. Staging **SalesOS** had `POSTGRES_HOST=postgres.railway.internal` and `POSTGRES_PORT=5432`.
4. Staging **celery-worker** / **celery-beat** had `APP_POSTGRES_*` + `DATABASE_URL` (`:5432`) but **missing** `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` → workers used defaults `postgres:6432` → connection refused.
5. Neo4j config was already correct on API + workers: `NEO4J_URI=bolt://neo4j-prod.railway.internal:7687`, user `neo4j`, password present (len match with `NEO4J_AUTH` prefix). SalesOS `/health` reported `graph=connected` / dependencies `neo4j=connected` **before** this fix.

---

## Fix applied (Railway staging — no auth weaken)

Set non-secret Postgres targeting on celery services to match SalesOS:

| Variable | Value |
|----------|-------|
| `POSTGRES_HOST` | `postgres.railway.internal` |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_DB` | `railway` |

Services: `celery-worker (Copy 3091)`, `celery-beat (Copy 5338)`.

Redeploys (triggered by variable set):

| Service | Deploy ID | Status |
|---------|-----------|--------|
| celery-worker | `f423f787-c047-45fd-a2c9-8689cd763b06` | **SUCCESS** |
| celery-beat | `bb5876c1-b0fe-4742-8ed2-f20e02f25770` | **SUCCESS** |

`FEATURE_AI_COPILOT=false` unchanged. No password rotation. No TCP proxy added (private DNS sufficient).

---

## Neo4j staging inventory (reachability)

| Check | Result |
|-------|--------|
| Service `neo4j-prod` | Online · image `neo4j:5-community` · region `sfo` · Bolt `0.0.0.0:7687` |
| Private domain | `neo4j-prod.railway.internal` |
| App `NEO4J_URI` (SalesOS / worker / beat) | `bolt://neo4j-prod.railway.internal:7687` |
| `NEO4J_USER` | `neo4j` |
| `NEO4J_PASSWORD` / `NEO4J_AUTH` | Present (values not recorded) |
| Staging `/health` | `graph=connected` |
| `/health/dependencies` | `neo4j.status=connected` |
| Volume `neo4j-volume` | **detached** — data ephemeral on restart; **not** a connect blocker |

Region note: celery services report **US West**; Neo4j/Postgres/SalesOS report **sfo**. Private DNS resolved; wrong **port** was the failure mode, not cross-region DNS.

---

## Validation (post-fix)

Worker logs after `f423f787` ready:

```text
celery@… ready.
Task agent_dispatch_all[…] succeeded … {'tenants_processed': 0, 'tasks_claimed': 0, 'errors': []}
```

- No `:6432` / `Connect call failed` on dispatch ticks sampled after redeploy.
- `tenants_processed=0` is SQL filter / seed posture (active tenants query), **not** a connect error.

---

## Human residual (optional, not step-6 blocker)

1. Attach `neo4j-volume` to staging `neo4j-prod` if graph persistence is required (parity with intent; currently detached).
2. Consider aligning celery region to `sfo` with data plane (ops hygiene; not required to close this residual).
3. ADR-108 keeps Neo4j offline for **v1.0 product activation**; this step only closes staging **reachability / misconfig** noise on dispatch.

---

## Commands run (redacted)

```text
railway environment staging
railway status / service list
railway variable list --service SalesOS|celery-worker|celery-beat|neo4j-prod --json  # secrets redacted in notes
railway logs --service celery-worker / neo4j-prod
Invoke-WebRequest https://salesos-staging.up.railway.app/health
Invoke-WebRequest https://salesos-staging.up.railway.app/health/dependencies
railway variable set POSTGRES_HOST=postgres.railway.internal POSTGRES_PORT=5432 POSTGRES_DB=railway \
  --service "celery-worker (Copy 3091)" --environment staging
railway variable set POSTGRES_HOST=postgres.railway.internal POSTGRES_PORT=5432 POSTGRES_DB=railway \
  --service "celery-beat (Copy 5338)" --environment staging
railway service status / deployment list (worker + beat)
```

---

*Step 6 agent-closed. A-09 overall remains OPEN (CI token, Human-Gates, soak claim).*
