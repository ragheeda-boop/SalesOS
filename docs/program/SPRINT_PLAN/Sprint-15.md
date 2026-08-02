# Sprint 15 — 2027-02-15 → 2027-02-28

> **Phase:** 3 — Tenant Studio Core · **Prior:** [Sprint 14](Sprint-14.md) · **Next:** [Sprint 16](Sprint-16.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)
> **Release gate:** Internal Beta — see [RELEASE_PLAN.md](../RELEASE_PLAN.md) §3

**Sprint Goal:** Branding + Notifications; Phase 3 exit. **Internal Beta gate.**

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-10-07 (Branding & Languages) | FE1 | P0 | Low | **LANDED BE (Stream A):** logo/color/name/locales live per tenant (`GET/PUT /api/v1/studio/branding`). Crumb [`PHASE1_STORY_10_07_BRANDING_STUDIO_CRUMB.md`](../PHASE1_STORY_10_07_BRANDING_STUDIO_CRUMB.md). Unblocks FE-S10-07. No new RLS. No Production GO. |
| FE-S10-07 (Branding Studio UI) | FE-Lead | P0 | Low | **LANDED FE (Stream B):** `/studio/branding` against tip branding HTTP. Crumb [`PHASE1_FE_S10_07_BRANDING_STUDIO_CRUMB.md`](../PHASE1_FE_S10_07_BRANDING_STUDIO_CRUMB.md). URL string only — no CDN upload claim. No Production GO. |
| STORY-10-08 (Notification Rules) | BE1 | P1 | Low | **LANDED BE (Stream A):** tenant event→channel routing via RulesEngine `send_notification` (`/api/v1/studio/notification-rules`). Crumb [`PHASE1_STORY_10_08_NOTIFICATION_RULES_CRUMB.md`](../PHASE1_STORY_10_08_NOTIFICATION_RULES_CRUMB.md). No new RLS. No Production GO. |
| FE-S10-08 (Notification Rules Studio UI) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** `/studio/notifications` against tip notification-rules. Crumb [`PHASE1_FE_S10_08_NOTIFICATION_RULES_CRUMB.md`](../PHASE1_FE_S10_08_NOTIFICATION_RULES_CRUMB.md). No Postgres claim. No Production GO. |
| Multi-tenant concurrency test (5 synthetic tenants) | QA-Lead | P0 | Medium | Zero schema-collision incidents |

**Expected Demo:** **Phase 3 Go/No-Go + Internal Beta release** across ≥3 internally-provisioned tenant workspaces, each with distinct branding/custom fields/workflows, dogfooded by the full internal team for 2 weeks starting this sprint.

**Technical Debt Created:** None carried forward; Internal Beta findings become Sprint 16 backlog input if any surface.
