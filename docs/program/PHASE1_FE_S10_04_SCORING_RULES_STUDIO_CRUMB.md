# FE-S10-04 — Scoring Rules Studio UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-10-04 `f7456f2` / tip `4230dad`+  
> **Honesty:** Not Production GO / RAG GO. Tip in-memory scoring-rules only.  
> `TenantList.tsx` untouched. Deterministic rules only (not LLM).

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | `GET/POST /api/v1/studio/scoring-rules` + `POST …/evaluate` |
| UI | `/studio/scoring` — list, upsert weights/boosts, evaluate panel |
| Honesty | Fail-safe → platform default; process-local store — not Postgres |

## Non-goals

- Postgres / Alembic scoring persistence
- LLM / AI Studio scoring
- Territory config (STORY-10-05 — BE not on tip)
- Production GO / RAG GO
