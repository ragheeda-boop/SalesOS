# Sprint 25 — 2027-07-05 → 2027-07-18

> **Phase:** 6 — Hardening, Scale, Compliance · **Prior:** [Sprint 24](Sprint-24.md) · **Next:** [Sprint 26](Sprint-26.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)
> **Release gate:** Release Candidate (feature freeze, 2-week soak begins) — see [RELEASE_PLAN.md](../RELEASE_PLAN.md) §6

**Sprint Goal:** SOC2 evidence + LLM regression suite; Phase 6 exit. **Release Candidate gate.**  
**Board hub:** [`PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md`](../PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md) · RC soak clock ≠ claimed until Board declares.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-14-05 (SOC2 Type I evidence) | Security, Program Director | P1 | Medium | **CLOSED (evidence pack)** · **light validated** @ tip `11d0d3f`: [`docs/compliance/soc2-type-i/`](../../compliance/soc2-type-i/README.md). Crumb [`PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md`](../PHASE1_STORY_14_05_SOC2_EVIDENCE_CRUMB.md). PD **templates LANDED** (`06`–`09`, unsigned) · signatures / screenshots / live 90d export **still residual**. Type I **audit** = **post-GA residual-external** (A5) — **NOT certified**. No Production GO. Stage 6 SKIPPED. |
| STORY-14-07 (LLM regression suite) | AI-Lead | P0 | Medium | **LANDED BE (AI-Lead):** non-prod golden LLM regression via `/api/v1/chaos/llm-regression` — baseline + injected regression detection + promote gate. Crumb [`PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md`](../PHASE1_STORY_14_07_LLM_REGRESSION_CRUMB.md). `feature_ai_copilot` False. No live LLM / Production GO. |
| Full regression suite (final) | QA-Lead | P0 | High | **CANDIDATE RC RE-PINNED / NOT VALIDATED:** candidate `RC_SHA`=`fe84441` (`fe844410415a284382671d406bef3e4c2e62dce8`) — Evidence #1 tip-line green; prior candidate `26f2ab5` superseded. Tip-line ≠ suite pass. All suite rows **NOT VALIDATED**. Crumb [`PHASE1_SPRINT25_QA_REGRESSION_CRUMB.md`](../PHASE1_SPRINT25_QA_REGRESSION_CRUMB.md). Board RC declare / soak **pending**. Plan AC “100% pass vs RC” **not claimed**. No full suite run without approval. No Production GO. Stage 6 SKIPPED. |

**Expected Demo:** **Phase 6 Go/No-Go + Release Candidate declared.** Feature freeze begins; RC soak clock starts.

**Technical Debt Created:** None — this is the pay-down phase, not a debt-creation phase.
