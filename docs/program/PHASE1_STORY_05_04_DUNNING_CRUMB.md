# Phase 1 — STORY-05-04 Dunning (Stream A)

> **Honesty:** Not Production GO. Env-only Stripe secrets (unchanged). DEC-085 untouched. BE-only.

## Landed

| Piece | Detail |
|-------|--------|
| Alembic | `b8f4c67d9e15` (revises `a7e3b56c8d04`) — `dunning_cases` |
| Policy | `Settings.dunning_grace_days` (default **7**, not a secret) |
| Open | Stripe `MARK_PAST_DUE` → open/bump case (first failure clock wins) |
| Clear | Activate/reactivate/resubscribe → clear open cases |
| Evaluate | `POST /billing/dunning/evaluate` — grace elapsed → SM suspend + `Tenant.provisioning_status=suspended` |
| Owner APIs | list / open / evaluate / clear |
| ORM | `DunningCaseModel` |

## Flow

```text
payment_failed → past_due + dunning open (grace_ends_at = failed_at + N days)
… grace …
evaluate → subscription suspended + tenant suspended (write-guard applies)
payment recovered → activate → dunning cleared
```

## Non-goals

- Stripe Smart Retries configuration (ops Dashboard)
- Email/SMS dunning communications
- Production GO / sandbox soak
