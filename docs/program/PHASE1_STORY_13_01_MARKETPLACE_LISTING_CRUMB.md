# STORY-13-01 — MarketplaceListing object (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS — Owner-platform catalog).  
> `feature_ai_copilot` unchanged (False). R-02 pilot soak residual OPEN (Ops).

## Landed

| Piece | Detail |
|-------|--------|
| Object | `MarketplaceListing` (OBJ-325) — one shape for connector/app/prompt_pack/playbook |
| Store | `MemMarketplaceListingStore` (in-memory Owner catalog) |
| HTTP | `GET/POST /api/v1/marketplace/listings` + meta/seed/get/delete |
| Seed | First-party Odoo + HubSpot connector listings (CI certify paths) |
| Tests | Cross-type single object; slug uniqueness; seed idempotent; semver |

## Non-goals

- STORY-13-02 certification pipeline / sandboxed trial
- STORY-13-03 FE browse/install UI
- Live HubSpot/Odoo sync as GO / R-02 close invent
- Studio Postgres / `for_each` / AI-Lead 12-01..03 invent
- Production GO
