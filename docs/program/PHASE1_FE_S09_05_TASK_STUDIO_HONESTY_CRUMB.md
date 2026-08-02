# FE-S09-05 — project.task / TaskCaseExtension Studio honesty (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-09-05 `8246024`  
> **Honesty:** Not Production GO / RAG GO. No invented Hub HTTP / unlinked badge list.  
> `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Constants | Mirror tip `DEFAULT_TASK_MAPPINGS` + case_type / classify fields |
| Map / Schedule | Model preset `project.task` against tip schedule+mapping HTTP |
| Honesty | TaskCaseExtension is VO on Task (no aggregate id); soft stages |
| Inventory | Owner Console lists FE-S09-05 |
| Tests | Task honesty unit + Studio preset Jest |

## Non-goals

- TaskCaseExtension list / ORM JSONB column UI
- Unlinked cr_number badge list API (BE-blocked)
- Owner mint / Production GO / RAG GO
