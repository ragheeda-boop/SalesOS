# Phase 1 — STORY-04-04 `deleted_at` + subscription lifecycle sync

> **Stream:** Backend A · tip after STORY-05-01 `4c2a5c9`  
> **Honesty:** Not Production GO. DEC-085 untouched. BE-only. No Stripe.

## STORY-04-04 column cutover

| Item | Detail |
|------|--------|
| Alembic | `d4b0e23f5a91` (revises `c3a9f12d4e80`) |
| Column | `tenants.deleted_at` TIMESTAMPTZ NULL + `ix_tenants_deleted_at` |
| Backfill | from `settings.deletion_requested_at` when parseable |
| Dual-write | `stamp`/`clear` update column **and** settings key (compat) |
| Prefer | `get_deletion_requested_at` reads column first, then settings |

## Subscription sync (STORY-05-01 follow-on)

| Owner action | Subscription event (best-effort) |
|--------------|----------------------------------|
| suspend | `suspend` when legal |
| activate | `reactivate` if suspended; else `resubscribe_active` if churned |
| soft-delete | `churn` when legal |

No subscription row → no-op (does not fail tenant lifecycle).

## API honesty

`TenantDetail.deleted_at` + `TenantLifecycleResponse.deleted_at` / `subscription_status`.

## Non-goals

- Stripe (STORY-05-02)
- Production migrate
- Dropping settings key (keep dual-write until FE/ops confirmed)
