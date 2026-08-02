# Phase 1 — STORY-06-01 Plan.entitlements (Stream A)

> **Honesty:** Not Production GO. Env-only Stripe secrets unused. DEC-085 untouched. BE-only.  
> Feature flags remain a **separate** layer (never conflated with commercial packaging).

## Landed

| Piece | Detail |
|-------|--------|
| Schema | `PlanEntitlements` v1 — `domains` / `quotas` / `deployment_tier` / `support_sla` |
| Source | `COMMERCIAL_LAUNCH_PLAN.md` §2 packaging matrix |
| Alembic | `d0f6e89b1a37` (revises `c9e5d78a0f26`) — `admin_plans.entitlements` JSONB + tier backfill |
| Defaults | `default_entitlements_for_tier(free\|starter\|growth\|enterprise)` |
| Owner API | `entitlements` on Plan create/update/response |
| Non-goal | Request middleware enforcement → **STORY-06-02** |

## Document shape

```json
{
  "version": 1,
  "domains": {
    "DOM-001": {"enabled": true},
    "DOM-021": {"enabled": true, "quota": 1},
    "DOM-022": {"enabled": true, "mode": "limited"},
    "DOM-024": {"enabled": true, "publish": false}
  },
  "quotas": {
    "seats": 5,
    "ai_tokens_monthly": 10000,
    "connectors": 1,
    "storage_mb": 1000,
    "api_calls_monthly": 10000
  },
  "deployment_tier": "pooled",
  "support_sla": "community"
}
```
