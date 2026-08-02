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
| FE-S07-06 Ops nav + tenant-JWT admin 401 honesty | **LANDED** (this tip) |

## Honesty

- Stripe status: env-only booleans; never echo secrets; `production_go=false`. No invented keys.
- Entitlements: empty create → BE tier defaults; edit JSON (DOM-* keys).
- Plan-change + pending_plan_* honesty; dunning evaluate/clear.
- Entitlement 403 → warning toast (upgrade / Owner edit Plan.entitlements).
- Quota `error=quota_exceeded` → warning toast (metric used/limit; seats/connectors/storage 403; ai_tokens 429). Upgrade or reduce usage. No fake GO.
- `TenantList.tsx` untouched. **No Production GO.**

**Validation:** focused Jest (formatProvisionToast helpers + quota parsers).
