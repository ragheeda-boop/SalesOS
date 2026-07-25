# Legacy → v3 Migration Map (1:1)

> **Date:** 2026-07-23  
> **Source of truth (routes):** [PAGE_MAP_SALESOS.md](../../audit/ga-engineering-audit/PAGE_MAP_SALESOS.md) — **54** App Router routes  
> **v3 code root:** `salesos/frontend/src/app/v3/`  
> **Validation:** **light validated** (static PAGE_MAP × `page.tsx` cross-check)  
> **Production GO:** **NO** — not claimed. Dual-run / Preview only.

---

## Status legend (honest)

| Status | Meaning |
|--------|---------|
| `dual-run` | Legacy page remains; matching `/v3/*` route exists with **real API wiring** (list/detail fetch). Not cutover. |
| `preview` | `/v3/*` IA shell exists (`PreviewBadge` / `DomainWorkbench` / popup) — **no** full data wire for that surface. |
| `stub` | v3 surface exists but is thin, partial-tab, or chrome-only (honest empty / placeholder tabs). |
| `not started` | No dedicated v3 target route yet; legacy remains sole UI. |
| `legacy-only` | Intentionally stays on legacy App Router for now (shared auth, ops deep links, honesty stubs). |
| `done` | Prod cutover complete; legacy retired. **None** as of this pass. |

**Rule:** feature flag / dual-run per domain; no big-bang; soak evidence before prod cutover. AI assists · humans decide · evidence governs.

---

## Current v3 routes (code)

| v3 route | Role | Wire note |
|----------|------|-----------|
| `/v3` | Sales home | Recent companies API; KPI tiles placeholder |
| `/v3/companies` | Companies list | `searchCompanies` wired |
| `/v3/companies/[id]` | **Company 360** | Overview + contacts + opportunities + **tasks** (`listTasks` by company) + timeline (`getEntityActivities`) wired; intelligence **stub** tab |
| `/v3/crm` | Deals / pipeline | `listOpportunities` + **kanban board** (Board/Table toggle); stage moves via `advanceOpportunity` (drag or table select) |
| `/v3/crm/[id]` | **Deal 360** | Overview + company contacts + activity (`getEntityActivities`) wired |
| `/v3/contacts` | Contacts list | `searchContacts` wired; company → Company 360 |
| `/v3/contacts/[id]` | **Contact 360** | Overview + company link + activity (`getEntityActivities`) wired |
| `/v3/people` | People list | `searchEmployees` wired |
| `/v3/people/[id]` | **Employee 360** | Overview + portfolio + activity wired; timeline / intelligence **stub** tabs |
| `/v3/activities` | Activities feed | `getGlobalActivities` wired; entity tabs use `getEntityActivities` |
| `/v3/tasks` | Tasks list | `listTasks` wired; priority/status filters; complete action |
| `/v3/tasks/[id]` | **Task detail** | List-resolved (no GET `/tasks/{id}`); company link when `company_id` present |
| `/v3/analytics` | Analytics Studio IA | Preview workbench — no chart APIs |
| `/v3/cs` | Customer Success IA | Preview workbench |
| `/v3/admin` | Admin IA | Preview workbench |
| `/v3/settings` | Settings IA | Preview workbench |
| `/v3/shell` | Shell contract page | Spec / spike only (not a PAGE_MAP legacy counterpart) |

Ask AI is **popup-only** (`V3AiPopup`) — there is **no** `/v3/ai` or `/v3/copilot` page by design ([AI_HONESTY.md](../../audit/ga-engineering-audit/AI_HONESTY.md)).

---

## 1:1 matrix — all 54 PAGE_MAP routes

| # | Product surface | Legacy route | v3 destination | Migration status | Notes |
|--:|-----------------|--------------|----------------|------------------|-------|
| 1 | Marketing | `/` | TBD marketing or redirect | `not started` | Legacy mini-landing stub; no `/v3` marketing |
| 2 | Auth | `/login` | Shared `/login?next=/v3…` | `legacy-only` | v3 reuses legacy login; no `/v3/login` |
| 3 | Auth | `/register` | Shared `/register` | `legacy-only` | Same session model as login |
| 4 | SalesOS core | `/dashboard` | `/v3` | `dual-run` | Home wired for recent companies; KPI placeholders remain |
| 5 | Company 360 | `/companies` | `/v3/companies` | `dual-run` | List + search wired |
| 6 | Company 360 | `/companies/[id]` | `/v3/companies/[id]` | `dual-run` | **Company 360** — timeline via `getEntityActivities`; **Tasks** tab filters `listTasks` by `company_id`; intelligence stub |
| 7 | Company 360 | `/companies/[id]/360` | `/v3/companies/[id]` | `dual-run` | Legacy dedicated 360 merges into single v3 Company 360 |
| 8 | Employee 360 | `/employees` | `/v3/people` | `dual-run` | People list wired |
| 9 | Employee 360 | `/employees/me` | `/v3/people/[id]` (self) | `not started` | No `/v3/people/me`; resolve self-id then dual-run Employee 360 |
| 10 | Employee 360 | `/employees/[id]` | `/v3/people/[id]` | `dual-run` | **Employee 360** current wire; timeline/intelligence stub tabs; Activity → `/v3/tasks` cross-link; portfolio contracts display-only |
| 11 | SalesOS core | `/contacts` | `/v3/contacts` (+ `/v3/contacts/[id]`) | `dual-run` | List + Contact 360 wired; company link → Company 360; activity via `getEntityActivities` |
| 12 | SalesOS core | `/opportunities` | `/v3/crm` | `dual-run` | **Opportunities wire** — CRM list + **pipeline kanban** (Board/Table); `advanceOpportunity` for stage moves |
| 13 | SalesOS core | `/opportunities/[id]` | `/v3/crm/[id]` | `dual-run` | **Deal 360** current wire; activity via `getEntityActivities` |
| 14 | SalesOS core | `/activities` | `/v3/activities` (+ 360 activity/timeline tabs) | `dual-run` | Global `getGlobalActivities`; entity tabs on Contact/Deal/Company |
| 15 | Revenue | `/revenue` | `/v3/analytics` → Revenue | `preview` | Analytics workbench section only |
| 16 | Revenue | `/revenue/territories` | TBD Analytics / Admin | `not started` | Legacy demoTerritories honesty risk remains on legacy |
| 17 | Revenue | `/revenue/quotas` | TBD Analytics / Admin | `not started` | Legacy demoQuotas honesty risk remains on legacy |
| 18 | Revenue | `/pipeline` | `/v3/crm` | `dual-run` | **Kanban board** on `/v3/crm` (Board view default) + Table; stage order matches backend default pipeline; Ask AI popup only |
| 19 | Analytics | `/pipeline/analytics` | `/v3/analytics` → Pipeline | `preview` | |
| 20 | Revenue | `/forecast` | `/v3/analytics` → Forecast | `preview` | Explicit “no invented scores” copy |
| 21 | Search | `/search` | CmdK + TBD Universal Search | `stub` | CmdK go-to only; no `/v3/search` page |
| 22 | Search | `/search/analytics` | TBD | `not started` | |
| 23 | Decision Center | `/decisions` | TBD Decision Center module | `not started` | Prefer Decision Center HTTP APIs; FE decision package is STUB |
| 24 | Decision Center | `/decisions/templates` | TBD | `not started` | |
| 25 | SalesOS core | `/meetings` | TBD CRM / Activities / Tasks | `not started` | Meeting Intelligence is opportunity-scoped (`GET /meetings/{opportunity_id}`); no tenant meetings list in `lib/api`. Prefer Tasks Objects dual-run (`/v3/tasks`) for follow-ups. |
| 26 | Knowledge / RAG | `/rag` | TBD Documents / Knowledge | `not started` | |
| 27 | AI / Copilot | `/ai` | Ask AI popup (no page) | `preview` | Honesty: popup Preview; not page chrome |
| 28 | Knowledge | `/graph` | TBD Company Graph | `not started` | Path-analysis UX still planned-missing |
| 29 | AI / Copilot | `/copilot` | Ask AI popup (no page) | `preview` | Legacy flag-off stub; `feature_ai_copilot` default false |
| 30 | AI / Copilot | `/copilot/telemetry` | — | `legacy-only` | Ops/debug; no v3 plan |
| 31 | Automation | `/automation` | TBD Automation | `not started` | |
| 32 | Automation | `/automation/workflows/new` | TBD | `not started` | |
| 33 | Automation | `/automation/analytics` | TBD | `not started` | |
| 34 | Analytics | `/analytics` | `/v3/analytics` | `preview` | Studio IA shell |
| 35 | Analytics | `/analytics/sales` | `/v3/analytics` → Sales performance | `preview` | |
| 36 | Analytics | `/analytics/revenue` | `/v3/analytics` → Revenue | `preview` | |
| 37 | Analytics | `/analytics/pipeline` | `/v3/analytics` → Pipeline | `preview` | |
| 38 | Analytics | `/analytics/employees` | `/v3/analytics` → Sales performance | `preview` | |
| 39 | Analytics | `/analytics/automation` | TBD | `not started` | |
| 40 | Analytics | `/analytics/reports/builder` | `/v3/analytics` → Custom reports | `preview` | Section documents “not wired” |
| 41 | Signals | `/signals` | TBD Signals | `not started` | |
| 42 | Automation / Rules | `/rules` | TBD Automation / Rules | `not started` | |
| 43 | Admin / Ops | `/monitoring` | TBD Admin / Ops | `not started` | Could later fold under `/v3/admin` |
| 44 | Customer Success | `/customer-success` | `/v3/cs` | `preview` | CS domain IA |
| 45 | Admin | `/settings` | `/v3/settings` | `preview` | Settings domain IA |
| 46 | Admin | `/admin` | `/v3/admin` | `preview` | Admin domain IA |
| 47 | Admin | `/admin/flags` | `/v3/admin` → Feature flags | `preview` | Flags section copy only |
| 48 | Admin | `/admin/config` | `/v3/admin` / `/v3/settings` | `preview` | Split IA TBD |
| 49 | Admin | `/admin/audit` | `/v3/admin` → Audit logs | `preview` | |
| 50 | Admin | `/admin/tenants` | `/v3/admin` → Organizations | `preview` | |
| 51 | Knowledge | `/knowledge` | TBD Knowledge | `not started` | Orphaned in legacy nav |
| 52 | Knowledge / Data Fabric | `/knowledge/connectors` | TBD Data Fabric | `not started` | |
| 53 | Marketplace | `/marketplace` | TBD Network marketplace | `not started` | Plugin gallery ≠ widget marketplace DoD |
| 54 | Marketplace | `/marketplace/[pluginId]/config` | TBD | `not started` | |

**Row coverage:** **54 / 54** PAGE_MAP code routes have a 1:1 migration row.

---

## Status counts (54 routes)

| Migration status | Count |
|------------------|------:|
| `dual-run` | **11** |
| `preview` | **18** |
| `stub` | **1** |
| `not started` | **21** |
| `legacy-only` | **3** |
| `done` | **0** |
| **Total** | **54** |

Dual-run set (current wire): `/dashboard`→`/v3`, companies list + Company 360 (incl. Tasks tab), contacts list + Contact 360, people list + Employee 360, CRM opportunities list + **pipeline kanban** + Deal 360, pipeline→CRM board, activities feed + 360 activity/timeline tabs.

**Objects dual-run (not in PAGE_MAP 54):** `/v3/tasks` + `/v3/tasks/[id]` via `listTasks` / `completeTask`. **Contracts deferred** — commercial API is create/sign only (no list/get in `lib/api`). **Meetings** remain `not started` (opportunity-scoped intelligence only).

---

## Planned-missing (PAGE_MAP appendix — no legacy route)

These are **not** among the 54 routes; tracked so the map does not pretend they are migrated.

| Intended UI | v3 destination | Status | Notes |
|-------------|----------------|--------|-------|
| Tasks list + detail | `/v3/tasks`, `/v3/tasks/[id]` | `dual-run` | Real `listTasks`; detail list-resolved (no GET by id). Company 360 Tasks tab. |
| Contracts list + Contract 360 | TBD `/v3/contracts` | `not started` | Backend create/sign only; portfolio contracts on People 360 stay display-only |
| Next Best Action screen | TBD / opportunity widgets | `not started` | i18n `nav.nba` only |
| Graph path analysis | TBD under Knowledge | `not started` | |
| Feature registry + drift | TBD | `not started` | |
| Ingestion / data quality dashboards | TBD | `not started` | Partial: legacy connectors |
| Widget marketplace | TBD | `not started` | Distinct from plugin `/marketplace` |
| Signal rule configuration UI | TBD | `not started` | |
| Full RBAC permission matrix editor | `/v3/admin` → RBAC matrix | `preview` | IA section only; not a live editor |

---

## Cutover principles

1. **Dual-run first** — keep legacy routes until soak evidence (flags per domain).
2. **360 consolidation** — legacy `/companies/[id]` + `/360` → one `/v3/companies/[id]`; employees → `/v3/people/[id]`; opportunities → `/v3/crm/[id]`.
3. **AI honesty** — never ship page-chrome AI; Ask AI popup only; copilot remains Preview / flag-gated.
4. **No Production GO** from this matrix alone — engineering audit remains **production no-go** until evidence closes P0s.
5. Promote nav orphans (`/knowledge*`, `/marketplace*`) into v3 IA before claiming discoverability parity.

---

## Validation

| Item | Status |
|------|--------|
| PAGE_MAP 54-row enumeration | **light validated** |
| v3 `page.tsx` inventory | **light validated** (`Glob` under `app/v3`) |
| `/v3/crm` Board+Table dual-run (HTTP 200 after FE image recreate) | **light validated** (curl only; browser soak **not validated**) |
| Browser dual-run soak | **not validated** |
| Feature-flag cutover | **not started** |
| Production GO | **NO** |

---

*Evidence governs. AI assists. Humans decide.*
