# FE-S08-08 — Conflict-policy Studio + Odoo connector honesty (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-09-01 `06c3da7` + Hub HTTP STORY-08-06  
> **Honesty:** Not Production GO. No invented Hub routes. `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Client | GET/PUT `/api/v1/integrations/connections/{id}/conflict-policy` |
| Hooks | `useHubConflictPolicy` / `usePutHubConflictPolicy` |
| Studio step | **Conflict** — rules JSON + authored/operational csv |
| Odoo honesty | connector_key `odoo` vs `fake`; test dispatches by tip router |
| Monitor | Unlinked cr_number badge list API honesty stub (no invent) |
| Tests | conflict-policy client Jest + Studio conflict step Jest |

## Non-goals

- Unlinked-record badge list API (BE residual)
- Live Odoo XML-RPC passwords in FE
- Owner mint / Production GO
