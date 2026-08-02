# Sprint 06 — 2026-10-12 → 2026-10-25

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 05](Sprint-05.md) · **Next:** [Sprint 07](Sprint-07.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Stripe integration live in sandbox.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-05-02 (Stripe integration) | BE-Lead, BE2 | P0 | High (R-05) | **IN PROGRESS (Stream A):** webhook+checkout `f7fffb8`; portal + `platform_billing_invoices` + plan Stripe Price catalog Alembic `f6d2a45b7c03`. Crumbs [`PHASE1_STORY_05_02_STRIPE_CRUMB.md`](../PHASE1_STORY_05_02_STRIPE_CRUMB.md), [`PHASE1_STORY_05_02B_PORTAL_INVOICES_CATALOG_CRUMB.md`](../PHASE1_STORY_05_02B_PORTAL_INVOICES_CATALOG_CRUMB.md). Sandbox soak residual. No Production GO. |
| STORY-05-03 (usage metering) | BE1 | P0 | Medium | **IN PROGRESS (Stream A):** `usage_meter_events` + `usage_meters` Alembic `a7e3b56c8d04`; Owner record/rollup/list APIs. Crumb [`PHASE1_STORY_05_03_USAGE_METER_CRUMB.md`](../PHASE1_STORY_05_03_USAGE_METER_CRUMB.md). No Production GO. |

**Expected Demo:** Full trial→active subscription cycle against Stripe sandbox, shown live including a simulated webhook replay proving idempotency.

**Technical Debt Created:** Usage metering granularity is hourly rollup, not real-time — flagged as acceptable for GA, revisit if a pricing tier ever needs real-time quota enforcement.
