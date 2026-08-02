# Sprint 14 — 2027-02-01 → 2027-02-14

> **Phase:** 3 — Tenant Studio Core · **Prior:** [Sprint 13](Sprint-13.md) · **Next:** [Sprint 15](Sprint-15.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Scoring Rules + Territories + Permissions Studio.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-10-04 (Scoring Rules Studio) | BE2 | P0 | Medium | **LANDED BE (Stream A):** tenant rule overrides platform default; fail-safe fallback on rule error (`GET/POST /api/v1/studio/scoring-rules` + `…/evaluate`). Crumb [`PHASE1_STORY_10_04_SCORING_RULES_STUDIO_CRUMB.md`](../PHASE1_STORY_10_04_SCORING_RULES_STUDIO_CRUMB.md). No new RLS. No Production GO. |
| FE-S10-04 (Scoring Rules Studio UI) | FE-Lead | P0 | Low | **LANDED FE (Stream B):** `/studio/scoring` against tip scoring-rules + evaluate. Crumb [`PHASE1_FE_S10_04_SCORING_RULES_STUDIO_CRUMB.md`](../PHASE1_FE_S10_04_SCORING_RULES_STUDIO_CRUMB.md). No Postgres claim. No Production GO. |
| STORY-10-05 (Territory config UI) | FE2 | P1 | Low | **BE READY (Stream A):** tip `/api/v1/studio/territories` (+ meta/assign). Crumb [`PHASE1_STORY_10_05_TERRITORIES_STUDIO_CRUMB.md`](../PHASE1_STORY_10_05_TERRITORIES_STUDIO_CRUMB.md). Unblocks FE-S10-05. In-memory; POLICY_COUNT 71. No Production GO. |
| FE-S10-05 (Territory Rules Studio UI) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** `/studio/territories` against tip territories HTTP. Crumb [`PHASE1_FE_S10_05_TERRITORIES_STUDIO_CRUMB.md`](../PHASE1_FE_S10_05_TERRITORIES_STUDIO_CRUMB.md). Live revenue DB / 141221 not claimed. No Production GO. |
| STORY-10-06 (Permissions UI) | BE-Lead | P0 | Medium | **LANDED BE (Stream A):** tenant-custom role capped at Plan.entitlements ceiling; privilege-escalation suite (`/api/v1/studio/permissions`). Crumb [`PHASE1_STORY_10_06_PERMISSIONS_STUDIO_CRUMB.md`](../PHASE1_STORY_10_06_PERMISSIONS_STUDIO_CRUMB.md). No new RLS. No Production GO. |
| FE-S10-06 (Permissions Studio UI) | FE-Lead | P0 | Low | **LANDED FE (Stream B):** `/studio/permissions` against tip catalog/ceiling/check/roles. Crumb [`PHASE1_FE_S10_06_PERMISSIONS_STUDIO_CRUMB.md`](../PHASE1_FE_S10_06_PERMISSIONS_STUDIO_CRUMB.md). No Postgres claim. No Production GO. |

**Expected Demo:** Tenant admin creates a custom scoring rule and a custom role, both take effect immediately without an engineering ticket.

**Technical Debt Created:** None.
