# STORY-11-01 — ICP Engine / versioned ICPProfile (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Deterministic weighted fit only — **no** historical won/lost Opportunity backtest claimed.  
> Live **141,221** Postgres adapter — **not claimed**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `ICPProfile` / `ICPCriteria` / `ICPWeights` (OBJ-350) |
| Engine | Deterministic `score_company_against_profile` |
| Store | In-memory tenant store; `schema_version` bumps on PUT |
| HTTP | `POST/GET/PUT /api/v1/gtm/icp-profiles` + `/{id}/score` + `/meta` |
| Tests | Create/list reuse, version bump, tenant isolation, fit scoring |

## Acceptance

Versioned, reusable `ICPProfile` object across sessions — covered in CI via in-memory store.

## Non-goals

- ML / Opportunity won-lost backtest (AI-Lead follow-on)
- Live 141221 Postgres company universe
- Territories BE (STORY-10-05)
- Production GO
