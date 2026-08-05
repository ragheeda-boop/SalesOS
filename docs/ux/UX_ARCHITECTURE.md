# UX Architecture

> **Last updated:** 2026-08-06  
> **Authority:** Derived from executable evidence — route configs, component trees, token sources, and feature directories.  
> **Status:** Architecture audit + phased remediation plan.

---

## 1. Current State Analysis

### 1.1 Shell Architecture

The application currently runs **two parallel shells** that are disconnected and share no unified navigation context.

| Shell | Routes | Sidebar | Topbar | Entry Point |
|-------|--------|---------|--------|-------------|
| `(dashboard)` | 63 | 44 nav items, 6 workspace presets | Dashboard topbar | Main authenticated layout |
| `v3` | 23 | V3Shell sidebar | V3Topbar | Separate experimental layout |

**Critical issue:** `WorkspaceSwitcher` only updates React state (`selectedWorkspace`) and does **not** trigger navigation. Switching workspaces in the sidebar has no routing effect — the user remains on the same page regardless of the selected workspace context.

**Routing concerns:**
- No shared `<Layout />` wrapper between shells.
- Each shell independently manages its own `Navbar`, `Sidebar`, and `Main` content area.
- Cross-shell navigation is impossible; a user on a V3 route cannot reach dashboard routes without a full page reload via URL.
- Workspace-aware nav items are hardcoded per shell rather than resolved from a centralized workspace registry.

### 1.2 Component Architecture

| Layer | Count | Description |
|-------|-------|-------------|
| `@salesos/ui` primitives | 28 | `forwardRef` + `cva` + `cn` pattern; Button, Card, Dialog, Input, Select, Table, Tabs, etc. |
| Page-level components | 77 | Route-level pages across both shells |
| Feature directories | 17 | Domain-specific modules (deals, contacts, pipeline, analytics, admin, gtm, etc.) |
| Widget implementations | ~62 | Dashboard and feature widgets across the 17 directories |

**Widget factory** follows a 3-tier composition model:

```
createWidget           → Base widget (title, icon, size, layout)
  └─ createDashboardWidget → Adds grid position, refresh interval, role-based visibility
       └─ createDecisionEnabledWidget → Adds decision-platform hooks, evidence gate, score overlay
```

Widgets are registered in a central `widget-registry.ts` and resolved at render time by the dashboard grid. The registry supports lazy-loading via `React.lazy` per widget slot.

**Identified gaps:**
- No shared component for empty/loading/skeleton states — each feature reimplements placeholders.
- Decision-enabled widget layer exists but is gated behind `FEATURE_AI_COPILOT` (currently `False`).
- `@salesos/ui` lacks a `Skeleton`, `ProgressRing`, and `StatusBadge` variant.

### 1.3 Design Token Architecture

There are **4 conflicting token sources** with no single authority:

| Source | Location | Role |
|--------|----------|------|
| `tokens.ts` | `@salesos/tokens/src/tokens.ts` | TypeScript token definitions |
| `tokens.css` | `@salesos/tokens/src/tokens.css` | CSS custom properties (standalone) |
| `globals.css` | `salesos/frontend/app/globals.css` | Duplicate `:root` variable definitions |
| `semantic-tokens.ts` | `@salesos/tokens/src/semantic-tokens.ts` | Semantic aliases (color, spacing, typography) |

**Disconnection chain:**

```
tailwind.config.ts
  └─ ❌ Does NOT import tokens preset
       └─ Defines its own colors, spacing, fonts inline
            └─ Conflicts with tokens.css values

globals.css
  └─ ❌ Does NOT import tokens.css
       └─ Redefines --text-*, --bg-*, --border-* variables
            └─ Value mismatches vs tokens.css (e.g., --text-primary: #0F172A vs #111827)
```

**Value mismatches observed:**
- `--text-primary`: `tokens.css` = `#0F172A` (slate-900), `globals.css` = `#111827` (gray-900)
- `--bg-surface`: `tokens.css` = `#FFFFFF`, `globals.css` = `#FAFAFA`
- `--border-default`: `tokens.css` = `#E2E8F0` (slate-200), `globals.css` = `#E5E7EB` (gray-200)

**RTL overrides** add a 5th implicit layer: ~535 lines of `[dir="rtl"]` utility overrides that flip spacing, alignment, and directional properties. These are defined inline in component files rather than being token-driven.

### 1.4 Dashboard

The dashboard is **production-grade** and serves as the primary landing experience.

| Aspect | Detail |
|--------|--------|
| Grid | 6-column responsive CSS grid (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6`) |
| Widgets | 13 registry-driven widgets loaded from the widget registry |
| Privileged widgets | `MorningBrief` (greeting + agenda), `ExecutiveSummary` (KPIs), `QuickActions` (contextual shortcuts) |
| Role-based filtering | Widgets resolve visibility via `useWorkspaceRole()` hook |
| Refresh | Configurable `refreshInterval` per widget; defaults to 300s for data widgets, 0 for static |
| Loading | Each widget slot renders its own `<WidgetSkeleton />` during lazy load |

**Health:** No critical gaps. The dashboard pattern is well-established and should serve as the template for other workspaces.

### 1.5 Company 360

The Company 360 page is a **full-page shell (724 lines)** that is at approximately 60% completion.

| Section | Status | Details |
|---------|--------|---------|
| Header | Implemented | Company name, industry, logo placeholder |
| Health score ring | Implemented | Circular progress with score label; data source unverified |
| Tab navigation | Implemented | 5 tabs: Contacts, Deals, Documents, Next Steps, Signals |
| Contacts panel | **EmptyState** | Displays fallback placeholder |
| Deals panel | **EmptyState** | Displays fallback placeholder |
| Documents panel | **EmptyState** | Displays fallback placeholder |
| Next Steps panel | **EmptyState** | Displays fallback placeholder |
| Signals panel | **EmptyState** | Displays fallback placeholder |
| Quick action buttons | **UI-only** | 6 buttons rendered; no `onClick` handlers wired |
| Knowledge Graph | Placeholder | Panel exists in layout but shows "Coming Soon" |

**Quick actions (all stub):**
1. Add Contact — no handler
2. Create Deal — no handler
3. Upload Document — no handler
4. Schedule Meeting — no handler
5. Add Note — no handler
6. Send Email — no handler

**Root cause:** The data layer for company-scoped entities (contacts, deals, documents) exists in the API but no React Query hooks are called from these panels. The tabs render their shell and fall through to the `EmptyState` component.

### 1.6 Employee 360

The Employee 360 is **production-grade** and the most complete domain page.

| Aspect | Detail |
|--------|--------|
| Tabs | 5 tabs — all fully implemented (Performance, Skills, Goals, Feedback, Coaching) |
| Scoring | Dual-source: domain API (`/api/employees/{id}/scores`) + Decision Platform (`/api/v2/decision/employee-score`) |
| Coaching | Pure client-side algorithm generates 6 insight types from score deltas; no external AI dependency |
| Components | 14 sub-component files organized by tab domain |
| Loading | Lazy-loading via `React.lazy` with visited-tabs pattern (loads tab content only when selected) |
| Data refresh | `staleTime: 5 * 60 * 1000` per React Query configuration |

**Health:** This page should serve as the quality benchmark for other domain pages. No remediation needed beyond the optional executive variant navigation entry.

### 1.7 i18n & RTL

| Aspect | Detail |
|--------|--------|
| Keys per language | 1,172 (en and ar parity — 100%) |
| Locale resolution | Hardcoded to `"ar"` in `providers.tsx` (see Phase 1 fix) |
| RTL utilities | ~535 lines of directional overrides across component files |
| Font stack | Primary: IBM Plex Sans Arabic (ar) / Inter (en); Fallback: system-ui, sans-serif |
| Date/Number formatting | `Intl` API via `useLocale()` hook; currency formatted per locale |

**Concern:** The hardcoded locale in `providers.tsx` means the application ignores browser preferences, user settings, and URL-based locale switching. The `"ar"` default is unconditional.

### 1.8 AI Workspace

| Component | Status | Location |
|-----------|--------|----------|
| AI popup (floating) | Implemented | V3 shell only |
| Command palette | Implemented | Global `Cmd+K` with AI search |
| AI Copilot panel | Implemented | Split-pane: Insights tab + Chat tab |
| Chat branching | Implemented | Conversation fork/merge UI |
| User feedback | Implemented | Thumbs up/down per AI response |
| Feature flag | `FEATURE_AI_COPILOT=False` | `salesos/backend/app/config.py` |

**GA honesty note:** All AI workspace UI is rendered behind the feature flag. Without it, the copilot panel, AI popup, and insight generation are not accessible to users. The frontend `@salesos/decision` package is a stub that returns mock responses when the flag is off.

---

## 2. Target Architecture

### 2.1 Unified Shell

```
Single Shell (authenticated layout)
├── Global Topbar
│   ├── Search (Cmd+K)
│   ├── AI Copilot toggle
│   ├── Notifications center
│   └── User menu (profile, settings, logout)
│
├── Collapsible Sidebar
│   ├── Workspace switcher (navigates on change)
│   ├── Workspace-aware nav items (resolved from registry)
│   ├── Quick access / favorites
│   └── Collapse/expand toggle
│
├── Main Content Area
│   ├── Dashboard (role-based widget grid)
│   ├── Company 360 (enriched entity view)
│   ├── Employee 360 (complete)
│   ├── Pipeline Workspace (kanban + analytics)
│   ├── AI Workspace (copilot + decision center)
│   ├── Analytics (charts, reports, exports)
│   ├── GTM (go-to-market operations)
│   └── Admin Console (owner platform)
│
└── Quick Actions Bar (context-aware, docked bottom-right)
    └── Actions change based on current workspace and route
```

### 2.2 Key Principles

1. **Single layout root.** One `<Shell />` component with slots for topbar, sidebar, content, and quick actions.
2. **Workspace-aware navigation.** The sidebar reads `workspaceRegistry` and renders nav items filtered by current workspace and user role.
3. **WorkspaceSwitcher navigates.** Clicking a workspace triggers `router.push()` to the workspace home route.
4. **Tokens flow one way.** `@salesos/tokens` → `tokens.css` → `globals.css` → Tailwind preset → component usage.
5. **All pages meet Employee 360 quality bar.** Real data, full tabs, wired actions, loading skeletons, error boundaries.

---

## 3. Token Consolidation Plan

### 3.1 Target State

```
@salesos/tokens/                       ← Single source of truth
├── src/
│   ├── tokens.ts                      ← TypeScript definitions (dev DX)
│   ├── tokens.css                     ← CSS custom properties (runtime)
│   └── semantic-tokens.ts            ← Semantic aliases (maps to CSS vars)
│
├── dist/
│   ├── tokens.css                     ← Built output
│   └── tailwind-preset.js             ← Tailwind preset (imports tokens)
│
salesos/frontend/
├── app/globals.css                    ← @import "@salesos/tokens/dist/tokens.css"
├── tailwind.config.ts                 ← presets: [require("@salesos/tokens/tailwind-preset")]
└── postcss.config.js                  ← Already set up
```

### 3.2 Consolidation Steps

1. **Import `tokens.css` into `globals.css`** — add `@import "@salesos/tokens/dist/tokens.css"` at the top.
2. **Wire Tailwind preset** — update `tailwind.config.ts` to include `presets: [require("@salesos/tokens/tailwind-preset")]`.
3. **Remove duplicate `:root` block** from `globals.css` (the one redefining `--text-*`, `--bg-*`, `--border-*`).
4. **Remove inline color/space definitions** from `tailwind.config.ts` that conflict with the preset.
5. **Align `semantic-tokens.ts` values** to match the CSS custom property values from `tokens.css`.
6. **Drive RTL from tokens** — add `--rtl-scale: -1` / `--rtl-scale: 1` CSS variable and use `calc(var(--spacing-x) * var(--rtl-scale))` instead of 535 lines of hardcoded `[dir="rtl"]` overrides.

### 3.3 Validation

- Visual diff all pages in both `en` and `ar` locales.
- Confirm computed CSS values match token source across light and dark modes.
- Run `npx tailwindcss --content` build without warnings.

---

## 4. Implementation Phases

### UX Phase 1: Immediate Fixes (Week 1)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| P1-01 | Fix hardcoded locale `"ar"` in providers | `salesos/frontend/app/providers.tsx` | S |
| P1-02 | Wire `tailwind.config.ts` to tokens preset | `salesos/frontend/tailwind.config.ts` | S |
| P1-03 | Import `tokens.css` into `globals.css` | `salesos/frontend/app/globals.css` | S |
| P1-04 | Add `Skeleton` component to `@salesos/ui` | `packages/ui/src/skeleton.tsx` | M |
| P1-05 | Replace Company 360 EmptyStates with loading skeletons | `salesos/frontend/app/(dashboard)/company-360/` | S |
| P1-06 | Remove duplicate `:root` definitions from `globals.css` | `salesos/frontend/app/globals.css` | S |

**Validation:** `light validated` — visual check of Company 360 tabs, tailwind build, locale detection in browser.

### Phase 2: Company 360 Enrichment (Week 2–3)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| P2-01 | Wire Contacts panel to `/api/companies/{id}/contacts` | `company-360/contacts-panel.tsx` | M |
| P2-02 | Wire Deals panel to `/api/companies/{id}/deals` | `company-360/deals-panel.tsx` | M |
| P2-03 | Wire Documents panel to `/api/companies/{id}/documents` | `company-360/documents-panel.tsx` | M |
| P2-04 | Wire Next Steps to `/api/companies/{id}/next-steps` | `company-360/next-steps-panel.tsx` | M |
| P2-05 | Add `onClick` handlers for 6 quick action buttons | `company-360/page.tsx` (line ~680–710) | M |
| P2-06 | Connect Knowledge Graph to live data endpoint | `company-360/knowledge-graph.tsx` | L |
| P2-07 | Add health score data source | `company-360/health-ring.tsx` | S |
| P2-08 | Add empty state (not error state) for zero-data scenarios | All panels | S |

**Validation:** `build validated` — React Query devtools confirm data fetching; each panel renders real data or intentional empty state.

### Phase 3: Employee 360 Polish (Week 3)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| P3-01 | Verify data integration with live API | `employee-360/` | S |
| P3-02 | Add Employee 360 entry to sidebar nav (executive variant) | `sidebar-nav.tsx` | S |
| P3-03 | Add Employee 360 to workspace registry | `workspace-registry.ts` | S |
| P3-04 | Run coaching algorithm validation against known score deltas | `employee-360/coaching-tab.tsx` | M |

**Validation:** `light validated` — navigation entry appears for executive role; coaching insights match expected output for sample scores.

### Phase 4: AI Workspace (Week 4–5)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| P4-01 | Enable conditional copilot activation behind feature flag | `ai-copilot-provider.tsx` | M |
| P4-02 | Integrate Decision Platform feedback loop | `chat-tab.tsx`, `insights-tab.tsx` | L |
| P4-03 | Add AI-generated signals to dashboard widget | `dashboard/signals-widget.tsx` | M |
| P4-04 | Hook command palette to AI search endpoint | `command-palette.tsx` | M |
| P4-05 | Add chat history persistence | `chat-tab.tsx` | M |

**Validation:** `pilot-ready with conditions` — copilot returns real Decision Platform responses (not stubs); feedback round-trips to `/api/v2/decision/feedback`.

### Phase 5: Shell Unification (Week 5–6)

| # | Task | Effort |
|---|------|--------|
| P5-01 | Create unified `Shell` layout component | L |
| P5-02 | Merge `(dashboard)` and `v3` route trees under single layout | L |
| P5-03 | Implement workspace-registry-driven sidebar | L |
| P5-04 | Fix WorkspaceSwitcher to navigate on change | M |
| P5-05 | Add collapsible sidebar toggle | S |
| P5-06 | Migrate V3Shell pages to unified layout | L |
| P5-07 | Remove V3Shell and V3Topbar from component tree | S |

**Validation:** `build validated` — single layout renders for all routes; workspace switcher navigates; no V3-specific layout references remain.

---

## 5. Gaps by Feature

| Feature / Page | Status | Gap Severity | Notes |
|----------------|--------|--------------|-------|
| **Dashboard** | Production-ready | None | 13 widgets, 3 privileged, 6-col grid. Reference implementation. |
| **Company 360** | 60% complete | High | 5 EmptyState stubs, 6 unhandled quick actions, no knowledge graph data. |
| **Employee 360** | Production-ready | None | 5 tabs complete, dual-score, coaching algorithm. Gold standard. |
| **Pipeline** | Production-ready | None | Kanban + analytics. Deals CRUD functional. |
| **Revenue** | Production-ready | None | Revenue charts, forecasts, exports. |
| **Analytics** | Implemented | Low | Charts and reports render. Export may need CSV field mapping review. |
| **GTM** | Implemented | Low | Go-to-market operations pages. May need role-based filtering audit. |
| **AI Copilot** | Behind feature flag | Medium | UI exists but returns stubs. Decision Platform integration pending. |
| **Search** | Implemented | Low | Global search with results. May need cross-entity indexing. |
| **Admin Console** | Shell exists | Medium | Owner console layout present. Content panels need audit. |
| **V3 Shell** | Preview/stub | High | 23 routes in separate layout; many panels are placeholders. Merge into unified shell. |
| **Workspace Switcher** | Broken | High | Updates state but does not navigate. Critical UX bug. |
| **Empty States** | Inconsistent | Medium | Each feature implements its own; no shared pattern or skeleton component. |
| **Error Boundaries** | Missing | Medium | No per-route error boundaries. Unhandled React errors crash to Next.js error page. |
| **Loading Skeletons** | None in @salesos/ui | Medium | No `Skeleton` primitive. Each feature hand-rolls placeholder logic. |

---

## 6. Design System Health

| Metric | Current | Target |
|--------|---------|--------|
| Token sources | 4 (conflicting) | 1 (`@salesos/tokens`) |
| UI primitives | 28 | 32 (+ Skeleton, ProgressRing, StatusBadge, EmptyState) |
| Empty state pattern | Ad-hoc per feature | Single `<EmptyState />` component |
| Loading pattern | Varies | Single `<Skeleton />` component with variants (text, card, table) |
| RTL approach | 535 lines of inline overrides | Token-driven via `--rtl-scale` CSS variable |
| Error handling | Next.js default error page | Per-route `<ErrorBoundary />` with retry and home-link |

---

## 7. Navigation Registry (Proposed)

```typescript
// workspace-registry.ts (centralized)
interface WorkspaceEntry {
  id: string;
  labelKey: string;       // i18n key
  icon: LucideIcon;
  route: string;
  roles: string[];         // ["admin", "executive", "sales", "viewer"]
  children?: WorkspaceEntry[];
}

// Each workspace maps to its nav items
// Sidebar resolves `workspaceRegistry[activeWorkspace]`
// WorkspaceSwitcher sets `activeWorkspace` AND calls router.push(entry.route)
```

---

## 8. Definition of Done (per phase)

- **Phase 1:** Locale detected from browser/URL; Tailwind uses token preset; `globals.css` imports `tokens.css`; Company 360 shows skeletons instead of EmptyState.
- **Phase 2:** All 5 Company 360 tabs render real data; 6 quick actions trigger modals or navigate; Knowledge Graph shows live graph.
- **Phase 3:** Employee 360 appears in sidebar for executive role; coaching outputs verified.
- **Phase 4:** Copilot activates with `FEATURE_AI_COPILOT=True`; insights and chat use Decision Platform API.
- **Phase 5:** Single `Shell` layout renders for all routes; V3 layout removed; WorkspaceSwitcher navigates correctly.
