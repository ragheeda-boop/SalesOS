# Sprint 05 — 2026-09-28 → 2026-10-11

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 04](Sprint-04.md) · **Next:** [Sprint 06](Sprint-06.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Suspension/deletion lifecycle; Subscription state machine designed.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-04-03 (suspend/reactivate) | BE1 | P0 | Medium | **LANDED (Stream A `fd5af4d`):** write-guard middleware + API-key gateway block; Owner `/activate` restores. Suspended tenant read-only for writes at app + gateway. |
| STORY-04-04 (deletion + retention) | BE2 | P1 | Medium | **LANDED interim (Stream A `fd5af4d`):** soft-delete stamps `deletion_requested_at`; hard-delete honors `tenant_deletion_retention_days` unless `force_immediate`. Dedicated `deleted_at` column still follow-on. |
| STORY-05-01 (Subscription state machine, design+build) | BE-Lead | P0 | High (R-05) | **LANDED BE (Stream A):** pure SM + `subscriptions` Alembic `c3a9f12d4e80` + provision wire + Owner transition API + unit matrix; CPO artifact [`PHASE1_STORY_05_01_SUBSCRIPTION_SM_CRUMB.md`](../PHASE1_STORY_05_01_SUBSCRIPTION_SM_CRUMB.md). Migrate notes [`PHASE1_A_STORY_05_01_MIGRATE_NOTES.md`](../PHASE1_A_STORY_05_01_MIGRATE_NOTES.md). No Stripe / Production GO. |

**Expected Demo:** Full lifecycle demo: provision → suspend → reactivate → delete, on a synthetic test tenant.

**Technical Debt Created:** None.

*Team note: BE2 joins the team this sprint per the Phase 1 roster plan.*
