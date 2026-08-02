# Phase 1 Stream A — Non-prod Alembic migrate notes (STORY-05-01)

> **Revision:** `c3a9f12d4e80` (revises `f6b2e84c1a90`)  
> **Honesty:** Non-prod only. No production migrate in this note. **No Production GO.** DEC-085 untouched. No RLS on `subscriptions` (Owner-only).

## What it does

Creates Owner-plane `subscriptions` (OBJ-321):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `tenant_id` | UUID UNIQUE | one current subscription per tenant |
| `plan_id` | VARCHAR(64) NULL | matches `tenants.plan_id` |
| `status` | VARCHAR(32) | trial\|active\|past_due\|suspended\|churned |
| `billing_cycle` | VARCHAR(16) | monthly\|yearly |
| `seats` | INT | default 1 |
| `trial_ends_at` / period / `canceled_at` | TIMESTAMPTZ | nullable |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

## Docker non-prod procedure

From `salesos/` with compose stack healthy:

```bash
docker exec salesos-backend-1 alembic current
# expect: f6b2e84c1a90 (pre) or c3a9f12d4e80 (post)

docker exec salesos-backend-1 alembic upgrade head
docker exec salesos-backend-1 alembic current
# expect: c3a9f12d4e80
```

## Validation status

| Check | Status |
|-------|--------|
| Pure state-machine smoke (host) | light validated |
| Full pytest / Docker migrate | not validated on this host wave |
| Production migrate | **not run** |
