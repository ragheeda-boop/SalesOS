# STORY-12-03 — AI Memory MVP (AI-Lead + Backend / CAP-063)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Conversation-level only (DEC-007 — cross-session long-term deferred).  
> **Opt-in** per tenant (default disabled).  
> Adversarial cross-tenant + provider-cache isolation covered in CI.  
> Encryption: tenant-bound fixture HMAC envelope (not KMS).  
> Live LLM / RAG GO — **not claimed**. `feature_ai_copilot` remains **False**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `ConversationMemory` / `MemoryTurn` / `TenantMemorySettings` |
| Engine | Tenant-bound `provider_cache_key` + adversarial probe |
| Crypto | `fixture-hmac-sha256-v1` tenant-bound at-rest envelope |
| Store | Opt-in settings, encrypted turns, retention purge, delete, provider-cache map |
| HTTP | `/api/v1/studio/ai-memory` — `/meta`, `/settings`, conversations turns CRUD, `/adversarial/probe` |
| Tests | Opt-in, round-trip, trim, encryption boundary, retention purge, cross-tenant DB + cache, flag False |

## Acceptance

Conversation-level memory with adversarial cross-tenant isolation (incl. provider-cache) — covered in CI.

## Unblocks

- FE Studio AI Memory surface (later — not invented here)

## Non-goals

- Cross-session long-term memory
- Live LLM / enabling `feature_ai_copilot`
- RAG GO / Production GO
- FE invent
- Postgres persistence / Alembic / new FORCE RLS
