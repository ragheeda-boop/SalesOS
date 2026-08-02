# Phase 1 — STORY-05-03 UsageMeter (Stream A)

> **Honesty:** Not Production GO. No Stripe keys invented/used. DEC-085 untouched. BE-only.  
> Tip prior: `0d04d6c` (portal/invoices/catalog).

## Landed

| Piece | Detail |
|-------|--------|
| Alembic | `a7e3b56c8d04` (revises `f6d2a45b7c03`) |
| Events | `usage_meter_events` — append-only buffer |
| Meters | `usage_meters` — hourly buckets (OBJ-324) |
| Metrics | `seats`, `ai_tokens`, `connector_syncs`, `api_calls`, `storage_mb` |
| Ops | `add` (counters) / `set` (gauges: seats, storage) |
| Service | `UsageMeterService.record_event` + `rollup_pending` |
| Owner API | `POST /billing/usage/events`, `POST /billing/usage/rollup`, `GET /billing/usage` |
| RLS | **not enabled** (Owner-only cross-tenant, same class as Subscription) |

## Rollup rule

Events with `rolled_up_at IS NULL` and `recorded_at < through` (default: start of current UTC hour) aggregate into `(tenant_id, metric_key, period_start)` rows. Avoids per-event write amplification on the meter table.

## Non-goals

- Quota enforcement middleware (STORY-06-03)
- Stripe metered billing push
- Production GO / sandbox soak
