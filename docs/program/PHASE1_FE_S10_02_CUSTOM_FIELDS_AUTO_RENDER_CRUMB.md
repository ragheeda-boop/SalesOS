# FE-S10-02 — Custom field auto-render on entity pages (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-10-02 `c4ae2f6` (+ FE-S10-01 `4fcd145`)  
> **Honesty:** Not Production GO / RAG GO. Tip form-schema + values only.  
> `TenantList.tsx` untouched. No invented Postgres persistence.

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | `GET .../form-schema`, `POST .../values` |
| Component | `CustomFieldsAutoRender` — generic field map (zero per-field code) |
| Pages | Company detail + Opportunity detail + Studio preview |
| Honesty | `metadata.custom_fields` bag; POST projects only (no ORM write) |

## Non-goals

- Postgres / Alembic definition or value persistence
- Hardcoded per-field React components
- STORY-10-03 Workflow Builder
- Production GO / RAG GO
