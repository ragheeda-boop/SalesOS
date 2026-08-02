# FE-S11-05 — Enrichment Waterfall UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-11-05 `96b9f8b` / tip after FE-S11-01 `df21966`+  
> **Honesty:** Not Production GO / RAG GO. Tip ≥2 FakeEnrichment providers only.  
> Live Clearbit/Apollo/ERP — **not claimed**. Live 141221 — **not claimed**.  
> `TenantList.tsx` untouched. FE-S10-05 territories LANDED (PHASE1_FE_S10_05). FE-S11-04 lookalikes LANDED.

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | meta, list, get, run |
| UI | `/gtm/enrichment` — seed form, known locks, provider order, hits |
| Hub | Linked from `/gtm` + `?run=` / `company_name` / `domain` deep-links |

## Non-goals

- Live vendor enrichment network calls
- Lookalike ML (STORY-11-04)
- Territory Studio (STORY-10-05)
- Production GO / RAG GO
