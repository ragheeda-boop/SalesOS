# STORY-14-06 — AI provider failover harness (AI-Lead / non-prod)

> **Honesty:** Not Production GO. Live LLM provider kill not performed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> Builds on STORY-14-02 chaos harness.  
> `feature_ai_copilot` remains **False**. No live LLM.  
> Does **not** reopen STORY-12-03 / FE Memory.

## Landed

| Piece | Detail |
|-------|--------|
| Scenarios | `primary_outage`, `cascade_to_tertiary`, `chain_exhausted`, `slo_budget` |
| Providers | Fake `MemFakeProvider` chain (openai→anthropic→gemini) |
| SLO | ≤30s (`AI_FAILOVER_SLO_SECONDS`) — PRODUCTION_READINESS_CHECKLIST |
| HTTP | `/api/v1/chaos/ai-failover` — `/meta`, `/scenarios`, `/run/{scenario}`, `/run-all`, `/drills`, `/postmortems` |
| Tests | `tests/unit/test_story_14_06_ai_failover.py` |

## Acceptance

Failover engages within defined SLO (CI/non-prod fake chain) — covered.

## Non-goals

- Live staging/prod AI provider kill (Ops field residual)
- Enabling `feature_ai_copilot` / live LLM
- Production GO
- STORY-12-03 reopen / FE invent
- STORY-14-04 pentest
