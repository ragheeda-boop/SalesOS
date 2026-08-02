# STORY-10-05 — Territory Rules Studio (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> In-memory Studio config over CAP-017 runtime — does **not** claim live revenue territory DB writes or 141221.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `TerritoryRule` / `TerritoryMatchCondition` (geography / industry / size) |
| Engine | `assign_territory` — priority match; honest unmatched (no invented key) |
| Store | `MemTerritoriesStore` tenant-scoped |
| HTTP | `GET/POST /api/v1/studio/territories` + `GET …/meta` + `POST …/assign` + `GET/DELETE …/{id}` |
| Tests | Region/industry/size match, priority, tenant isolation, unmatched honesty |

## Acceptance

- Tip HTTP `/api/v1/studio/territories` unblocks FE-S10-05.
- Tenant rules assign by geography/industry/size — covered.
- Unmatched does not invent a territory — covered.

## Non-goals

- FE `/studio/territories` page (FE-S10-05)
- Postgres `territory_rule_sets` persistence / new RLS (deferred)
- Live CAP-017 revenue repository mutation / 141221
- Production GO
