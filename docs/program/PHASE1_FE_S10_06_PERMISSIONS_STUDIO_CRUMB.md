# FE-S10-06 — Permissions Studio UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-10-06 `98d9532` / tip `2d26cae`+  
> **Honesty:** Not Production GO / RAG GO. Tip in-memory custom roles only.  
> `TenantList.tsx` untouched. Does not mutate Owner `/admin/roles`.

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | catalog, ceiling GET/PUT, check, roles list/upsert |
| UI | `/studio/permissions` — ceiling, catalog checkboxes, roles, check |
| Honesty | Plan.entitlements ceiling; privilege escalation 403; process-local store |

## Non-goals

- Postgres role persistence / new RLS
- Owner Admin `/admin/roles` mutation
- Territory config (STORY-10-05 — still BE-blocked)
- Production GO / RAG GO
