# Phase 1 — STORY-05-05 Proration (Stream A)

> **Honesty:** Not Production GO. Env-only Stripe secrets (unused here). DEC-085 untouched. BE-only.

## Landed

| Piece | Detail |
|-------|--------|
| Pure math | `proration.py` — remaining fraction, upgrade/downgrade quote |
| Alembic | `c9e5d78a0f26` (revises `b8f4c67d9e15`) — `subscriptions.pending_plan_id` / `pending_effective_at` |
| Policy | Upgrade → immediate prorated charge; Downgrade → period-end (default); Downgrade + `downgrade_immediate` → credit now |
| Owner APIs | `POST /billing/plan-change/quote`, `/apply`, `/apply-pending` |
| Sync | Immediate apply also stamps `Tenant.plan_id` |

## Non-goals

- Stripe InvoiceItem / Subscription Schedule push (sandbox soak residual)
- Entitlement enforcement (STORY-06-02)
- Production GO
