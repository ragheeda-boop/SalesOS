# FE-S09-02 — Opportunity Studio presets + stage honesty (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-09-02 `1987e3b`  
> **Honesty:** Not Production GO. No invented Hub HTTP / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Constants | Mirror tip canonical stages + default `crm.lead` mappings |
| Map / Schedule | Model presets `company` / `crm.lead` against tip schedule+mapping HTTP |
| Honesty | Translated stages strip; unmapped fail loudly; no raw passthrough |
| Inventory | Owner Console lists STORY-09-01/09-02 BE + FE-S09-02 |
| Tests | Honesty unit + Studio preset Jest |

## Non-goals

- New opportunity list/sync HTTP (not on tip)
- Unlinked cr_number badge list API (BE-blocked)
- Persist to commercial ORM UI
- Owner mint / Production GO
