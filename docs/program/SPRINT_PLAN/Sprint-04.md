# Sprint 04 — 2026-09-14 → 2026-09-27

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 03](Sprint-03.md) · **Next:** [Sprint 05](Sprint-05.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** `Tenant` object extended; provisioning workflow skeleton live.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-04-01 (Tenant extension) | BE-Lead | P0 | Low | Migration applied; `plan_id`/`region`/`data_residency`/`provisioning_status`/`trial_ends_at` present |
| STORY-04-02 (provisioning workflow) | BE1 | P0 | Medium | Idempotent provisioning job creates a tenant + seeds default Studio config + assigns first admin |
| STORY-02-03 (JWT audience split, consume) | BE2 | P1 | Medium | Owner-audience token type exists (unused by any endpoint yet) |

**Expected Demo:** Provision a brand-new test tenant end-to-end via a script (no UI yet), show it isolated from Muhide's tenant in the RLS test suite.

**Technical Debt Created:** Default Studio config templates are hardcoded per plan tier (not yet Studio-editable) — acceptable, since Tenant Studio itself is Phase 3.
