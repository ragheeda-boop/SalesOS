# FE-S11-01 — ICP Profiles UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-11-01 `d5e40a8` / tip `96b9f8b`+ (post FE-S11-03b + STORY-11-05 BE)  
> **Honesty:** Not Production GO / RAG GO. Tip in-memory versioned ICP only.  
> Deterministic fit — **no** ML / won-lost backtest. Live 141221 **not claimed**.  
> `TenantList.tsx` untouched. FE-S10-05 territories still BLOCKED.

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | meta, list, create, update, get, score |
| UI | `/gtm/icp` — profiles, version bump PUT, score panel |
| Hub | Linked from `/gtm` + handoff to lead-discovery filters |

## Non-goals

- ML / Opportunity won-lost backtest
- Live 141221 Postgres adapter
- Territory Studio (STORY-10-05)
- Production GO / RAG GO
