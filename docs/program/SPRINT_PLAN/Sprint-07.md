# Sprint 07 — 2026-10-26 → 2026-11-08

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 06](Sprint-06.md) · **Next:** [Sprint 08](Sprint-08.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)
> **Release gate:** Alpha (internal-only) — see [RELEASE_PLAN.md](../RELEASE_PLAN.md) §1

**Sprint Goal:** Dunning + proration; Entitlement Engine v1; Owner Console MVP. **Alpha gate.**

**Team note:** AI-Lead joins the team this sprint per the Phase 2 roster plan (ramping up ahead of Sprint 11's InteractionNote/PII work).

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-05-04 (dunning) | BE2 | P0 | High (R-05) | **LANDED BE (Stream A):** dunning_cases Alembic 8f4c67d9e15; grace (dunning_grace_days) → evaluate auto-suspend; webhook open/clear. Crumb [PHASE1_STORY_05_04_DUNNING_CRUMB.md](../PHASE1_STORY_05_04_DUNNING_CRUMB.md). No Production GO. |
| STORY-05-05 (proration) | BE1 | P1 | Medium | **LANDED BE (Stream A):** quote/apply + deferred downgrade cols Alembic c9e5d78a0f26; Owner /billing/plan-change/*. Crumb [PHASE1_STORY_05_05_PRORATION_CRUMB.md](../PHASE1_STORY_05_05_PRORATION_CRUMB.md). No Production GO. |
| STORY-06-01 (Plan.entitlements schema) | BE-Lead | P0 | Medium | **LANDED BE (Stream A):** dmin_plans.entitlements JSONB Alembic d0f6e89b1a37; v1 schema + tier defaults from commercial packaging. Crumb [PHASE1_STORY_06_01_PLAN_ENTITLEMENTS_CRUMB.md](../PHASE1_STORY_06_01_PLAN_ENTITLEMENTS_CRUMB.md). No Production GO. |
| STORY-06-02 (entitlement middleware) | BE-Lead | P0 | Medium | **LANDED BE (Stream A):** path→DOM gates (011/012/023/021) + EntitlementEnforcementMiddleware; flag entitlement_enforcement_enabled. Crumb [PHASE1_STORY_06_02_ENTITLEMENT_MIDDLEWARE_CRUMB.md](../PHASE1_STORY_06_02_ENTITLEMENT_MIDDLEWARE_CRUMB.md). No Production GO. |
| STORY-07-01/02/03 (Owner Console MVP) | FE-Lead, FE1 | P1 | Low | **CLOSED FE MVP (Stream B / FE-S07-07):** `/admin` shell + tenants/billing/flags/config/audit + audience/host/page honesty. Crumb [PHASE1_STORY_07_OWNER_CONSOLE_CRUMB.md](../PHASE1_STORY_07_OWNER_CONSOLE_CRUMB.md). Residuals: DEC-093 mint, deferred refund/override writes. No Production GO. |

**Expected Demo:** **Phase 1 Go/No-Go + Alpha release.** Full commercial lifecycle demo end-to-end: provision tenant → subscribe → use a gated feature → downgrade → see entitlement change take effect → Owner Console shows accurate status throughout.

**Technical Debt Created:** Owner Console is read-only — write actions (manual suspend override, refund) deferred to a later increment, explicitly tracked, not silently dropped.
