# STORY-14-07 — LLM regression suite (AI-Lead / non-prod)

> **Honesty:** Not Production GO. No live LLM calls.  
> **POLICY_COUNT unchanged** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**.  
> Does **not** reopen STORY-12-03 or STORY-14-06.

## Landed

| Piece | Detail |
|-------|--------|
| Golden set | 3 fixture cases (ICP / outreach / AI honesty) |
| Scoring | Token Jaccard + required keywords; threshold 0.70 |
| Modes | `baseline`, `injected_regression`, `promote_gate` |
| HTTP | `/api/v1/chaos/llm-regression` — `/meta`, `/modes`, `/run/{mode}`, `/run-all`, `/drills`, `/postmortems` |
| Tests | `tests/unit/test_story_14_07_llm_regression.py` |

## Acceptance

- Baseline established (all golden cases pass under fixture "good" model).
- Deliberately injected quality regression is detected (`injected_regression` → `regression_detected=true`).
- Promote gate blocks when regression present.

## Non-goals

- Live provider model update watch (Ops residual)
- Enabling `feature_ai_copilot` / live LLM
- Production GO
- STORY-12-03 / STORY-14-06 reopen
- FE invent
