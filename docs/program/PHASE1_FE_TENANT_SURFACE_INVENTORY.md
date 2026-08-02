# Phase 1 — Frontend B1 Tenant surface inventory

> **Stream:** Frontend B1 — [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1  
> **Triggered:** 2026-08-02 **TRIGGER_POST_PHASE0_PLAN**  
> **Status:** INVENTORY COMPLETE — stubs wait on A1 field contract  
> **Honesty:** Decision package remains STUB; `feature_ai_copilot` default False.

## Surfaces touching Tenant

| Path | Role |
|------|------|
| `salesos/frontend/src/app/(dashboard)/admin/tenants/page.tsx` | Admin tenant list/create/update/delete |
| `salesos/frontend/src/features/admin/` queries/hooks (`useAdminTenants`, create/update/delete) | API client for admin tenants |
| Admin tests under `features/admin/__tests__/` | Mock tenant fixtures |

## Gap vs STORY-04-01 fields

Admin UI currently models name/plan-as-string style payloads (see test mocks). No FE fields yet for:

- `plan_id`, `region`, `data_residency`, `provisioning_status`, `trial_ends_at`

## Next (B2)

After A1 field contract stable: minimal read-path display (optional edit) — no fake GA AI, no heavy npm without approval.
