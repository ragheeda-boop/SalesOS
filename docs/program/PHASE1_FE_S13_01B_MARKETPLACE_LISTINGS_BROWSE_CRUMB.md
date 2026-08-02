# FE-S13-01b — Marketplace listings browse (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-13-01 @ tip parent `d8efdf7` (tip at land may include STORY-13-02 BE; FE still browse-only)  
> **Honesty:** Memory catalog only. Not CAP-036 plugin stub. Not Production GO.  
> No install/certify UI (STANDBY until STORY-13-02). `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | GET list/meta/detail + POST seed-first-party |
| UI | `/marketplace/listings` — read-only browse + seed |
| Separation | CAP-036 stub remains at `/marketplace` with honesty link to tip listings |
| Nav / cmd | `nav.marketplace_listings`; `go.marketplace.listings` |

## Non-goals

- Install / certify UI (wait 13-02)
- Full STORY-13-03 supersede of CAP-036 stub
- FE-S11-07/08 invent
- Production GO
