# FE-S11-06b — GTM enrichment ↔ verification handoffs (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** `50f8e0b`+ (FE-S11-01/05/06 on tip)  
> **Honesty:** Not Production GO / RAG GO. Tip query-param handoffs only.  
> No invented APIs. Territories / Lookalike still BLOCKED. Live 141221 **not claimed**.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Helpers | `buildEnrichmentHref` / `buildVerificationHref` / `buildIcpProfileHref` / `contactFieldsFromFilled` |
| Enrichment → Verification | When filled has tip `email`/`phone` |
| Enrichment → Lead Discovery | Filled industry/city criteria |
| Lead Discovery → Enrichment | Per discovered company_name |
| ICP → Enrichment | Seed company_name handoff |

## Non-goals

- Territories Studio (STORY-10-05)
- Lookalike ML (STORY-11-04)
- Live vendor enrichment/verification
- Production GO / RAG GO
