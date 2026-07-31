# Sprint 06 — 2026-10-12 → 2026-10-25

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 05](Sprint-05.md) · **Next:** [Sprint 07](Sprint-07.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Stripe integration live in sandbox.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-05-02 (Stripe integration) | BE-Lead, BE2 | P0 | High (R-05) | Checkout, webhook handling (idempotent), invoice sync all working in Stripe sandbox |
| STORY-05-03 (usage metering) | BE1 | P0 | Medium | `UsageMeter` records seats/tokens/syncs/storage via hourly rollup job |

**Expected Demo:** Full trial→active subscription cycle against Stripe sandbox, shown live including a simulated webhook replay proving idempotency.

**Technical Debt Created:** Usage metering granularity is hourly rollup, not real-time — flagged as acceptable for GA, revisit if a pricing tier ever needs real-time quota enforcement.
