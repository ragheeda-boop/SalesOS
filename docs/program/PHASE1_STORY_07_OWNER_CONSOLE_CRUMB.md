# Phase 1 — EPIC-07 Owner Console MVP (Stream B FE)

> **Date:** 2026-08-02  
> **Owner:** Frontend Lead  
> **Stories:** STORY-07-01 / 07-02 / 07-03  
> **Tip base:** after FE-S06-03b `c16b6c8`  

| Story | Status | Surface |
|-------|--------|---------|
| STORY-07-01 `/tenants` list + detail + usage | **LANDED** (prior FE-S04/S05 + this shell) | `/admin/tenants` |
| STORY-07-02 `/billing` subscription/invoices/dunning | **LANDED** (FE-S06-01 + shell nav) | `/admin/billing` |
| STORY-07-03 Owner-only auth shell + audience honesty | **LANDED** | `OwnerConsoleShell` + `ownerAudience.ts` |
| FE-S07-04 Host honesty + overview deep-links + E2E shell hooks | **LANDED** | overview MVP links; host banner; e2e hooks |
| FE-S07-05 Ops runbook + read-path honesty + billing E2E | **LANDED** | `OPERATIONS_MANUAL` §15; cross-audience Jest |
| FE-S07-06 Ops nav + tenant-JWT admin 401 honesty toast | **LANDED** (this tip) | flags/config/audit nav; keep tenant session |

## Honesty

- JWT audiences: tenant `salesos-api` vs owner `salesos-owner-platform` (DEC-093).
- FE surfaces audience honesty + gate banner when session is not owner audience; does not weaken BE `owner_auth` (API still rejects tenant JWT).
- Children stay mounted so Stage 7 Owner Console E2E hooks remain usable; enforcement remains BE.
- Owner login mint UX remains BE follow-up (DEC-093). No invented tokens / Stripe keys / mint.
- `owner.salesos.io` host honesty classified (owner-target / local / shared-app) — **not** claimed as live separate deploy.
- `TenantList.tsx` untouched. **No Production GO.**

**Validation:** focused Jest (`ownerAudience.test.ts`). CI FE Lint/Types/Unit after land.
