# Phase 1/2 boundary — FE-S08-00 Integration Hub inventory (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Honesty:** Not Production GO. No invented Hub HTTP / Odoo GA / owner mint.  
> `TenantList.tsx` untouched.

## Why this story

EPIC-07 Owner Console FE MVP closed (FE-S07-07). BE STORY-08-01..06 landed including Hub HTTP. STORY-08-07 Studio is at `/integrations`.

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

**STORY-08-07 LANDED** after Hub HTTP `f1d06aa` — see [`PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md`](PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md).
