# Phase 1 — A2 Alembic draft crumb (STORY-04-01)

> **Stream:** Backend A2  
> **Date:** 2026-08-02  
> **Honesty:** Migration drafted + ORM/API wired. Docker upgrade/downgrade proof **not validated** this land (low-load). No production migrate. No Production GO.

## Artifacts

| Item | Path |
|------|------|
| Alembic | `salesos/backend/app/alembic/versions/f6b2e84c1a90_story_04_01_tenant_owner_platform_fields.py` (revises `a4f7c29e1b80`) |
| ORM | `Tenant.plan_id` / `region` / `data_residency` / `provisioning_status` / `trial_ends_at` |
| Admin API | list/detail/create/update map new fields; create → `provision_workflow` |
| A3 skeleton | `TenantProvisioningService.provision_workflow` + `scripts/provision_tenant.py` |
| CI unblock | `import os` for `SALESOS_TESTING` dispose in `probe_login_tenant_id` (tip `69da589` F821) |

## Backfill

Existing rows → `provisioning_status='active'`. New defaults → `pending`.

## Next

1. Non-prod Docker `alembic upgrade head` / `downgrade -1` / re-upgrade proof (explicit approval).  
2. D3 adversarial RLS after migrate.  
3. Keep tip Stages 1–5 green.
