# Phase-2 continue — B.1 / B.2 / C.1 / C.4

**Date:** 2026-08-08 (كمل الكل)  
**Production migrate:** **not run**. Evidence-based Production GO: **not claimed**.

## B.1 Opportunity SoT (Partial — routes unified)

| Surface | After this wave |
|---------|-----------------|
| All `/api/v1/opportunities*` | `commercial.py` → `commercial_opportunities` (list/create/GET/PUT/PUT stage/advance/won/lost/close-won\|lost) |
| `routers/opportunities.py` | **Unmounted** (file kept; do not remount without distinct prefix) |
| `revenue_execution` | `/api/v1/revenue-execution/opportunities*` + `/tasks` + `/pipeline` |
| Dual tables | **still both exist**. Local COUNT both **0** (re-verified 2026-08-08). Staging/prod COUNT **NOT VERIFIED** — do not drop `opportunities` |

FE `pipeline.ts` query-param create; hooks + `opportunity.store` now match commercial query-param create + PUT `{stage}`.

## B.2 Decision Center (Partial)

`/decisions` list → `GET /api/v1/decisions`. Accept/dismiss → Center feedback **and** status flip (`up`→`accepted`, `down`→`rejected`) via `update_decision_status`. Evaluate/scores stay Platform. Runtime DIE unchanged for NBA widgets.

## C.4 `tasks.opportunity_id`

Nullable `String(36)`. **Local Docker upgrade applied** (`f7a1b82c3d09`). Create/list + FE `createTask` / v3 tasks column. Prod/staging upgrade **not run**.

## C.1 Signals → Postgres (Partial — local)

Tables exist locally; RLS FORCE on `signal_subscriptions` + `signal_events`; catalog global (no RLS). Local compose `FEATURE_SIGNAL_MARKETPLACE_POSTGRES=true` after upgrade. Catalog empty until pack seed/`load_all_packs`. Unit tests still InMemory.

## Validation

| Check | Result |
|-------|--------|
| Local `alembic current` | **f7a1b82c3d09 (head)** after `upgrade head` |
| Local COUNT opp tables | both 0 |
| `python -m pytest` Decision Center | **not validated** — slim image missing `pygments` |
| Staging/prod migrate | **not run** |
| Soak claim | **false** (PID 16044; 264 loops @ 2026-08-08T12:21Z; mid-window) |

## Human next

1. Staging/prod `COUNT(*)` both opportunity tables before any unify/drop.  
2. Staging/prod Alembic only after maintenance window you accept.  
3. Soak ≥48–72h then TL K2–K6 — do not flip claim.  
