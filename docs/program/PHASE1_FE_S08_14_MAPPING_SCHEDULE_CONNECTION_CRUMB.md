# FE-S08-14 — Mapping version + schedule name + connection GET (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub MappingCreate.version + ScheduleCreate.name + GET connection  
> **Honesty:** Not Production GO / RAG GO. No invented Hub routes.  
> Unlinked badge list + STORY-09-04 SupportTicket **not on tip** — not invented.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Map | Tip `MappingCreate.version` input (hydrates from active mapping) |
| Schedule | Optional tip `ScheduleCreate.name` |
| Connect | Tip GET `/connections/{id}` refresh via `useHubConnection` |
| Cmd | Palette deep-links `?step=map|monitor|schedule` |

## Non-goals

- Unlinked cr_number badge list API
- `helpdesk.ticket` / SupportTicket Studio (BE not on tip)
- Owner mint / Production GO / RAG GO
