# A.1 / A.2 — Opportunity route collision + table census

**Date:** 2026-08-08  
**Priority:** P0  
**Production migrate:** not run. Staging/prod row counts: **NOT VERIFIED**.

## A.1 Fix (code)

`revenue_execution` registered first with `POST/GET /api/v1/opportunities` → won FastAPI match; FE (`pipeline.ts`) uses **query-param** create + `{items,total}` list + `/advance|/won|/lost` = **commercial.py** contract.

| Router | After A.1 |
|--------|-----------|
| `modules/revenue_execution/router.py` | `/api/v1/revenue-execution/opportunities*` only. `/tasks` + `/pipeline` unchanged |
| `routers/commercial.py` | **SoT** for `GET/POST /api/v1/opportunities` + advance/won/lost |
| `routers/opportunities.py` | **Unmounted** — commercial owns all `/api/v1/opportunities*` |

## A.2 Census (local Docker Postgres)

```
opportunities            COUNT = 0
commercial_opportunities COUNT = 0
```

**Migration strategy (local):** no live rows to move. **Staging/prod:** operator must re-run the same `COUNT(*)` before B.1 unify.

## Residual

- Dual tables remain until staging/prod `COUNT(*)` (operator). Do not drop `opportunities`.  
- Local Alembic **f7a1b82c3d09** applied. See [PHASE2-B1-B2-C1-C4.md](./PHASE2-B1-B2-C1-C4.md).  

**Validation:** A.1+B.1 local SQL **light validated**. Staging/prod census **not verified**.
