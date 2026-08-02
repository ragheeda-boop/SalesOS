# Sprint 21 — 2027-05-10 → 2027-05-23

> **Phase:** 5 — AI Studio + Marketplace · **Prior:** [Sprint 20](Sprint-20.md) · **Next:** [Sprint 22](Sprint-22.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Marketplace object model + certification pipeline.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-13-01 (MarketplaceListing object) | BE1 | P0 | Low | **LANDED BE (Stream A):** single `MarketplaceListing` across connector/app/prompt_pack/playbook via `/api/v1/marketplace/listings` (+ seed Odoo/HubSpot). Crumb [`PHASE1_STORY_13_01_MARKETPLACE_LISTING_CRUMB.md`](../PHASE1_STORY_13_01_MARKETPLACE_LISTING_CRUMB.md). No new RLS. No Production GO. |
| STORY-13-02 (certification pipeline) | BE-Lead, Security | P0 | Medium | **LANDED BE (Stream A):** CAP-094 submit/certify on listings — conformance via Hub certify suite + security checklist + trial sandbox; negative reject. Crumb [`PHASE1_STORY_13_02_CERTIFICATION_PIPELINE_CRUMB.md`](../PHASE1_STORY_13_02_CERTIFICATION_PIPELINE_CRUMB.md). No new RLS. No Production GO. |

**Expected Demo:** Submit a test connector listing, watch it move through the certification pipeline stages live.

**Technical Debt Created:** None.
