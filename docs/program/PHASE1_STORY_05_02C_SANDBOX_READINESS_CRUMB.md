# Phase 1 — STORY-05-02c Stripe sandbox readiness (Stream A)

> **Honesty:** Not Production GO. **No invented Stripe keys.** DEC-085 untouched. BE-only.  
> Live 20-txn soak remains **ops** (real `sk_test_` / `whsec_` in env).

## Landed

| Piece | Detail |
|-------|--------|
| Owner API | `GET /api/v1/admin/billing/stripe/status` — booleans only (never echoes secrets) |
| Flags | `secret_key_configured`, `webhook_secret_configured`, `publishable_key_configured` |
| Ready | `sandbox_soak_ready` = secret ∧ webhook configured |
| Explicit | `production_go: false`, `production_billing: false` |

## Ops soak checklist (human / CI with secrets)

1. Set env-only `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` (+ optional publishable).
2. Confirm `GET .../billing/stripe/status` → `sandbox_soak_ready: true`.
3. Bind Price ids on plans (`stripe_price_id_monthly` / `_yearly`).
4. Checkout → webhook activate → invoice sync → portal session.
5. Replay same webhook `event.id` → idempotent duplicate (ledger).

## Non-goals

- Committing keys / inventing fixtures that look like live secrets
- Production billing mode flip
