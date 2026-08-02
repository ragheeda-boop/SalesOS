# FE-S11-02 — Market Sizing (TAM/SAM/SOM) UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-11-02 `4f69d1f` / tip `2b521fc`+  
> **Honesty:** Not Production GO / RAG GO. Tip in-memory gov-dataset-shaped universe only.  
> `TenantList.tsx` untouched. FE-S10-05 territories LANDED (see PHASE1_FE_S10_05_TERRITORIES_STUDIO_CRUMB.md).

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | meta, list, compute (`POST/GET /api/v1/gtm/market-sizing`) |
| UI | `/gtm/market-sizing` |
| Honesty | Live 141221 Postgres adapter not claimed; scale_hint only |

## Non-goals

- Live prod SELECT of 141221
- ICP Engine / Lead Discovery UIs (tip BE not ready)
- Territory Studio (STORY-10-05 — still BE-blocked)
- Production GO / RAG GO
