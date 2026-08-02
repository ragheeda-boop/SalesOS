# Sprint 20 — 2027-04-26 → 2027-05-09

> **Phase:** 5 — AI Studio + Marketplace · **Prior:** [Sprint 19](Sprint-19.md) · **Next:** [Sprint 21](Sprint-21.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** AI Studio complete (Prompt Library, Policies, Memory MVP).

**Team note:** Release Manager becomes active this sprint per the roster plan, ramping up ahead of the Release Candidate/GA gates.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-12-01 (Prompt Library) | AI-Lead | P0 | Medium | Tenant CRUD + versioning + rollback |
| STORY-12-02 (AI Policies UI) | AI-Lead | P0 | Medium | Reuses existing `AI-GR-*` guardrails |
| STORY-12-03 (AI Memory MVP) | BE-Lead, AI-Lead | P0 | High (R-06) | Conversation-level only; adversarial cross-tenant isolation test passes |
| STORY-12-04 (per-plan model tier) | BE2 | P1 | Medium | **LANDED BE (Stream A):** Plan.entitlements `ai_model_tier` (Starter economy / Enterprise full) + `GET /api/v1/studio/ai-model-tiers`. Crumb [`PHASE1_STORY_12_04_AI_MODEL_TIERS_CRUMB.md`](../PHASE1_STORY_12_04_AI_MODEL_TIERS_CRUMB.md). `feature_ai_copilot` False. No new RLS. No Production GO. |
| FE-S12-04 (AI Model Tiers Studio UI) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** `/studio/ai-model-tiers` against tip GET catalog/defaults/resolve. Crumb [`PHASE1_FE_S12_04_AI_MODEL_TIERS_CRUMB.md`](../PHASE1_FE_S12_04_AI_MODEL_TIERS_CRUMB.md). No invent PUT. `feature_ai_copilot` False. No Production GO. |

**Expected Demo:** Tenant customizes a prompt, sees AI Memory retain conversation context within a session, adversarial test shown failing to leak across tenants.

**Technical Debt Created:** Cross-session long-term memory explicitly deferred (flagged in `PROGRAM_PLAN.md` EPIC-12), not silently dropped.
