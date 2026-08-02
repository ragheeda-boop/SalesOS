# Phase 1 — STORY-05-02b Portal + invoices + plan catalog

> **Honesty:** Not Production GO. **No invented Stripe keys.** DEC-085 untouched. BE-only.  
> Continues `f7fffb8` Stripe scaffold.

## Landed

| Piece | Detail |
|-------|--------|
| Alembic | `f6d2a45b7c03` (revises `e5c1f34a6b02`) |
| Plan catalog | `admin_plans.stripe_price_id_monthly` / `_yearly` |
| Catalog API | `GET /api/v1/admin/billing/catalog` |
| Checkout | accepts `plan_id` + `billing_cycle` → resolves Price id |
| Portal | `POST /api/v1/admin/billing/stripe/portal-session` (needs `stripe_customer_id`) |
| Invoices | `platform_billing_invoices` (OBJ-323) + webhook upsert on `invoice.*` |
| List | `GET /api/v1/admin/billing/platform-invoices?tenant_id=` |
| Client | `stripe_client.stripe_post_form` — fail-closed without `STRIPE_SECRET_KEY` |

## Ops (env only — never commit)

```text
STRIPE_SECRET_KEY=sk_test_…
STRIPE_WEBHOOK_SECRET=whsec_…
```

Bind real Stripe Price ids on plans via Owner `PUT /plans/{id}` (`stripe_price_id_monthly` / `_yearly`).

## Residual

- Sandbox soak / live portal demo (ops keys)
- STORY-05-03 UsageMeter
- Production billing mode
