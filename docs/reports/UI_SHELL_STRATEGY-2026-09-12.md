# UI Shell Strategy — SalesOS (2026-09-12)

**Audience:** Product Owner  
**Author:** B1 — UI Shell Strategy (read-only inventory)  
**Scope:** `salesos/frontend/src/app/**/page.tsx` + `nav.ts` + `commands.ts` + `workspaces.ts`  
**Method:** Disk enumeration (PowerShell `Get-ChildItem` + glob). Live browser **not** run.  
**Labels:** **FACT** / **INFERENCE** / **RECOMMENDATION** / **UNKNOWN**

---

## 1. Verdict (read this first)

**FACT — default shell after login is already v3.** `salesos/frontend/src/app/(auth)/login/page.tsx` fallback is `"/v3"`.

**FACT — two live shells still coexist.** A customer who bookmarks, uses register, or hits command-palette shortcuts can land in the legacy `(dashboard)` chrome.

**RECOMMENDATION — customer MVP default = v3 only.** Freeze the legacy shell for internal/studio/GTM/ops. Do not sell it. Do not revive it. Redirect overlapping CRM URLs into `/v3/*` after a short freeze window.

| Claim in `project-audit` | Disk 2026-09-12 | Verdict |
|-------------------------|-----------------|---------|
| ~40 v3 pages | **40** `v3/**/page.tsx` | **CONFIRMED** |
| ~78 legacy `(dashboard)` pages | **78** | **CONFIRMED** |
| 24-item v3 nav | **25** items in `V3_DOMAIN_NAV` | **STALE** (off by +1: Review Queue) |
| Command palette 35 | **51** `registerCommand` in `commands.ts`; **26** destinations in v3 CmdK (`V3_DOMAIN_NAV` 25 + `V3_CMD_EXTRA` 1) | **STALE** — two palettes, not one |

---

## 2. Actual page counts — FACT (glob / dir evidence)

**Command run (read-only):**

```text
Get-ChildItem -Path salesos/frontend/src/app -Recurse -Filter page.tsx
```

| Bucket | Count | Evidence |
|--------|------:|----------|
| **v3 shell** `src/app/v3/**/page.tsx` | **40** | listed in §4.1 |
| **Legacy shell** `src/app/(dashboard)/**/page.tsx` | **78** | listed in §4.2 |
| **Auth** `src/app/(auth)/**/page.tsx` | **3** | `/login`, `/register`, `/admin/login` |
| **Other pages** | **2** | `/` (marketing splash), `/system` (build-parity) |
| **Total `page.tsx`** | **123** | 40+78+3+2 |
| Layouts (not pages) | 4 | `app/layout.tsx`, `v3/layout.tsx`, `(dashboard)/layout.tsx`, `(dashboard)/admin/layout.tsx` |
| API route handlers (not pages) | 2 | `app/api/v1/copilot/query/route.ts`, `app/api/auth/callback/google/route.ts` |

**INFERENCE:** `project-audit/11_CAPABILITY_MATRIX.md` §1.12 “v3 = 40 / legacy = 78” counted the two product shells only and excluded auth + splash + `/system`. That subset is correct. The “109-page FE build” note in `01_CURRENT_STATE.md` §2.5 is a **2026-09-05 build claim**, not today’s `page.tsx` count (123). Those are different units (build graph vs route files).

**FACT — `getDemoData` remnants:** zero production matches under `salesos/frontend/src` (only test `mockData` fixtures). Graph + knowledge keep API calls + honest empty states.

---

## 3. How the two shells work

| | **v3** | **Legacy `(dashboard)`** |
|--|--------|--------------------------|
| URL prefix | `/v3/*` | no prefix (`/companies`, `/gtm`, `/studio`, …) |
| Layout | `v3/layout.tsx` → `V3Shell` + `V3Topbar` + `V3CommandPalette` | `(dashboard)/layout.tsx` → `GroupedSidebar` from `workspaces.ts` |
| Sidebar source | `components/v3/nav.ts` → `V3_DOMAIN_NAV` (**25**) | `lib/workspaces.ts` → **44** items across 6 workspaces |
| Command palette | **Separate:** `V3CommandPalette` = nav + `/v3/shell` | **Separate:** `lib/commands.ts` (**51** commands, mostly legacy URLs) |
| Post-login | **FACT:** `/v3` | Register still `router.push("/dashboard")` |
| Honesty markers | “Not Production GO” **removed** from v3 layout (2026-09-05 claim; not re-browsered) | Studio / Admin / GTM pages still stamp “Not Production GO” in source |

**FACT — shell leak:** `/v3/employee` redirects to `/employees/me` (legacy layout). `/v3/companies/[id]/360` redirects **inside** v3 (`/v3/companies/{id}`). `/v3/data/review-queue` re-exports `/v3/review-queue` (alias, same shell).

---

## 4. Full inventory

**Nav column:** `V3` = `V3_DOMAIN_NAV`; `V3+` = `V3_CMD_EXTRA` only; `L` = `workspaces.ts` sidebar; `L-hub` = linked from `/admin` hub (`AdminWorkspace`); `M` = `MobileNav` only (not desktop sidebar); `child` = reachable from a list page; `N` = no product nav.

**Cmd column:** `V3` = v3 CmdK; `L` = `commands.ts`; `both`; `N`.

**Data:** from static read of `page.tsx` (and obvious wrappers). Runtime API health = **UNKNOWN**.

**Rec:** MERGE (customer uses v3) / FREEZE (keep code, hide from customer) / REMOVE (delete or stop shipping the URL).

### 4.1 v3 — 40 pages

| Path | Shell | Nav | Cmd | Data source | Counterpart | Rec |
|------|-------|-----|-----|-------------|-------------|-----|
| `/v3` | v3 | V3 | V3 | API (`executive/dashboard` + recent companies + deals) | `/dashboard` | **MERGE** (keep; customer home) |
| `/v3/companies` | v3 | V3 | V3 | API | `/companies` | **MERGE** (keep) |
| `/v3/companies/[id]` | v3 | child | N | API (company, contacts, tasks, activities) + honest empty | `/companies/[id]` | **MERGE** (keep) |
| `/v3/companies/[id]/360` | v3 | N | N | **redirect** → `/v3/companies/{id}` | `/companies/[id]/360` | **REMOVE** URL after freeze (alias only) |
| `/v3/crm` | v3 | V3 | V3 | API (opportunities) | `/opportunities`, `/pipeline` | **MERGE** (keep) |
| `/v3/crm/[id]` | v3 | child | N | API + honest empty | `/opportunities/[id]` | **MERGE** (keep) |
| `/v3/contacts` | v3 | V3 | V3 | API | `/contacts` | **MERGE** (keep) |
| `/v3/contacts/[id]` | v3 | child | N | API + honest empty | `/contacts/[id]` | **MERGE** (keep) |
| `/v3/people` | v3 | V3 | V3 | API | none (MD people) | **MERGE** (keep; hide from thin MVP nav if needed) |
| `/v3/people/[id]` | v3 | child | N | API | `/employees/[id]` (different job) | **MERGE** (keep) |
| `/v3/activities` | v3 | V3 | V3 | API | `/activities` | **MERGE** (keep) |
| `/v3/tasks` | v3 | V3 | V3 | API `/api/v1/tasks` + honest empty | `/tasks` (page **does** exist — v3 comment claiming otherwise is stale) | **MERGE** (keep) |
| `/v3/tasks/[id]` | v3 | child | N | API list-resolved (no GET `/tasks/{id}`) | none | **MERGE** (keep) |
| `/v3/proposals` | v3 | V3 | V3 | API | none | **MERGE** (keep) |
| `/v3/proposals/[id]` | v3 | child | N | API | none | **MERGE** (keep) |
| `/v3/quotes` | v3 | V3 | both | API | none | **MERGE** (keep) |
| `/v3/quotes/[id]` | v3 | child | N | API | none | **MERGE** (keep) |
| `/v3/contracts` | v3 | V3 | both | API | none | **FREEZE** in thin MVP nav; keep route |
| `/v3/contracts/[id]` | v3 | child | N | API | none | **FREEZE** with list |
| `/v3/reviews` | v3 | V3 | V3 | API | none | **FREEZE** in thin MVP nav; keep route |
| `/v3/reviews/[id]` | v3 | child | N | API | none | **FREEZE** with list |
| `/v3/approvals` | v3 | V3 | both | API | `/decisions` (related, not same) | **MERGE** (keep — HITL) |
| `/v3/approvals/[id]` | v3 | child | N | API | none | **MERGE** (keep) |
| `/v3/analytics` | v3 | V3 | V3 | API executive dashboard | `/analytics`, `/revenue`, `/forecast`, `/pipeline` | **MERGE** (keep one analytics home) |
| `/v3/sales-dashboard` | v3 | V3 | V3 | API signal-actions | `/dashboard`, `/signals` | **MERGE** (keep — NBA/actions) |
| `/v3/my-day` | v3 | V3 | V3 | API work queue | `/dashboard`, `/tasks` | **MERGE** (keep — daily queue) |
| `/v3/effectiveness` | v3 | V3 | V3 | API | none | **MERGE** (keep — MVP #9) |
| `/v3/cs` | v3 | V3 | V3 | API executive + companies | `/customer-success` | **FREEZE** in MVP nav (hide CS) |
| `/v3/admin` | v3 | V3 | V3 | API (users/roles/flags/audit) + **PreviewBadge “Not wired”** panels linking to legacy admin | `/admin` + `/admin/*` | **FREEZE** as preview; customer uses Settings |
| `/v3/settings` | v3 | V3 | V3 | API (notifications, API keys) + PreviewBadge gaps | `/settings` | **MERGE** (keep — MVP onboarding home) |
| `/v3/data` | v3 | V3 | both | API counts | none | **MERGE** (keep — MD hub) |
| `/v3/data/companies` | v3 | V3 | both | API `master-data/global-companies` | `/v3/companies` (tenant CRM vs global MD) | **MERGE** (keep; label the job) |
| `/v3/data/people` | v3 | V3 | both | API `master-data/global-people` | `/v3/people` | **MERGE** (keep; label the job) |
| `/v3/data/imports` | v3 | V3 | L | API source files | none | **MERGE** (keep) |
| `/v3/data/er` | v3 | V3 | both | API ER stats/conflicts/matches | none | **MERGE** (keep) |
| `/v3/review-queue` | v3 | V3 | L | API review-queue queries | `/v3/data/review-queue` (alias) | **MERGE** (keep — canonical) |
| `/v3/data/review-queue` | v3 | N | N | **re-export** of review-queue | `/v3/review-queue` | **REMOVE** from nav (already); keep alias 1 release then redirect-only |
| `/v3/icp` | v3 | **N (orphan)** | N | API `/api/v1/icp/profiles` | `/gtm/icp` | **MERGE** — **add to v3 nav** (MVP ICP) |
| `/v3/shell` | v3 | V3+ | V3 | **hardcoded** spec copy | none | **REMOVE** from customer CmdK (internal spec) |
| `/v3/employee` | v3 | N | N | **redirect** → `/employees/me` (**leaves v3**) | `/employees/me` | **REMOVE** or retarget to a v3 people/settings page |

### 4.2 Legacy `(dashboard)` — 78 pages

| Path | Shell | Nav | Cmd | Data source | Counterpart | Rec |
|------|-------|-----|-----|-------------|-------------|-----|
| `/dashboard` | legacy | L | L | workspace `DashboardPage` — **UNKNOWN** depth (wrapper) | `/v3` | **FREEZE** then redirect → `/v3` |
| `/companies` | legacy | L | L | API + export | `/v3/companies` | **FREEZE** → redirect |
| `/companies/[id]` | legacy | child | N | API | `/v3/companies/[id]` | **FREEZE** → redirect |
| `/companies/[id]/360` | legacy | child | N | API | `/v3/companies/[id]` (360 is alias there) | **FREEZE** → redirect |
| `/contacts` | legacy | L | N | API | `/v3/contacts` | **FREEZE** → redirect |
| `/contacts/[id]` | legacy | child | N | API | `/v3/contacts/[id]` | **FREEZE** → redirect |
| `/opportunities` | legacy | L | N | **UNKNOWN** (not opened this pass) | `/v3/crm` | **FREEZE** → redirect |
| `/opportunities/[id]` | legacy | child | N | **UNKNOWN** | `/v3/crm/[id]` | **FREEZE** → redirect |
| `/pipeline` | legacy | L | N | `PipelineWorkspace` — **UNKNOWN** | `/v3/crm` | **FREEZE** → redirect |
| `/pipeline/analytics` | legacy | N | N | API `/pipeline/analytics` | `/v3/analytics` | **FREEZE** |
| `/activities` | legacy | L | N | API | `/v3/activities` | **FREEZE** → redirect |
| `/tasks` | legacy | **N** | N | API | `/v3/tasks` | **FREEZE** → redirect |
| `/meetings` | legacy | L | N | API opportunities + meeting brief | none in v3 | **FREEZE** (post-MVP) |
| `/employees` | legacy | L | N | API | `/v3/people` (not the same: employee 360 vs MD people) | **FREEZE** — hide (MVP out-of-scope) |
| `/employees/me` | legacy | L | N | **UNKNOWN** | `/v3/employee` leak | **FREEZE** |
| `/employees/[id]` | legacy | child | N | **UNKNOWN** | none | **FREEZE** |
| `/customer-success` | legacy | L | N | `CustomerSuccessWorkspace` — API in tests | `/v3/cs` | **FREEZE** |
| `/revenue` | legacy | L | N | API revenue/forecast/kpis | `/v3/analytics` | **FREEZE** → redirect |
| `/revenue/territories` | legacy | N | N | API + **honest empty** (no Aramco/SABIC demo) | `/studio/territories` | **FREEZE** |
| `/revenue/quotas` | legacy | N | N | API + **honest empty** (no quota API → no invented reps) | none | **FREEZE** |
| `/forecast` | legacy | L | N | API `/forecast` | `/v3/analytics` | **FREEZE** → redirect |
| `/analytics` | legacy | L | N | API executive dashboard | `/v3/analytics` | **FREEZE** → redirect |
| `/analytics/sales` | legacy | N | N | API revenue + pipeline | `/v3/analytics` | **FREEZE** |
| `/analytics/revenue` | legacy | N | N | API | `/v3/analytics` | **FREEZE** |
| `/analytics/pipeline` | legacy | N | N | API | `/v3/analytics` | **FREEZE** |
| `/analytics/employees` | legacy | N | N | API + honest empty trend | none | **FREEZE** |
| `/analytics/automation` | legacy | N | N | API `/workflows/analytics` | `/automation/analytics` | **FREEZE** |
| `/analytics/reports/builder` | legacy | N | N | **honest empty preview** (no random metrics) | none | **FREEZE** |
| `/search` | legacy | L | L | API search | none in v3 (topbar search trigger only) | **FREEZE** — later embed in v3 topbar |
| `/search/analytics` | legacy | N | N | API | none | **FREEZE** |
| `/signals` | legacy | L | N | API catalog/events/subs | `/v3/sales-dashboard` | **FREEZE** (v3 consumes actions; catalog stays internal) |
| `/monitoring` | legacy | L | N | API `/monitoring/metrics` | none | **FREEZE** (ops) |
| `/rules` | legacy | L | N | `RulesWorkspace` — **UNKNOWN** | none | **FREEZE** |
| `/graph` | legacy | L | N | API `/graph/*` + honest empty; **no getDemoData** | `/knowledge` (same graph API) | **FREEZE** — ADR-108 KG offline; do not sell |
| `/knowledge` | legacy | **N** | N | API `/graph/*` + honest empty | `/graph` | **FREEZE** / later **REMOVE** (duplicate of graph) |
| `/knowledge/connectors` | legacy | **N** | N | API connectors | `/integrations` | **FREEZE** |
| `/rag` | legacy | **M only** | N | `RagWorkspace` — API | none in v3 | **FREEZE** — not in desktop sidebar |
| `/ai` | legacy | **N** | N | API `/ai/prompts`, `/ai/generate` | `/studio/prompt-library`, v3 Ask AI popup | **FREEZE** |
| `/copilot` | legacy | **N** | action (toggle event) | `CopilotPanel` + flag gate | v3 Ask AI popup | **FREEZE** — customer AI = v3 popup |
| `/copilot/telemetry` | legacy | **N** | N | API `/copilot/telemetry` | none | **FREEZE** (ops) |
| `/decisions` | legacy | L | N | API Decision Center (`decisionQueries`) | `/v3/approvals` (HITL, different contract) | **FREEZE** — do not sell as GA AI |
| `/decisions/templates` | legacy | N | N | **UNKNOWN** | none | **FREEZE** |
| `/gtm` | legacy | L | L | hub copy + “Not Production GO” | `/v3/icp` (partial) | **FREEZE** entire GTM pack (MVP out) |
| `/gtm/icp` | legacy | L | L | API + fixture honesty banner | `/v3/icp` | **FREEZE** — **v3 is the merge target** |
| `/gtm/market-sizing` | legacy | L | L | fixture / in-memory universe | none | **FREEZE** |
| `/gtm/lead-discovery` | legacy | L | L | fixture | none | **FREEZE** |
| `/gtm/enrichment` | legacy | L | L | FakeEnrichment providers | none | **FREEZE** |
| `/gtm/website-intelligence` | legacy | L | L | fixture analyzer | none | **FREEZE** |
| `/gtm/outreach` | legacy | L | L | fixture drafts, `draft_only` | none | **FREEZE** |
| `/gtm/verification` | legacy | L | L | `fake_verify` | none | **FREEZE** |
| `/gtm/lookalikes` | legacy | L | L | CI fixtures, not live ML | none | **FREEZE** |
| `/gtm/sequences` | legacy | L | L | tip sequences | none | **FREEZE** |
| `/studio/custom-fields` | legacy | L | L | tip API; “Not Production GO” | none | **FREEZE** |
| `/studio/scoring` | legacy | L | L | in-memory | none | **FREEZE** |
| `/studio/permissions` | legacy | L | L | tip API | none | **FREEZE** |
| `/studio/workflows` | legacy | L | L | tip API | `/automation` | **FREEZE** |
| `/studio/notifications` | legacy | L | L | tip API | `/v3/settings` (partial) | **FREEZE** |
| `/studio/branding` | legacy | L | L | tip API | none | **FREEZE** |
| `/studio/territories` | legacy | L | L | in-memory over CAP-017 | `/revenue/territories` | **FREEZE** |
| `/studio/ai-model-tiers` | legacy | L | L | GET-only catalog | `/v3/admin` | **FREEZE** |
| `/studio/prompt-library` | legacy | L | L | tip API | `/ai` | **FREEZE** |
| `/studio/ai-policies` | legacy | L | L | tip API | none | **FREEZE** |
| `/studio/ai-memory` | legacy | L | L | tip API; Decision package STUB noted | none | **FREEZE** |
| `/settings` | legacy | L | L | API | `/v3/settings` | **FREEZE** → redirect |
| `/admin` | legacy | L | L | `AdminWorkspace` hub | `/v3/admin` | **FREEZE** (ops) |
| `/admin/tenants` | legacy | L-hub | N | API | none | **FREEZE** |
| `/admin/billing` | legacy | L-hub | N | API; “Not Production GO” | none | **FREEZE** |
| `/admin/flags` | legacy | L-hub | N | API | `/v3/admin` | **FREEZE** |
| `/admin/config` | legacy | L-hub | N | YAML editor UI | none | **FREEZE** |
| `/admin/audit` | legacy | L-hub | N | API + export | `/v3/admin` | **FREEZE** |
| `/admin/integrations` | legacy | L-hub | N | owner/integrations; “Not Production GO” | `/integrations` | **FREEZE** |
| `/integrations` | legacy | L | L (incl. 7 step deep-links) | Hub HTTP; “Not Production GO” | `/v3/settings` Google panel | **FREEZE** — Gmail OAuth is MVP via settings, not this studio |
| `/marketplace` | legacy | N | N | CAP-036 **plugin stub** | `/marketplace/listings` | **REMOVE** from customer paths (stub) |
| `/marketplace/listings` | legacy | L | L | tip memory catalog | `/marketplace` stub | **FREEZE** (MVP out) |
| `/marketplace/[pluginId]/config` | legacy | child | N | stub config | none | **REMOVE** with stub |
| `/automation` | legacy | M | N | `AutomationWorkspace` | `/studio/workflows` | **FREEZE** |
| `/automation/analytics` | legacy | N | N | API `/workflows/analytics` | `/analytics/automation` | **FREEZE** |
| `/automation/workflows/new` | legacy | N | N | local builder form (hardcoded step UI) | `/studio/workflows` | **FREEZE** |

### 4.3 Auth + other — 5 pages

| Path | Shell | Nav | Cmd | Data source | Counterpart | Rec |
|------|-------|-----|-----|-------------|-------------|-----|
| `/` | none | N | N | **hardcoded** splash → login/register | none | **KEEP** (entry) |
| `/login` | auth | N | N | API login; next=`/v3` | none | **KEEP** |
| `/register` | auth | N | N | API register; **success → `/dashboard`** | `/login` | **KEEP** but **P0 retarget → `/v3`** |
| `/admin/login` | auth | N | N | API owner login | `/login` | **KEEP** (ops) |
| `/system` | other | N | N | API `/api/v1/version` + FE build env | none | **KEEP** (ops/build-parity) |

---

## 5. Overlap map — same job, two URLs

**FACT** unless marked otherwise.

| Job a customer thinks they are doing | v3 URL | Legacy URL(s) | Winner | Action |
|--------------------------------------|--------|---------------|--------|--------|
| Home / “my workspace” | `/v3` | `/dashboard` | v3 | Redirect legacy |
| Companies (tenant CRM) | `/v3/companies` + `[id]` | `/companies` + `[id]` + `[id]/360` | v3 | Redirect; 360 already folded on v3 |
| Contacts | `/v3/contacts` | `/contacts` | v3 | Redirect |
| Deals / pipeline | `/v3/crm` | `/opportunities`, `/pipeline` | v3 | Redirect both |
| Activities | `/v3/activities` | `/activities` | v3 | Redirect |
| Tasks | `/v3/tasks` | `/tasks` (orphan in legacy nav) | v3 | Redirect |
| Analytics / forecast / revenue | `/v3/analytics` | `/analytics/*`, `/revenue`, `/forecast` | v3 | Redirect hubs; freeze sub-cubes |
| Customer success | `/v3/cs` | `/customer-success` | v3 (hide in MVP) | Freeze both in nav |
| Settings | `/v3/settings` | `/settings` | v3 | Redirect |
| Admin / flags / audit | `/v3/admin` (partial + preview) | `/admin` + 6 subpages | legacy for ops; v3 is preview | Freeze legacy; do not sell v3 admin as complete |
| ICP | `/v3/icp` (**not in nav**) | `/gtm/icp` (**in nav + CmdK**) | v3 API page | **P0: put v3 ICP in nav**; freeze GTM ICP |
| Approvals / decisions | `/v3/approvals` (HITL FSM) | `/decisions` (Decision Center) | **different products** | Do not merge blindly; customer HITL = v3 |
| Signals / daily actions | `/v3/sales-dashboard` | `/signals` | v3 for seller; catalog stays legacy | Freeze catalog |
| People vs employees | `/v3/people` (MD) | `/employees*` (employee 360) | different | Freeze employees; do not auto-redirect |
| CRM companies vs MD companies | `/v3/companies` vs `/v3/data/companies` | — | both stay | Label: “Accounts” vs “Global master data” |
| Graph / knowledge | — | `/graph` ≈ `/knowledge` | neither for MVP | Freeze; ADR-108 offline |
| Workflows | — | `/studio/workflows` ≈ `/automation` | studio | Freeze both |
| AI chat | v3 Ask AI popup | `/copilot`, `/ai` | v3 popup | Freeze pages |
| Review queue | `/v3/review-queue` | `/v3/data/review-queue` (alias) | first | Keep alias one release |
| Marketplace | — | `/marketplace` stub vs `/marketplace/listings` | listings (still not MVP) | Remove stub URL |

**INFERENCE:** The worst customer confusion is **Companies / CRM / Analytics / Settings** — same nouns, two chromes, two command palettes.

---

## 6. Orphans (page exists, no product sidebar)

### 6.1 v3 orphans

| Path | Why it matters |
|------|----------------|
| `/v3/icp` | **P0 product gap.** Live ICP API UI, not in `V3_DOMAIN_NAV` or either CmdK. Customers cannot discover the MVP ICP surface unless they type the URL. |
| `/v3/employee` | Cross-shell redirect. Bookmark trap. |
| `/v3/shell` | Internal spec; only v3 CmdK extra. |
| `/v3/data/review-queue` | Alias; canonical is `/v3/review-queue`. |
| `/v3/companies/[id]/360` | Redirect alias. |
| All `[id]` detail pages | Expected children — not orphans in the product sense. |

### 6.2 Legacy orphans (not in `workspaces.ts`)

`/tasks`, `/knowledge`, `/knowledge/connectors`, `/ai`, `/copilot`, `/copilot/telemetry`, `/marketplace` (stub), `/marketplace/[pluginId]/config`, `/automation`, `/automation/analytics`, `/automation/workflows/new`, `/revenue/territories`, `/revenue/quotas`, `/pipeline/analytics`, `/search/analytics`, `/analytics/{sales,revenue,pipeline,employees,automation,reports/builder}`, `/decisions/templates`.

`/rag` is **desktop-orphan** but **mobile-nav linked**.

Admin subpages are **hub-linked** from `/admin`, not sidebar items — treat as ops, not orphans.

---

## 7. Dead links, placeholders, mock remnants

### 7.1 Dead or misleading links — FACT

| Issue | Evidence | Severity |
|-------|----------|----------|
| Register lands on **legacy** `/dashboard` while login lands on **`/v3`** | `register/page.tsx` `router.push("/dashboard")` vs login `fallback = "/v3"` | **P0** — first-run shell split |
| Legacy CmdK “الشركات” / “لوحة المعلومات” go to `/companies` and `/dashboard`, not v3 | `commands.ts` | **P0** if customer can open legacy CmdK |
| `/v3/employee` exits v3 | `redirect("/employees/me")` | **P1** |
| v3 tasks copy: “There is no dedicated legacy `/tasks` page” | False — `(dashboard)/tasks/page.tsx` exists | Honesty bug (docs-in-UI) |
| `/nba` page | **No** `page.tsx`. i18n has no `/nba` href this pass. PAGE_MAP (2026-07-22) is stale. | Not a live dead link |
| Dual review-queue URLs | Both resolve (alias). Not dead. | P2 cleanup |
| v3 admin “Not wired — no invented controls” + links to `/admin/*` | `v3/admin/page.tsx` `PreviewBadge` | Honest placeholder, not a 404 |

### 7.2 Placeholders / honesty stamps — FACT

- **v3:** `/v3/shell` (spec); `/v3/admin` and `/v3/settings` PreviewBadge gaps; `/v3/companies/[id]/360` and `/v3/employee` redirects.
- **GTM (10 pages):** fixture / FakeEnrichment / `draft_only` / “Not Production GO”.
- **Studio (11 pages):** “Not Production GO / RAG GO”; several in-memory.
- **Marketplace `/marketplace`:** CAP-036 plugin stub (distinct from listings).
- **Revenue quotas/territories:** honest empty (demo names removed).
- **Graph / knowledge:** demo loader removed.

### 7.3 `getDemoData` / mock remnants — FACT

**Zero** `getDemoData` in `salesos/frontend/src` production files. Residual `mockData` is test-only (`CustomerSuccessWorkspace.test.tsx`, tour tests).

---

## 8. What a customer should see in MVP

Aligned with `project-audit/06_MVP_SCOPE.md` (input only) + disk.

**RECOMMENDATION — customer chrome = v3 only. ~12 nav items, not 25.**

| Show | Route | Why |
|------|-------|-----|
| Home | `/v3` | Already login default |
| Companies | `/v3/companies` | Product core |
| Contacts | `/v3/contacts` | Product core |
| People | `/v3/people` | Optional; hide if MD confuses the tenant |
| CRM | `/v3/crm` | Deals + pipeline |
| Activities | `/v3/activities` | Core loop |
| Tasks | `/v3/tasks` | Core loop |
| Approvals | `/v3/approvals` | HITL |
| Sales Dashboard | `/v3/sales-dashboard` | Signals → actions |
| My Day | `/v3/my-day` | Work queue |
| Effectiveness | `/v3/effectiveness` | MVP #9 |
| ICP | `/v3/icp` | **Add to nav** — today orphan |
| Data + Review Queue | `/v3/data`, `/v3/review-queue` | Master data for that tenant |
| Settings | `/v3/settings` | Onboarding / Gmail |
| Quotes / Proposals | `/v3/quotes`, `/v3/proposals` | If the design partner issues offers |

**Hide from customer nav (routes may stay):** CS, Admin, Contracts, Reviews, Shell spec, Employee, all legacy URLs, entire GTM + Studio + Marketplace + Graph/Knowledge/RAG/Copilot page/Decision Center/Employees.

**Ask AI:** v3 popup only. Do not send them to `/copilot`.

**Auth:** `/`, `/login`, `/register` → always `/v3`. Owner `/admin/login` stays for platform ops.

---

## 9. Cluster recommendations (MERGE / FREEZE / REMOVE)

| Cluster | Pages (approx.) | Decision | Notes |
|---------|-----------------|----------|-------|
| v3 Product Core (companies, crm, contacts, activities, tasks, proposals, quotes, approvals) | ~20 | **MERGE — keep v3** | Redirect legacy twins |
| v3 daily intel (home, sales-dashboard, my-day, effectiveness, analytics) | 5 | **MERGE — keep v3** | One analytics URL |
| v3 Master Data (data/*, review-queue) | 7 | **MERGE — keep v3** | Collapse alias |
| v3 ICP | 1 | **MERGE — promote into nav** | Freeze `/gtm/icp` |
| v3 CS / contracts / reviews / admin preview | ~8 | **FREEZE in nav** | Routes stay for later |
| v3 shell spec + employee redirect + 360 alias | 3 | **REMOVE** from customer IA | Keep 360 redirect internally if bookmarks exist |
| Legacy CRM twins | ~15 | **FREEZE → redirect to v3** | Do not edit features; wrap with banner then 308 |
| Legacy GTM | 10 | **FREEZE** | Fixture pack; out of MVP |
| Legacy Studio | 11 | **FREEZE** | Enterprise config; post-PMF |
| Legacy Admin + integrations + billing | ~9 | **FREEZE** | Ops / owner |
| Legacy AI/KG/RAG/Decisions/Copilot | ~8 | **FREEZE** | Honesty: provider DEV-ONLY; KG offline |
| Legacy marketplace stub | 2 | **REMOVE** from IA | Keep listings frozen |
| Graph vs Knowledge | 2 | **FREEZE**; treat as 1 job | Knowledge is unofficial duplicate |
| Auth + `/system` | 5 | **KEEP** | Fix register target |

---

## 10. Actions

### P0 — do before a design-partner sits down

1. **One post-auth landing:** change register success from `/dashboard` to `/v3`. **RECOMMENDATION** (code change is out of this memo’s write scope).
2. **Put `/v3/icp` in `V3_DOMAIN_NAV` + v3 CmdK.** Orphan today. MVP requires ICP.
3. **Stop selling / linking the legacy shell** to customers: banner on `(dashboard)/layout` (“Internal / previous UI”) or hide workspace switcher. **RECOMMENDATION.**
4. **Do not use `commands.ts` as the customer palette.** Either stop mounting it on paths a customer can reach, or retarget `go.dashboard` / `go.companies` / `go.settings` / `go.admin` to `/v3*`. **RECOMMENDATION.**
5. **Keep login → `/v3`.** Already FACT. Do not revert.

### P1 — first sprint after P0

1. Redirect overlapping legacy hubs → v3 (`/companies` → `/v3/companies`, `/opportunities` → `/v3/crm`, `/dashboard` → `/v3`, `/contacts` → `/v3/contacts`, `/activities` → `/v3/activities`, `/tasks` → `/v3/tasks`, `/analytics` + `/revenue` + `/forecast` → `/v3/analytics`, `/settings` → `/v3/settings`).
2. Retarget or delete `/v3/employee` so it never opens legacy chrome.
3. Prune v3 sidebar to the MVP list in §8 (hide CS, Admin, maybe Contracts/Reviews).
4. Label `/v3/companies` vs `/v3/data/companies` in the UI (“Accounts” vs “Master data”).
5. Remove `/v3/shell` from customer CmdK.

### P2 — cleanup

1. Delete or 308 `/v3/data/review-queue` and `/v3/companies/[id]/360` after bookmark window.
2. Collapse `/knowledge` into `/graph` or remove both from IA (KG offline).
3. Remove CAP-036 `/marketplace` stub from routable IA.
4. Fix v3 tasks “no legacy /tasks page” copy.
5. Reconcile stale counts in `project-audit` (nav 24→25; palette 35→51+26). **Out of this file’s write scope.**

---

## 11. What this memo did **not** prove

| Item | Label |
|------|-------|
| Live HTTP 200/401/500 per route | **UNKNOWN** — not probed |
| Browser QA / visual dual-chrome | **not validated** |
| Whether production Vercel currently serves all 123 files | **UNKNOWN** |
| Backend completeness of `/v3/contracts` | **UNKNOWN** (route exists; audit already PARTIAL) |
| Wrapper workspaces (`DashboardPage`, `PipelineWorkspace`, `AutomationWorkspace`, `RulesWorkspace`, `RagWorkspace`) data path | **UNKNOWN** beyond import + sibling API pages |
| i18n keys still pointing at retired URLs beyond `/nba` | **UNKNOWN** (spot-check only) |

---

## 12. Evidence index

| Artifact | Role |
|----------|------|
| `salesos/frontend/src/app/**/page.tsx` | 123 routes (PowerShell listing) |
| `salesos/frontend/src/components/v3/nav.ts` | 25 `V3_DOMAIN_NAV` + 1 `V3_CMD_EXTRA` |
| `salesos/frontend/src/components/v3/V3CommandPalette.tsx` | v3 CmdK = nav ∪ extra |
| `salesos/frontend/src/lib/commands.ts` | 51 legacy-biased commands |
| `salesos/frontend/src/lib/workspaces.ts` | 44 legacy sidebar items |
| `salesos/frontend/src/components/foundation/MobileNav.tsx` | mobile subset + `/rag` + `/automation` |
| `salesos/frontend/src/app/(auth)/login/page.tsx` | default `/v3` |
| `salesos/frontend/src/app/(auth)/register/page.tsx` | default `/dashboard` |
| `project-audit/11_CAPABILITY_MATRIX.md` §1.12 | claimed 40 / 78 / 24-nav |
| `project-audit/01_CURRENT_STATE.md` §5 | dual-shell flag + C-06 |
| `project-audit/06_MVP_SCOPE.md` | v3-only MVP; park legacy 78 |

---

*Read-only inventory. No product code edited. No git writes. Validation: **light validated** (static). Not a production GO claim.*
