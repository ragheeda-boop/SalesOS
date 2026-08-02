# STORY-12-01 — Prompt Library (AI-Lead / CAP-089)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> In-memory tenant Prompt Library extending CAP-023 shape.  
> Live LLM execution / RAG GO / Marketplace prompt-pack install — **not claimed**.  
> `feature_ai_copilot` default remains **False**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `PromptLibraryEntry` / `PromptVersionRecord` |
| Store | `MemPromptLibraryStore` — create, version, rollback, delete |
| HTTP | `POST/GET/PATCH/DELETE /api/v1/studio/prompt-library` + `/{id}/versions` + `/{id}/rollback` + `/meta` |
| Tests | Version+rollback, duplicate key, tenant isolation, flag False |

## Acceptance

Tenant CRUD + versioning + rollback — covered in CI (in-memory).

## Unblocks

- FE Prompt Library Studio surface (Sprint-20 FE follow-on)
- STORY-12-02 AI Policies (next AI-Lead)

## Parked

- STORY-12-03 AI Memory MVP — **PARK** until BE pair

## Non-goals

- Live LLM / enabling `feature_ai_copilot`
- RAG GO / Production GO
- Postgres persistence / Alembic
- Marketplace prompt-pack install
