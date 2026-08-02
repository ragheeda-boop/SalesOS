# FE-S13-03 — Marketplace listings browse + certify UX (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-13-02 `d4a1a9b` (+ FE browse `ed24955`)  
> **Honesty:** Memory catalog + CAP-094 CI certify. Not CAP-036 stub.  
> No invented tenant `/install` HTTP. Live HubSpot/Odoo sync not claimed.  
> `TenantList.tsx` untouched. Not Production GO.

## Landed

| Piece | Detail |
|-------|--------|
| Client | GET list/meta/detail/certify/meta; POST seed/submit/certify |
| UI | `/marketplace/listings` — browse + Submit + Certify + report |
| Honesty | Trial install is pipeline-internal only |

## Non-goals

- Invented tenant install endpoint
- Full CAP-036 stub replacement as sole `/marketplace`
- FE-S11-07/08 invent
- Production GO / live network GO
