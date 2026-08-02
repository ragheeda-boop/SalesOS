# Phase 1 — Frontend B1 inventory + B2/B5 Owner Platform UI

> **Stream:** Frontend B1–B5 — [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1  
> **Status:** **B1 COMPLETE** · **B2 COMPLETE** · **B3 AFFIRMED** · **B5 WRITE-PATH LANDED**  
> **Contract:** [`PHASE1_STORY_04_01_PRETASK.md`](PHASE1_STORY_04_01_PRETASK.md) A1  
> **Honesty:** Decision package remains STUB; `feature_ai_copilot` default **False**. **No Production GO.**

## Surfaces touching Tenant (Owner Console = Platform admin)

| Path | Role | Touch |
|------|------|-------|
| `salesos/frontend/src/app/(dashboard)/admin/tenants/page.tsx` | Tenant Management | B2 list/detail · B5 create+edit Owner Platform |
| `salesos/frontend/src/features/admin/widgets/TenantOwnerPlatformFields.tsx` | Read + write Owner Platform panel | B2/B5 |
| `.../widgets/__tests__/TenantOwnerPlatformFields.test.tsx` | Unit tests | B5 |
| `salesos/frontend/src/lib/api/types/admin.ts` | Optional STORY-04-01 fields | B2 |
| `salesos/frontend/src/lib/api/admin.ts` | create/update payloads | B5 create fields |
| `salesos/frontend/src/features/admin/widgets/TenantList.tsx` | Embedded table | **RESERVED — untouched** |

## Field mapping

| Field | Read | Write (detail) | Create |
|-------|------|----------------|--------|
| `plan_id` | yes | yes | optional |
| `region` | yes | yes | optional |
| `data_residency` | yes | yes | optional |
| `provisioning_status` | badge | select | default via API/backend |
| `trial_ends_at` | yes | date input | not on create form yet |

## Provisioning honesty

Sprint-04 expected demo is **script-first** (`provision_tenant` / STORY-04-02). FE exposes status correction + create field pass-through; does **not** claim full idempotent Studio seed UI.

## Validation

| Label | Notes |
|-------|-------|
| **light validated** | Focused Jest `TenantOwnerPlatformFields` **6/6 PASS**; full FE suite not run |
| **not validated** | Browser / production migrate |

## Non-goals

- `TenantList.tsx` edits  
- GA AI enablement  
- Production GO  
- B4 heavy npm holdout burn unless approved  
