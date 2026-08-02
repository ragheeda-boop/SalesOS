# Sprint 18 — 2027-03-29 → 2027-04-11

> **Phase:** 4 — GTM Intelligence Nativization · **Prior:** [Sprint 17](Sprint-17.md) · **Next:** [Sprint 19](Sprint-19.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Website Intelligence + AI Outreach + Sequencing (email channel).

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-11-07 (Website Intelligence) | AI-Lead | P0 | Medium | **LANDED BE (AI-Lead):** fixture `WebsiteIntelligenceSnapshot` via `/api/v1/gtm/website-intelligence` (+ /meta), governed prompt `gtm.website_intelligence.v1` (platform LLM spend path — no Claygent). Crumb [`PHASE1_STORY_11_07_WEBSITE_INTELLIGENCE_CRUMB.md`](../PHASE1_STORY_11_07_WEBSITE_INTELLIGENCE_CRUMB.md). Live crawl/LLM/RAG not claimed. `feature_ai_copilot` stays False. No new RLS. No Production GO. Unblocks FE-S11-07. |
| STORY-11-08 (AI Outreach) | AI-Lead | P0 | Medium | **LANDED BE (AI-Lead):** fixture `OutreachDraft` via `/api/v1/gtm/outreach` (+ /meta), governed prompt `gtm.ai_outreach.v1` (Prompt Registry spend path — not disconnected tool). Crumb [`PHASE1_STORY_11_08_AI_OUTREACH_CRUMB.md`](../PHASE1_STORY_11_08_AI_OUTREACH_CRUMB.md). `delivery_status=draft_only`. Live LLM/SMTP/LI/WA not claimed. `feature_ai_copilot` stays False. No new RLS. No Production GO. Unblocks FE-S11-08. |
| STORY-11-09 (Sequencing Engine, email channel) | BE1, FE2 | P0 | Medium | **LANDED BE (Stream A):** email-only `SequenceDefinition` + enrollment state machine via `/api/v1/gtm/sequences`, bound to Task/Activity-shaped refs. Crumb [`PHASE1_STORY_11_09_SEQUENCING_CRUMB.md`](../PHASE1_STORY_11_09_SEQUENCING_CRUMB.md). Live SMTP / LinkedIn / WhatsApp not claimed. No new RLS. No Production GO. |
| FE-S11-09 (Email Sequencing UI) | FE-Lead | P0 | Medium | **LANDED FE (Stream B):** `/gtm/sequences` against tip sequences HTTP (create/enroll/advance/pause/resume/cancel). Crumb [`PHASE1_FE_S11_09_SEQUENCING_CRUMB.md`](../PHASE1_FE_S11_09_SEQUENCING_CRUMB.md). Live SMTP / LinkedIn / WhatsApp not claimed. No Production GO. |

**Expected Demo:** End-to-end GTM flow: ICP → Lead Discovery → Enrichment → Website Intelligence → AI-drafted outreach → email sequence sent to a test inbox.

**Technical Debt Created:** LinkedIn/WhatsApp channels for Sequencing land next sprint — email-only this sprint, explicitly scoped.
