# Sprint 25 — 2027-07-05 → 2027-07-18

> **Phase:** 6 — Hardening, Scale, Compliance · **Prior:** [Sprint 24](Sprint-24.md) · **Next:** [Sprint 26](Sprint-26.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)
> **Release gate:** Release Candidate (feature freeze, 2-week soak begins) — see [RELEASE_PLAN.md](../RELEASE_PLAN.md) §6

**Sprint Goal:** SOC2 evidence + LLM regression suite; Phase 6 exit. **Release Candidate gate.**

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-14-05 (SOC2 Type I evidence) | Security, Program Director | P1 | Medium | Audit logging/access review/change management evidence assembled (Type I audit itself is post-GA) |
| STORY-14-07 (LLM regression suite) | AI-Lead | P0 | Medium | **LANDED BE (AI-Lead):** non-prod golden LLM regression via `/api/v1/chaos/llm-regression` — baseline + injected regression detection + promote gate. Crumb [`PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`](../PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md). `feature_ai_copilot` False. No live LLM / Production GO. |
| Full regression suite (final) | QA-Lead | P0 | High | 100% pass against the RC candidate build |

**Expected Demo:** **Phase 6 Go/No-Go + Release Candidate declared.** Feature freeze begins; RC soak clock starts.

**Technical Debt Created:** None — this is the pay-down phase, not a debt-creation phase.
