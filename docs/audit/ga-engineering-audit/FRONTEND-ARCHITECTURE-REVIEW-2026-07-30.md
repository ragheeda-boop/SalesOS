# SalesOS Frontend — Architecture Review & Refactoring Strategy

**Date:** 2026-07-30
**Reviewer stance:** Principal Frontend Architect / Staff Engineer / Next.js 15 & React 19 Expert / Enterprise SaaS Architect / UX Platform Architect
**Method:** Six parallel evidence-gathering passes (app-router/layout mapping, route-by-route V3 migration status, feature architecture across all 13 features, package/workspace classification, shared-layer duplicate/dead-code hunt) over `salesos/frontend/`. No Node/npm/madge/depcheck is available in this environment — dependency-graph claims (circular deps, dead code, unused packages) are grep- and read-based, not tool-verified. Confidence is noted per-finding; treat "zero importers found" as a strong lead, not absolute proof (a dynamic `import()` or an untraced barrel re-export could hide a real usage).
**Companion document:** [`EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30.md`](EXEC-ARCHITECTURE-PRODUCT-REVIEW-2026-07-30.md) covers the whole product; this document goes far deeper on the frontend specifically, at the user's request, and supersedes that document's frontend section wherever they differ (this one has better evidence).

---

## Phase 1 — Understanding the Frontend

### Routing
Three route trees under `src/app/`: `(auth)` (login/register, no shared layout), `(dashboard)` (legacy, 51 `page.tsx` files, full-featured), and `v3` (rebuild in progress, 18 `page.tsx` files). All three sit under one root `layout.tsx`.

### Providers
`src/app/layout.tsx` → `src/app/providers.tsx` composes, in order: `ToastViewport` (`@salesos/ui`), `I18nProvider` (`@/lib/i18n`, locale read from `localStorage['salesos-locale']`), `RuntimeContext.Provider` (`@salesos/hooks` + `createFrontendRuntime` from `@salesos/runtime` — websocket, localization, named app state), `QueryClientProvider` (`@tanstack/react-query`, staleTime 10s, retry 1). Neither `(dashboard)/layout.tsx` nor `v3/layout.tsx` redeclares any of this — they compose correctly, adding only their own chrome.

### Layouts
Exactly three `layout.tsx` files exist in the whole app (root, `(dashboard)`, `v3`) — no per-route-segment layouts anywhere. `(dashboard)/layout.tsx` renders a full sidebar/topbar `AppShell` (22 hardcoded nav keys), mobile drawer, lazy command bar/search/copilot panels, and does its own **client-side-only** auth guard (`useEffect` checking `localStorage.getItem('access_token')`, redirecting to `/login`). `v3/layout.tsx` renders `V3Shell`/`V3Topbar`/`V3CommandPalette`/`V3AiPopup`, with no auth guard found in the layout itself. **No `middleware.ts` exists anywhere in the frontend** — there is no server-side or edge-level auth/locale gating; the only protection is the `(dashboard)` layout's client-side check, which `v3` does not replicate.

### App Router hygiene
`(dashboard)` has exactly one set of `loading.tsx`/`error.tsx`/`not-found.tsx`, at the group root (inherited by all descendants — reasonable). `v3` has **none of the three, at any level** — no loading skeleton, no error boundary, no custom 404 for the entire new tree, which directly conflicts with the product's own stated UX rule ("any loading over 300ms must show a skeleton screen matching page structure").

### Feature modules
13 directories under `src/features/`: admin, analytics, automation, company-intelligence, customer-success, dashboard, demo, monitoring, rag, revenue-execution, rules, scoring, search. Of these, **three are dead code with zero importers anywhere** (analytics, demo, search — the live pages that cover this functionality were built independently, bypassing the feature module), and a fourth (scoring, new today) is registered into the dashboard's widget system but has no backing data path, so it is functionally inert in production. That leaves **9 features that are actually live**: admin, automation, company-intelligence, customer-success, dashboard, monitoring, rag, revenue-execution, rules.

### Workspace / package architecture
`salesos/frontend/package.json` declares `"workspaces": ["packages/*"]` — this is the **only** workspace glob in the repo (no `pnpm-workspace.yaml`, no root `package.json` at `salesos/`). This means the 20 directories under `salesos/frontend/packages/` are the entire real package graph; the 2 directories under `salesos/packages/` (`platform`, `plugin-sdk`) are **structurally outside the build** — not ambiguous, confirmed orphaned. Of the 20 real packages, a real layered platform exists — `runtime`/`renderer` (foundational) → `hooks`/`widget-sdk` (consumption layer) → `workspace` (aggregator, 35 importers) → `src/features/dashboard` and `src/features/company-intelligence` (consumers) — but it coexists with 8 packages that are empty scaffolds and several more with real code and zero consumers (detailed in Phase 6).

### Design system
`@salesos/ui` is the actual design system in production use (54 files, 172 importers across `src/` — the single most-depended-upon package in the monorepo). `design-language` is the real token system (colors/type/spacing/motion/elevation, 19 files) and is genuinely consumed. `design-system`, `theme`, and `tokens` are three additional packages implying the same responsibility; all three are empty or near-empty scaffolds with zero consumers.

### Application layer
`src/application/` is a DTO/store/hook layer, and — correcting an assumption this review started with — it is **not** dashboard-only. Three of its four subtrees (`dashboard/`, `company-intelligence/`, `revenue-execution/`) are genuinely used by their respective features. The fourth (`api/`) and part of a fifth (`search/search.hooks.ts`) are dead code, superseded by parallel implementations in `src/lib/hooks/`.

### State management
No global store (no Redux/Zustand-at-app-level) — state is React Query (server state, via either `application/*` DTO hooks or `lib/hooks/*Queries.ts`, inconsistently depending on feature) plus local `useState`/Context for UI state. The dashboard/company-intelligence features use a Context-based provider (`dashboard-provider.tsx`) driving their widget registries.

### API/hooks layer
One canonical HTTP client (`src/lib/api/client.ts`, axios with bearer-token + `X-Tenant-Id` interceptors and 401/422 handling) — genuinely singular, which is good. But there are **two parallel conventions for how features reach it**: `src/application/<feature>/*.dto.ts` (used by dashboard, company-intelligence, revenue-execution) vs. `src/lib/hooks/*Queries.ts` / `src/lib/<name>Queries.ts` (used by admin, automation, customer-success, monitoring, rag, rules, search-page). This is not a per-feature stylistic choice — it's a real, unresolved architectural fork that has been running long enough to accumulate independent duplicate implementations of the same hooks on both sides (`useOpportunities`, `useTasks`, `useSearch` each exist twice — once live, once dead).

---

## Phase 2 — Complete Architecture Map

### 2.1 Routing hierarchy
```
src/app/
├── layout.tsx                    [root: ToastViewport, I18nProvider, RuntimeContext, QueryClientProvider]
├── providers.tsx
├── (auth)/                       [no layout — bare under root]
│   ├── login/
│   └── register/
├── (dashboard)/                  [layout: AppShell, client-side auth guard — 51 pages]
│   ├── loading.tsx / error.tsx / not-found.tsx   [only set in the whole app]
│   ├── activities, admin/{audit,config,flags,tenants}, ai, analytics/{automation,employees,
│   │   pipeline,reports→builder-only,revenue,sales}, automation/{analytics,workflows→new-only},
│   │   companies/{[id],[id]/360}, contacts, copilot/{telemetry}, customer-success, dashboard,
│   │   decisions/{templates}, employees/{[id],me}, forecast, graph, knowledge/{connectors},
│   │   marketplace/{[pluginId]→config-only}, meetings, monitoring, opportunities/{[id]},
│   │   pipeline/{analytics}, rag, revenue/{quotas,territories}, rules, search/{analytics},
│   │   settings, signals
├── v3/                           [layout: V3Shell/V3Topbar/V3CommandPalette — 18 pages, NO loading/error/404]
│   ├── _components/ (private)    [own EmptyState/LoadingState/ErrorState/PermissionState — parallel to guidance/]
│   ├── _hooks/ (private)
│   ├── activities, admin, analytics, companies/{[id]}, contacts/{[id]}, crm/{[id]}, cs,
│   │   employee [→ redirects to /employees/me], people/{[id]}, settings/{integrations→
│   │   orphaned, no page.tsx}, shell [→ static design-spec page, not the actual shell], tasks/{[id]}
└── api/auth/callback/google/route.ts   [thin redirect bridge, defers token exchange to backend]
```

### 2.2 Feature hierarchy (live vs dead)
```
src/features/
├── LIVE, well-integrated:
│   ├── dashboard/            [_registry, _providers, _telemetry, _hooks, 13 widgets — reference implementation]
│   ├── company-intelligence/ [_registry, _layout, _providers, 10 widgets + company-360/ — structurally best, functionally thin]
│   ├── revenue-execution/    [largest, 20 widget dirs — has a 534-line god-file, duplicate NBA widgets]
│   ├── admin/                [16 files — scope disproportionate: owns 10 unrelated admin domains]
│   ├── automation/           [workflow builder — ad hoc integration style, not widget-sdk]
│   ├── customer-success/     [telemetry dashboard — backend routes live under /admin/telemetry/*]
│   ├── rag/                  [chat + document manager — clean, no streaming]
│   ├── rules/                [single 494-line file — backed by localStorage, not a real API]
│   └── monitoring/           [single 96-line widget — hand-rolled polling, bypasses every shared pattern]
├── ORPHANED (zero importers — dead code):
│   ├── analytics/            [real page built independently instead]
│   ├── demo/                 [unmounted anywhere]
│   └── search/               [real search page uses a separate, duplicate implementation]
└── REGISTERED BUT INERT:
    └── scoring/               [wired into dashboard widget-registry; NOT wired into dashboard.mapper.ts/widget.store.ts
                                 → will render its loading skeleton forever in production]
```

### 2.3 Package hierarchy
```
salesos/frontend/packages/   (the ONLY real workspace — "packages/*" glob)
├── Real, load-bearing platform layer:
│   runtime → renderer → hooks/widget-sdk → workspace (35 importers) → features/{dashboard,company-intelligence}
├── Real, load-bearing standalone:
│   ui (172 importers, the design system), design-language (tokens, consumed by workspace + 2 files),
│   charts (15 importers), search (19 importers, used by application/search + features/search)
└── Empty scaffolds / zero-consumer dead weight (8 of 20):
    charts-v3 (package.json only), layouts (package.json only), providers (package.json only),
    theme (package.json only — superseded by design-language), tokens (package.json only — ditto),
    widgets (package.json only — name collides with widget-sdk), workspace-generator (index.js = `module.exports = {}`),
    icons (real code, 0 importers — app likely uses lucide-react directly)
    + real-code-but-unused: config (0 importers), forms (0 importers), platform (19-file permission/flag/telemetry
      kernel, 0 importers — its responsibilities are duplicated ad hoc inside runtime instead), design-system
      ("alpha...Not production GA", 0 importers)

salesos/packages/   (OUTSIDE the workspace glob — not part of the frontend build at all)
├── platform     [backend-shaped: agent-orchestration/RAG/decision-engine content, unrelated to frontend/packages/platform]
└── plugin-sdk   [standalone plugin-interface package, 0 references from frontend/src]
```

### 2.4 Cross-feature / cross-layer dependencies found
- `features/dashboard` → imports `features/scoring/widgets/company-scoring` and `features/revenue-execution/_providers/DecisionProvider` directly — a "reference" feature reaching into two others rather than going through the registry abstraction it otherwise champions.
- `features/customer-success` and `features/admin` both call backend routes under `/api/v1/admin/telemetry/*` and `/api/v1/admin/*` respectively — real ownership overlap not reflected in the folder boundary.
- No circular-dependency inversions found in the sampled foundational files (`lib/api/*`, `lib/utils.ts`, `lib/i18n`, `application/dashboard/*`, `components/error-boundary.tsx`, `components/foundation/*`) reaching back into `features/*` or `components/v3/*` — this sample is not exhaustive (grep-based, ~15 files checked out of hundreds), so treat as a positive signal, not a clean bill of health.

### 2.5 Duplicate implementations (confirmed, with evidence)
| Concept | Live implementation | Dead/duplicate implementation |
|---|---|---|
| `useOpportunities`/`useCreateOpportunity` | `lib/hooks/opportunityQueries.ts` | `application/api/hooks.ts` (0 importers) |
| `useTasks`/`useCompleteTask` | `lib/hooks/taskQueries.ts` | `application/api/hooks.ts` (0 importers) |
| `useSearch` | `lib/hooks/searchQueries.ts` (used by `(dashboard)/search/page.tsx`) | `application/search/search.hooks.ts` (0 importers) |
| Lazy-loaded component registry | `components/lazy-exports.tsx` (used by `(dashboard)/layout.tsx`) | `lib/dynamic-imports.tsx` (0 importers, wraps the same components) |
| Search UI | `(dashboard)/search/page.tsx` + `components/search/SearchHistory.tsx` | `features/search/*` incl. `features/search/components/SearchHistory.tsx` (0 importers, entire feature orphaned) |
| Empty/loading/error states | `components/guidance/empty-states/EmptyState.tsx` (richer, tour-integrated) | `app/v3/_components/states.tsx` (independent reimplementation, incompatible props) |
| NBA (next-best-action) widget | one of the two | `features/revenue-execution/widgets/{nba-widget, next-best-action}` — two competing implementations in the same feature |
| Company `/companies` mutation endpoints | `lib/api/company.ts` | re-implemented again in `lib/hooks/mutationHooks.ts` (separate `api.post/patch/delete` calls to the same paths) |
| Company intelligence fetch | `lib/api/company.ts:160` | re-implemented again in `application/company-intelligence/useCompanyIntelligence.ts:13` (third independent call site) |
| `Skeleton` component | `@salesos/ui`'s `Skeleton` (used by feature pages) | `components/skeleton.tsx` (`Skeleton`/`WidgetSkeleton`, 0 importers found) |
| Error-boundary-named files | `components/error-boundary.tsx` (real class-based `ErrorBoundary` + `withErrorBoundary`) | `components/foundation/error-boundary.tsx` (`ErrorFallback` — presentational only, not an actual boundary; different abstraction, confusing shared name) |

### 2.6 Unused modules / dead code (grep-confidence, not tool-verified)
`features/analytics/*`, `features/demo/*`, `features/search/*` (whole features), `application/api/hooks.ts`, `application/search/search.hooks.ts`, `lib/dynamic-imports.tsx`, `components/skeleton.tsx`, plus the 8 empty package scaffolds and 4 real-but-unconsumed packages listed in 2.3.

---

## Phase 3 — Architectural Problems

**Duplicate pages:** `(dashboard)` and `v3` cover the same logical destinations (companies, contacts, activities, admin, analytics, customer-success/cs, employees/people, settings) with two independent implementations each. This is by explicit design (v3 is a preview layer — see Phase 4), but it is currently a permanent-feeling duplication, not a short-lived transitional one, since every v3 list page explicitly links back to legacy for any real functionality.

**Duplicate layouts:** Only 3 layouts exist, so this isn't a proliferation problem — but the two top-level ones (`(dashboard)` and `v3`) each hand-roll their own nav shell, command palette, and (in `(dashboard)`'s case) auth guard, with zero shared chrome code between them.

**Duplicate components/hooks/business logic/API calls:** Extensively documented in 2.5 — this is the single largest concrete problem this review found. At least 10 distinct instances of "the same concept implemented twice, one path live, one dead" were confirmed with file-level evidence.

**Large components:** `revenue-execution/workspace/pipeline/PipelineWorkspace.tsx` (534 lines) is the standout god-file inside `features/`; several `(dashboard)` route pages exceed 600–900 lines (`graph/page.tsx` 999, `decisions/page.tsx` 827, `marketplace/page.tsx` 791, `employees/page.tsx` 738, `knowledge/page.tsx` 732) — the route-as-god-component pattern is systemic in the legacy tree specifically, not evenly distributed.

**Feature leakage:** `dashboard` imports `scoring` and `revenue-execution` internals directly; `customer-success` and `admin` both own pieces of `/admin/telemetry/*`. `admin` itself is the biggest leakage case in the other direction — it isn't leaking into other features, but its own scope (tenants, plans, billing, feature flags, jobs, AI costs, AI audit, health, roles, permissions, DLQ, entity-resolution, general audit log) is ten-plus unrelated platform-operations domains bundled under one "feature" folder, which is really a second architectural tier (platform administration) mis-modeled as a peer of product features.

**Incorrect folder ownership:** `rules` persists to `localStorage`, not the backend — it is UI-complete but has no real data layer, which is a mislabeled "feature" (should be flagged as a prototype, not production functionality). `monitoring` bypasses both `application/*` and `lib/hooks/*Queries` conventions with inline `fetch`-in-component polling.

**Poor separation of concerns:** The `application/*` vs `lib/*Queries` fork (Phase 1) is the clearest instance — the same architectural decision (where does data-fetching logic live?) has two different answers depending which feature you're reading, with no documented rule for which to use going forward, and each fork has independently reinvented some of the same hooks.

**App Router misuse:** `v3`'s complete absence of `loading.tsx`/`error.tsx`/`not-found.tsx` at any level is a genuine App-Router-feature-non-adoption issue, not a stylistic gap — Next.js provides these specifically to avoid hand-rolled loading/error state per page, and `v3` instead built its own `_components/states.tsx` micro-library to compensate, achieving a worse version of what the framework offers natively. `v3/shell` is also a minor App Router misuse: a route path (`/v3/shell`) that resolves to a static documentation page describing the shell, rather than being excluded via a private (`_shell`) folder or moved into `/docs`.

**Workspace misuse:** `salesos/packages/{platform,plugin-sdk}` sitting entirely outside the npm workspace glob is a workspace-topology bug waiting to confuse anyone who assumes "packages/" means "in the build" — it doesn't, at that path.

**Package misuse:** Five package names (`design-language`, `design-system`, `theme`, `tokens`, plus `widgets` vs `widget-sdk`) imply five distinct responsibilities but resolve to two real packages and effectively three-to-four abandoned name-squats. This actively misleads a new engineer's mental model of "where do design tokens live" or "where does the widget contract live" — they will reasonably guess wrong at least once.

**Design System violations:** `v3` built its own state-component set instead of extending `guidance/empty-states`; several `admin`/`automation`/`customer-success`/`monitoring`/`rules` features bypass the widget-sdk registry pattern that `dashboard`/`company-intelligence` use, producing at least three different "how does a feature render itself" conventions in one codebase.

**Widget SDK violations:** `scoring`'s widget is correctly built against the widget-sdk contract (`createDashboardWidget`) but was registered without completing the corresponding `widget.store.ts`/`dashboard.mapper.ts` entry — a process gap (the SDK pattern itself wasn't violated, its *completion checklist* was skipped).

---

## Phase 4 — V3 Migration Review

**Ground truth, from direct source reading:** nearly every `v3` list page explicitly self-labels as a read-only preview. Verbatim comments found in source: `v3/companies/page.tsx:62` "Legacy /companies is unchanged"; `v3/contacts/page.tsx:52` same; `v3/admin/page.tsx:43` "Not wired — no invented controls"; `v3/analytics/page.tsx:36` "Not wired — no invented metrics"; `v3/cs/page.tsx:40` "Not wired — no fake health AI"; `v3/settings/page.tsx:37` "Not wired." Every one of these pages renders a `GhostButtonLink` back to its legacy equivalent for any real work. This is an intentional, disciplined "honesty" pattern (consistent with the AI-honesty culture found in the backend review) — v3 is explicitly a design/UX preview layer today, not a functional replacement, and the code says so in its own comments. That is good engineering honesty and a bad state to still be in for however many sprints it's been running.

**Which routes are fully migrated?** None, strictly. The closest cases are the **detail** pages: `v3/companies/[id]` (682 lines) and `v3/people/[id]` (602 lines) both reuse real, shared feature components (`features/company-intelligence/widgets/*`, `components/employee-360/*`) — the same components the legacy detail pages use — so at the detail-page level, migration is substantively real, not cosmetic.

**Which routes are partially migrated, and what's missing:**
| v3 route | Has | Missing vs. legacy |
|---|---|---|
| companies (list) | read-only search/table | create/edit/delete/bulk-edit/export/6 filter types |
| contacts (list) | read-only search/table | full CRUD |
| people (list) | read-only search/table | full CRUD (detail page is genuinely migrated) |
| admin | users/flags/audit-log/roles (read-only) | tenants, plans, billing, jobs, AI-cost dashboard, AI-audit-log widget, health dashboard |
| analytics | one high-level exec dashboard | 5 legacy drill-down subpages (automation, employees, pipeline, reports, revenue, sales) have no v3 equivalent at all |
| crm | stage-advance kanban | forecast/health/analytics views (legacy `pipeline` + standalone `forecast` route) |
| settings | API keys, notification prefs, real Google integration panel | broader tenant/user/security settings |
| activities | roughly at parity, arguably ahead (adds activity-intelligence metrics) | needs verification of full feed parity |

**Which v3 routes still depend on/point back to legacy?** Every one listed above, via explicit `GhostButtonLink`s. `v3/employee/page.tsx` literally `redirect()`s into the legacy `/employees/me` route rather than rendering its own page.

**Not migrated / functionally different, not a port:** `v3/cs` calls generic `getExecutiveDashboard`/`searchCompanies` data — it does not call any of the `/admin/telemetry/*` endpoints the legacy `CustomerSuccessWorkspace` depends on. This isn't "partially migrated," it's a different, shallower dashboard reusing unrelated data sources under the same route name.

**Can the legacy dashboard be removed today? No — and not soon.** No `v3` equivalent exists at all (not even a stub) for: opportunity detail/pipeline analytics, forecast, decisions, marketplace, knowledge (+connectors), graph, rag, rules, signals, meetings, monitoring, copilot, ai, automation (workflows/analytics), revenue (quotas/territories), search, and five analytics drill-down subpages. That is roughly **19 legacy route groups with zero v3 presence**, on top of the 6+ partially-migrated ones above still missing CRUD/bulk/filter/export.

**What's blocking full migration?** Not a technical blocker — the pattern for a real port is proven (the two detail pages). It's a sequencing/prioritization gap: v3 has so far invested in list-page previews and two real detail-page ports, but not yet in the CRUD/mutation layer, the five analytics drill-downs, or any of the 12+ legacy-only feature areas.

**Effort estimate:** ~19 legacy-only route groups needing a v3 port at ~3–6 eng-days each ≈ **50–70 eng-days**. CRUD/bulk/filter/export for the 6 partially-migrated list pages at ~3–5 eng-days each ≈ **20–25 eng-days**. Rewiring `cs` to real telemetry endpoints ≈ **5 eng-days**. **Total: roughly 75–100 engineer-days** (not counting QA, design review, or the state/error-boundary/loading-page gaps in Phase 1 that v3 needs closed regardless of route count).

---

## Phase 5 — Feature Architecture Evaluation

Full per-feature detail is in Phase 2.2 and the underlying research; verdicts summarized:

| Feature | Cohesion verdict | Recommendation |
|---|---|---|
| dashboard | Cohesive, best-architected (reference registry pattern) | Keep as the template; fix its own boundary violation (direct imports of scoring/revenue-execution internals) |
| company-intelligence | Structurally cohesive, functionally shallow | Keep structure; invest engineering into the widget bodies (most are 2–3 line stubs) — this is the product's stated P0 feature and currently the least-built relative to its importance |
| revenue-execution | Not fully cohesive — correctly scoped domain, but internally messy | Split `PipelineWorkspace.tsx` (534L); consolidate the two NBA widgets; standardize on the DTO layer instead of mixed direct-API calls |
| admin | Cohesive as "one team's concern" but disproportionately large | Should become its own top-level architectural tier (e.g. `src/admin/` or a separate app), not a peer feature — it owns ~10 unrelated platform-ops domains |
| automation | Cohesive, single-purpose | Fix the double-nested `workspace/automation/` folder path; adopt the widget-sdk pattern for consistency |
| customer-success | Cohesive, but backend-route ownership blurs into admin | Resolve `/admin/telemetry/*` ownership question jointly with the admin feature |
| rag | Cohesive, clean | No structural change needed; consider adding streaming/SSE for a better chat UX |
| rules | Cohesive but a prototype, not production | Either wire to a real backend endpoint or explicitly label as a preview/mock feature |
| monitoring | Too small to meaningfully evaluate as a "feature" | Fold into a shared health/ops widget under `admin`, using the standard hook+application pattern instead of hand-rolled polling |
| analytics | N/A — dead code | Delete, or actually mount it and delete the ad hoc page that replaced it |
| demo | N/A — dead code | Delete |
| search | N/A — dead code, duplicated by a separate live implementation | Delete the orphaned copy; the live one (`(dashboard)/search` + `components/search/*`) is authoritative |
| scoring | Cohesive but currently non-functional | 1-line-scale fix: add `companyScoring` to `dashboard.mapper.ts`/`widget.store.ts` |

**Should Features become the primary architectural boundary?** Partially — it already is the primary boundary for the 6 well-built features (dashboard, company-intelligence, revenue-execution, rag, automation, customer-success), and that pattern should be reinforced. But two categories don't fit the "feature" model at all: **admin** (a second architectural tier — platform operations, not a product feature) and the **3 dead + 1 inert modules** (analytics/demo/search/scoring), which inflate the feature count without representing real boundaries. A clean target state has roughly 7–8 real product features, one platform-admin tier, and zero placeholder directories.

---

## Phase 6 — Package Review

Full evidence and per-package table in Phase 2.3. Summary classification:

| Class | Packages | Count |
|---|---|---|
| **Core / load-bearing, keep as-is** | ui, design-language, hooks, runtime, renderer, widget-sdk, workspace, charts, search | 9 |
| **Legacy/duplicate, delete** | charts-v3, theme, tokens, widgets (name-collides with widget-sdk), layouts, providers | 6 |
| **Experimental, delete unless a concrete owner claims it in the next sprint** | design-system, workspace-generator | 2 |
| **Real code, zero consumers — delete or deliberately integrate** | config, forms, icons, frontend `platform` (permission/flag/telemetry kernel — its job is already done ad hoc inside `runtime`) | 4 |
| **Outside the workspace glob entirely — not a frontend concern, needs an ownership decision** (backend/platform team, not frontend) | root `salesos/packages/platform`, `salesos/packages/plugin-sdk` | 2 |

**Net: 8 of 20 real frontend packages are pure name-squats with no source code at all**, and a further 4 have real implementations nobody calls. That's 12 of 20 (60%) contributing zero runtime value today, against 9 genuinely load-bearing packages (45%, rounding — `search` slightly overlaps both counts due to one stale unused dependency declaration). This is a workspace that grew by speculatively creating package scaffolding ahead of need, and the need for most of them never materialized.

---

## Phase 7 — Enterprise Frontend Assessment (0–100)

| Dimension | Score | Rationale |
|---|---:|---|
| Scalability | 58 | App Router + widget-sdk/workspace platform is a sound foundation for team scale; undermined by two full route trees running in parallel, which is a team-scaling *cost*, not a runtime one |
| Maintainability | 40 | Weakest dimension — extensive confirmed duplication (routes, states, error boundaries, lazy-loading registries, hooks, NBA widgets, search UI) plus 60% of the package graph being dead weight |
| Extensibility | 52 | The widget-sdk/registry pattern is genuinely extensible where adopted (dashboard, company-intelligence); not consistently adopted elsewhere (3 different "how a feature renders" conventions coexist) |
| Modularity | 48 | Feature-folder boundaries leak (dashboard reaches into scoring/revenue-execution; admin/customer-success share backend route ownership); admin's scope alone undermines the model |
| Developer Experience | 48 | A new engineer must learn two data-fetching conventions (`application/*` vs `lib/*Queries`) and will likely guess wrong at least once about which of 5 similarly-named design-token packages to use |
| Reusability | 50 | `@salesos/ui` (172 importers) and `widget-sdk` are strong reuse wins; undercut by 3 dead features and at least 5 duplicated hook/API implementations that represent failed reuse |
| Performance | 50 | React Query caching + route-level code splitting are in place; `v3`'s total absence of loading states plus systemic 600–900-line route components in the legacy tree work against the product's own "<2s page load, always show a skeleton" principle |
| Design System | 52 | Real, well-used core (`ui`, `design-language`); diluted by 3 competing empty/near-empty token packages and `v3`'s independent state-component reimplementation instead of reuse |
| Accessibility | 45 | **Not independently re-verified this pass** (no agent was scoped to grep aria-*/focus-management/contrast); carried forward at low confidence from the prior audit's own admission that a11y was never browser-validated — treat as unknown-leaning-weak, not measured |
| Testing | 45 | Scattered `__tests__` directories exist (graph, monitoring, rules, settings, rag widgets) but no frontend coverage threshold is enforced anywhere (confirmed in the companion executive review) |
| Code Organization | 46 | Feature-based top-level structure is a reasonable choice; a newcomer currently has to discern which of 2–3 competing conventions is canonical in any given corner of the tree |
| **Overall Frontend Score** | **50** | A well-intentioned platform layer and a genuinely good reference feature (dashboard) sitting inside a tree that has accumulated a full sibling route system, a full sibling state-component library, and a package graph that's 60% unused — the architecture is not fundamentally wrong, it's fundamentally under-consolidated |

---

## Phase 8 — Target Architecture

Ignoring current constraints, the ideal SalesOS frontend for enterprise SaaS, multi-tenancy, large-team parallel development, a widget SDK/design system, AI-first experiences, and future mobile/desktop/plugin/micro-frontend optionality:

```
salesos/frontend/
├── src/
│   ├── app/                        ONE route tree (v3 fully cut over, legacy deleted)
│   │   ├── layout.tsx              root providers (unchanged — already correct)
│   │   ├── middleware.ts           NEW: real auth/locale gating at the edge, not client-side-only
│   │   ├── (product)/              renamed from v3; every segment has loading/error/not-found
│   │   └── (admin)/                platform-admin tier, physically separated from product routes
│   ├── admin/                      NEW top-level tier (not a "feature") — tenants/plans/billing/
│   │                               flags/jobs/AI-cost/AI-audit/health/roles/DLQ/entity-resolution,
│   │                               each as its own sub-module, sharing one admin data-access layer
│   ├── features/                   7-8 real product features only, ALL on one convention:
│   │   ├── company-intelligence/   (P0 — target for the deepest investment)
│   │   ├── revenue-execution/      (post-split, no god-files, one NBA widget)
│   │   ├── dashboard/              (reference registry pattern, boundary-clean — no reaching into siblings)
│   │   ├── automation/, customer-success/, rag/, rules/ (wired to a real backend)
│   │   └── (scoring folded into revenue-execution or company-intelligence — it's too small to be its own top-level feature)
│   ├── application/                ONE data-access convention for every feature (DTO + query hook
│   │                               per resource) — `lib/*Queries.ts` retired into this layer
│   ├── components/                 shared UI only; ONE empty/loading/error/state library;
│   │                               ONE error-boundary implementation, clearly named
│   └── lib/                        pure utilities + the single API client only — no feature-shaped
│                                   query hooks left here once `application/` absorbs them
├── packages/                       trimmed to the 9 load-bearing packages + any genuinely new
│                                   ones added with an immediate real consumer (no speculative
│                                   scaffolding merged without a consumer in the same PR)
│   ├── runtime/, renderer/, hooks/, widget-sdk/, workspace/   [platform layer — unchanged, it's good]
│   ├── ui/, design-language/, charts/, search/                [design-system + domain layer]
│   └── (a documented rule: proposing a new package requires an owning feature in the same change)
└── (mobile/desktop/plugins, when real): consume `workspace`/`widget-sdk`/`ui` as the shared
    contract layer — this is exactly what those packages already exist to make possible, once
    they're the only version of themselves rather than one of three
```

**Why this shape:** the platform layer (`runtime`→`renderer`→`hooks`/`widget-sdk`→`workspace`) and the registry-driven feature pattern (`dashboard`, `company-intelligence`) already ARE most of a correct target architecture — they were built once, correctly, and then not consistently reused as the rest of the app grew around them. The target architecture is not a rewrite; it's what's already here with the duplicates, dead branches, and inconsistent adopters removed. Multi-tenancy, AI-first widgets, and future mobile/plugin surfaces are all already expressible through `widget-sdk`/`workspace` — the missing piece is discipline, not new abstraction. Micro-frontends are explicitly **not recommended** at this stage — the codebase doesn't have team-scale or deployment-cadence pressure that would justify the operational cost, and it has the opposite problem right now (too many parallel structures, not too few).

---

## Phase 9 — Migration Plan

### Phase 1 — Quick Wins (1–2 weeks, low risk)
- Delete the 8 empty package scaffolds (`charts-v3`, `layouts`, `providers`, `theme`, `tokens`, `widgets`) and the zero-consumer real ones (`config`, `forms`, `icons`, `platform`, `design-system`) after a final grep confirmation. *Priority: high. Risk: low (zero importers verified). Dependency: none. Impact: removes 60% of package-graph noise immediately.*
- Delete `application/api/hooks.ts`, `application/search/search.hooks.ts`, `lib/dynamic-imports.tsx`, `components/skeleton.tsx`, and the entire `features/demo/` and `features/analytics/` directories. *Priority: high. Risk: low. Dependency: none. Impact: removes confirmed dead code.*
- Wire `companyScoring` into `dashboard.mapper.ts`/`widget.store.ts` (or unregister the widget). *Priority: high. Risk: low. Impact: fixes a visibly broken production widget.*
- Add `loading.tsx`/`error.tsx`/`not-found.tsx` to the `v3` route group root. *Priority: high. Risk: low. Impact: closes a real UX gap and a stated-product-principle violation.*
- Rename `components/foundation/error-boundary.tsx`'s export or file to remove the shared-name confusion with `components/error-boundary.tsx` (they are different abstractions — this is a naming fix, not a merge). *Priority: medium. Risk: low.*

### Phase 2 — Architecture Cleanup (3–6 weeks, medium risk)
- Delete `features/search/` (orphaned duplicate); confirm `(dashboard)/search` + `components/search/*` remain the single implementation. *Risk: low-medium (re-verify zero external references first). Dependency: Phase 1 dead-code removal patterns established.*
- Consolidate the two NBA widget implementations in `revenue-execution` into one. *Risk: medium (need to confirm which is actually rendered in production before deleting the other). Dependency: none.*
- Split `revenue-execution/workspace/pipeline/PipelineWorkspace.tsx` (534 lines) into sub-components. *Risk: low (pure refactor, should be covered by existing tests if any). Dependency: none.*
- Merge `components/guidance/empty-states/*` and `app/v3/_components/states.tsx` into one shared state-component library; migrate `v3` onto it. *Risk: medium (prop-shape differences need reconciling). Dependency: none. Impact: removes a real, confirmed duplication and improves v3's currently-absent loading/error UX.*
- Decide and document the `application/*` vs `lib/*Queries` question: pick `application/*` (it already covers 3 of 4 major features and is the more scalable DTO pattern) as the standard, and write a one-page ADR. *Risk: low to decide, medium to execute the follow-on migration (Phase 3/4 work). Dependency: none for the decision itself.*
- Resolve the `admin`/`customer-success` `/admin/telemetry/*` ownership overlap. *Risk: low. Dependency: a product/eng decision on where CS metrics conceptually live.*

### Phase 3 — Legacy Removal (6–12 weeks, higher risk, product-dependent)
- Execute the ~19-route-group v3 port backlog identified in Phase 4 (opportunities/pipeline detail, forecast, decisions, marketplace, knowledge, graph, rag, rules, signals, meetings, monitoring, copilot, ai, automation sub-pages, revenue sub-pages, 5 analytics drill-downs, search). *Priority: this is the actual product-facing work, not incidental cleanup — sequence by usage frequency/business value, not file-count. Risk: high if rushed (these are real user-facing features, not previews). Dependency: Phase 2's shared-state-component and data-layer decisions should land first so new v3 pages aren't built against soon-to-be-deprecated patterns.*
- Add CRUD/bulk/export/filter to the 6 partially-migrated v3 list pages. *Risk: medium. Dependency: same as above.*
- Rewire `v3/cs` to the real `/admin/telemetry/*` endpoints. *Risk: low-medium.*
- Only once the above is functionally complete: delete the entire `(dashboard)` route tree, its dedicated nav shell, and any legacy-only shared components proven unreferenced by `v3` at that point. *Risk: high if done before the above — this is explicitly the LAST step, not a parallel one.*

### Phase 4 — Package Consolidation (2–4 weeks, low-medium risk, can run parallel to Phase 3)
- Move `admin` out of `src/features/` into a dedicated top-level `src/admin/` tier with its own sub-module boundaries (tenants/plans/billing/flags/jobs/AI-cost/AI-audit/health/roles). *Risk: medium (import-path churn across the app, mechanical but wide). Dependency: none, but easier once Phase 1/2 dead code is gone (fewer files to update imports in).*
- Resolve `salesos/packages/{platform,plugin-sdk}` — either bring them inside the workspace glob with a real frontend consumer, or explicitly document them as backend/plugin-author-facing and move them out of a path that looks like a frontend package directory. *Risk: low. Dependency: a decision from whoever owns those packages' intended consumer.*
- Fully migrate `lib/*Queries.ts` call sites onto `application/*` per the Phase 2 ADR. *Risk: medium, mechanical. Dependency: Phase 2 decision.*

### Phase 5 — Final Enterprise Architecture (ongoing discipline, not a one-time project)
- Adopt a "no new package without a consumer in the same PR" rule to prevent the 8-scaffold pattern from recurring.
- Adopt a file-size lint gate (matches the companion executive review's recommendation) to prevent new god-files.
- Revisit mobile/desktop/plugin surfaces only once the single-route-tree, single-data-layer, trimmed-package-graph state above is reached — building those on top of today's dual-everything foundation would double the migration debt being paid down right now.

---

## Phase 10 — Final CTO Report

### 1. Executive Summary
SalesOS's frontend has a genuinely good platform core — a layered widget/design-system stack (`runtime`→`renderer`→`hooks`/`widget-sdk`→`workspace`) and at least one reference-quality feature (`dashboard`) built correctly against it. The problem is not that architecture; it's that the codebase has, over its life, grown a nearly-complete *shadow copy* of itself at almost every layer: a second route tree, a second state-component library, a second lazy-loading registry, a second data-access convention, duplicate hooks for opportunities/tasks/search, two NBA widgets, and eight empty package scaffolds implying capabilities that were never built. None of these shadow copies were malicious or careless in isolation — each reads as a reasonable attempt (a v3 redesign, a DTO-layer improvement, a package split-out) — but none of them were finished and retired their predecessor, so the codebase now pays the maintenance cost of both versions of everything, indefinitely, with the current version count as evidence. The fix is overwhelmingly deletion and consolidation, not new architecture.

### 2. Current Architecture Diagram
See Phase 2.1–2.3 for the full annotated trees (routing, features, packages).

### 3. Ideal Architecture Diagram
See Phase 8.

### 4. Top 20 Architectural Improvements
1. Delete the 8 empty package scaffolds (`charts-v3`, `layouts`, `providers`, `theme`, `tokens`, `widgets`) plus zero-consumer real ones (`config`, `forms`, `icons`, frontend `platform`, `design-system`).
2. Delete dead code: `application/api/hooks.ts`, `application/search/search.hooks.ts`, `lib/dynamic-imports.tsx`, `components/skeleton.tsx`.
3. Delete orphaned features: `features/demo/`, `features/analytics/`, `features/search/`.
4. Wire `companyScoring` into `dashboard.mapper.ts`/`widget.store.ts`.
5. Add `loading.tsx`/`error.tsx`/`not-found.tsx` to `v3`.
6. Add a real `middleware.ts` for auth/locale gating instead of client-side-only checks.
7. Merge the two empty-state component libraries (`guidance/empty-states` vs `v3/_components/states.tsx`) into one.
8. Rename `components/foundation/error-boundary.tsx` to remove the misleading shared name with the real `ErrorBoundary`.
9. Consolidate the two NBA widget implementations in `revenue-execution`.
10. Split `revenue-execution/workspace/pipeline/PipelineWorkspace.tsx` (534 lines).
11. Write and adopt an ADR standardizing on `application/*` over `lib/*Queries.ts` for all data access.
12. Move `admin` out of `src/features/` into its own top-level architectural tier.
13. Resolve `customer-success`/`admin` ownership overlap of `/admin/telemetry/*`.
14. Fix `rules` to call a real backend endpoint instead of `localStorage`, or explicitly label it a prototype.
15. Fix `monitoring` to use the standard hook + application pattern instead of hand-rolled `fetch`-in-component polling.
16. Resolve `salesos/packages/{platform,plugin-sdk}` sitting outside the workspace glob.
17. Execute the ~19-route-group v3 migration backlog (Phase 4/Phase 9-Phase-3), prioritized by usage/business value.
18. Add CRUD/bulk/filter/export to the 6 partially-migrated v3 list pages.
19. Adopt a file-size lint gate to stop god-files recurring (route pages regularly hit 600–999 lines in the legacy tree).
20. Adopt a "no new package without a same-PR consumer" rule to prevent the scaffold pattern from recurring.

### 5. Files/Folders to Remove
`packages/{charts-v3,layouts,providers,theme,tokens,widgets}`, `packages/{config,forms,icons,platform,design-system}` (pending final re-grep), `src/application/api/`, `src/application/search/search.hooks.ts`, `src/lib/dynamic-imports.tsx`, `src/components/skeleton.tsx`, `src/features/demo/`, `src/features/analytics/`, `src/features/search/` (after confirming `(dashboard)/search` is fully self-sufficient), one of the two `revenue-execution` NBA widget directories (confirm which is live first), `src/app/v3/settings/integrations/` route folder (has no `page.tsx` — either add one or remove the orphaned directory).

### 6. Files/Folders to Merge
`components/guidance/empty-states/*` + `app/v3/_components/states.tsx` → one shared state-component module. `lib/api/company.ts` + `lib/hooks/mutationHooks.ts`'s duplicate company mutations + `application/company-intelligence/useCompanyIntelligence.ts`'s duplicate intelligence fetch → one canonical company data-access module. `lib/*Queries.ts` files → progressively into `src/application/*` per the Phase-9 ADR.

### 7. Files/Folders to Split
`src/features/admin/` → a new top-level `src/admin/` tier with per-domain sub-modules (tenants/plans/billing/flags/jobs/AI-cost/AI-audit/health/roles). `revenue-execution/workspace/pipeline/PipelineWorkspace.tsx` (534 lines) → sub-components by concern (kanban board, filters, bulk actions, forecast panel). The systematically oversized `(dashboard)` route pages (graph, decisions, marketplace, employees, knowledge — 700–999 lines each) → extract page-level logic into feature components, leaving the `page.tsx` as a thin composition shell (matching the pattern `dashboard`/`company-intelligence` already use correctly).

### 8. Legacy Code Candidates
The entire `(dashboard)` route tree is the largest legacy-code candidate in the codebase — not for deletion today (Phase 4's migration-blocker list makes clear it's load-bearing for ~19 feature areas), but it should be explicitly labeled and budgeted as a retiring asset with the Phase 9/Phase-3 migration plan as its retirement schedule, rather than continuing to receive net-new feature investment in parallel with `v3`. `rules` (localStorage-backed) and `monitoring` (hand-rolled, unshared patterns) are legacy in spirit even though recently touched — both look like early prototypes that were never upgraded to the codebase's now-established conventions.

### 9. Technical Debt Register
| Priority | Item | Effort | Impact |
|---|---|---|---|
| Critical | Shadow duplication across routes/state-components/hooks/registries/packages (see Top 20 #1–10) | 2–4 weeks | Removes the single largest maintainability drag in the frontend |
| Critical | `v3` missing loading/error/not-found + client-only auth guard with no `middleware.ts` | 2–4 days | Closes a real production UX/security-hygiene gap |
| High | `application/*` vs `lib/*Queries` fork | 1 ADR + 2–4 weeks phased migration | Removes the root cause of the hook-duplication pattern, not just its symptoms |
| High | `admin` feature scope (10+ unrelated domains in one folder) | 1–2 weeks to extract | Fixes the most severe modularity violation found |
| High | V3 migration backlog (19 route groups, 6 partial pages) | 75–100 eng-days | This is the actual product-completeness gap, not incidental debt |
| Medium | `revenue-execution` god-file + duplicate NBA widgets | 3–5 days | Localized, contained fix |
| Medium | Route-page god-components in legacy tree (5+ files 700–999 lines) | Ongoing, opportunistic | Improves maintainability of the tree being retired anyway — low priority relative to migration work |
| Low | `rules`/`monitoring` prototype-quality features | 2–3 days each | Cosmetic/completeness, not urgent |

### 10. Final Frontend Score
**50 / 100** (see Phase 7 for the full dimension breakdown). The number reads low for a codebase with a genuinely good platform layer underneath it — that's the point: architecture quality where it exists is undermined by how much of the rest of the tree is an unfinished duplicate of something else.

### 11. Final Recommendation

**If I were the Frontend Architect of SalesOS, this is exactly how I would evolve the frontend over the next 12 months:**

I would not start with `v3` feature parity. I would start with a two-week deletion sprint — the 8 empty packages, the dead application-layer files, the three orphaned features, the duplicate lazy-loading registry — because every one of those is a zero-risk, evidence-confirmed removal that immediately shrinks the surface area every subsequent decision has to account for. This is the cheapest, fastest way to make the codebase's real shape legible again, to the team and to whoever reviews it next.

Then I would spend a month on the shared layer specifically: one state-component library, one error boundary, one data-access convention (`application/*`, because it already covers the majority of real features and is the better long-term pattern), one canonical company/data-fetching module. This is where the actual leverage is — every route ported into `v3` afterward inherits a clean foundation instead of another set of ad hoc choices to disambiguate later.

Only then would I sequence the v3 migration itself — by business value, not file count, starting with whatever the sales/BD/investment personas from the product bible actually live in day-to-day (company workspace CRUD, pipeline, opportunities) rather than the currently-implemented order. I would treat `(dashboard)` explicitly as a retiring asset on a published schedule, not a permanent second tree, and stop letting it receive genuinely new functionality in parallel with `v3` — every feature built into legacy-only from this point forward is next year's migration backlog item.

**What I would remove:** the eight empty packages, without ceremony — they represent good intentions, not working software, and a monorepo package graph should describe what's true, not what was once planned. I would also remove the “admin as a feature” framing entirely; it’s not a peer of `company-intelligence`, it’s a different kind of thing, and modeling it honestly (its own tier) will make both it and the product features easier to reason about.

**What I would redesign:** nothing at the platform-layer level — `runtime`/`renderer`/`widget-sdk`/`workspace` is a good design that simply needs to be the *only* design, consistently applied. The redesign needed is organizational, not technical: one convention per concern, enforced by the file-size and no-new-package-without-a-consumer rules, so the shadow-copy pattern that produced today's state can't recur as the team scales.

**What I would leave unchanged:** the `dashboard` feature's registry pattern and the `company-intelligence`/`revenue-execution` detail-page work — these are the parts of the codebase that already look like the target architecture. The job over the next 12 months isn't to invent a better frontend architecture for SalesOS. It's to finish building the one that's already, partially, sitting right there.

---

*This review is grep- and read-based (no Node/npm/madge/depcheck available in this environment). Dead-code and unused-package findings are strong leads with concrete evidence, not tool-verified certainty — re-confirm with `depcheck`/`ts-prune`/`madge` before deleting anything at scale, and check for dynamic imports or barrel re-exports this pass may have missed.*
