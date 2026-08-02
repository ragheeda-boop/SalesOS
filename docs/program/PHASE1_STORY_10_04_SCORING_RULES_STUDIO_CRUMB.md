# STORY-10-04 — Scoring Rules Studio (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Deterministic rules only (not LLM). Fail-safe → platform default on rule error.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `ScoringRule` / `ScoringBoost` + platform default weights |
| Engine | `evaluate_score` / `get_effective_dimension_weights` (fail-safe) |
| Store | `MemScoringRulesStore` tenant-scoped |
| HTTP | `POST/GET /api/v1/studio/scoring-rules` + `POST …/evaluate` |
| Tests | Override ≠ platform; boost; **fail-safe** on zero weights / bad boost |

## Acceptance

- Tenant rule overrides platform default — covered.
- Fail-safe fallback on rule error verified — covered.

## Non-goals

- FE `/studio/scoring` page wire-up
- Postgres rule persistence / new RLS
- LLM / AI Studio scoring
- Production GO
