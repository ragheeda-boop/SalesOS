# STORY-11-04 — Lookalike Accounts (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> CI uses in-memory won/lost Opportunity-**shaped** fixtures.  
> Live Muhide Opportunity ML backtest / **141,221** — **not claimed**.  
> Territories BE (STORY-10-05) — **not invented**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `LookalikeModel` / `LookalikeHit` / `OpportunityRecord` (OBJ-352) |
| Engine | Deterministic firmographic similarity + won/lost affinity boost |
| History | `MemOpportunityHistory` demo fixture (won + lost) |
| HTTP | `POST/GET /api/v1/gtm/lookalikes` + `/meta` |
| Tests | Ranking, empty-history reject, tenant isolation, version bump |

## Acceptance

Trained on tenant's own won/lost Opportunity-shaped history — covered in CI via fixture (not live DB ML).

## Non-goals

- Live Opportunity Postgres training / ML embeddings
- Live 141221 company universe
- Territories BE (STORY-10-05)
- Production GO
