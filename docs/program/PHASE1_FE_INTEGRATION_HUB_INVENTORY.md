# Phase 1/2 boundary — FE-S08-00 Integration Hub inventory (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Honesty:** Not Production GO. No invented Hub HTTP / Odoo GA / owner mint.  
> `TenantList.tsx` untouched.

## Why this story

EPIC-07 Owner Console FE MVP closed (FE-S07-07). BE STORY-08-01..05 landed framework + SyncRun without Owner/tenant Hub HTTP. STORY-08-07 Integrations Studio UI remains blocked on Hub HTTP APIs.

## Landed

| Piece | Detail |
|-------|--------|
| FE-S08-00 | `/admin/integrations` honesty inventory + Owner Console nav |
| FE-S08-01 (this tip) | Thin Studio step chrome — all steps **disabled**; `Hub HTTP API not live` honesty |
| Copy | BE 08-01..05 landed; 08-06 + full 08-07 gated |
| Tests | Jest inventory + studio shell; E2E disabled-step hooks |

## Non-goals

- Live connect/test/map/schedule/monitor/disconnect (full STORY-08-07 AC)
- Invented REST clients / fake Hub endpoints
- Production GO / Odoo adapter GA claims

## Next FE

**Standby for Hub HTTP.** The moment BE exposes Integration Hub HTTP (after STORY-08-06 as needed), resume full STORY-08-07 Studio wiring on this shell — do not invent APIs meanwhile.
