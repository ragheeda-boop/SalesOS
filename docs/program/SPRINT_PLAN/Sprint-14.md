# Sprint 14 — 2027-02-01 → 2027-02-14

> **Phase:** 3 — Tenant Studio Core · **Prior:** [Sprint 13](Sprint-13.md) · **Next:** [Sprint 15](Sprint-15.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Scoring Rules + Territories + Permissions Studio.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-10-04 (Scoring Rules Studio) | BE2 | P0 | Medium | **LANDED BE (Stream A):** tenant rule overrides platform default; fail-safe fallback on rule error (`GET/POST /api/v1/studio/scoring-rules` + `…/evaluate`). Crumb [`PHASE1_STORY_10_04_SCORING_RULES_STUDIO_CRUMB.md`](../PHASE1_STORY_10_04_SCORING_RULES_STUDIO_CRUMB.md). No new RLS. No Production GO. |
| STORY-10-05 (Territory config UI) | FE2 | P1 | Low | Tenant-defined territory rules over existing `CAP-017` |
| STORY-10-06 (Permissions UI) | BE-Lead | P0 | Medium | Tenant-custom role capped at plan entitlement ceiling; privilege-escalation test passes |

**Expected Demo:** Tenant admin creates a custom scoring rule and a custom role, both take effect immediately without an engineering ticket.

**Technical Debt Created:** None.
