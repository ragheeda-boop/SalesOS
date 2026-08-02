# FE-S11-02b — Market Sizing detail + nested bands (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-11-02 `4f69d1f` / FE-S11-02 `d96a940`+  
> **Honesty:** Not Production GO / RAG GO. Tip in-memory gov-dataset-shaped universe only.  
> Live 141221 Postgres adapter **not claimed**. `TenantList.tsx` untouched.  
> FE-S10-05 territories still BLOCKED. FE-S11-03 Lead Discovery **STANDBY** until tip HTTP lands (local WIP ignored).

## Landed

| Piece | Detail |
|-------|--------|
| Detail | Tip `GET /api/v1/gtm/market-sizing/{id}` on row select |
| UI | Nested TAM/SAM/SOM/universe bands + criteria reload into form |
| Meta | Surfaces tip `/meta` honesty string |

## Non-goals

- Live 141221 Postgres adapter
- ICP / Lead Discovery UIs (tip BE not ready)
- Territory Studio
- Production GO / RAG GO
