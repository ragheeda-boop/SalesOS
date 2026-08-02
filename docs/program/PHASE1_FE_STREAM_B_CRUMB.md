# Phase 1 — Frontend Stream B crumb (through FE-S04-28)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Evidence tip base:** `5d052cf` · this land = FE-S04-24…28  
> **Prior:** FE-S04-21/22/23 @ `7828008` · activate API @ `d9d1472`  
> **Plan:** [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1 B  

| Task | Status |
|------|--------|
| FE-S04-24 URL query sync | **LANDED** |
| FE-S04-25 Trial badge | **LANDED** |
| FE-S04-26 Result count | **LANDED** |
| FE-S04-27 Wire Activate to `POST .../activate` | **LANDED** |
| FE-S04-28 Wire sort to `GET ...?sort=` + lifecycle types | **LANDED** |
| B4b FE lint/tsc holdouts | Skipped (needs approval) |

**FE-S04-28:** `useAdminTenants({ sort })` → server order (`5d052cf`); client `sortAdminTenants` no longer applied in page. Types unified on `AdminTenantLifecycleResponse` for suspend/activate/soft-delete.

**Non-touch:** `TenantList.tsx`.  
**Validation:** focused Jest. **No Production GO.**
