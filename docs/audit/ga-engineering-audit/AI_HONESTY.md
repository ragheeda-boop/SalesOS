# AI Honesty Statement — SalesOS / AQLIYA (Wave 6–7 gate)

**Date:** 2026-07-22 (Phase 1 live reconciliation note: 2026-08-04)  
**Status:** Documentation + **runtime/UI gates** — **not** an AI GA claim  
**Classification:** AI surface is **not production-ready** for marketing as “AI-native GA”  
**Authority:** [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md) PROD-W6-001 / W6-002 / W6-003; audit **NO-GO** ([00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md))  
**Progress evidence:** [PROGRESS-WAVE6-7-AI-GATE.md](./PROGRESS-WAVE6-7-AI-GATE.md)

> **Principle:** AI assists. Humans decide. Evidence governs.  
> Do not ship release notes, sales decks, or PRC language that imply production AI agents/copilot while flags are off and stubs throw.  
> **Agree with audit:** Production GA remains **NO-GO**. Live Phase 1 evidence does **not** overturn that.

---

## 1. Product scope (honest)

| Claim | Reality (2026-07-22 audit + gate) |
|-------|-----------------------------------|
| AQLIYA multi-product GA | **No** — repo is SalesOS-first; AuditOS / DecisionOS / LocalContentOS are not shipped products in this codebase |
| SalesOS “AI-native OS” GA | **No** — see stubs + `feature_ai_copilot=False` + UI/API gates |
| Copilot production-ready | **No** — default flag off; product API **403** when False; GA nav/header panel **hidden** |
| Decision Engine FE package live | **No** — `@salesos/decision-platform` package still throws STUB on direct calls; **DecisionProvider** now prefers Decision Platform **HTTP API** |
| Gate G-4 “98% AI PASS” | **Superseded / overclaimed** relative to runtime stubs and flag defaults |

**Launch scope for any future PRC:** **SalesOS GA only** ≠ AQLIYA platform GA.

---

## 2. Feature flags (source of truth)

| Flag / key | Location | Default | GA guidance |
|------------|----------|---------|-------------|
| `feature_ai_copilot` | `salesos/backend/app/config.py` (`Settings`) | **`False`** | Keep False for GA unless evidence-validated |
| Admin seed `ai_copilot` | `salesos/backend/app/modules/admin/repositories.py` | **`False`** | Must not seed `enabled=True` while Settings is False |
| FE discovery | `GET /api/v1/copilot/status` | mirrors Settings | Always `ga_ready=false` in response |
| FE lab override | `NEXT_PUBLIC_FEATURE_AI_COPILOT=true` | unset | Lab only — still not a GA claim |

**Honesty rule:** Env override to enable copilot in a non-prod lab is fine; production templates and marketing must not present it as GA.

**Enforcement (Wave 6–7 gate):** When `feature_ai_copilot=False`, `POST /api/v1/copilot/query`, `search-companies`, and `feedback` return **403**. Status endpoint remains readable for FE gating. UI hides `/copilot` nav, header Bot button, and slide-out panel.

---

## 3. Stubbed / incomplete AI-related surfaces

| Surface | Path | Evidence | GA treatment |
|---------|------|----------|--------------|
| FE Decision package | `salesos/frontend/packages/platform/decision/index.ts` | Throws `STUB: … not implemented` on evaluate/explain/history/feedback | Do not import for product paths; **DecisionProvider** wired to `/api/v1/decision/*` |
| Agent tools placeholder | `salesos/frontend/packages/platform/agents/tools/index.ts` | `search_companies` returns empty placeholder | Not GA |
| Copilot UI | `/copilot`, header panel | Gated behind flag + Preview badge | Not GA while flag False |
| AI Prompt Registry | `/ai` | Preview badge + honesty copy | Experimental — not GA |
| Decision Center UI | `/decisions` | Uses Decision Center / Platform HTTP APIs | Operational surface — **not** the FE stub package; still not “AI-native GA” marketing |
| Missing agent/workflow/scheduler/execution/simulation runtimes | Historically referenced under `backend/runtime/*` | Capability hole | Do not claim orchestration GA |
| Intelligence agents package | `salesos/backend/intelligence/agents/` | Code exists; production proof **not validated** | Needs evidence before GO |
| G-4 AI validation doc | `docs/vnext/reports/gates/G04_AI_VALIDATION.md` | Claims PASS / 98% | **SUPERSEDED** for GA decisions |

Technical debt pointer: `salesos/memory/technical-debt.md` TD-S0-07 (Decision Engine stub).

---

## 4. What may be said honestly

Allowed:

- “SalesOS includes experimental / opt-in AI surfaces behind feature flags.”
- “Decision Center / RAG / providers exist as code; production readiness requires Wave 2–6 evidence.”
- “Post-GA roadmap: agent runtime, workflow orchestration, production copilot.”

Forbidden until a new PRC with evidence:

- “AI-native GA”
- “98% AI coverage production-ready”
- “Autonomous agents in production”
- Equating SalesOS GA with full AQLIYA multi-product intelligence platform

---

## 5. Acceptance (Wave 6–7)

- [x] Stubbed surfaces documented here  
- [x] `feature_ai_copilot` default False documented and commented in config  
- [x] In-memory admin seed for `ai_copilot` aligned to False  
- [x] FE decision package marked STUB in code  
- [x] Copilot product API gated when flag False  
- [x] Copilot GA nav / header panel hidden when flag False  
- [x] `/copilot` + `/ai` honest Preview badges  
- [x] DecisionProvider prefers Decision Platform HTTP API (not stub throws)  
- [ ] Product/CTO signed sentence in PRC: **SalesOS GA only; AI not marketed as GA** — **يحتاج تحقق** (human sign-off)

---

---

## 6. Phase 6 harness residuals (Sprint 24–25 — not GA AI)

Non-prod / CI-only surfaces landed for readiness evidence. **Do not** treat as live LLM or Production GO:

| Story | Surface | Honesty |
|-------|---------|---------|
| STORY-14-06 | `/api/v1/chaos/ai-failover` | Fake providers; `feature_ai_copilot=False`; no live kill |
| STORY-14-07 | `/api/v1/chaos/llm-regression` | Golden fixtures + similarity; detects injected regression; no live LLM |

Program crumbs: `docs/program/PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md`, `docs/program/PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`.  
SOC2 Type I (STORY-14-05) evidence packs must index this file + flag/stub reality — not invent AI GA.

---

## 7. Phase 1 live evidence vs audit NO-GO (do not invent GO)

Audit scoreboard: **Production GA = NO-GO**. AI-Lead **agrees**. The following live Phase 1 facts must **not** be marketed as overturning that:

| Live fact | Honest label | Forbidden overclaim |
|-----------|--------------|---------------------|
| Optional STORY-14-01 field soak **r3 PASS** (wall 2h + `all_iters_ok`) | Optional load evidence only — see `PHASE1_STORY_14_01_LOAD_SLO_CRUMB.md` / board hub | **Not** Companion acceptance · **not** GA/staging soak closure · **not** Production GO |
| Evidence #1 tip HOLD (`100cce8`) while abs tip / crypto fix (`bee3276`) settles; prior `6a21ff7` tip-line RED | Tip-line **settling / HOLD** — cite Watchdog | **Not** whole-pipeline green · **not** CI GREEN invented |
| `feature_ai_copilot=False` + FE Decision package **STUB** | Standing AI honesty | **Not** live AI / AI-native GA |
| 14-06 / 14-07 chaos harnesses | CI/non-prod fixtures only | **Not** live LLM / live provider kill |
| External blockers (unsigned GO/RPO, OAuth, firm pentest) | **residual-external** / open | **Not** closed by AI crumbs or soak r3 |

Board language for soak: use **“optional field soak r3 PASS (not Companion / not Production GO)”** — never “soak PASS → GA ready.”

*This file does not grant Production GO.*
