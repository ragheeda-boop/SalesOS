# FE-S08-12 — Monitor SyncRun model filter + tip field polish (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub SyncRun HTTP + FE-S09-01/02  
> **Honesty:** Not Production GO. No invented Hub routes / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Monitor | Client-side SyncRun **model** filter (tip `SyncRun.model`) |
| URL | `?runStatus=` / `?runModel=` when step=monitor |
| Row | tip `finished_at` + `scheduled_job_id` + copy run id |
| Honesty | Unlinked badge list still BE-blocked |

## Non-goals

- Unlinked cr_number badge list API
- Owner mint / Production GO
