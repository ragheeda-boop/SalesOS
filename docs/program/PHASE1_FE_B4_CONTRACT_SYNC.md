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
| FE-S04-12 | Region + data_residency list columns/filters | **LANDED** |
| FE-S04-13 | Inactive vs Suspended list honesty | **LANDED** — `activityStatusLabel` |
| FE-S04-14 | E2E region/residency + delete modal (cancel, no mutate) | **HOOKS LANDED** |
| FE-S04-15 | Trial ends column + filter (has/expired/none) | **LANDED** |
| FE-S04-16 | Opaque plan_id column + search + clear filters | **LANDED** |
| FE-S04-17 | Detail lifecycle honesty (soft-delete vs suspend) | **LANDED** |
| FE-S04-18 | Copy tenant id/slug from detail | **LANDED** |
| FE-S04-19 | Client list sort (created/name) | **LANDED** |
| FE-S04-20 | Wire list hooks to server filter query params (`0782fa4`) | **LANDED** |
| FE-S04-21 | Debounce search + plan_id (400ms) | **LANDED** |
| FE-S04-22 | Active filter chips (dismissible) | **LANDED** |
| FE-S04-23 | Detail modal → soft/hard delete entry | **LANDED** |
| FE-S04-24 | URL query sync for filters/sort/page | **LANDED** |
| FE-S04-25 | Trial badge (active/expired/none) | **LANDED** |
| FE-S04-26 | Result count honesty | **LANDED** |
| FE-S04-27 | Wire Activate to `POST .../activate` (`d9d1472`) | **LANDED** |
| FE-S04-28 | Wire sort to `GET ...?sort=` + `TenantLifecycleResponse` types (`5d052cf`) | **LANDED** |
| FE-S04-29 | Shareable filter URL query helper | **LANDED** |
| FE-S04-33 | Server `page`/`page_size` + `X-Total-Count` (`e9ef08d`) | **LANDED** |
| FE-S04-34 | Reprovision failed/pending via `POST .../reprovision` (`e9ef08d`) | **LANDED** |
| FE-S04-35 | Soft-delete retention + hard-delete `force_immediate` (`fd5af4d`) | **LANDED** |
