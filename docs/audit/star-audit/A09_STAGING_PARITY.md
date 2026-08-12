# A-09: Staging Parity Assessment

> **Last Updated:** 2026-08-12 (ENV + celery-worker + celery-beat ops)  
> Classification: INFRASTRUCTURE AUDIT  
> **Validation:** **light validated** for host liveness + Decision seed + CI wire + ENV/worker/beat fix  
> **A-09 residual:** **OPEN** (not closed — Human-Gate + CI deploy success + soak claim remain)

---

## Current State (2026-08-12 advancement)

| Metric | Production | Staging | Status |
|--------|------------|---------|--------|
| **Host** | `salesos-production-96c0.up.railway.app` | `salesos-staging.up.railway.app` | Both `/health` **200** (probed) |
| **Git branch** | `master` | **`staging` branch strategy + remote branch** | Closed (agent) — see [staging-branch-strategy.md](../ga-engineering-audit/runbooks/staging-branch-strategy.md) |
| **CI deploy workflow** | `deploy.yml` / `deploy-production.yml` | `deploy-staging.yml` wired with `--environment staging` (name) | Partial — gate PASS; deploy FAIL `Unauthorized` on [31630383949](https://github.com/ragheeda-boop/SalesOS/actions/runs/31630383949) |
| **Parity baseline** | See EAB-003 DIFF (2026-08-07) | Same commit class at baseline freeze | Machine baseline exists; Human-Gate residuals OPEN |
| **Business data for Decision soak** | Populated | **Seeded** muhide tenant + 5 companies (2026-08-12) | Agent closed seed gap; login round-trip **not validated** |
| **48–72h health soak claim** | N/A | Harness finished 2026-08-10; **`soak_complete_claim=false`** | OPEN |

Evidence deposits: [`A09-ADVANCEMENT-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-ADVANCEMENT-2026-08-12.md) · [`A09-OPS-ENV-CELERY-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-OPS-ENV-CELERY-2026-08-12.md)

Supersedes the stale “409 commits behind / no staging host” reading for **host existence**. Critical diffs and Human-Gate items in [`STAGING-vs-PRODUCTION-DIFF.md`](../ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-vs-PRODUCTION-DIFF.md) and [`staging-parity-checklist.md`](../ga-engineering-audit/runbooks/staging-parity-checklist.md) still govern **parity complete**.

---

## Closed this pass (agent)

1. **Staging branch strategy documented** + remote `staging` branch  
2. **CI path hardened** — `deploy-staging.yml` uses Railway env **name** `staging` (UUID-only path failed 2026-08-09)  
3. **Minimal Decision seed** — `seed_staging_decision_minimal.py` → muhide + 5 companies (`CONFIRM_STAGING_SEED=1`)  
4. Confirmed `FEATURE_AI_COPILOT=false` on staging service  
5. **`ENV=staging`** on SalesOS (mislabel closed) — CLI env `5ce7864a-…`  
6. Staging **celery-worker** deploy `3c9de5f4` **SUCCESS** (`celery@… ready`)  
7. Staging **celery-beat** deploy `81de263f` **SUCCESS** (`beat: Starting…` + `agent-dispatch-every-1m`)  

---

## Still OPEN / Human-Gate

1. Rotate `RAILWAY_TOKEN` for GH Environment `staging` → green `deploy-staging.yml` (gate PASS; token Unauthorized)  
2. Google OAuth staging app  
3. WAL/PITR/offsite posture accept-or-enable  
4. Postgres `max_connections` 100→500 or signed acceptance  
5. Rollback tabletop dated notes  
6. Wave 11 / PROD-W11-002 soak claim flip after human review of 72h failures  
7. Push A-09 `6cbcf9f` (branching `railway.json`) to `origin/master` so GitHub tip is not uvicorn-only  
8. Reconcile user-supplied Railway env UUIDs (`1ef5b31a-…` / `29252eae-…`) — not in CLI workspace  
9. Staging Neo4j reachability (`:6432` connect failures on `agent_dispatch_all`) — separate from beat online  

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
| P1 | Staging login + Decision evaluate smoke on muhide seed | Backend |
| P1 | Human review of 72h health-loop failures → Soak Report before any claim flip | TL / DevOps |

---

*A-09 remains OPEN. Evidence governs. Do not claim staging parity complete.*
