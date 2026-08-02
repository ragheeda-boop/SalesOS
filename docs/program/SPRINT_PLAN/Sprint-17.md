# Sprint 17 — 2027-03-15 → 2027-03-28

> **Phase:** 4 — GTM Intelligence Nativization · **Prior:** [Sprint 16](Sprint-16.md) · **Next:** [Sprint 18](Sprint-18.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Lookalikes + Enrichment + Verification.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-11-04 (Lookalike Accounts) | AI-Lead | P0 | Medium | Trained on tenant's own won/lost Opportunity history |
| STORY-11-05 (Enrichment Waterfall) | BE2 | P0 | Medium | **LANDED BE (Stream A):** ≥2 swappable providers via `/api/v1/gtm/enrichment` (CI: fake_a/fake_b). Crumb [`PHASE1_STORY_11_05_ENRICHMENT_WATERFALL_CRUMB.md`](../PHASE1_STORY_11_05_ENRICHMENT_WATERFALL_CRUMB.md). Live vendor enrichment not claimed. No new RLS. No Production GO. |
| FE-S11-05 (Enrichment Waterfall UI) | FE-Lead | P0 | Medium | **LANDED FE (Stream B):** `/gtm/enrichment` against tip enrichment HTTP. Crumb [`PHASE1_FE_S11_05_ENRICHMENT_CRUMB.md`](../PHASE1_FE_S11_05_ENRICHMENT_CRUMB.md). Live Clearbit/Apollo/ERP / 141221 not claimed. No Production GO. |
| STORY-11-06 (Contact Verification) | BE3 | P1 | Low | **LANDED BE (Stream A):** single `VerificationConnector` swap-in via `/api/v1/gtm/verification` (CI: fake_verify). Crumb [`PHASE1_STORY_11_06_CONTACT_VERIFICATION_CRUMB.md`](../PHASE1_STORY_11_06_CONTACT_VERIFICATION_CRUMB.md). Live vendor verification not claimed. No new RLS. No Production GO. |
| FE-S11-06 (Contact Verification UI) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** `/gtm/verification` against tip verification HTTP. Crumb [`PHASE1_FE_S11_06_VERIFICATION_CRUMB.md`](../PHASE1_FE_S11_06_VERIFICATION_CRUMB.md). Live NeverBounce/ZeroBounce/Twilio / 141221 not claimed. No Production GO. |

**Expected Demo:** Feed a seed account through Lookalikes, show ranked similar accounts from the tenant's real pipeline history.

**Technical Debt Created:** None.
