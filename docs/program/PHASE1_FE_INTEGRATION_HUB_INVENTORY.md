# Phase 1/2 boundary — Integration Hub FE inventory (Stream B)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Honesty:** Not Production GO. No invented Postgres persistence / owner mint.  
> `TenantList.tsx` untouched.

## Landed track

| Piece | Status |
|-------|--------|
| FE-S08-00 | `/admin/integrations` inventory |
| FE-S08-01 | Thin shell (superseded) |
| STORY-08-07 | Live Studio against Hub HTTP |
| FE-S08-08 | Conflict-policy + Odoo honesty |
| FE-S08-09 | Active mapping GET + tenant nav |
| FE-S08-10 | Connection detail + baseline_fields + cmd palette |
| FE-S08-11 | URL deep-link + schedule/monitor polish |
| FE-S08-12 | Monitor SyncRun model filter + tip fields |
| FE-S08-13 | Schedule job_type + conflict tip defaults + connection polish |
| FE-S08-14 | Mapping version + schedule name + connection GET refresh |
| FE-S08-15 | Cmd palette remaining steps + tip timestamps / mapping id |
| FE-S09-01 | Partner presets + cr_number join honesty (tip 09-01) |
| FE-S09-02 | Opportunity presets + stage honesty (tip 09-02) |
| FE-S09-03 | InteractionNote presets + PII honesty (tip 09-03) |
| FE-S09-04 | SupportTicket presets + stage honesty (tip 09-04) |
| FE-S09-05 | project.task / TaskCaseExtension VO honesty (tip 09-05) |
| FE-S09-06 | CustomerInvoice presets + payment honesty (tip 09-06) |
| FE-S09-07 | Odoo flag + write_date cursor honesty (tip 09-07) |
| FE-S09-07b | Owner /admin/flags Odoo gate honesty |
| FE-S09-08 | Unlinked badge Monitor list (tip 09-08) |
| FE-S09-09 | SyncRun cursor Monitor columns (tip 09-09) |
| FE-S09-10 | Hub honesty sync (unlinked tip) |
| FE-S10-01 | Custom field definition Studio (tip 10-01) |
| FE-S10-02 | Custom field auto-render form-schema (tip 10-02) |
| FE-S10-04 | Scoring Rules Studio (tip 10-04) |
| FE-S10-06 | Permissions Studio (tip 10-06) |
| FE-S10-03 | Workflow Builder Studio (tip 10-03) |
| FE-S10-08 | Notification Rules Studio (tip 10-08) |
| FE-S10-cmd | Cmd palette deep-links for tip Studio pages |
| FE-S10-07 | Branding Studio (tip 10-07 GET/PUT) |
| FE-S10-07b | Branding chrome — tip display_name + colors on shell |
| FE-S11-02 | Market Sizing TAM/SAM/SOM (tip 11-02) |
| FE-S11-02b | Market Sizing detail GET + nested bands |
| FE-S11-03 | Lead Discovery gov-first UI (tip 11-03) |
| FE-S11-03b | GTM hub + criteria handoff / deep-links |
| FE-S11-01 | ICP Profiles UI (tip 11-01) |
| FE-S11-05 | Enrichment Waterfall UI (tip 11-05) |
| FE-S11-06 | Contact Verification UI (tip 11-06) |
| FE-S11-06b | GTM enrichment↔verification / ICP / discovery handoffs |
| FE-S11-04 | Lookalike Accounts UI (tip 11-04) |
| FE-S11-09 | Email Sequencing UI (tip 11-09) |
| FE-S11-09b | Sequencing multi-channel UI (tip 11-09b partner LI/WA) |
| FE-S11-10 | Second connector certify UI (tip 11-10 HubSpot) |
| FE-S10-05 | Territory Studio UI (tip 10-05 `/studio/territories`) |
| FE-S12-04 | AI Model Tiers Studio UI (tip 12-04 GET-only) |
| FE-S13-01b | Marketplace listings browse (tip 13-01 memory; not CAP-036) |
| FE-S13-03 | Marketplace certify UX (tip 13-02 submit/certify; no invent /install) |
| FE-S13-04 | Marketplace publish/install UX (tip 13-04; catalog install ≠ live ERP) |
| FE-S11-07 | Website Intelligence UI (tip 11-07 fixture; feature_ai_copilot False) |
| FE-S11-08 | AI Outreach UI (tip 11-08 draft_only; no live SMTP/LI/WA) |
| FE-S12-01 | Prompt Library Studio UI (tip 12-01; feature_ai_copilot False) |

## Blocked (do not invent)

- Live SMTP / LinkedIn / WhatsApp send via outreach drafts — **not claimed** (`delivery_status=draft_only`)
- Live website crawl / live LLM via website-intelligence — **not claimed**
- Live HubSpot/Odoo/REST GO via catalog install — **not claimed**
- Postgres custom-field / workflow persistence beyond tip in-memory stores
- Workflow for_each / loop canvas nodes (deferred)
