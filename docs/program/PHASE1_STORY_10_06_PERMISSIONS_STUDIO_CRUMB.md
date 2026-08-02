# STORY-10-06 — Permissions Studio (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Tenant-custom roles capped at Plan.entitlements ceiling (EPIC-06).

## Landed

| Piece | Detail |
|-------|--------|
| Catalog | Tenant-grantable permission keys → DOM (+ publish) |
| Ceiling | `assert_within_ceiling` / fail-closed privilege escalation |
| Store | `MemCustomRolesStore` tenant-scoped |
| HTTP | `/api/v1/studio/permissions` catalog, ceiling, check, roles |
| Tests | Starter blocks AI; Growth allows; publish flag; Owner keys blocked |

## Acceptance

- Tenant-custom role capped at plan entitlement ceiling — covered.
- Privilege-escalation test passes — covered (AI on Starter, Owner keys, downgrade).

## Non-goals

- FE `/studio/permissions` page wire-up — **LANDED FE-S10-06** (Stream B)
- Postgres role persistence / new RLS
- Mutating Owner Admin `/admin/roles` (separate plane)
- Production GO
