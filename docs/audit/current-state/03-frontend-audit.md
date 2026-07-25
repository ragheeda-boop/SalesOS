# 03 — Frontend Current-State Audit

> **Generated:** 2026-07-14
> **Scope:** `salesos/frontend/` — Next.js App Router, Tailwind CSS, React Query, Radix UI
> **Methodology:** Manual file-by-file inspection of routes, pages, components, hooks, features, and packages

---

## Table of Contents

1. [Tech Stack Summary](#1-tech-stack-summary)
2. [Routes & Pages](#2-routes--pages)
3. [Layouts](#3-layouts)
4. [Components](#4-components)
5. [Hooks](#5-hooks)
6. [Contexts & Providers](#6-contexts--providers)
7. [Feature Modules](#7-feature-modules)
8. [Internal Packages](#8-internal-packages)
9. [Utilities & Libraries](#9-utilities--libraries)
10. [Dependency Map](#10-dependency-map)

---

## 1. Tech Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | latest |
| Runtime | React 19 | ^19.0 |
| Styling | Tailwind CSS | latest (custom `muhide` theme) |
| State / Server | TanStack React Query | ^5.60 |
| UI Primitives | Radix UI (Dialog, Dropdown, Tabs, Toast, Tooltip, Avatar, Select) | ^1.x / ^2.x |
| Forms | react-hook-form + @hookform/resolvers + zod | ^7.54 / ^3.9 / ^3.23 |
| Charts | Recharts | ^2.15 |
| Tables | @tanstack/react-table | ^8.20 |
| HTTP | Axios | ^1.7 |
| Icons | lucide-react | ^0.460 |
| Utility | clsx + tailwind-merge + class-variance-authority | latest |
| i18n | Custom (ar/en, localStorage-persisted) | — |
| State (global) | Zustand (via @salesos/runtime) | — |

---

## 2. Routes & Pages

All routes live under `src/app/`. Each `page.tsx` is a `"use client"` component.

| Route | File | Status | Description |
|-------|------|--------|-------------|
| `/` | `src/app/page.tsx` | ✅ Active | Landing page with login/register links |
| `/login` | `src/app/(auth)/login/page.tsx` | ✅ Active | Email/password login form, calls `useLogin()` |
| `/register` | `src/app/(auth)/register/page.tsx` | ✅ Active | Registration form, calls `useRegister()` |
| `/dashboard` | `src/app/(dashboard)/page.tsx` | ✅ Active | Delegates to `<DashboardPage />` (executive dashboard) |
| `/companies` | `src/app/(dashboard)/companies/page.tsx` | ✅ Active | Company list with search, filter, create modal |
| `/companies/[id]` | `src/app/(dashboard)/companies/[id]/page.tsx` | ✅ Active | Company detail — renders `<CompanyWorkspace>` |
| `/contacts` | `src/app/(dashboard)/contacts/page.tsx` | ✅ Active | Full CRUD contacts table with search/pagination (~500 lines) |
| `/activities` | `src/app/(dashboard)/activities/page.tsx` | ✅ Active | Global activity feed with filters |
| `/employees/me` | `src/app/(dashboard)/employees/me/page.tsx` | ✅ Active | Current employee 360 view |
| `/employees/[id]` | `src/app/(dashboard)/employees/[id]/page.tsx` | ✅ Active | Employee 360 view (delegates to `<Employee360View>`) |
| `/opportunities` | `src/app/(dashboard)/opportunities/page.tsx` | ✅ Active | Pipeline kanban board (delegates to `<PipelineKanban>`) |
| `/opportunities/[id]` | `src/app/(dashboard)/opportunities/[id]/page.tsx` | ✅ Active | Opportunity detail page |
| `/pipeline` | `src/app/(dashboard)/pipeline/page.tsx` | ✅ Active | DecisionProvider + PipelineWorkspace |
| `/revenue` | `src/app/(dashboard)/revenue/page.tsx` | ✅ Active | RevenueWorkspace (revenue health, forecast, opportunities) |
| `/forecast` | `src/app/(dashboard)/forecast/page.tsx` | ✅ Active | Forecast cards with direct API call |
| `/meetings` | `src/app/(dashboard)/meetings/page.tsx` | ✅ Active | Meeting briefs from AI |
| `/search` | `src/app/(dashboard)/search/page.tsx` | ✅ Active | Fulltext/semantic/hybrid search page |
| `/ai` | `src/app/(dashboard)/ai/page.tsx` | ✅ Active | Prompt template manager |
| `/copilot` | `src/app/(dashboard)/copilot/page.tsx` | ✅ Active | Embedded `<CopilotPanel>` (fullscreen mode) |
| `/decisions` | `src/app/(dashboard)/decisions/page.tsx` | ✅ Active | Decision center with accept/dismiss |
| `/monitoring` | `src/app/(dashboard)/monitoring/page.tsx` | ✅ Active | System metrics dashboard (CPU, memory, API, active users) |
| `/graph` | `src/app/(dashboard)/graph/page.tsx` | ✅ Active | D3 force-directed knowledge graph (~1000 lines) |
| `/signals` | `src/app/(dashboard)/signals/page.tsx` | ✅ Active | Signal marketplace/feed/subscriptions |
| `/rules` | `src/app/(dashboard)/rules/page.tsx` | ✅ Active | Delegates to `<RulesWorkspace>` |
| `/rag` | `src/app/(dashboard)/rag/page.tsx` | ✅ Active | Delegates to `<RagWorkspace>` |
| `/automation` | `src/app/(dashboard)/automation/page.tsx` | ✅ Active | Delegates to `<AutomationWorkspace>` |
| `/analytics` | `src/app/(dashboard)/analytics/page.tsx` | ✅ Active | Delegates to `<AnalyticsWorkspace>` |
| `/customer-success` | `src/app/(dashboard)/customer-success/page.tsx` | ✅ Active | Delegates to `<CustomerSuccessWorkspace>` |
| `/settings` | `src/app/(dashboard)/settings/page.tsx` | ✅ Active | Profile/security/notifications/API keys/data tabs (~600 lines) |
| `/admin` | `src/app/(dashboard)/admin/page.tsx` | ✅ Active | Delegates to `<AdminWorkspace>` |

**Total routes: 30**

---

## 3. Layouts

| File | Status | Description |
|------|--------|-------------|
| `src/app/layout.tsx` | ✅ Active | Root layout — locale detection script, Arabic/English i18n bootstrap, `<Providers>` wrapper |
| `src/app/(auth)/layout.tsx` | ✅ Active | Auth layout (if present) |
| `src/app/(dashboard)/layout.tsx` | ✅ Active | Full AppShell — sidebar nav, `<CommandBar>`, `<SearchPanel>`, `<CopilotPanel>`, `<MobileNav>`, theme toggle, notification bell |

**Layout details:**

- **Root Layout** (`src/app/layout.tsx`): Sets HTML `lang` and `dir` attributes, injects inline script for locale detection from `localStorage` before paint to avoid FOUC, wraps children in `<Providers>`.
- **Dashboard Layout** (`src/app/(dashboard)/layout.tsx`): Uses `<AppShell>` foundation component with collapsible sidebar, keyboard shortcuts (`Ctrl+K` for command bar, `Ctrl+I` for copilot), mobile hamburger nav, and RTL-aware layout.

---

## 4. Components

### 4.1 Core Components (`src/components/`)

| File | Status | Description | Dependencies |
|------|--------|-------------|--------------|
| `executive-dashboard.tsx` | ✅ Active | Executive dashboard with KPI cards, progress bars, trend indicators — fetches via `useExecutiveDashboard()` | `@salesos/ui`, `lucide-react`, `@/lib/hooks/executiveQueries` |
| `company-workspace.tsx` | ✅ Active | Tabbed company detail view (overview/intelligence/contacts/government/documents/timeline/AI) — renders 10 company-intelligence widgets | `@salesos/ui`, `company-intelligence/widgets/*`, `@/lib/hooks/companyQueries`, `company360Queries` |
| `employee-360-view.tsx` | ✅ Active | Full employee 360° view with stats, metrics, activity timeline, pipeline, AI insights — 5 tabs (overview/activity/pipeline/AI/timeline) | `@salesos/ui`, `employeeQueries`, `timeline-widget` |
| `copilot-panel.tsx` | ✅ Active | AI chat panel — message history, streaming responses, collapsed/expanded/fullscreen modes, entity context | `@salesos/ui`, `api`, `useTenant`, `useTranslation` |
| `pipeline-kanban.tsx` | ✅ Active | Drag-and-drop pipeline kanban — 4 stages (prospecting/qualification/proposal/negotiation), create via Radix dialog, advance/close mutations | `@radix-ui/react-dialog`, `@salesos/ui`, `opportunityQueries`, `companyQueries` |
| `search-panel.tsx` | ✅ Active | Modal search overlay — debounced unified search, grouped results by type, keyboard navigation | `@salesos/ui`, `useUnifiedSearch`, `useFocusTrap` |
| `command-bar.tsx` | ✅ Active | Command palette (Cmd+K) — filterable command list, keyboard navigation, executes registered commands | `@salesos/hooks` (useCommands, useKeyboard), `@salesos/ui`, `useFocusTrap` |
| `timeline-widget.tsx` | ✅ Activity timeline | Renders entity activity feed with action-specific icons/colors, relative timestamps (Arabic) | `@salesos/ui`, `activityQueries` |
| `error-boundary.tsx` | ✅ Active | React error boundary | — |
| `skeleton.tsx` | ✅ Active | Loading skeleton components | — |

### 4.2 Foundation Components (`src/components/foundation/`)

| File | Status | Description |
|------|--------|-------------|
| `app-shell.tsx` | ✅ Active | App shell with collapsible sidebar, `AppShellContext` (sidebarCollapsed, commandOpen), route announcer for a11y |
| `card.tsx` | ✅ Active | Card layout component |
| `error-boundary.tsx` | ✅ Active | Foundation-level error boundary |
| `LanguageSwitcher.tsx` | ✅ Active | Arabic/English language toggle |
| `MobileNav.tsx` | ✅ Active | Mobile hamburger navigation |
| `index.ts` | ✅ Active | Barrel export |

### 4.3 Guidance Components (`src/components/guidance/`)

| File | Status | Description |
|------|--------|-------------|
| `tour/` | ✅ Active | Guided tour system — `TourProvider`, `TourOverlay`, `useTour`, `TOUR_REGISTRY`, `TOUR_LABELS` |
| `coach-mark/` | ✅ Active | Coach mark tooltips — `CoachMarkProvider`, `useCoachMark`, `CoachMarkBubble`, `CoachMarkRenderer` |
| `empty-states/` | ✅ Active | Empty state components — `EmptyState`, `EmptyPipeline`, `EmptyNBA`, `EmptyWorkflows`, `EmptyRAG`, `EmptyMeetings`, `EmptyAnalytics` |
| `onboarding/` | ✅ Active | Onboarding checklist — `OnboardingProvider`, `OnboardingChecklist`, `useOnboarding` |
| `index.ts` | ✅ Active | Barrel export |

### 4.4 Layout Components (`src/components/layout/`)

Contains layout-related components (directory exists, not individually audited).

---

## 5. Hooks

All hooks live in `src/lib/hooks/`. Each is a React Query wrapper or utility hook.

### 5.1 Query Hooks (React Query)

| File | Exported Hooks | Status | Description |
|------|---------------|--------|-------------|
| `companyQueries.ts` | `useCompany`, `useCompanySearch`, `useCompanySearchCursor` | ✅ Active | Company detail, search, infinite cursor pagination |
| `company360Queries.ts` | `useCompany360` | ✅ Active | Company 360° aggregated data |
| `contactQueries.ts` | `useContactSearch`, `useContact`, `useCreateContact`, `useUpdateContact`, `useDeleteContact` | ✅ Active | Full contact CRUD with React Query mutations |
| `employeeQueries.ts` | `useEmployee360`, `useMy360` | ✅ Active | Employee 360 view and current user's 360 |
| `opportunityQueries.ts` | `useOpportunities`, `useCreateOpportunity`, `useAdvanceOpportunity`, `useCloseWon`, `useCloseLost` | ✅ Active | Opportunity pipeline CRUD and stage mutations |
| `activityQueries.ts` | `useEntityActivity`, `useGlobalActivities` | ✅ Activity feeds | Entity-specific and global activity queries |
| `executiveQueries.ts` | `useExecutiveDashboard` | ✅ Active | Executive dashboard data (60s stale, 120s refetch) |
| `searchQueries.ts` | `useSearch` | ✅ Active | Unified search query (enabled when query >= 2 chars) |
| `taskQueries.ts` | `useTasks`, `useCompleteTask` | ✅ Active | Task list and completion mutation |
| `ruleQueries.ts` | `useRules`, `useCreateRule`, `useUpdateRule`, `useDeleteRule`, `useToggleRule` | ✅ Active | Business rules CRUD (localStorage-backed) |
| `adminQueries.ts` | 25+ hooks (health, metrics, tenants, plans, users, flags, jobs, ai-costs, roles, permissions, audit) | ✅ Active | Full admin panel data layer |
| `mutationHooks.ts` | `useLogin`, `useRegister`, `useCreateCompany`, `useUpdateCompany`, `useDeleteCompany`, `useBulkEnrich` | ✅ Active | Auth mutations + company CRUD + bulk enrichment |

### 5.2 Utility Hooks

| File | Exported Hooks | Status | Description |
|------|---------------|--------|-------------|
| `useTenant.ts` | `getTenantId`, `useTenant` | ✅ Active | Extracts `tenant_id` from localStorage or JWT payload |
| `useUnifiedSearch.ts` | `useUnifiedSearch` | ✅ Active | Debounced hybrid search with abort, grouped results, suggestions |
| `useFocusTrap.ts` | `useFocusTrap` | ✅ Active | Keyboard focus trap for modals/overlays (Tab cycling, restore on close) |

---

## 6. Contexts & Providers

| Provider | Location | Status | Description |
|----------|----------|--------|-------------|
| `QueryClientProvider` | `src/app/providers.tsx` | ✅ Active | TanStack React Query client |
| `I18nProvider` | `src/lib/i18n/index.tsx` | ✅ Active | Custom i18n — ar/en locales, `t()` function, `dir` (RTL/LTR), localStorage persistence |
| `RuntimeContext` | `src/app/providers.tsx` | ✅ Active | Runtime context from `@salesos/runtime` |
| `ToastViewport` | `src/app/providers.tsx` | ✅ Active | Radix Toast viewport |
| `AppShellContext` | `src/components/foundation/app-shell.tsx` | ✅ Active | Sidebar collapsed state + command bar open state |
| `DashboardProvider` | `src/features/dashboard/_providers/` | ✅ Active | Dashboard-specific context (widget registry, telemetry) |
| `CompanyIntelligenceProvider` | `src/features/company-intelligence/_providers/` | ✅ Active | Company intelligence widget context |
| `TourProvider` | `src/components/guidance/tour/` | ✅ Active | Guided tour state |
| `CoachMarkProvider` | `src/components/guidance/coach-mark/` | ✅ Active | Coach mark state |
| `OnboardingProvider` | `src/components/guidance/onboarding/` | ✅ Active | Onboarding checklist state |

---

## 7. Feature Modules

All features live in `src/features/`. Each follows a Container/View pattern with widgets.

### 7.1 Dashboard (`src/features/dashboard/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `DashboardLayout` | ✅ Active | Dashboard grid layout |
| `DashboardGrid` | ✅ Active | Responsive widget grid |
| `DashboardErrorBoundary` | ✅ Active | Dashboard-level error boundary |
| `DashboardLoading` | ✅ Active | Dashboard loading state |
| `DashboardProvider` / `useDashboardContext` | ✅ Active | Dashboard context with widget registry |
| `createRegistry` | ✅ Active | Widget registry factory |
| `WIDGET_CONFIG` / `getWidgetConfig` | ✅ Active | Widget configuration map |
| `dashboardTelemetry` | ✅ Active | Dashboard telemetry collector |
| **SDK** (`sdk/`) | ✅ Active | Widget SDK — `createWidget()`, `createDashboardWidget()`, `createDecisionWidget()`, contract tests, feature flags, lifecycle, permissions, telemetry |
| **Widgets** | ✅ Active | `ai-brief/`, `company-health/`, `decision-queue/`, `intelligence-feed/`, `market-pulse/`, `mission-center/`, `pipeline/`, `recent-activity/`, `widget-card.tsx` |

### 7.2 Company Intelligence (`src/features/company-intelligence/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `CompanyIntelligenceProvider` | ✅ Active | Provider for company intelligence widgets |
| `CompanyIntelligenceGrid` | ✅ Active | Widget grid layout |
| `COMPANY_INTELLIGENCE_WIDGET_CONFIG` | ✅ Active | Widget configuration |
| **Widgets (10)** | ✅ Active | `smart-timeline/`, `signals-feed/`, `decision-makers/`, `relationship-graph/`, `ai-recommendation/`, `company-dna/`, `government-intelligence/`, `document-intelligence/`, `buying-journey/`, `golden-record/` |

### 7.3 Company Intelligence Layout/Registry

| Component | Status | Description |
|-----------|--------|-------------|
| `_layout/` | ✅ Active | Company intelligence layout |
| `_providers/` | ✅ Active | Company intelligence provider |
| `_registry/` | ✅ Active | Widget registry |

### 7.4 Employee Intelligence (`src/features/employee-intelligence/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `_layout/` | ✅ Active | Employee intelligence layout |
| `_providers/` | ✅ Active | Employee intelligence provider |
| `widgets/` | ✅ Active | Employee intelligence widgets |
| `workspace/` | ✅ Active | Employee workspace |

### 7.5 Revenue Execution (`src/features/revenue-execution/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `_layout/` | ✅ Active | Revenue execution layout |
| `_providers/` | ✅ Active | Revenue execution provider |
| `_registry/` | ✅ Active | Widget registry |
| `widgets/` | ✅ Active | `revenue-health/`, `forecast-intelligence/`, `opportunity-list/`, `meeting-intelligence/` |
| `workspace/` | ✅ Active | Revenue workspace |

### 7.6 Search (`src/features/search/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `CommandBar` | ✅ Active | Command palette (re-exported) |
| `QuickOverlay` | ✅ Active | Quick search overlay |
| `SearchPage` | ✅ Active | Full search page |
| `AIAnswerCard` | ✅ Active | AI-generated search answers |
| `_layout/` | ✅ Active | Search layout |
| `_providers/` | ✅ Active | Search provider |
| `ai-search/` | ✅ Active | AI search components |
| `command-bar/` | ✅ Active | Command bar feature module |
| `components/` | ✅ Active | Search-specific components |
| `quick-overlay/` | ✅ Active | Quick overlay feature |
| `search-page/` | ✅ Active | Search page feature |

### 7.7 Analytics (`src/features/analytics/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `AnalyticsWorkspace` | ✅ Active | Analytics workspace container |
| `AnalyticsContainer` | ✅ Active | Analytics data container |
| `AnalyticsView` | ✅ Active | Analytics view |
| `FeedbackWidget` | ✅ Active | Feedback collection widget |
| `types.ts` | ✅ Active | Analytics type definitions |

### 7.8 Automation (`src/features/automation/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `widgets/` | ✅ Active | Automation widgets |
| `workspace/` | ✅ Active | Automation workspace |

### 7.9 Rules (`src/features/rules/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `RulesWorkspace` | ✅ Active | Full rules CRUD UI — domain tabs (company/opportunity/scoring/workflow), condition/action builder, trigger types, localStorage persistence (~494 lines) |

### 7.10 RAG (`src/features/rag/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `widgets/` | ✅ Active | RAG widgets |
| `workspace/` | ✅ Active | RAG workspace |

### 7.11 Customer Success (`src/features/customer-success/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `widgets/` | ✅ Active | Customer success widgets |
| `workspace/` | ✅ Active | Customer success workspace |

### 7.12 Admin (`src/features/admin/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `AdminWorkspace` | ✅ Active | Admin panel — 8 tabs (overview/tenants/plans/users/flags/jobs/ai-costs/health) with sidebar nav |
| `widgets/` | ✅ Active | `TenantList`, `PlanManager`, `UserList`, `FeatureFlagManager`, `JobList`, `AICostDashboard`, `HealthDashboard` |

### 7.13 Monitoring (`src/features/monitoring/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `MonitoringWidget` | ✅ Active | System monitoring widget |

### 7.14 Demo (`src/features/demo/`)

| Component | Status | Description |
|-----------|--------|-------------|
| `DemoBadge` | ✅ Active | Demo mode badge |
| `DemoResetButton` | ✅ Active | Demo data reset |
| `ScenarioLauncher` | ✅ Active | Demo scenario launcher |

---

## 8. Internal Packages

All 13 packages live in `packages/` as workspace dependencies (version `5.0.0` unless noted).

| Package | Version | Dependencies | Description |
|---------|---------|-------------|-------------|
| `@salesos/ui` | 5.0.0 | Radix UI (Avatar, Dialog, Dropdown, Select, Tabs, Toast, Tooltip, Slot), lucide-react, clsx, tailwind-merge, CVA, @tanstack/react-table | Core UI component library — buttons, cards, badges, inputs, modals, tabs, toasts, tables |
| `@salesos/hooks` | 5.0.0 | React, axios, @tanstack/react-query | Shared hooks — `useCommands`, `useKeyboard`, `useDebounce`, `registerCommand` |
| `@salesos/design-language` | 5.0.0 | (none) | Design tokens, AI_ACTIONS constants, brand definitions |
| `@salesos/icons` | 5.0.0 | React, lucide-react | Icon wrapper/re-export package |
| `@salesos/charts` | 5.1.0 | React, recharts, @salesos/ui | Chart components (recharts wrappers) |
| `@salesos/forms` | 5.0.0 | React, react-hook-form, @hookform/resolvers, zod | Form utilities — zod validation, field wrappers |
| `@salesos/config` | 5.0.0 | (none) | App configuration constants |
| `@salesos/runtime` | 5.0.0 | React, @tanstack/react-query, axios, zod | Runtime context, API client, validation |
| `@salesos/renderer` | 5.0.0 | React, @salesos/ui, @salesos/icons, @salesos/charts, @salesos/forms, @salesos/runtime, clsx | Widget renderer — renders widget configs into UI |
| `@salesos/workspace` | 5.0.0 | React, @salesos/ui, @salesos/icons, @salesos/charts, @salesos/runtime, @salesos/hooks, @salesos/design-language, @salesos/renderer | Workspace container framework |
| `@salesos/search` | 1.0.0 | React, @salesos/workspace | Search workspace components |
| `@salesos/platform` | 0.1.0 | (none) | Platform kernel — contracts for AI recommendations, revenue opportunities |
| `@salesos/workspace-generator` | 5.0.0 | (none) | Code generation tool for new workspaces |

### Package Dependency Graph

```
@salesos/ui (base)
├── @salesos/icons → lucide-react
├── @salesos/charts → recharts, @salesos/ui
├── @salesos/forms → react-hook-form, zod
├── @salesos/config
├── @salesos/design-language
├── @salesos/hooks → axios, @tanstack/react-query
├── @salesos/runtime → axios, @tanstack/react-query, zod
├── @salesos/renderer → ui, icons, charts, forms, runtime
├── @salesos/workspace → ui, icons, charts, runtime, hooks, design-language, renderer
├── @salesos/search → workspace
└── @salesos/platform
```

---

## 9. Utilities & Libraries

### 9.1 Core Utilities (`src/lib/`)

| File | Status | Description |
|------|--------|-------------|
| `api.ts` | ✅ Active | Axios instance with auth interceptors (Bearer token from localStorage), 401/422/403 handling, redirect to `/login`. Exports ~60 typed API functions for all domains (companies, contacts, opportunities, employees, search, admin, decisions, monitoring, RAG, telemetry, tasks, rules, workflow, analytics, graph) |
| `utils.ts` | ✅ Active | `cn()` (clsx + twMerge), `formatDate()` (Arabic locale), `formatNumber()` (Arabic locale) |
| `commands.ts` | ✅ Active | Registers 9 built-in commands — navigation (G+D dashboard, G+C companies, G+S search, G+, settings, G+A admin) and actions (Ctrl+I copilot, Ctrl+K search, Ctrl+T theme, ? help) |
| `queryKeys.ts` | ✅ Active | Centralized React Query key factory — companies, search, tenants, dashboard, company360, employees, contacts, activities, tasks, opportunities, pipeline, admin (15+ sub-keys), rules, decisions |
| `dynamic-imports.tsx` | ✅ Active | 15 `next/dynamic` wrappers — all heavy widgets lazy-loaded with skeleton placeholders (SearchPanel, CopilotPanel, ExecutiveDashboard, PipelineKanban, TimelineWidget, MissionCenter, SmartTimeline, SignalsFeed, RelationshipGraph, CompanyDNA, AIRecommendation, DecisionMakers, BuyingJourney, RevenueHealth, Forecast, OpportunityList, MeetingIntelligence) |
| `monitoring.ts` | ✅ Active | Client-side monitoring — `Monitor` class that batches events (api_call, error, render, metric, page_load, web_vital) and flushes to `/api/v1/monitoring/events` every 60s or at 100 events |
| `monitoring-init.ts` | ✅ Active | Monitoring initialization |
| `analytics.ts` | ✅ Active | Analytics utilities |
| `decisionQueries.ts` | ✅ Active | Decision platform query hooks |
| `ragQueries.ts` | ✅ Active | RAG query hooks |
| `telemetryQueries.ts` | ✅ Active | Telemetry query hooks |
| `workflowQueries.ts` | ✅ Active | Workflow query hooks |

### 9.2 i18n (`src/lib/i18n/`)

| File | Status | Description |
|------|--------|-------------|
| `index.tsx` | ✅ Active | Custom I18nProvider — locale detection (localStorage → browser language → default "en"), `t(key, params)` with interpolation, `dir` (RTL/LTR) applied to `<html>`, locale persistence |
| `ar.json` | ✅ Active | Arabic translations (full locale file) |
| `en.json` | ✅ Active | English translations (full locale file) |

### 9.3 API Layer (`src/lib/api/`)

Directory exists for additional API modules (supplements the main `api.ts`).

---

## 10. Dependency Map

### External Dependencies (from `package.json`)

| Dependency | Version | Purpose |
|-----------|---------|---------|
| next | latest | Framework |
| react / react-dom | ^19.0 | Runtime |
| @tanstack/react-query | ^5.60 | Server state management |
| axios | ^1.7 | HTTP client |
| zod | ^3.23 | Schema validation |
| recharts | ^2.15 | Charts |
| d3 / d3-force | — | Knowledge graph visualization |
| @tanstack/react-table | ^8.20 | Data tables |
| @radix-ui/* (7 packages) | ^1.x / ^2.x | UI primitives |
| react-hook-form + @hookform/resolvers | ^7.54 / ^3.9 | Forms |
| lucide-react | ^0.460 | Icons |
| clsx + tailwind-merge + class-variance-authority | latest | Styling utilities |
| zustand | — | Client state (via @salesos/runtime) |

### Internal Package Dependencies

```
App → @salesos/workspace → @salesos/renderer → @salesos/ui
                                              → @salesos/icons
                                              → @salesos/charts
                                              → @salesos/forms
                                              → @salesos/runtime
              ↳ @salesos/hooks
              ↳ @salesos/design-language

App → @salesos/search → @salesos/workspace

App → @salesos/platform (kernel, contracts)
```

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Routes / Pages | 30 |
| Layouts | 2-3 |
| Core Components | 10 |
| Foundation Components | 6 |
| Guidance Components | 4 systems (tour, coach-mark, empty-states, onboarding) |
| Query Hook Files | 12 |
| Utility Hook Files | 3 |
| Context Providers | 10 |
| Feature Modules | 14 |
| Internal Packages | 13 |
| Utility/Library Files | 12+ |
| Dynamic Imports (lazy widgets) | 15 |
| Registered Commands | 9 |

---

## Key Architectural Patterns

1. **Container/View Pattern**: Features use Container components (data fetching) + View components (pure UI), connected via providers
2. **Widget SDK**: Dashboard widgets created via `createWidget()` / `createDashboardWidget()` with contract tests, permissions, feature flags, telemetry
3. **Workspace Pattern**: Complex pages use Workspace components that compose multiple widgets in a tabbed/grid layout
4. **React Query everywhere**: All API data flows through React Query with centralized key factories
5. **Lazy loading**: All heavy widgets wrapped in `next/dynamic` with skeleton placeholders
6. **RTL-first**: Arabic is the primary language, RTL layout applied at `<html>` level
7. **Multi-tenant**: Tenant ID extracted from JWT/localStorage, passed as `X-Tenant-Id` header
8. **Command palette**: Keyboard-driven navigation via `@salesos/hooks` command registry
9. **Progressive enhancement**: Focus trap, route announcer, reduced motion support
