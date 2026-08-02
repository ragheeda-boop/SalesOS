# FE-S11-10 — Second connector certify UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-11-10 `3d4d122`+  
> **Honesty:** Not Production GO / RAG GO. Tip CI HubSpot adapter only.  
> Live HubSpot network / production pilot sync — **not claimed**.  
> `TenantList.tsx` untouched. FE-S10-05 territories LANDED (see PHASE1_FE_S10_05_TERRITORIES_STUDIO_CRUMB.md).

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | `GET .../certify/meta`, `POST .../certify/{key}` |
| UI | `/integrations` — SecondConnectorCertPanel (hubspot default) |
| Studio | Tip connect keys mention `hubspot` |

## Non-goals

- Live HubSpot OAuth / CRM sync
- Claiming R-02 fully closed (pilot soak residual OPEN)
- Territory Studio (STORY-10-05)
- Production GO / RAG GO
