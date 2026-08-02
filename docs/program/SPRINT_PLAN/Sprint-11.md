# Sprint 11 — 2026-12-21 → 2027-01-03

> **Phase:** 2 — Integration Hub + Odoo GA · **Prior:** [Sprint 10](Sprint-10.md) · **Next:** [Sprint 12](Sprint-12.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)
> **Release gate:** Private Alpha (Muhide as first external design partner) — see [RELEASE_PLAN.md](../RELEASE_PLAN.md) §2

**Sprint Goal:** Odoo adapter complete across all 4 new objects; 14-day production soak begins. **Private Alpha gate.**

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-09-02 (Opportunity sync, translated stages) | BE3 | P0 | Medium | **LANDED BE (Stream A):** `crm.lead` pull + `sync_opportunity_records` with `strict_stages` ACL (no raw passthrough). Crumb [`PHASE1_STORY_09_02_ODOO_OPPORTUNITY_SYNC_CRUMB.md`](../PHASE1_STORY_09_02_ODOO_OPPORTUNITY_SYNC_CRUMB.md). No new RLS. No Production GO. |
| FE-S09-01 (Partner Studio presets + cr_number join honesty) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** Map/Schedule `res.partner` tip presets + join-outcome honesty; badge list still BE-blocked. Crumb [`PHASE1_FE_S09_01_PARTNER_STUDIO_HONESTY_CRUMB.md`](../PHASE1_FE_S09_01_PARTNER_STUDIO_HONESTY_CRUMB.md). No Production GO. |
| FE-S09-02 (Opportunity Studio presets + stage honesty) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** Map/Schedule `crm.lead` tip presets + translated stage honesty. Crumb [`PHASE1_FE_S09_02_OPPORTUNITY_STUDIO_HONESTY_CRUMB.md`](../PHASE1_FE_S09_02_OPPORTUNITY_STUDIO_HONESTY_CRUMB.md). No Production GO. |
| STORY-09-03 (InteractionNote/TimelineEvent + PII scrubbing) | BE-Lead, AI-Lead | P0 | High | **LANDED BE (Stream A):** `mail.message` pull + `sync_interaction_notes` + AI-GR-001 `scrub_pii_for_rag` before RAG. Crumb [`PHASE1_STORY_09_03_INTERACTION_NOTE_PII_CRUMB.md`](../PHASE1_STORY_09_03_INTERACTION_NOTE_PII_CRUMB.md). No new RLS. Live ≥100 prod-note audit residual. No Production GO. |
| FE-S09-03 (InteractionNote Studio presets + PII honesty) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** Map/Schedule `mail.message` tip presets + AI-GR-001 PII honesty (no RAG GO). Crumb [`PHASE1_FE_S09_03_NOTE_STUDIO_HONESTY_CRUMB.md`](../PHASE1_FE_S09_03_NOTE_STUDIO_HONESTY_CRUMB.md). No Production GO. |
| STORY-09-04 (SupportTicket) | BE2 | P1 | Medium | **BE-OPEN / not on tip** — do not invent FE `helpdesk.ticket` Studio until BE lands on tip. No Production GO. |
| STORY-09-05 (TaskCaseExtension) | BE1 | P0 | High | Modeled as Value Object on `Task`, not standalone aggregate; JSON Schema validated per case_type |
| STORY-09-06 (CustomerInvoice) | BE2 | P1 | Medium | Distinct from `PlatformBillingInvoice`, no naming collision |
| STORY-09-07 (incremental sync, feature flag) | BE3 | P0 | High | `write_date` cursor working; `feature_odoo_integration` flag live for Muhide |

**Expected Demo:** **Phase 2 Go/No-Go + Private Alpha release** (Muhide as first external design partner on real data). Live Company 360 page for a real Muhide customer, populated from real Odoo data, Golden Record matched, InteractionNote feeding AI Coach with PII scrubbed.

**Technical Debt Created:** Second connector doesn't exist yet — explicitly tracked as Phase 4 scope, not silently assumed solved by Odoo alone.
