# Sprint 19 — 2027-04-12 → 2027-04-25

> **Phase:** 4 — GTM Intelligence Nativization · **Prior:** [Sprint 18](Sprint-18.md) · **Next:** [Sprint 20](Sprint-20.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)
> **Release gate:** Partner Beta (3-5 paying pilots) — see [RELEASE_PLAN.md](../RELEASE_PLAN.md) §4

**Sprint Goal:** Multi-channel Sequencing; second connector certified. **Partner Beta gate.**

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-11-09 (Sequencing, LinkedIn + WhatsApp channels) | BE1 | P0 | Medium | **LANDED BE (Stream A):** LinkedIn/WhatsApp via compliant partner sender ports on `/api/v1/gtm/sequences` (no ToS-risk automation). Crumb [`PHASE1_STORY_11_09B_SEQUENCING_MULTICHANNEL_CRUMB.md`](../PHASE1_STORY_11_09B_SEQUENCING_MULTICHANNEL_CRUMB.md). Live network sends not claimed. No new RLS. No Production GO. |
| STORY-11-10 (second connector certification) | BE3 (new engineer, not OdooAdapter's author) | P0 | High (R-02) | **LANDED BE (Stream A):** `HubSpotAdapter` passes identical `certify_source_connector` suite; `POST /api/v1/integrations/certify/hubspot`. Crumb [`PHASE1_STORY_11_10_SECOND_CONNECTOR_CRUMB.md`](../PHASE1_STORY_11_10_SECOND_CONNECTOR_CRUMB.md). Production pilot sync residual OPEN. No new RLS. No Production GO. |
| Partner Beta pilot onboarding (3-5 tenants) | Program Director, CS (contracted) | P0 | Medium | Pilots provisioned, billed in Stripe test mode |

**Expected Demo:** **Phase 4 Go/No-Go + Partner Beta release.** Second connector syncing live for a real pilot tenant, certified by an engineer with no prior context on the first connector — direct proof the framework generalizes.

**Technical Debt Created:** None — R-02 explicitly closed this sprint, not deferred further.
