# FE-S09-01 — Partner Studio presets + cr_number join honesty (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-09-01 + FE-S09-02  
> **Honesty:** Not Production GO. No invented Hub HTTP / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Constants | Mirror tip `DEFAULT_PARTNER_MAPPINGS` + join outcomes |
| Map / Schedule | Model preset `res.partner` against tip schedule+mapping HTTP |
| Honesty | cr_number join outcomes strip; badge **list** API still BE-blocked |
| Inventory | Owner Console lists FE-S09-01 |
| Tests | Partner honesty unit + Studio preset Jest |

## Non-goals

- Unlinked cr_number badge list API (BE-blocked)
- Persist commercial ORM UI
- Owner mint / Production GO
