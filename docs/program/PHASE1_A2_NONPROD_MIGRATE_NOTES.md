# Phase 1 A2 — Non-prod Alembic migrate notes (STORY-04-01)

> **Revision:** `f6b2e84c1a90` (revises `a4f7c29e1b80`)  
> **Honesty:** Non-prod only. No production migrate in this note. **No Production GO.** DEC-085 untouched.

## What it does

Additive columns on `tenants`:

| Column | Type | Default / backfill |
|--------|------|--------------------|
| `plan_id` | `VARCHAR(64)` NULL | null |
| `region` | `VARCHAR(32)` NULL | null |
| `data_residency` | `VARCHAR(32)` NULL | null |
| `provisioning_status` | `VARCHAR(32)` NOT NULL | server default `pending`; existing rows → `active` |
| `trial_ends_at` | `TIMESTAMPTZ` NULL | null |

Keeps legacy `tenants.plan` (display/tier label). Does **not** alter RLS policies or `set_config`.

## Docker non-prod procedure

From `salesos/` with compose stack healthy:

```bash
docker exec salesos-backend-1 alembic current
# expect: a4f7c29e1b80 (pre) or f6b2e84c1a90 (post)

docker exec salesos-backend-1 alembic upgrade head
docker exec salesos-backend-1 alembic current
# expect: f6b2e84c1a90

# Downgrade proof
docker exec salesos-backend-1 alembic downgrade -1
docker exec salesos-backend-1 alembic current
# expect: a4f7c29e1b80

docker exec salesos-backend-1 alembic upgrade head
docker exec salesos-backend-1 alembic current
# expect: f6b2e84c1a90
```

SQL spot-check:

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name='tenants'
  AND column_name IN ('plan_id','region','data_residency','provisioning_status','trial_ends_at')
ORDER BY 1;

SELECT version_num FROM alembic_version;
```

## D3 after migrate

```bash
docker exec salesos-backend-1 poetry run pytest \
  tests/integration/test_adversarial_rls_story_04_01.py -q --tb=short
```

Suite skips if columns absent (pre-migrate). After upgrade: expect PASS; `POLICY_COUNT` remains **67**.

## Local tip pin (2026-08-02)

Host Docker DB observed at `a4f7c29e1b80` before A2 apply (backend container restart flaky). Upgrade still required on local non-prod before D3 can run unskipped.

## Forbidden

- Production Railway migrate without explicit human/ops approval  
- Claiming Production GO / GA GO  
- Reopening GHCR as Phase 0 gate / weakening DEC-085
