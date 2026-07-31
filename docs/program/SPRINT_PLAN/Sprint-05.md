# Sprint 05 — 2026-09-28 → 2026-10-11

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 04](Sprint-04.md) · **Next:** [Sprint 06](Sprint-06.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Suspension/deletion lifecycle; Subscription state machine designed.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-04-03 (suspend/reactivate) | BE1 | P0 | Medium | Suspended tenant is read-only at both app and gateway layer |
| STORY-04-04 (deletion + retention) | BE2 | P1 | Medium | Deletion honors a configurable retention window before hard delete |
| STORY-05-01 (Subscription state machine, design+build) | BE-Lead | P0 | High (R-05) | State machine diagram reviewed by CPO; all transitions unit-tested |

**Expected Demo:** Full lifecycle demo: provision → suspend → reactivate → delete, on a synthetic test tenant.

**Technical Debt Created:** None.

*Team note: BE2 joins the team this sprint per the Phase 1 roster plan.*
