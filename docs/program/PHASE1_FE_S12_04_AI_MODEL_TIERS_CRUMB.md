# FE-S12-04 — AI Model Tiers Studio UI (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Tip base:** STORY-12-04 `c8dedfc`  
> **Honesty:** Not Production GO / RAG GO. Tip GET-only.  
> `feature_ai_copilot` remains **False** — not enabled by this UI.  
> No invented PUT/write. `TenantList.tsx` untouched.

## Landed

| Piece | Detail |
|-------|--------|
| Client/hooks | catalog, defaults(`plan_tier`), tenant resolve(`requested_tier`) |
| UI | `/studio/ai-model-tiers` — read-only catalog + defaults + resolve |
| Nav / cmd | `nav.ai_model_tiers`; `go.studio.ai-model-tiers` |

## Non-goals

- PUT/write for `ai_model_tier`
- Enabling `feature_ai_copilot` / live LLM
- FE-S11-07/08 invent
- Production GO
