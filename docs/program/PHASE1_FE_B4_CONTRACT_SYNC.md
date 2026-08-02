# Phase 1 — Frontend B4 contract sync (Backend A2)

> **Stream:** Frontend B4 — contract sync after Backend A2 land  
> **Date:** 2026-08-02  
> **Backend tip:** `64b44e9` (Alembic `f6b2e84c1a90` + `TenantCreate`/`TenantUpdate`/`TenantListItem`/`TenantDetail`)  
> **Honesty:** FE types/API client aligned. **No Production GO.** Plan §4.1 B4 *lint/tsc holdouts* remain optional (needs approval).

## Sync matrix

| Backend field | FE type | Create | Update | List/Detail |
|---------------|---------|--------|--------|-------------|
| `plan_id` String(64) | `string \| null` | optional | optional | required-nullable |
| `region` String(32) | `string \| null` | optional | optional | required-nullable |
| `data_residency` String(32) | `string \| null` | optional | optional | required-nullable |
| `provisioning_status` | `pending\|active\|suspended\|failed` | via workflow | optional | required (default pending) |
| `trial_ends_at` | ISO string \| null | optional | optional | required-nullable |
| `admin_email` (create only) | optional string | **wired** | — | — |

## Artifacts

- `AdminTenantOwnerPlatformFields` / `AdminTenantCreate` / `AdminTenantUpdate`
- `ADMIN_PROVISIONING_STATUS_VALUES`
- Create UI: `admin_email` + Owner Platform + trial date
- Contract + admin-queries fixtures updated

## Non-touch

- `TenantList.tsx`
- Heavy npm lint/tsc holdout burn (plan B4 optional — separate approval)

## Next FE stories (Sprint-04+)

| ID | Item | Status |
|----|------|--------|
| FE-S04-06 | Suspend path uses `/suspend` (sets provisioning_status) | **LANDED** — `suspendAdminTenant` + detail toggle |
| FE-S04-07 | Surface provision_workflow result fields in toast | **LANDED** — `formatProvisionResultDescription` |
| FE-S04-08 | E2E admin tenant create smoke | **HOOKS LANDED** — `28-admin-tenants-owner-platform.spec.ts` (nav+modal; no mutate; creds skip) |
| FE-S04-09 | Soft-delete honesty (not “permanent”) | **LANDED** |
| FE-S04-10 | List filter by activity + provisioning_status | **LANDED** |
| FE-S04-11 | Hard-delete API + confirm checkbox | **LANDED** |
