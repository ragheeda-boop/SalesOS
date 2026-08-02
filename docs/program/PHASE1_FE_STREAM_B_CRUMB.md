# Phase 1 — Frontend Stream B crumb (through FE-S04-35)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Evidence tip base:** `fd5af4d` / `e9ef08d` · this land = FE-S04-33/34/35  
> **Prior:** FE-S04-24…28 @ `78e4c26`  
> **Plan:** [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1 B  

| Task | Status |
|------|--------|
| FE-S04-24…28 | **LANDED** @ `78e4c26` |
| FE-S04-29 Filter URL query helper | **LANDED** — `buildAdminTenantsFilterQuery` |
| FE-S04-33 Server `page`/`page_size` + `X-Total-Count` | **LANDED** — `useAdminTenantsPaged` (`e9ef08d`) |
| FE-S04-34 Reprovision failed/pending | **LANDED** — `POST .../reprovision` |
| FE-S04-35 Retention + `force_immediate` hard-delete | **LANDED** — STORY-04-04 (`fd5af4d`) |
| B4b FE lint/tsc holdouts | Skipped (needs approval) |

**FE-S04-33:** Owner Console always sends `page` + `page_size=20`; result count + pager use `X-Total-Count`. Legacy `useAdminTenants` still returns `items[]` for `TenantList` / AdminWorkspace (omit page → BE returns all).

**FE-S04-34:** Detail modal Reprovision when `provisioning_status` is `failed` or `pending` (no `force_active` from UI).

**FE-S04-35:** Soft-delete honesty mentions retention stamp; hard-delete modal exposes retention copy + `force_immediate` checkbox; API sends `force_immediate` (default false). Surfaces 409 retention detail in toast.

**Non-touch:** `TenantList.tsx`.  
**Validation:** focused Jest. **No Production GO.**
