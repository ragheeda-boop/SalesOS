# Sprint 06 — 2026-10-12 → 2026-10-25

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 05](Sprint-05.md) · **Next:** [Sprint 07](Sprint-07.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Stripe integration live in sandbox.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-05-02 (Stripe integration) | BE-Lead, BE2 | P0 | High (R-05) | **LANDED BE (Stream A):** webhook+checkout+portal+invoices+catalog; readiness `GET /billing/stripe/status` (05-02c). Crumbs [`PHASE1_STORY_05_02_STRIPE_CRUMB.md`](../PHASE1_STORY_05_02_STRIPE_CRUMB.md), [`PHASE1_STORY_05_02B_PORTAL_INVOICES_CATALOG_CRUMB.md`](../PHASE1_STORY_05_02B_PORTAL_INVOICES_CATALOG_CRUMB.md), [`PHASE1_STORY_05_02C_SANDBOX_READINESS_CRUMB.md`](../PHASE1_STORY_05_02C_SANDBOX_READINESS_CRUMB.md). **Ops residual:** live sandbox soak needs real env keys. No Production GO. |
| STORY-05-03 (usage metering) | BE1 | P0 | Medium | **LANDED BE (Stream A):** events + hourly meters Alembic `a7e3b56c8d04`. Crumb [`PHASE1_STORY_05_03_USAGE_METER_CRUMB.md`](../PHASE1_STORY_05_03_USAGE_METER_CRUMB.md). No Production GO. |

**Expected Demo:** Full trial→active subscription cycle against Stripe sandbox, shown live including a simulated webhook replay proving idempotency.

**Technical Debt Created:** Usage metering granularity is hourly rollup, not real-time — flagged as acceptable for GA, revisit if a pricing tier ever needs real-time quota enforcement.
