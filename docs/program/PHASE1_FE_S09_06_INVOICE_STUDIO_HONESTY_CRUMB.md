# FE-S09-06 — CustomerInvoice Studio presets + payment honesty (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-09-06 `6f02362`  
> **Honesty:** Not Production GO / RAG GO. No invented Hub HTTP / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Constants | Mirror tip `DEFAULT_INVOICE_MAPPINGS` + payment states + move types |
| Map / Schedule | Model preset `account.move` against tip schedule+mapping HTTP |
| Honesty | CustomerInvoice ≠ PlatformBillingInvoice; AR `out_invoice`/`out_refund` only |
| Inventory | Owner Console lists FE-S09-06 |
| Tests | Invoice honesty unit + Studio preset Jest |

## Non-goals

- CustomerInvoice list / ORM UI
- Platform billing / Stripe invoice surfaces
- Unlinked cr_number badge list API (BE-blocked)
- Owner mint / Production GO / RAG GO
