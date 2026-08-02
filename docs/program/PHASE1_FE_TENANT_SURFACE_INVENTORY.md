# Phase 1 — Frontend B1/B2 Tenant surface inventory

> **Stream:** Frontend B1 → B2 — [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1  
> **Triggered:** 2026-08-02 **TRIGGER_POST_PHASE0_PLAN**  
> **Status:** B1 COMPLETE · B2 READ-PATH LANDED (detail modal)  
> **Honesty:** Decision package remains STUB; `feature_ai_copilot` default False. No Production GO.

## Surfaces touching Tenant

| Path | Role |
|------|------|
| `salesos/frontend/src/app/(dashboard)/admin/tenants/page.tsx` | Admin tenant list/create/update/delete + B2 detail read-path |
| `salesos/frontend/src/features/admin/widgets/TenantOwnerPlatformFields.tsx` | B2 Owner Platform field display |
| `salesos/frontend/src/lib/api/types/admin.ts` | `AdminTenantOwnerPlatformFields` contract |
| `salesos/frontend/src/features/admin/` queries/hooks | API client for admin tenants |
| Admin tests under `features/admin/__tests__/` | Mock tenant fixtures |

## STORY-04-01 fields (B2)

Read-path wired for: `plan_id`, `region`, `data_residency`, `provisioning_status`, `trial_ends_at`.

Absent API values show placeholders until Backend A2 schema is migrated in the target env.

## Non-goals

- No edit forms for Owner Platform fields in this land  
- No TenantList widget edits (parallel-agent reserved)  
- No heavy npm / full FE suite without approval  
- No GA AI / Production GO
