# STORY-14-07 — LLM regression suite (AI-Lead / non-prod)

> **Honesty:** Not Production GO. No live LLM calls.  
> **POLICY_COUNT unchanged** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` remains **False**.  
> FE Decision package remains **STUB** (not live GA AI) — see [`AI_HONESTY.md`](../audit/ga-engineering-audit/AI_HONESTY.md).  
> Does **not** reopen STORY-12-03 or STORY-14-06.

## Landed

| Piece | Detail |
|-------|--------|
| Golden set | 3 fixture cases (ICP / outreach / AI honesty) |
| Scoring | Token Jaccard + required keywords; threshold 0.70 |
| Modes | `baseline`, `injected_regression`, `promote_gate` |
| HTTP | `/api/v1/chaos/llm-regression` — `/meta`, `/modes`, `/run/{mode}`, `/run-all`, `/drills`, `/postmortems` |
| Tests | `tests/unit/test_story_14_07_llm_regression.py` |
| Land commit | `3a25c76` |
| Tip-line settle | Absolute tip ancestor chain through `594deaa`; CI [30759940969](https://github.com/ragheeda-boop/SalesOS/actions/runs/30759940969) Stages 1–5 **SUCCESS** |

## Acceptance

- Baseline established (all golden cases pass under fixture "good" model).
- Deliberately injected quality regression is detected (`injected_regression` → `regression_detected=true`).
- Promote gate blocks when regression present.

## Security / Evidence residual (14-05 support)

| Item | Label |
|------|-------|
| Suite proves | Non-prod golden quality gate + injected-regression detection in CI |
| Suite does **not** prove | Live provider model watch, production LLM quality, SOC2 Type I audit |
| Cite with | `feature_ai_copilot=False` + Decision **STUB** + [`AI_HONESTY.md`](../audit/ga-engineering-audit/AI_HONESTY.md) §6–7 |
| Checklist row | `PRODUCTION_READINESS_CHECKLIST.md` — LLM regression suite (AI Lead) — **CI harness landed**; live continuous watch = Ops residual |
| Audit vs live | Production GA **NO-GO** (agree). Optional 14-01 soak r3 PASS ≠ Companion / ≠ GA soak. Tip-line HOLD/`bee3276` settling ≠ whole-pipeline green |

Prior land CI [30759755215](https://github.com/ragheeda-boop/SalesOS/actions/runs/30759755215): Stages 1–3 green; overall FAILURE was Stage-4 **Upload integration coverage** FinalizeArtifact 404 (**infra flake**, tests OK) — DevOps/Watchdog; **do not product-reopen 14-07**.

## Non-goals

- Live provider model update watch (Ops residual)
- Enabling `feature_ai_copilot` / live LLM
- Production GO
- STORY-12-03 / STORY-14-06 reopen
- FE invent
- Claiming SOC2 Type I audit complete
