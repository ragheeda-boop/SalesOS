# Phase 1 — Frontend Stream B crumb (through stripe status + entitlements)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Evidence tip base:** `e0cde3f` (stripe/status) / `08aa56f` (entitlement middleware) / `ca1fb19` (plan-change)  

| Task | Status |
|------|--------|
| FE-S05-05 Dunning | **LANDED** |
| FE-S05-06 Plan-change quote/apply/pending | **LANDED** |
| FE-S05-02c Stripe status banner (booleans) | **LANDED** |
| FE-S06-01 `/admin/billing` read view | **LANDED** |
| FE-S06-02 Plan.entitlements editor/display | **LANDED** |
| FE-S06-02b Honest 403 entitlement upgrade toast | **LANDED** |
| FE-S06-03 Resolved entitlements on TenantBillingPanel | **LANDED** |
| FE-S06-03b Honest quota_exceeded toast (403/429) | **LANDED** |
| FE-S07-01/02/03 Owner Console MVP shell + audience | **LANDED** — crumb [`PHASE1_STORY_07_OWNER_CONSOLE_CRUMB.md`](PHASE1_STORY_07_OWNER_CONSOLE_CRUMB.md) |
| FE-S07-04 Host honesty + overview deep-links + E2E hooks | **LANDED** |
| FE-S07-05 Ops runbook + read-path honesty + billing E2E | **LANDED** |
| FE-S07-06 Ops nav + tenant-JWT admin 401 honesty | **LANDED** |
| FE-S07-07 Ops page honesty + EPIC-07 MVP close | **LANDED** |
| FE-S08-00 Integration Hub inventory honesty stub | **LANDED** — crumb [`PHASE1_FE_INTEGRATION_HUB_INVENTORY.md`](PHASE1_FE_INTEGRATION_HUB_INVENTORY.md) |
| FE-S08-01 Thin Studio shell (API not live) | **LANDED** — superseded by STORY-08-07 live Studio |
| STORY-08-07 Integrations Studio UI | **LANDED** (this tip) — `/integrations` against Hub HTTP; crumb [`PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md`](PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md) |
| FE-S08-08 Conflict-policy Studio + Odoo honesty | **LANDED** — crumb [`PHASE1_FE_S08_08_CONFLICT_POLICY_STUDIO_CRUMB.md`](PHASE1_FE_S08_08_CONFLICT_POLICY_STUDIO_CRUMB.md) |
| FE-S08-09 Active mapping load + tenant Integrations nav | **LANDED** — crumb [`PHASE1_FE_S08_09_ACTIVE_MAPPING_NAV_CRUMB.md`](PHASE1_FE_S08_09_ACTIVE_MAPPING_NAV_CRUMB.md) |
| FE-S08-10 Studio connection detail + baseline_fields polish | **LANDED** — crumb [`PHASE1_FE_S08_10_STUDIO_DETAIL_POLISH_CRUMB.md`](PHASE1_FE_S08_10_STUDIO_DETAIL_POLISH_CRUMB.md) |
| FE-S08-11 Studio URL deep-link + schedule/monitor polish | **LANDED** — crumb [`PHASE1_FE_S08_11_STUDIO_URL_DEEPLINK_CRUMB.md`](PHASE1_FE_S08_11_STUDIO_URL_DEEPLINK_CRUMB.md) |
| FE-S08-12 Monitor SyncRun model filter + tip fields | **LANDED** — crumb [`PHASE1_FE_S08_12_MONITOR_MODEL_FILTER_CRUMB.md`](PHASE1_FE_S08_12_MONITOR_MODEL_FILTER_CRUMB.md)
| FE-S08-13 Schedule job_type + conflict tip defaults | **LANDED** — crumb [`PHASE1_FE_S08_13_SCHEDULE_CONFLICT_POLISH_CRUMB.md`](PHASE1_FE_S08_13_SCHEDULE_CONFLICT_POLISH_CRUMB.md)
| FE-S08-14 Mapping version + schedule name + connection GET | **LANDED** — crumb [`PHASE1_FE_S08_14_MAPPING_SCHEDULE_CONNECTION_CRUMB.md`](PHASE1_FE_S08_14_MAPPING_SCHEDULE_CONNECTION_CRUMB.md)
| FE-S09-01 Partner Studio presets + cr_number join honesty | **LANDED** — crumb [`PHASE1_FE_S09_01_PARTNER_STUDIO_HONESTY_CRUMB.md`](PHASE1_FE_S09_01_PARTNER_STUDIO_HONESTY_CRUMB.md)
| FE-S09-02 Opportunity Studio presets + stage honesty | **LANDED** — crumb [`PHASE1_FE_S09_02_OPPORTUNITY_STUDIO_HONESTY_CRUMB.md`](PHASE1_FE_S09_02_OPPORTUNITY_STUDIO_HONESTY_CRUMB.md) |
| FE-S09-03 InteractionNote Studio presets + PII honesty | **LANDED** — crumb [`PHASE1_FE_S09_03_NOTE_STUDIO_HONESTY_CRUMB.md`](PHASE1_FE_S09_03_NOTE_STUDIO_HONESTY_CRUMB.md)
| FE-S09-04 SupportTicket Studio presets + stage honesty | **LANDED** — crumb [`PHASE1_FE_S09_04_TICKET_STUDIO_HONESTY_CRUMB.md`](PHASE1_FE_S09_04_TICKET_STUDIO_HONESTY_CRUMB.md)
| FE-S09-05 project.task / TaskCaseExtension Studio honesty | **LANDED** — crumb [`PHASE1_FE_S09_05_TASK_STUDIO_HONESTY_CRUMB.md`](PHASE1_FE_S09_05_TASK_STUDIO_HONESTY_CRUMB.md)

## Honesty

- Stripe status: env-only booleans; never echo secrets; `production_go=false`. No invented keys.
- Entitlements: empty create → BE tier defaults; edit JSON (DOM-* keys).
- Plan-change + pending_plan_* honesty; dunning evaluate/clear.
- Entitlement 403 → warning toast (upgrade / Owner edit Plan.entitlements).
- Quota `error=quota_exceeded` → warning toast (metric used/limit; seats/connectors/storage 403; ai_tokens 429). Upgrade or reduce usage. No fake GO.
- `TenantList.tsx` untouched. **No Production GO.**

**Validation:** focused Jest (formatProvisionToast helpers + quota parsers).
