# Soak Gate Checklist — OPS-01 / Wave 11

**Date:** 2026-08-06  
**Parent:** [OPS-01-ADVANCEMENT.md](./OPS-01-ADVANCEMENT.md)  
**Claim file:** [PROGRESS-WAVE11-SOAK-CLAIM.md](../../../PROGRESS-WAVE11-SOAK-CLAIM.md)  
**Current `soak_complete_claim`:** **false**

---

## 2026-08-07 UPDATE — Railway staging is production-parity (EXECUTE + VERIFY)

Machine verification this run ([STAGING-vs-PRODUCTION-DIFF.md](./STAGING-vs-PRODUCTION-DIFF.md), [SOAK-READINESS.md](./SOAK-READINESS.md)):

- **K1 now PASSES parity**: staging runs prod baseline `4750038c`, `/openapi.json` byte-identical to prod (881,643 B), alembic at repo head `e5f9a32b0c08`, `DEBUG=false`, secrets distinct from prod, celery-worker/beat synced, Neo4j connected in **both** staging and prod (inversion resolved), `RAILWAY_STAGING_*` CI secrets wired, Postgres saturation cleared (active=12/100).
- `soak_complete_claim` remains **false**; K2–K6 still OPEN (soak not started).
- Remaining preconditions: staging Google OAuth app (SSO_CLIENT_ID/SECRET — human), staging WAL/offsite-backup gap decision, optional `max_connections` 100→500.

## What exists (local / health-only)

| Evidence | Duration / notes | Completes 48–72h gate? |
|----------|------------------|------------------------|
| [PROGRESS-WAVE11-SOAK.md](../../../PROGRESS-WAVE11-SOAK.md) short loop | ~0.2h / 5 iters | **No** |
| Same — 4h extended local | 45 iters; hard fails present; exit 1 | **No** |
| [PROGRESS-WAVE11-SOAK-48H.md](../../../PROGRESS-WAVE11-SOAK-48H.md) + `evidence/wave11-soak-48h*` | Started / incomplete / instability noted historically | **No** (claim false) |
| Wave 16 Railway health harness | Health-only; see soak-claim honesty | **No** |
| Gate script | `salesos/scripts/wave11-soak-gate.py` | Tooling only |

Runbook: [staging-soak.md](../../../runbooks/staging-soak.md)

---

## Still missing for 48–72h (honest close)

| # | Requirement | Status |
|---|-------------|--------|
| K1 | Target environment = **staging cloud** (not laptop-only) | **PASS** — Railway staging = prod baseline `4750038c`, parity verified (see 2026-08-07 UPDATE) |
| K2 | Continuous window ≥ **48h** (prefer **72h**) with dated start/end UTC | OPEN |
| K3 | Evidence dir with loop summaries + hard-fail triage | OPEN for cloud path |
| K4 | No new P0 during soak (or P0s closed before claim) | N/A until run |
| K5 | Project Owner review of report before flipping claim | OPEN |
| K6 | `soak_complete_claim: true` only after K1–K5 | **false** today |

---

## Flip rules (do not violate)

1. Local loops with high fail rate **must not** set claim true.  
2. Health-only remote probes ≠ full soak.  
3. Agents must not forge claim JSON or SIGN_HERE.  
4. New P0 during soak → automatic NO-GO until closed.

---

## Soak window — IN PROGRESS (started 2026-08-07, Project Owner directive)

| Field | Value |
|-------|-------|
| Start UTC | **2026-08-07T14:10:06Z** |
| End UTC (target) | 2026-08-10T14:10:06Z (72h) |
| Environment URL | `https://salesos-staging.up.railway.app` (FE `https://sales-os-jet.vercel.app`) |
| Command | `python salesos/scripts/wave11-soak-gate.py --loop --interval 300 --duration-hours 72 --api https://salesos-staging.up.railway.app --fe https://sales-os-jet.vercel.app --skip-alembic --skip-flags --fail-soft` |
| PID / host | 16044 (Windows, detached; evidence flushed to JSON per iteration) |
| Iterations / PASS / FAIL | i1: PASS 7/0 (2026-08-07T14:10:06Z) |
| Evidence path | `evidence/ops01-staging/` (under this history dir) |
| TL reviewer | OPEN (human — Project Owner) |
| `soak_complete_claim` | **false** until signed review |

## Preconditions noted by Project Owner (2026-08-07)

- Google OAuth for staging (`SSO_GOOGLE_CLIENT_ID/SECRET`) still **not set** — human task, tracked separately.
- Soak intentionally independent of the DB migration (validates runtime/stability/workers/memory/health).
- Prod DB migration to `e5f9a32b0c08` deferred to **Maintenance Window** after soak (Project Owner approved `REQUIRES MAINTENANCE WINDOW`, not `SAFE TO EXECUTE`); a **Migration Dress Rehearsal** (restore prod copy to separate env, run the 15 migrations, measure time/lock/errors/resources) is recommended before the window.

**OPS-01 impact:** Until K1–K6 close, checklist row **4** remains **OPEN** (staging exists but not parity; soak not run).
