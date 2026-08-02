# FE-S11-03b — GTM hub + criteria handoff (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** FE-S11-02/03 `a81153a`+ (hub later expanded with tip 11-01/04/05/06/09)  
> **Honesty:** Not Production GO / RAG GO. Tip GTM pages only.  
> Live 141221 / live ERP / territories **not claimed**.  
> Tip ICP / lookalikes / enrichment / verification / sequences are **LANDED** on tip (see Stream B crumb) — do not treat as missing.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Hub | `/gtm` lists tip GTM pages present on tip (ICP, market-sizing, lead-discovery, lookalikes, enrichment, verification, sequences) |
| Handoff | Market sizing → lead-discovery query params (tip filter fields) |
| Deep-links | `?snapshot=` / `?run=` against tip GET-by-id |

## Non-goals

- Territory Studio (STORY-10-05) — still BLOCKED
- Live 141221 / live ERP
- Production GO / RAG GO
