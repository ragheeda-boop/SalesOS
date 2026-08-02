# FE-S08-13 — Schedule job_type + conflict tip defaults + connection polish (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub ScheduleCreate + ConflictResolutionPolicy.default + ConnectionResponse  
> **Honesty:** Not Production GO / RAG GO. No invented Hub routes / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Schedule | Tip `job_type` select (`interval` / `cron` / `one_time`) + result display |
| Conflict | Load tip `ConflictResolutionPolicy.default()` rules/fields |
| Connect | Client active/inactive filter; show tip `connection_config` |
| Note honesty | Labeled-name scrub tighten note (tip 915f9cd) |

## Non-goals

- Unlinked cr_number badge list API
- Owner mint / Production GO / RAG GO
