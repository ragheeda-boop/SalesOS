# Phase 1/2 boundary — FE-S08-00 Integration Hub inventory (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Honesty:** Not Production GO. No invented Hub HTTP / Odoo GA / owner mint.  
> `TenantList.tsx` untouched.

## Why this story

EPIC-07 Owner Console FE MVP closed (FE-S07-07). BE STORY-08-01..05 landed framework + SyncRun without Owner/tenant Hub HTTP. STORY-08-07 Integrations Studio UI remains blocked on Hub HTTP APIs.

## Landed (this tip)

| Piece | Detail |
|-------|--------|
| Route | `/admin/integrations` honesty inventory |
| Shell | Owner Console nav + overview deep-link |
| Copy | BE 08-01..05 landed; 08-06..07 gated |
| Tests | Jest inventory page + E2E shell hooks |

## Non-goals

- Connect/test/map/schedule UI (STORY-08-07)
- Invented REST clients for ExternalSystemConnection
- Production GO / Odoo adapter GA claims

## Next FE

Wait for Hub HTTP evidence, then STORY-08-07 Studio flow.
