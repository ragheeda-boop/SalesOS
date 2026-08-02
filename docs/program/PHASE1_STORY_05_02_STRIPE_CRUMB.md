# Phase 1 — STORY-05-02 Stripe scaffold (Stream A)

> **Honesty:** Not Production GO. **No invented Stripe keys.** DEC-085 untouched. BE-only.  
> Sandbox credentials must come from real env (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`).

## Landed this wave

| Piece | Path / detail |
|-------|----------------|
| Signature verify | `billing/stripe_signature.py` — HMAC v1, fail-closed if secret empty |
| Event → SM map | `billing/stripe_events.py` |
| Idempotency | table `stripe_webhook_events` (PK `event_id`) Alembic `e5c1f34a6b02` |
| Webhook | `POST /api/v1/billing/stripe/webhook` — 503 if secret unset; 400 bad sig |
| Checkout | `POST /api/v1/admin/billing/stripe/checkout-session` — 503 if secret unset |
| Subscription cols | `stripe_customer_id`, `stripe_subscription_id` |
| CSRF / suspend skip | webhook path exempt (signature is the authz) |
| Config | `Settings.stripe_*` default `""` (env-only) |
| Tests | `tests/unit/test_stripe_webhook_story_05_02.py` |

## Event map (subset)

| Stripe | SM |
|--------|-----|
| `checkout.session.completed` / `invoice.paid` | activate (+ reactivate/resubscribe adapters) |
| `invoice.payment_failed` | mark_past_due |
| `customer.subscription.deleted` | churn |
| `customer.subscription.updated` | by Stripe status |

## Explicit non-goals / residual

- Live sandbox soak / 20-txn demo (needs real Stripe test keys in ops)
- Invoice sync UI / `platform_billing_invoices` rename cutover
- Dunning job (STORY-05-04)
- Production billing mode
- Adding `stripe` PyPI SDK (httpx REST only)

## Ops

Set in non-prod secrets store (never commit):

```text
STRIPE_SECRET_KEY=sk_test_…
STRIPE_WEBHOOK_SECRET=whsec_…
STRIPE_PUBLISHABLE_KEY=pk_test_…
```

Point Stripe CLI / Dashboard webhook to `/api/v1/billing/stripe/webhook`.
Pass `metadata.tenant_id` on Checkout / Subscription.
