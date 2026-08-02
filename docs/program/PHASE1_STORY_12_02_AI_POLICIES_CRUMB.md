# STORY-12-02 — AI Policies (AI-Lead / CAP-091)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Reuses existing `AI-GR-*` primitives in `intelligence.guardrails` — not reinvented.  
> Live LLM / RAG GO — **not claimed**. `feature_ai_copilot` remains **False**.

## Landed

| Piece | Detail |
|-------|--------|
| Catalog | AI-GR-001..006 toggles + data-class → max model tier rules |
| Engine | Evaluate via sanitize/PII scrub + harmful-input detect + tier ceiling |
| HTTP | `POST/GET/DELETE /api/v1/studio/ai-policies` + `/evaluate` + `/meta` |
| Tests | PII ceiling, public allow, jailbreak block, tenant isolation, flag False |

## Acceptance

AI Policies UI backend: data-class-to-model-tier rules extending existing AI-GR-* — covered in CI.

## Parked

- STORY-12-03 AI Memory MVP — **PARK** until BE pair

## Non-goals

- Live LLM / enabling `feature_ai_copilot`
- RAG GO / Production GO
- Reinventing guardrail implementations
- AI Memory (12-03)
