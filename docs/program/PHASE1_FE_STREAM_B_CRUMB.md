# Phase 1 — Frontend Stream B crumb (through FE-S05-04 UsageMeter)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Evidence tip base:** `0a5f198` (UsageMeter) + `0d04d6c` (portal/catalog/invoices)  
> **Prior:** FE-S04-40…44 @ `3895e7c`  
> **Plan:** [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1 B  

| Task | Status |
|------|--------|
| FE-S04-40…44 | **LANDED** @ `3895e7c` |
| FE-S04-45 Surface `tenants.deleted_at` + retention | **LANDED** (this wave) |
| FE-S05-01 Owner subscription read (404 empty) | **LANDED** (this wave) |
| FE-S05-02 Checkout + 503 empty-state | **LANDED** (this wave) |
| FE-S05-03 Catalog + Portal + platform invoices | **LANDED** (this wave) |
| FE-S05-04 UsageMeter list + Owner rollup | **LANDED** (this wave) |
| B4b FE lint/tsc holdouts | Skipped (needs approval) |

## Honesty

- Stripe Checkout/Portal: 503 fail-closed without `STRIPE_SECRET_KEY` — no invented keys.
- Catalog resolves ops-bound `stripe_price_id_*` or operator-supplied real `price_id`.
- UsageMeter: `GET /billing/usage` view + `POST /billing/usage/rollup` (no Stripe).
- `TenantList.tsx` untouched. **No Production GO.**

**Validation:** focused Jest.
