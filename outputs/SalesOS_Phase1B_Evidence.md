# SalesOS Frontend — Phase 1B Structural Evidence Pack

**Purpose:** deeper, cited evidence to support the Phase 1B strategic design-vision doc. Builds on `/sessions/.../outputs/SalesOS_Phase1_Audit.md`. All counts below were produced by direct `grep -rl`/`find` runs against the checked-out tree at `salesos/frontend/` — commands are described inline so counts are reproducible, not invented.

---

## 1. Component Variant Counts

### Card
Definition files (real components, not usages):
| File | Notes | Import/usage count |
|---|---|---|
| `packages/ui/src/card.tsx` | Canonical. `cva`-based: variants `default/dark/bordered`, `padding sm/md/lg`, `accent none/orange`. Exports `Card`, `CardHeader`, `CardContent`, `CardFooter`. | **73 files** import `Card`-family from `@salesos/ui` (`grep -rl "Card" src --include=*.tsx \| xargs grep -l "@salesos/ui"`) |
| `src/components/foundation/card.tsx` | 2-line re-export shim of the above (`export { Card, CardHeader, CardContent, CardFooter } from "@salesos/ui"`) — not a competing implementation, confirms prior audit's finding | 0 direct importers found (dead re-export path) |
| `src/features/dashboard/widgets/widget-card.tsx` | Bespoke dashboard `WidgetCard` — builds its own shell via **inline styles** (`borderRadius: "0.75rem"`, `padding: "0.75rem 1rem"`), not the `Card` primitive; carries an active `/* eslint-disable custom-rules/no-hardcoded-colors */` suppression | **8 files** import it (`grep -rl "widget-card" src`) |
| `src/features/dashboard/widgets/executive-summary/ExecutiveSummaryCards.tsx` | Bespoke card grid rendered directly under the dashboard header | 2 importers |
| `src/features/customer-success/widgets/customer-success/HealthScoreCard.tsx` | Feature-specific card | 1 external importer (`CustomerSuccessView.tsx`) + own test |
| `src/features/revenue-execution/widgets/nba-widget/RecommendationCard.tsx` | Feature-specific card | 1 external importer (`NBAWidgetView.tsx`) + own test |
| `src/features/search/components/SearchResultCard.tsx` | Feature-specific card | 3 external importers (`CommandBarResults.tsx`, `QuickOverlay.tsx`, `SearchPage.tsx`) + own test |
| `src/app/v3/_components/metric-cards.tsx` | v3-only metric card, independent of `@salesos/ui` | Confined to `v3/*` (analytics, cs, and root v3 page) |

**Bottom line:** one true canonical `Card` primitive (73 importers — genuinely dominant), but **7 distinct bespoke "card" implementations** exist alongside it for specific widget types, the most consequential being `widget-card.tsx` (the entire dashboard grid's visual shell bypasses the design-system `Card`, using inline styles instead of the `cva` variant system). This is a smaller fragmentation story than the "14 variants" framing implies for the raw `Card` primitive — the real risk is that dashboard's highest-visibility surface (13 widgets) doesn't consume the primitive at all.

### Button
| File | Notes |
|---|---|
| `packages/ui/src/button.tsx` | Only real named `Button` component file found (`find src packages -iname "*button*.tsx"`) |
| `src/features/demo/DemoResetButton.tsx` | Single-purpose demo utility button, not a primitive variant |

No competing `Button` primitive exists — this is the cleanest primitive in the system. (Visual inconsistency instead shows up as **raw `<button>` HTML** bypassing the component — see Forms section below, e.g. `revenue/quotas/page.tsx`.)

### Modal / Dialog
| File | Notes |
|---|---|
| `packages/ui/src/modal.tsx` | Only named `Modal`/`Dialog` component file (`find src packages -iname "*modal*.tsx" -o -iname "*dialog*.tsx"`). Proper Radix `Dialog.Root/Trigger/Portal/Overlay/Content/Close`. | **16 files** in `src` import `Modal` and reference `@salesos/ui` together |
| Hand-rolled `fixed inset-0` overlays (not using `Modal`) | **14 files** confirmed via `grep -rl "fixed inset-0" src`: `(dashboard)/layout.tsx` (mobile sidebar, legitimate drawer use), `(dashboard)/revenue/quotas/page.tsx`, `(dashboard)/revenue/territories/page.tsx`, `components/command-bar.tsx`, `components/foundation/MobileNav.tsx`, `components/guidance/tour/TourOverlay.tsx`, `components/lazy-exports.tsx`, `components/pipeline-kanban.tsx`, `components/search-panel.tsx`, `components/v3/V3AiPopup.tsx`, `components/v3/V3CommandPalette.tsx`, `features/automation/widgets/workflow-builder/WorkflowBuilderView.tsx`, `features/rag/widgets/rag-documents/RagDocumentManagerView.tsx`, `features/search/command-bar/CommandBar.tsx`, `features/search/quick-overlay/QuickOverlay.tsx` |

**Bottom line:** 1 canonical Modal (16 real "create/edit record" consumers) vs. **~12 non-drawer hand-rolled overlays** (excluding the two legitimate slide-in drawers: dashboard layout's mobile sidebar and `MobileNav`). Of those 12, only 3 (`command-bar.tsx`, `search-panel.tsx`, `V3CommandPalette.tsx`) use the app's own `useFocusTrap` hook — the rest have no focus trap (ties directly to the Phase 1 a11y findings in §11).

### Badge / Tag
| File | Import count |
|---|---|
| `packages/ui/src/badge.tsx` | **68 files** import `Badge` from `@salesos/ui` |
| `src/components/ai-insights/ConfidenceBadge.tsx` | Feature-specific badge variant |
| `src/components/ai/ExperimentalAiBadge.tsx` | Feature-specific badge variant |
| `src/features/demo/DemoBadge.tsx` | Feature-specific badge variant |
| `src/features/search/components/SearchBadge.tsx` | Feature-specific badge variant |
| Ad hoc inline badges (not using any Badge component) | Numerous — e.g. Company 360's `<span className="rounded bg-purple-100 ... text-purple-700">360</span>` (raw Tailwind stock-purple, not a token), status pills like `<span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 ...">{company.status}</span>` |

**Bottom line:** 1 dominant canonical Badge (68 importers) + 4 named specialty variants + an unquantified but real volume of raw inline `<span>` "badge" markup on high-traffic pages like Company 360 that bypass the component and the token system simultaneously.

### Table
| File | Notes |
|---|---|
| `packages/ui/src/data-table.tsx` | 327-line `@tanstack/react-table` wrapper — sortable/paginated/filterable | 5 direct app consumers per prior audit (`companies/page.tsx`, `companies/[id]/360/page.tsx`, `decisions/page.tsx`, `decisions/templates/page.tsx`, `employees/page.tsx`) |
| `packages/ui/src/table.tsx` | 84-line plain table primitives (no sort/filter/paginate) | Used inside `DataTable` and elsewhere as raw building blocks |
| Raw hand-coded `<table>` HTML | **28 files** confirmed (`grep -rl "<table" src`) — matches and confirms the Phase 1 audit's §17 count exactly. Includes `admin/audit`, `admin/tenants`, most `analytics/*`, `contacts/page.tsx` (imports `@salesos/ui` elsewhere but still hand-rolls a `<table>` at line 418), `copilot/telemetry`, `pipeline/analytics`, `revenue/quotas`, `search/analytics`, and essentially the entire `v3/` tree |

**Bottom line:** the sortable/paginated `DataTable` pattern only reaches 5 of 33 table-bearing screens; 28 screens (85% of table surfaces) render static, unsortable, unpaginated, non-virtualized markup — a much bigger practical inconsistency than the Card/Badge fragmentation.

### Empty State
| File | Notes |
|---|---|
| `packages/ui/src/empty-state.tsx` | Canonical, generic, the only axe-tested component in the whole a11y suite | Widely imported (icon+title+description+optional action props) |
| `src/components/guidance/empty-states/EmptyState.tsx` | A second wrapper living in `guidance/empty-states/`, alongside... |
| `src/components/guidance/empty-states/{EmptyAnalytics,EmptyMeetings,EmptyNBA,EmptyPipeline,EmptyRAG,EmptyWorkflows}.tsx` | 6 feature-specific pre-configured empty states |
| `src/features/search/components/SearchEmpty.tsx` | Search-specific empty state |

**Bottom line:** 1 canonical `EmptyState` + a `guidance/empty-states` family of 7 (including its own generic `EmptyState.tsx`) + 1 more in `features/search` = **9 distinct empty-state files**. Company 360 (the flagship record page) does **not** consistently use any of them for its 7+ tab-panel empty conditions — it uses `@salesos/ui`'s `EmptyState` directly in most tabs but falls back to a `showSampleData` toggle that renders **fabricated Arabic demo data** (fake contacts, fake deals, fake documents, fake signals — see §3 below) instead of a true empty state in the default view.

### Loading / Skeleton
| File | Notes |
|---|---|
| `packages/ui/src/skeleton.tsx` | Canonical | **33 files** import `Skeleton` from `@salesos/ui` |
| `src/components/skeleton.tsx` | A second, fuller implementation (99 lines, `variant: "text"\|"title"\|"avatar"\|"card"\|"list"`, `SkeletonPulse` sub-component, `motion-reduce:animate-none` support) — **confirmed zero importers anywhere in `src`** via `grep -rn "components/skeleton"` (only self-matches) | **0 importers — fully dead code**, more feature-complete than the one actually in use |
| Plain `<Spinner>` / raw loading text (not Skeleton at all) | Confirmed on Contacts list ("no Skeleton"), Opportunities Kanban (plain text `{t("common.loading")}`), Admin panels (hardcoded Arabic "جاري التحميل..." outside `t()`) — per Phase 1 §15, re-confirmed here |

**Bottom line:** the duplicate local `Skeleton` is not just redundant — it's strictly better-designed (motion-reduce support, 5 named variants) than the one actually wired up, and nobody uses it.

---

## 2. Dashboard Page Structure (`(dashboard)/dashboard/page.tsx` → `src/features/dashboard/_layout/dashboard-page.tsx`)

Render order, top to bottom:
1. Header row: `<h1>{t("dashboard.title")}</h1>` + subtitle + `QuickActionsBar` (right-aligned)
2. `MorningBriefWidget`
3. `ExecutiveSummaryCards`
4. `DashboardMetricsHeader` (5 metric cards + its own internal `QuickActions` — a second action bar, duplicating "New Company"/"Search" per Phase 1 §10)
5. `DashboardGrid` — 13 registry-driven widgets, in this exact order: **Mission Center, Decision Queue, Intelligence Feed, AI Brief, Market Pulse, Recent Activity, Pipeline, Company Health, Company Engagement, Email Intelligence, Calendar Intelligence, Follow-up Center, Company Scoring**

**Widget size/prominence** — from `src/features/dashboard/_registry/widget-config.ts` (`gridColumn`/`minHeight`, 12-column-equivalent grid where columns=6 base but spans are literal grid-column counts):

| Widget | gridColumn | minHeight | Relative prominence |
|---|---|---|---|
| Intelligence Feed | span 4 | 400px | **Largest (tied)** |
| Follow-up Center | span 4 | 400px | **Largest (tied)** |
| Pipeline | span 4 | 350px | Large |
| Company Engagement | span 4 | 280px | Large footprint, shorter |
| Email Intelligence | span 4 | 320px | Large |
| Calendar Intelligence | span 4 | 320px | Large |
| Company Scoring | span 4 | 320px | Large |
| Decision Queue | span 3 | 320px | Medium |
| Market Pulse | span 3 | 300px | Medium |
| Recent Activity | span 3 | 300px | Medium |
| Company Health | span 3 | 300px | Medium |
| Mission Center | span 3 | 200px | Medium footprint, short |
| AI Brief | span 2 | 200px | **Smallest** |

**Key structural finding:** the widget most likely to catch the eye first by DOM order + size is **Intelligence Feed** (4th in render order among widgets, tied-largest at span-4/400px), not the literally-first widget (**Mission Center**, which is span-3/200px — one of the smallest). "First in the list" and "most prominent visually" are two different widgets — worth flagging for the design-vision doc's "what does the user see first" analysis.

**Grid mechanism:** `DashboardGrid` (`src/features/dashboard/_layout/dashboard-grid.tsx`) implements its own responsive breakpoints via an **inline `<style>` tag injected into the JSX** (not Tailwind classes, not the existing `.widget-grid` class in `globals.css`) — a third parallel responsive-grid strategy, confirming/extending Phase 1 §12's finding about widgets bypassing `.widget-grid`.

**Loading/Error:** `DashboardLoading` (config-driven skeleton) / `role="alert"` panel with retry button — confirmed as the best-built pattern in the app (Phase 1 §9/§15 reconfirmed).

---

## 3. Company 360 Page Structure (`(dashboard)/companies/[id]/360/page.tsx`)

Render order, top to bottom:
1. `Breadcrumbs` (Companies → [Company Name] → "360") — the **only page in the app** with breadcrumbs (reconfirms Phase 1 §4)
2. Identity header card: 56px icon chip → company name (`text-xl font-bold`) + a raw `bg-purple-100`/`text-purple-700` "360" pill badge (stock Tailwind purple, not a design token) → CR number/city/status row → `HealthScoreRing` (custom inline SVG donut, top-right, largest single visual element in the header at 84×84px)
3. A standalone **"عرض بيانات تجريبية" (Show sample/demo data) toggle button** — a full-width bar by itself, sitting between the header and the tab bar
4. Quick Actions row (6 icon-labeled links: Add Contact, New Deal, Add Note, Schedule Meeting, Send Email, Log Call)
5. `Tabs` — 5 tabs in this order: **Overview, People, Deal Room, Activity, More**
6. Tab content (Overview shown by default): 4 `MetricBox` cards (Revenue/Active Contracts/Contacts/Opportunities) in a `grid-cols-2 md:grid-cols-4`, then a 2-column `lg:grid-cols-2` row with `DecisionPlatformPanel` + a "Financial & Enrichment Data" `Card` containing a `DataTable`

**Notable finding — fabricated demo data:** the `showSampleData` state toggle, when enabled, renders **hardcoded fictional Arabic content** directly in production JSX instead of live API data — fake contacts (e.g. "أحمد محمد", "sara@example.com"), fake deals ("عقد خدمات استشارية" — 450,000 ر.س), fake documents, fake buying signals. This is not a Storybook fixture or dev-only flag — it's a `useState` toggle button rendered to every real user on every real company record (lines 397–404, 539–557, 653–671, 691–706, 727–751, 779–793, 812–829 of `companies/[id]/360/page.tsx`). This is a material finding for the design-vision doc: the "flagship" record-intelligence view can silently show fake data next to real header data.

**Visual inconsistency within the same file:** the page carries an active `/* eslint-disable custom-rules/no-tailwind-color-classes */` suppression at line 2, and mixes token-driven `Card`/`bg-[var(--...)]` classes with raw Tailwind `bg-purple-100`, `bg-red-100`/`text-red-700`, `bg-yellow-100`, `bg-green-100` for priority pills inside the Deal Room tab (lines 744–747) — a different "success green"/"danger red" than the token system's `success-*`/`danger-*` classes used two lines away in the same component.

---

## 4. Employee 360 Page Structure (`(dashboard)/employees/[id]/page.tsx` → `src/components/employee-360-page.tsx`)

Render order:
1. A single "← Back" link (`ArrowRight` icon, RTL-aware) — **no breadcrumbs**, no identity header card, no health-ring hero (much leaner opening than Company 360)
2. `Employee360Page` component: `Tabs` with 5 tabs in order — **Overview, Signals, Scoring, Timeline, Performance**
3. Each tab body is `lazy()`-loaded via `React.lazy`/`Suspense`, and only mounted once visited (`visitedTabs` Set) — genuinely more performant than Company 360, which renders all tab content eagerly

**Structural contrast with Company 360:** no hero header, no quick-actions bar, no demo-data toggle, no breadcrumbs, no raw Tailwind color leaks found in this file. This is the cleanest, most consistent detail-page pattern in the app and should likely be the template Phase 1B recommends generalizing to Company 360 (and Opportunity Detail), not the other way around.

---

## 5. Settings Page Structure (`(dashboard)/settings/page.tsx`)

Render order:
1. `<h1 className="text-2xl font-bold">{t("settings.title")}</h1>`
2. Layout: a **vertical left-rail tab list** (`TabsList className="hidden w-56 shrink-0 sm:flex sm:flex-col ..."`) — structurally different from the horizontal pill-tab pattern used on Company 360 and Employee 360
3. 5 tabs in order: **Profile, Security, Notifications, API Keys, Data** (`TAB_KEYS` order: profile → security → notifications → api → data)
4. Profile tab: `Input` components used with a built-in `label` prop (`<Input label={t("settings.name_en")} />`) — **different label pattern** than Companies' create modal, which pairs a separate `<label>` element with `<Input>` (see §9)
5. Security tab: password change form, same `useState`-based pattern, includes manual `passwordError` string state (no schema validation)
6. Notifications / API Keys / Data tabs follow

**Structural finding:** Settings is the third distinct "detail page shell" pattern in the app (vertical rail tabs) alongside Company/Employee 360's horizontal pill tabs — a third tab-navigation visual language for conceptually similar "tabbed record/config view" screens.

---

## 6. Search Experience Structure

**Confirmed live in the production route tree** (via `(dashboard)/layout.tsx`, lines 10, 260–261):
- `LazyCommandBar` (→ `src/components/command-bar.tsx`) — mounted unconditionally, opened by the topbar "⌘K" button (`setCommandOpen(true)`, line 123) and the `commandOpen` state from `useAppShell()`
- `LazySearchPanel` (→ `src/components/search-panel.tsx`) — mounted unconditionally, opened via a custom `window` event `salesos:toggle-search` (line 74)
- Dedicated full-page route `(dashboard)/search/page.tsx` — a **fourth, independent search surface**: local `useState` for query/strategy/page, `useSearch()` React Query hook, `fulltext`/`semantic`/`hybrid` strategy toggle, `localStorage`-persisted history (`salesos-search-history` key, capped at 10 entries), links out to `/search/analytics`

**Confirmed dead / unwired:** `src/features/search/command-bar/CommandBar.tsx` — the most feature-complete implementation (integrates the real `@salesos/search` package: `SearchProvider`, telemetry, sub-components, its own test suite) has **zero importers outside its own directory** — reconfirms Phase 1 §18 exactly; grep for `fixed inset-0` (used for its overlay) shows it alongside the other 13 hand-rolled overlay files but it is never rendered from any layout.

**v3-only:** `src/components/v3/V3CommandPalette.tsx` — wired only into `v3/layout.tsx`, fully independent keybind/state logic, shares no code with the production `command-bar.tsx`.

**Net count:** 4 distinct "search" UI surfaces are live simultaneously in production (CommandBar palette, SearchPanel overlay, full `/search` page, plus facets/results wiring inside each) + 1 dead CommandBar + 1 v3-only palette = **6 total search-adjacent UI implementations** in the codebase for what a user experiences as "press ⌘K or click search."

---

## 7. Navigation Structure (production sidebar, `src/lib/workspaces.ts` + `src/components/navigation/grouped-sidebar.tsx`)

Full nav tree, in file-declared order — **6 workspaces**, each independently switchable via `WorkspaceSwitcher`:

1. **Sales** (`DollarSign` icon)
   - Core: Dashboard, Companies, Employees, My Profile (`/employees/me`), Contacts, Opportunities
   - Pipeline: Revenue, Pipeline, Forecast
   - Activity: Activities, Meetings, Customer Success
2. **Executive** (`Brain` icon)
   - Decision: Decisions, Analytics, Graph
3. **Intelligence** (`Search` icon)
   - Discover: Search, Signals, Monitoring, Rules
4. **GTM** (`Crosshair` icon) — 10 flat items, no sub-grouping: GTM Hub, ICP Profiles, Market Sizing, Lead Discovery, Enrichment, Website Intelligence, Outreach, Verification, Lookalikes, Sequences
5. **Studio** (`Palette` icon)
   - Customize: Custom Fields, Scoring Rules, Permissions Studio, Workflow Studio, Notification Rules, Branding Studio, Territories Studio
   - AI: AI Model Tiers, Prompt Library, AI Policies, AI Memory
6. **Admin** (`Settings` icon)
   - System: Settings, Admin, Integrations, Marketplace Listings

**Admin sub-console has its own separate nav** (`src/features/admin/OwnerConsoleShell.tsx`, lines 22–51): Overview (`/admin`), Tenants, Billing, Flags, Config, Audit, Integrations — a 7-item flat nav independent of the main sidebar, rendered only inside `/admin/*` routes (`OwnerConsoleShell` wraps `admin/layout.tsx`). Confirmed these ARE reachable (not orphaned) — just isolated to their own chrome.

**Click-depth from `/dashboard`** (verified by reading the actual link targets, not inferred):
| Destination | Path | Clicks |
|---|---|---|
| Company 360 | Sidebar→Companies→row (→`/companies/[id]`, confirmed via `companies/page.tsx` lines 427/473/770 all point at the plain detail route, not `/360`) → "360 View" button on that page | **3** |
| Employee 360 | Sidebar→Employees→row (→`/employees/[id]` directly) | **2** |
| Search | Sidebar workspace-switch→Intelligence→Search (2 clicks), OR topbar "Quick search" button (1 click), OR ⌘K (0 clicks/1 keystroke) | **2 / 1 / 0** depending on entry point |
| Settings | Topbar avatar→user menu→Settings (confirmed at `(dashboard)/layout.tsx` lines 168–175) | **2** |
| Admin | Sidebar workspace-switch→Admin→Admin item, OR topbar avatar menu does **not** list Admin (only Profile/Settings/Logout) | **2** (sidebar only — no topbar shortcut) |

All figures match/confirm Phase 1 §4.

---

## 8. Orphaned / Unlinked Routes

Full route inventory (`find (dashboard) -name page.tsx`) cross-referenced against `getAllNavItems()` (`src/lib/workspaces.ts`) hrefs, plus a grep for any in-page `<Link href="...">` back-reference. Routes below have **no sidebar entry and no found in-app forward link** — reachable only by typed URL, browser history, or the command palette:

| Route | File | Notes |
|---|---|---|
| `/ai` | `(dashboard)/ai/page.tsx` | Zero `href="/ai"` hits anywhere in `src` |
| `/rag` | `(dashboard)/rag/page.tsx` | Zero forward links found; only server component in `(dashboard)` per Phase 1 §2 |
| `/copilot` | `(dashboard)/copilot/page.tsx` | Only self-referential back-link from `/copilot/telemetry` |
| `/copilot/telemetry` | `(dashboard)/copilot/telemetry/page.tsx` | Same — reachable only from within `/copilot` itself |
| `/knowledge` | `(dashboard)/knowledge/page.tsx` | Only self-referential back-link from `/knowledge/connectors` |
| `/knowledge/connectors` | — | same |
| `/automation` | `(dashboard)/automation/page.tsx` | Only self-referential back-links from its own sub-pages (`automation/analytics`, `automation/workflows/new`) |
| `/automation/workflows/new` | — | Confirmed orphaned per Phase 1 §10 point 3 — this is the full-page drag-and-drop workflow canvas, unreachable from anywhere |
| `/marketplace` | `(dashboard)/marketplace/page.tsx` | Nav only links `/marketplace/listings`; `/marketplace` root itself has no inbound sidebar link, only self-referential back-links from `listings` and `[pluginId]/config` |
| `/pipeline/analytics` | `(dashboard)/pipeline/analytics/page.tsx` | No nav entry, no forward link found |
| `/revenue/quotas` | — | No nav entry |
| `/revenue/territories` | — | No nav entry |
| `/decisions/templates` | — | No nav entry (only `/decisions` in nav) |
| `/search/analytics` | — | Reachable only as an outbound link **from** `/search/page.tsx` itself, not from nav |
| `/analytics/sales`, `/analytics/revenue`, `/analytics/pipeline`, `/analytics/employees`, `/analytics/automation`, `/analytics/reports/builder` | — | Nav only links parent `/analytics`; none of the 6 sub-reports have a sidebar entry |

**Total: ~18 route files with no sidebar path in.** Combined with the entire `v3` tree (18 routes, its own independent nav, not linked from the production sidebar at all) and `apps/*` (0 files), a large fraction of the shipped route surface is only discoverable via direct URL knowledge or the command palette — a strong signal for the "journey heatmap" / IA-simplification argument in Phase 1B.

**Not orphaned (confirmed reachable via secondary nav):** `/admin/*` sub-routes (via `OwnerConsoleShell`'s own nav) — do not count these as dead ends, they're intentionally isolated, not abandoned.

---

## 9. Form Implementation Consistency

Four representative forms compared directly by source:

| Form | File | Component used for text fields | Label pattern | Button component | Container |
|---|---|---|---|---|---|
| Company create/edit | `(dashboard)/companies/page.tsx` (~line 491) | `@salesos/ui` `Input` | Separate `<label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">` above each `Input` | `@salesos/ui` `Modal`/`ModalContent`/`ModalFooter` (Radix-backed) | Design-system `Modal` |
| Settings profile/password | `(dashboard)/settings/page.tsx` (~line 271+) | `@salesos/ui` `Input` | **Built-in** `label` prop on `Input` itself (`<Input label={t(...)} />`) — no separate `<label>` element | `@salesos/ui` `Button` (inferred from imports) | Inline page section (not a modal) |
| Revenue Quota create/edit | `(dashboard)/revenue/quotas/page.tsx` (~line 125–183) | **Raw HTML** `<input>` (not the design-system `Input`) | Separate `<label className="block text-sm font-medium text-[var(--text-primary)] mb-1">` — similar wording to Companies' label class but **not identical** (`text-secondary` vs `text-primary`) | **Raw HTML** `<button>` — no `Button` primitive | Hand-rolled `fixed inset-0 z-50` div — no Radix, no focus trap, no `role="dialog"` |
| Companies form (state pattern reference) | same file as above | — | All 4 sampled forms use ad hoc `useState({...})` object state, zero `zod`/`react-hook-form` usage (confirms Phase 1 §16 exactly — `@salesos/forms` remains 0 consumers) | — | — |

**Verdict — not visually consistent.** Two different label patterns (separate `<label>` vs. built-in `Input label` prop) and two different form-primitive tiers (styled `Input`/`Button`/`Modal` vs. raw unstyled `<input>`/`<button>`/hand-rolled overlay div) coexist for the same conceptual action ("create/edit a record"). The Companies-modal pattern is closer to a "canonical" form look; Revenue Quotas is a visible regression from it in the same app, same sidebar workspace family (Sales → Pipeline → Revenue).

---

## 10. Git Churn — Top Files Changed in Last 90 Days

Command: `git log --since="90 days ago" --name-only --pretty=format: -- src` (804 total commits in repo history; run scoped to `salesos/frontend/src`), aggregated with `sort | uniq -c | sort -rn`.

| # changes (90d) | File |
|---|---|
| 42 | `src/lib/queryKeys.ts` |
| 42 | `src/app/(dashboard)/layout.tsx` |
| 34 | `src/lib/i18n/en.json` |
| 34 | `src/lib/i18n/ar.json` |
| 34 | `src/lib/api.ts` |
| 26 | `src/lib/commands.ts` |
| 25 | `src/components/foundation/MobileNav.tsx` |
| 24 | `src/lib/__tests__/commands.test.tsx` |
| 24 | `src/features/integrations/IntegrationsStudio.tsx` |
| 24 | `src/app/(dashboard)/admin/integrations/page.tsx` |
| 20 | `src/features/integrations/__tests__/integrations-studio.test.tsx` |
| 20 | `src/app/(dashboard)/admin/tenants/page.tsx` |
| 17 | `src/features/admin/lib/formatProvisionToast.ts` |
| 16 | `src/features/admin/lib/__tests__/formatProvisionToast.test.ts` |
| 14 | `src/lib/hooks/adminQueries.ts` |
| 13 | `src/lib/api/types/admin.ts` |
| 13 | `src/lib/api/admin.ts` |
| 12 | `src/lib/api/client.ts` |
| 11 | `src/features/gtm/GtmHub.tsx` |
| 11 | `src/features/dashboard/_layout/dashboard-page.tsx` |
| 11 | `src/application/dashboard/widget.store.ts` |
| 10 | `src/lib/__tests__/api.contract.test.ts` |
| 10 | `src/features/admin/__tests__/admin-workspace.test.tsx` |
| 10 | `src/components/copilot-panel.tsx` |
| 10 | `src/app/providers.tsx` |

**Reading:** the churn signal is dominated by **infrastructure/plumbing files** (`queryKeys.ts`, `api.ts`, the dashboard layout shell, i18n dictionaries, command registry) rather than any single feature screen — consistent with the "dense recent security-hardening + repo-canonicalization cycle" the Phase 1 audit inferred from the git log. The one clear *feature* cluster in the top 25 is **Admin/Integrations/Tenants** (5 of the top 25 entries: `IntegrationsStudio.tsx` + test, `admin/integrations/page.tsx`, `admin/tenants/page.tsx`, `adminQueries.ts`, `api/admin.ts`, `api/types/admin.ts`) — the Owner Console / Admin surface has clearly been the most actively iterated *product* area in the last 90 days, despite being explicitly marked "Not Production GO" and living behind a separate, audience-isolated shell. This is worth flagging directly: real recent engineering effort is going into a surface the source code says isn't shippable yet.

---

## Notes on Method / Reliability

- All import/usage counts were produced with `grep -rl` against `src` and `packages/ui/src` with `--include=*.tsx`, cross-checked in most cases by opening the actual source file to confirm intent (not just string matches).
- Route inventory was produced by `find (dashboard) -name page.tsx` directly on the checked-out filesystem, not inferred from documentation.
- Nav structure was read directly from `src/lib/workspaces.ts` (single source of truth per Phase 1 §4) and `src/features/admin/OwnerConsoleShell.tsx`, not from the rendered `GroupedSidebar` component (which consumes the same data) — sidebar grouping/rendering logic in `grouped-sidebar.tsx` was not separately re-verified line-by-line but its data source was.
- Git churn figures are exact `uniq -c` counts from `git log --since="90 days ago"` scoped to `src` only (excludes `packages/*`, `apps/*`, `e2e/*`, `docs/*`).
