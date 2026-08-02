# FE-S08-11 — Studio URL deep-link + schedule/monitor polish (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub HTTP + FE-S08-10  
> **Honesty:** Not Production GO. No invented Hub routes / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| URL | `?step=` + `?connection=` sync (shareable Studio deep-link) |
| Owner shell | Step links → `/integrations?step=<id>` |
| Schedule | Persist tip `HubScheduleResult` (`job_id`, `next_run_at`) |
| Monitor | Client status filter on tip SyncRun rows + refresh |
| Copy | Connection id copy from tip connection detail |
| Helpers | `studioUrl.ts` + Jest |

## Non-goals

- Unlinked cr_number badge list API (BE-blocked)
- Owner mint / Production GO
