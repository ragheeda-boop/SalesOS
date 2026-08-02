# FE-S08-15 — Cmd palette Studio steps + tip field polish (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** Hub HTTP + FE-S09-06  
> **Honesty:** Not Production GO / RAG GO. No invented Hub HTTP / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Cmd palette | Deep-links for connect / test / conflict / disconnect (`?step=`) |
| Connection detail | Tip `created_at` / `updated_at` when present |
| Active mapping | Tip mapping `id` + `is_active` on status line |
| Inventory | Owner honesty banner through FE-S09-06 |

## Non-goals

- Unlinked cr_number badge list API (BE-blocked)
- STORY-09-07 incremental sync FE (wait for BE tip)
- Owner mint / Production GO / RAG GO
