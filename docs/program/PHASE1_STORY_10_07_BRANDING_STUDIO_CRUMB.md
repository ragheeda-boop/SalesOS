# STORY-10-07 — Branding & Languages Studio (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Unblocks FE-S10-07 `/studio/branding`.

## Landed

| Piece | Detail |
|-------|--------|
| Model | `BrandingConfig` (display_name, logo_url, colors, locales) |
| Store | `MemBrandingStore` tenant-scoped |
| HTTP | `GET/PUT /api/v1/studio/branding` |
| Tests | Live per tenant, isolation, hex/locale/logo scheme validation |

## Acceptance

Logo/color/name live per tenant — covered (in-memory Studio; FE renders from HTTP).

## Non-goals

- Object upload / CDN provisioning (URL string only)
- Postgres branding persistence / new RLS
- Territories BE (STORY-10-05)
- Production GO
