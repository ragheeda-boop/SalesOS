# A-09: Staging Parity Assessment

> **Last Updated:** 2026-08-12 (parallel-stream checklist rollup)  
> Classification: INFRASTRUCTURE AUDIT  
> **Validation:** **light validated** for host + login + Decision runtime evaluate + worker/beat/dispatch + Postgres/Neo4j reachability on dispatch; CI token still FAIL  
> **A-09 residual:** **OPEN** (not closed — Human-Gate `RAILWAY_TOKEN` + CI deploy success + Human-Gate ops + soak claim remain)  
> **Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false` · no forge CLOSE · `feature_ai_copilot` unchanged (`false`)

---

## Current State (2026-08-12 advancement)

| Metric | Production | Staging | Status |
|--------|------------|---------|--------|
| **Host** | `salesos-production-96c0.up.railway.app` | `salesos-staging.up.railway.app` | Both `/health` **200** (probed) |
| **Git branch** | `master` | **`staging` branch strategy + remote branch** | Closed (agent) — see [staging-branch-strategy.md](../ga-engineering-audit/runbooks/staging-branch-strategy.md) |
| **CI deploy workflow** | `deploy.yml` / `deploy-production.yml` | `deploy-staging.yml` wired with `--environment staging` (name) | **FAIL** — gate PASS; `railway up` **Unauthorized** on [31638994692](https://github.com/ragheeda-boop/SalesOS/actions/runs/31638994692) |
| **Parity baseline** | See EAB-003 DIFF (2026-08-07) | Same commit class at baseline freeze | Machine baseline exists; Human-Gate residuals OPEN |
| **Business data for Decision soak** | Populated | **Seeded** muhide tenant + 5 companies (2026-08-12) | Login **PASS**; Decision-runtime evaluate **PASS** (`recommend_call`) |
| **Worker / beat / dispatch** | Online | Online — beat `agent-dispatch-every-1m`; worker `agent_dispatch_all` succeeded (`errors=[]`) | **PASS** (light) |
| **Neo4j / graph** | Connected class | SalesOS `graph=connected`; `:6432` residual was **Postgres misconfig on celery** (closed) | **PASS** (light) · SHA `1baae84` |
| **48–72h health soak claim** | N/A | Harness finished 2026-08-10; triage **DONE** (`ae76dae`); **`soak_complete_claim=false`** | OPEN — claim cannot advance (97.6% fails = DB outage) |
| **Final staging parity** | N/A | Checklist incomplete | **OPEN** / `staging_parity_complete=false` |

Progress rollup: [`A09-CHECKLIST-PROGRESS-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-PROGRESS-2026-08-12.md)

Evidence deposits: [`A09-CHECKLIST-6-NEO4J-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-6-NEO4J-2026-08-12.md) · [`A09-CHECKLIST-1-5-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-1-5-2026-08-12.md) · [`A09-ADVANCEMENT-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-ADVANCEMENT-2026-08-12.md) · [`A09-OPS-ENV-CELERY-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-OPS-ENV-CELERY-2026-08-12.md) · [`SOAK-72H-FAILURE-TRIAGE-2026-08-12.md`](../ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-72H-FAILURE-TRIAGE-2026-08-12.md)

Supersedes the stale “409 commits behind / no staging host” reading for **host existence**. Critical diffs and Human-Gate items in [`STAGING-vs-PRODUCTION-DIFF.md`](../ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-vs-PRODUCTION-DIFF.md) and [`staging-parity-checklist.md`](../ga-engineering-audit/runbooks/staging-parity-checklist.md) still govern **parity complete**.

---

## Closed this pass (agent)

1. **Staging branch strategy documented** + remote `staging` branch  
2. **CI path hardened** — `deploy-staging.yml` uses Railway env **name** `staging` (UUID-only path failed 2026-08-09)  
3. **Minimal Decision seed** — `seed_staging_decision_minimal.py` → muhide + 5 companies (`CONFIRM_STAGING_SEED=1`)  
4. Confirmed `FEATURE_AI_COPILOT=false` on staging service  
5. **`ENV=staging`** on SalesOS (mislabel closed) — CLI env `5ce7864a-…`  
6. Staging **celery-worker** deploy `3c9de5f4` → refreshed `f423f787` **SUCCESS** (`celery@… ready`)  
7. Staging **celery-beat** deploy `81de263f` → refreshed `bb5876c1` **SUCCESS** (`beat: Starting…` + `agent-dispatch-every-1m`)  
8. Checklist **step 6** — closed `:6432` residual (celery missing `POSTGRES_*`; Neo4j already reachable) — SHA `1baae84`  
9. Checklist **step 8** — 72h failure triage filed; Wave 11 claim **not** advanced — SHA `ae76dae`  

---

## Checklist 1–10 (2026-08-12 parallel streams)

| # | Step | Result |
|---|------|:------:|
| 1 | Verify/rotate `RAILWAY_TOKEN` via deploy attempt | **FAIL** — Unauthorized; **human rotate required** |
| 2 | `deploy-staging.yml` SUCCESS | **FAIL** — blocked by #1 |
| 3 | Staging login (seeded muhide) | **PASS** |
| 4 | Decision smoke (runtime evaluate) | **PASS** (`recommend_call`) |
| 5 | Worker + beat + `agent_dispatch_all` | **PASS** (light) |
| 6 | Neo4j / `:6432` on dispatch | **CLOSED** — was Postgres `POSTGRES_HOST/PORT/DB` missing on celery; Neo4j Bolt OK · `1baae84` |
| 7 | Human-Gate OAuth / PITR / WAL / `max_connections` / rollback | **OPEN** |
| 8 | 72h triage | **DONE** · `ae76dae` — claim cannot advance (97.6% fails = DB outage) |
| 9 | Wave 11 soak claim | **false** (stays false) |
| 10 | Final parity | **OPEN** / not complete · `staging_parity_complete=false` |

Evidence: [`A09-CHECKLIST-PROGRESS-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-PROGRESS-2026-08-12.md) · [`A09-CHECKLIST-1-5-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-1-5-2026-08-12.md) · [`A09-CHECKLIST-6-NEO4J-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-6-NEO4J-2026-08-12.md).

---

## Still OPEN / Human-Gate

1. **Rotate `RAILWAY_TOKEN`** for GH Environment `staging` → green `deploy-staging.yml` (gate PASS; token Unauthorized on [31638994692](https://github.com/ragheeda-boop/SalesOS/actions/runs/31638994692)) — **P0 / step 1**  
2. Google OAuth staging app  
3. WAL/PITR/offsite posture accept-or-enable  
4. Postgres `max_connections` 100→500 or signed acceptance  
5. Rollback tabletop dated notes  
6. Wave 11 / PROD-W11-002 soak claim flip after human review of 72h triage (`ae76dae`) — claim stays **false** until PO/TL  
7. Push A-09 `6cbcf9f` (branching `railway.json`) to `origin/master` so GitHub tip is not uvicorn-only — verify against current tip after this doc commit  
8. Reconcile user-supplied Railway env UUIDs (`1ef5b31a-…` / `29252eae-…`) — not in CLI workspace  
9. Local WIP (entrypoint / Dockerfile / salesos/railway.json startCommand removal + celery_app imports) — **left uncommitted** after df5028c; see [A09-OPS-ENV-CELERY-2026-08-12.md](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-OPS-ENV-CELERY-2026-08-12.md) residual  
10. ~~Staging Neo4j / `:6432` on `agent_dispatch_all`~~ — **CLOSED** (misdiagnosed; celery missing `POSTGRES_HOST/PORT/DB`; Neo4j already `connected`). Optional human: attach detached `neo4j-volume` for persistence only. See [A09-CHECKLIST-6-NEO4J-2026-08-12.md](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-6-NEO4J-2026-08-12.md).  

---

## 2026-08-12 bounded prod IL-2A soak (not staging parity)

Documented in [`docs/reports/A09-BOUNDED-PROD-IL2A-SOAK-2026-08-12.md`](../../reports/A09-BOUNDED-PROD-IL2A-SOAK-2026-08-12.md).

- 8/8 evaluate **200**; AgentTask isolation/idempotency **PASS** (DB)  
- Explicitly **not** A-09 / Wave 11 close  

---

## Recommendations

| Priority | Action | Owner |
|----------|--------|-------|
| P0 | Confirm green `deploy-staging.yml` after `RAILWAY_TOKEN` rotate | DevOps |
| P0 | Close Human-Gate (OAuth, backup posture, max_connections, rollback) | DevOps / Platform |
| P1 | Staging login + Decision evaluate smoke on muhide seed | Backend — **PASS** this pass (see checklist 1–5) |
| P1 | Human review of 72h health-loop failures → Soak Report before any claim flip | TL / DevOps — **agent triage DONE** [SOAK-72H-FAILURE-TRIAGE-2026-08-12.md](../ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-72H-FAILURE-TRIAGE-2026-08-12.md) (`ae76dae`); claim still **false** |

---

*A-09 remains OPEN. Evidence governs. Do not claim staging parity complete. Do not forge CLOSE.*
