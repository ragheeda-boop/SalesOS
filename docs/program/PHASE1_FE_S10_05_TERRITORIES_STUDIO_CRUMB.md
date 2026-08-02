# FE-S10-05 — Territory Rules Studio UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-10-05 `85156e4`+  
> **Honesty:** Not Production GO / RAG GO. Tip in-memory over CAP-017.  
> Live revenue territory DB / 141221 — **not claimed**.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | meta, list, upsert, delete, assign |
| UI | `/studio/territories` — CRUD + assign JSON probe |
| Nav / cmd | `nav.territories_studio`; `go.studio.territories` |

## Non-goals

- Postgres territory_rule_sets / new RLS
- Live CAP-017 revenue repository mutation
- Live 141221 / Production GO
