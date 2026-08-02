# STORY-11-02 — TAM/SAM/SOM Market Sizing (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> CI uses gov-dataset-**shaped** in-memory universe (250 rows).  
> Live **141,221** count requires Postgres `CompanyUniverse` adapter — **not claimed**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `MarketSizingCriteria` / `MarketSizingSnapshot` |
| Engine | `compute_tam_sam_som` — invariant SOM ≤ SAM ≤ TAM |
| Universe | `MemCompanyUniverse` + pluggable `CompanyUniversePort` |
| HTTP | `POST/GET /api/v1/gtm/market-sizing` + `/meta` |
| Tests | Nesting invariant, demo universe, tenant snapshot isolation |

## Acceptance

Computed against government-dataset-shaped company universe for ≥1 tenant — covered in CI via fixture; scale hint documents 141221.

## Non-goals

- Live prod SELECT count of 141221 in this land
- ICP Engine (STORY-11-01, AI-Lead)
- Lead Discovery (STORY-11-03)
- Territories BE (STORY-10-05)
- Production GO
