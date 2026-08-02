# FE-S09-08 — Unlinked badge Monitor list (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-09-08 `43d52c9`  
> **Honesty:** Not Production GO / RAG GO. Tip Hub HTTP only.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Types + client | Tip `GET .../unlinked-badges` → `HubUnlinkedBadgeList` |
| Hook | `useHubUnlinkedBadges(connectionId)` |
| Monitor | List external_id / status / cr_number / message / sync_run_id |
| Honesty | Replaces BE-blocked copy with tip list honesty |
| Tests | Client unit + Studio Monitor Jest |

## Non-goals

- Dedicated badge ORM table UI
- SyncRun cursor_before/after HTTP (still not on SyncRunResponse)
- Sprint-12 custom objects
- Owner mint / Production GO / RAG GO
