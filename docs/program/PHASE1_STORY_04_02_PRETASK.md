# Phase 1 — STORY-04-02 Provisioning workflow pre-task (A3)

> **Stream:** Backend A3 — [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1  
> **Depends:** A1 field contract stable; A2 Alembic `f6b2e84c1a90`  
> **Status:** SKELETON LANDED with A2 (same wave)  
> **Honesty:** Not Production GO. DEC-085 untouched.

## Goal

Idempotent provisioning job:

1. Create tenant (or reuse by slug)
2. Seed default roles/permissions
3. Seed default Studio config (`studio.defaults` YAML per plan tier — hardcoded debt)
4. Assign first admin (optional email/password)

## Implementation pin

| Artifact | Path |
|----------|------|
| Workflow | `TenantProvisioningService.provision_workflow` |
| Studio seed | `TenantProvisioningService.seed_studio_config` |
| CLI demo | `salesos/backend/scripts/provision_tenant.py` |
| API | `POST /api/v1/admin/tenants` → workflow |

## Non-goals

- Stripe / billing / dunning  
- Tenant Studio editor UI (Phase 3)  
- Production GO / GA GO
