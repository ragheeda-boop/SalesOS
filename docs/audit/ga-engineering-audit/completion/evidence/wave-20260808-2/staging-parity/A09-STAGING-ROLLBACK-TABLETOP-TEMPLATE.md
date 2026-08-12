# Staging cloud rollback tabletop — TEMPLATE (unsigned)

**Date prepared:** 2026-08-13 (agent)  
**ID:** A-09 step 7 / checklist P5  
**Status:** **TEMPLATE ONLY** — execution **OPEN**; local Wave 12 tabletop does **not** satisfy this  
**Host:** `https://salesos-staging.up.railway.app`  
**Related:** [deploy-rollback.md](../../../../runbooks/deploy-rollback.md) · [A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md](./A09-CHECKLIST-7-HUMAN-GATE-2026-08-13.md)

> Fill during a real tabletop. Agents must not forge SIGN_HERE or invent deployment IDs.

---

## Preconditions

| # | Check | Status (fill) |
|---|-------|---------------|
| 1 | Staging `/health` **200** before start | ☐ |
| 2 | Record current SalesOS deployment ID + commit SHA | ☐ |
| 3 | Prefer green `deploy-staging.yml` path — if CI still Unauthorized, use Railway CLI/UI redeploy of **previous SUCCESS** deployment only | ☐ |
| 4 | On-call / owner named for rollback decision | ☐ ________________ |

**Note (2026-08-13):** Sister retry [31647956116](https://github.com/ragheeda-boop/SalesOS/actions/runs/31647956116) still **Unauthorized** on `RAILWAY_TOKEN` — pipeline rollback unproven until token rotate.

---

## Procedure (Railway staging)

1. **Baseline**
   - `GET https://salesos-staging.up.railway.app/health` → record status + timestamp  
   - Note SalesOS / celery-worker / celery-beat deployment IDs (UI or `railway deployment list`)
2. **Deploy forward (optional)**
   - Ship a known-good staging commit (CI or CLI) → wait healthy
3. **Rollback**
   - Redeploy **previous** known-good deployment (Railway “Redeploy” on prior SUCCESS) **or** `railway up` pinned SHA  
   - Do **not** experiment on production
4. **Verify**
   - `/health` **200**  
   - Login smoke (muhide password) **or** Decision evaluate smoke  
   - celery-worker/beat still scheduling if in scope
5. **Record**
   - Before/after deployment IDs, SHAs, UTC times, who approved

---

## Results (human fill)

| Field | Value |
|-------|-------|
| Tabletop date (UTC) | |
| Operator name | |
| Before deployment ID / SHA | |
| After rollback deployment ID / SHA | |
| Health before | |
| Health after | |
| Smoke result | PASS / FAIL |
| Issues | |
| Evidence links | |

---

## SIGN_HERE (human only)

```text
I confirm this staging rollback tabletop was executed as recorded.
Name: ____________________  Date: __________  Role: __________
```

**Agent:** leave blank. Forging this block is forbidden.

---

*Template prepared 2026-08-13. Execution remains Human-Gate.*
