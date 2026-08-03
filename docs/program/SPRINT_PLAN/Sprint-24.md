# Sprint 24 — 2027-06-21 → 2027-07-04

> **Phase:** 6 — Hardening, Scale, Compliance · **Prior:** [Sprint 23](Sprint-23.md) · **Next:** [Sprint 25](Sprint-25.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** DR drill + pentest + AI provider failover hardening.  
**Board hub:** [`PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md`](../PHASE1_BOARD_SPRINT_23_25_ORCHESTRATION_CRUMB.md)

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-14-03 (DR drill) | DevOps/SRE, BE-Lead | P0 | High | **LANDED BE (Stream A):** CI/non-prod backup/restore + PITR — RTO≤4h / RPO≤1h measured + practice postmortem via `/api/v1/dr/*`. Crumb [`PHASE1_STORY_14_03_DR_DRILL_CRUMB.md`](../PHASE1_STORY_14_03_DR_DRILL_CRUMB.md). No new RLS. Live prod restore / Production GO not claimed. |
| STORY-14-04 (penetration test) | Security (+ external firm) | P0 | Critical | **CLOSED (in-repo)** · **handoff READY** @ tip `fe84441` (brief v1.2, vendor, tracker v1.3). FE-SEC-02 **Open** (slice). FE-SEC-03 **Fixed** @ `d9f0eba`. Scrub **CLOSED**. Tip-live `https://salesos-production-96c0.up.railway.app`. AC **not validated** — firm **residual-external**. No Production GO / zero-criticals claim. |
| STORY-14-06 (AI provider failover) | AI-Lead | P0 | Medium | **LANDED BE (AI-Lead):** non-prod fake-provider failover harness via `/api/v1/chaos/ai-failover` (builds on 14-02). SLO ≤30s. Crumb [`PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md`](../PHASE1_STORY_14_06_AI_FAILOVER_CRUMB.md). Live LLM kill / Production GO not claimed. `feature_ai_copilot` False. |

**Expected Demo:** DR restore executed live (to a non-production target), timed against RTO/RPO.

**Technical Debt Created:** Any pentest finding below "critical" severity is triaged into a tracked backlog with an explicit fix-by date, reviewed at the Sprint 25 gate.
