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
| FE-S10-06 | Permissions Studio (tip 10-06) — next READY |
| FE-S10-03 | Workflow Builder Studio (tip 10-03) — READY |
| FE-S10-05 | Territory config — **BLOCKED** (no tip `/studio/territories` BE) |

## Blocked (do not invent)

- Postgres custom-field / workflow persistence beyond tip in-memory stores
- Workflow for_each / loop canvas nodes (deferred)
