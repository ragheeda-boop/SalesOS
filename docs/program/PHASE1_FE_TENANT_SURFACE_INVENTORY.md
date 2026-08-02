# Phase 1 — Frontend B1 inventory + B2/B4/B5 Owner Platform UI

> **Stream:** Frontend B1–B5 — [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1  
> **Status:** **B1–B5 + B4 + FE-S04-06..11 COMPLETE** (soft/hard delete + filters)  

> **Backend contract:** A2 @ `64b44e9` — [`PHASE1_FE_B4_CONTRACT_SYNC.md`](PHASE1_FE_B4_CONTRACT_SYNC.md)  
> **Honesty:** Decision STUB; `feature_ai_copilot` default **False**. **No Production GO.**

## Surfaces

| Path | Role | Touch |
|------|------|-------|
| `admin/tenants/page.tsx` | Tenant Management | B2/B4/B5 |
| `TenantOwnerPlatformFields.tsx` | Read + write panel | B2/B5 |
| `lib/api/types/admin.ts` | A2-aligned types + Create/Update | B4 |
| `lib/api/admin.ts` | Typed create/update clients | B4 |
| `TenantList.tsx` | Embedded table | **RESERVED — untouched** |

## Field mapping (post-B4)

| Field | List/Detail | Create | Update |
|-------|-------------|--------|--------|
| `plan_id` | required-nullable | optional | optional |
| `region` | required-nullable | optional | optional |
| `data_residency` | required-nullable | optional | optional |
| `provisioning_status` | required | workflow default | optional select |
| `trial_ends_at` | required-nullable | optional date | optional date |
| `admin_email` | — | optional (wired) | — |

## Validation

| Label | Notes |
|-------|-------|
| **light validated** | Focused Jest for widget + admin tenant contracts + admin-queries |
| **not validated** | Full FE suite / browser / prod migrate |

## Non-goals

- `TenantList.tsx` edits  
- Heavy npm holdout burn without approval  
- Production GO  
