# A-09: Staging Parity Assessment

> **Last Updated:** 2026-08-13 (checklist steps 7 / 9 / 10)  
> Classification: INFRASTRUCTURE AUDIT  
> **Validation:** **light validated** for host + login + Decision runtime evaluate + worker/beat/dispatch + Postgres/Neo4j reachability on dispatch; CI token still FAIL  
> **A-09 residual:** **CONDITIONAL / OPEN** (not closed — Human-Gate `RAILWAY_TOKEN` + CI deploy success + Human-Gate ops + soak claim remain)  
> **Claims:** `staging_parity_complete=false` · `soak_complete_claim=false` · `production_go=false` · no forge CLOSE · `feature_ai_copilot` unchanged (`false`)  
> **Final assessment:** [A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md) — **CONDITIONAL / OPEN** (PASS: 3–6, 8; BLOCKED: 1–2, 7, 9)

---

## Current State (2026-08-13)

| Metric | Production | Staging | Status |
|--------|------------|---------|--------|
| **Host** | `salesos-production-96c0.up.railway.app` | `salesos-staging.up.railway.app` | Both `/health` **200** (probed) |
| **Git branch** | `master` | **`staging` branch strategy + remote branch** | Closed (agent) — see [staging-branch-strategy.md](../ga-engineering-audit/runbooks/staging-branch-strategy.md) |
| **CI deploy workflow** | `deploy.yml` / `deploy-production.yml` | `deploy-staging.yml` wired with `--environment staging` (name) | **FAIL** — gate PASS; `railway up` **Unauthorized** on [31648777919](https://github.com/ragheeda-boop/SalesOS/actions/runs/31648777919) (post «تم التدوير»; same class) |
| **Parity baseline** | See EAB-003 DIFF (2026-08-07) | Same commit class at baseline freeze | Machine baseline exists; Human-Gate residuals OPEN |
| **Business data for Decision soak** | Populated | **Seeded** muhide tenant + 5 companies (2026-08-12) | Login **PASS**; Decision-runtime evaluate **PASS** (`recommend_call`) |
| **Worker / beat / dispatch** | Online | Online — beat `agent-dispatch-every-1m`; worker `agent_dispatch_all` succeeded (`errors=[]`) | **PASS** (light) |
| **Neo4j / graph** | Connected class | SalesOS `graph=connected`; `:6432` residual was **Postgres misconfig on celery** (closed) | **PASS** (light) · SHA `1baae84` |
| **Human-Gate ops (OAuth / PITR / max_conn / rollback)** | Prod DR drills DONE\* | Staging residuals documented; prep templates ready; **ink OPEN** | **OPEN** · [step 7](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md) |
| **48–72h health soak claim** | N/A | Harness finished 2026-08-10; triage **DONE** (`ae76dae`); **`soak_complete_claim=false`** | OPEN — unlock criteria · [step 9](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md) |
| **Final staging parity** | N/A | Checklist incomplete | **CONDITIONAL / OPEN** · `staging_parity_complete=false` |

Progress rollup: [`A09-CHECKLIST-PROGRESS-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-PROGRESS-2026-08-12.md)

Evidence deposits: [`A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md) · [`A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md) · [`A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md) · [`A09-CHECKLIST-6-NEO4J-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-6-NEO4J-2026-08-12.md) · [`A09-CHECKLIST-1-5-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-1-5-2026-08-12.md) · [`A09-ADVANCEMENT-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-ADVANCEMENT-2026-08-12.md) · [`A09-OPS-ENV-CELERY-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-OPS-ENV-CELERY-2026-08-12.md) · [`SOAK-72H-FAILURE-TRIAGE-2026-08-12.md`](../ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-72H-FAILURE-TRIAGE-2026-08-12.md)

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
10. Checklist **step 7 prep** — Human-Gate status matrix + OAuth runbook + rollback template (ink OPEN) — 2026-08-13  
11. Checklist **step 9** — soak unlock criteria documented; `soak_complete_claim` stays **false**  
12. Checklist **step 10** — final assessment **CONDITIONAL / OPEN** (not parity complete)  

---

## Checklist 1–10 (2026-08-13)

| # | Step | Result |
|---|------|:------:|
| 1 | Verify/rotate `RAILWAY_TOKEN` via deploy attempt | **FAIL** — still Unauthorized after «تم التدوير» ([31648777919](https://github.com/ragheeda-boop/SalesOS/actions/runs/31648777919)) |
| 2 | `deploy-staging.yml` SUCCESS | **FAIL** — blocked by #1 |
| 3 | Staging login (seeded muhide) | **PASS** |
| 4 | Decision smoke (runtime evaluate) | **PASS** (`recommend_call`) |
| 5 | Worker + beat + `agent_dispatch_all` | **PASS** (light) |
| 6 | Neo4j / `:6432` on dispatch | **CLOSED** — was Postgres `POSTGRES_HOST/PORT/DB` missing on celery; Neo4j Bolt OK · `1baae84` |
| 7 | Human-Gate OAuth / PITR / WAL / `max_connections` / rollback | **OPEN** — prep DONE; signed acceptance **not** forged |
| 8 | 72h triage | **DONE** · `ae76dae` — claim cannot advance (97.6% fails = DB outage) |
| 9 | Wave 11 soak claim | **false** (stays false) — unlock path documented |
| 10 | Final parity | **CONDITIONAL / OPEN** · `staging_parity_complete=false` |

Evidence: [`A09-CHECKLIST-PROGRESS-2026-08-12.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-PROGRESS-2026-08-12.md) · [`A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md`](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-10-FINAL-PARITY-2026-08-13.md).

---

## Still OPEN / Human-Gate

1. **Re-verify `RAILWAY_TOKEN`** for GH Environment `staging` → green `deploy-staging.yml` (post-rotate still Unauthorized on [31648777919](https://github.com/ragheeda-boop/SalesOS/actions/runs/31648777919)) — **P0 / step 1**  
2. Google OAuth staging app — [staging-oauth-setup.md](../ga-engineering-audit/runbooks/staging-oauth-setup.md)  
3. WAL/PITR/offsite posture accept-or-enable  
4. Postgres `max_connections` 100→500 or signed acceptance  
5. Rollback tabletop dated notes — template [A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-STAGING-ROLLBACK-TABLETOP-TEMPLATE.md)  
6. Wave 11 / PROD-W11-002 soak claim flip after unlock U1–U5 ([step 9](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-CHECKLIST-9-SOAK-CLAIM-UNLOCK-2026-08-13.md)) — claim stays **false** until PO/TL  
7. Reconcile user-supplied Railway env UUIDs (`1ef5b31a-…` / `29252eae-…`) — not in CLI workspace  
8. Local WIP (entrypoint / Dockerfile / salesos/railway.json startCommand removal + celery_app imports) — **left uncommitted** after df5028c; see [A09-OPS-ENV-CELERY-2026-08-12.md](../ga-engineering-audit/completion/evidence/wave-20260808-2/staging-parity/A09-OPS-ENV-CELERY-2026-08-12.md) residual  
9. ~~Staging Neo4j / `:6432` on `agent_dispatch_all`~~ — **CLOSED** (misdiagnosed; celery missing `POSTGRES_HOST/PORT/DB`; Neo4j already `connected`). Optional human: attach detached `neo4j-volume` for persistence only.  

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
| P1 | Staging login + Decision evaluate smoke on muhide seed | Backend — **PASS** (checklist 1–5) |
| P1 | Human review of 72h failures → unlock U1–U5 before any claim flip | TL / DevOps — triage DONE; claim still **false** |

---

*A-09 remains CONDITIONAL / OPEN. Evidence governs. Do not claim staging parity complete. Do not forge CLOSE.*
