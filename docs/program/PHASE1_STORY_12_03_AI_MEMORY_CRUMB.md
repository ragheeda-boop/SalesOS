# STORY-12-03 — AI Memory MVP (AI-Lead + Backend / CAP-063)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Conversation-level only (DEC-007 — cross-session long-term deferred).  
> **Opt-in** per tenant (default disabled).  
> Adversarial cross-tenant + provider-cache isolation covered in CI.  
> Live LLM / RAG GO — **not claimed**. `feature_ai_copilot` remains **False**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `ConversationMemory` / `MemoryTurn` / `TenantMemorySettings` |
| Engine | Tenant-bound `provider_cache_key` + adversarial probe |
| Store | In-memory opt-in settings, turns, delete, provider-cache map |
| HTTP | `/api/v1/studio/ai-memory` — `/meta`, `/settings`, conversations CRUD turns, `/adversarial/probe` |
| Tests | Opt-in gate, round-trip, max_turns trim, cross-tenant DB + cache isolation, flag False |

## Acceptance

Conversation-level memory with adversarial cross-tenant isolation (incl. provider-cache) — covered in CI.

## Unblocks

- FE Studio AI Memory surface (later — not invented here)

## Non-goals

- Cross-session long-term memory
- Live LLM / enabling `feature_ai_copilot`
- RAG GO / Production GO
- FE invent
- Postgres persistence / Alembic
