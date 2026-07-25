# SalesOS Component Inventory

> Generated: 2026-07-16
> Source: `salesos/frontend/`
> Scope: All reusable UI components across `@salesos/ui`, `@salesos/charts`, `@salesos/forms`, `@salesos/icons`, `@salesos/renderer`, `@salesos/workspace`, and `src/components/`

---

## 1. UI Primitives (`packages/ui/src/`)

| # | Component | File | Purpose | Key Props | Uses Design Tokens |
|---|-----------|------|---------|-----------|:---:|
| 1 | **Button** | `packages/ui/src/button.tsx` | Action trigger with variants, sizes, loading state, icon slots | `variant: 'primary'\|'secondary'\|'outline'\|'ghost'\|'danger'`, `size: 'sm'\|'md'\|'lg'`, `loading?: boolean`, `leftIcon?: ReactNode`, `rightIcon?: ReactNode`, `asChild?: boolean` | ✅ `--muhide-orange`, `--bg-secondary`, `--border-default`, `--text-primary`, `--bg-tertiary` |
| 2 | **Card** / **CardHeader** / **CardContent** / **CardFooter** | `packages/ui/src/card.tsx` | Content container with header/body/footer anatomy | `extends HTMLAttributes<HTMLDivElement>` | ✅ `--border-default`, `--bg-primary`, `shadow-muhide-1` |
| 3 | **Modal** / **ModalTrigger** / **ModalContent** / **ModalHeader** / **ModalBody** / **ModalFooter** | `packages/ui/src/modal.tsx` | Dialog overlay with portal rendering, close button, sub-components | `open?: boolean`, `onOpenChange?: (open) => void` | ✅ `--bg-primary`, `shadow-muhide-4`, `z-overlay`, `z-modal` |
| 4 | **Input** | `packages/ui/src/input.tsx` | Text input with label, error, left/right icon support | `label?: string`, `error?: string`, `leftIcon?: ReactNode`, `rightIcon?: ReactNode` | ✅ `--border-default`, `--bg-primary`, `--text-primary`, `--text-muted`, `--muhide-orange` |
| 5 | **Select** | `packages/ui/src/select.tsx` | Dropdown selector via Radix, with error state | `options: {label,value}[]`, `placeholder?: string`, `error?: string`, `value?: string`, `onChange?: (value) => void` | ✅ `--border-default`, `--bg-primary`, `--text-primary`, `--text-muted`, `--muhide-orange` |
| 6 | **Table** | `packages/ui/src/table.tsx` | Data table with @tanstack/react-table, loading skeletons, empty state | `columns: ColumnDef<TData>[]`, `data: TData[]`, `loading?: boolean`, `onRowClick?: (row) => void` | ✅ `--border-default`, `--bg-secondary`, `--text-secondary`, `--bg-tertiary`, `--text-muted` |
| 7 | **Tabs** / **TabsList** / **Tab** / **TabsPanel** | `packages/ui/src/tabs.tsx` | Tabbed navigation via Radix | `value?: string`, `onValueChange?: (v) => void`, `defaultValue?: string` | ✅ `--border-default`, `--muhide-orange`, `--text-muted`, `--text-secondary`, `--text-primary` |
| 8 | **Badge** | `packages/ui/src/badge.tsx` | Small status label with semantic color variants | `variant: 'default'\|'primary'\|'success'\|'warning'\|'danger'\|'outline'` | ✅ `--muhide-orange`, semantic color tokens |
| 9 | **Spinner** | `packages/ui/src/spinner.tsx` | Loading indicator via lucide Loader2 | `className?: string` | ✅ `--text-muted` |
| 10 | **Toast** / **ToastProvider** / **ToastViewport** / **useToast** | `packages/ui/src/toast.tsx` | Notification toasts with variants, auto-dismiss, context-based API | `variant: 'default'\|'success'\|'error'`, `title?: string`, `description?: string`, `duration?: number` | ✅ `--bg-primary`, `--text-primary`, `--border-default`, semantic color tokens |
| 11 | **Tooltip** | `packages/ui/src/tooltip.tsx` | Hover tooltip via Radix with arrow | `content: ReactNode`, `side?: 'top'\|'right'\|'bottom'\|'left'` | ✅ `--muhide-ink`, `shadow-muhide-2` |
| 12 | **Avatar** | `packages/ui/src/avatar.tsx` | User avatar with image, fallback initials, sizes | `src?: string`, `alt?: string`, `fallback?: string`, `size: 'sm'\|'md'\|'lg'` | ✅ `--bg-secondary`, `--text-muted` |
| 13 | **Dropdown** / **DropdownTrigger** / **DropdownContent** / **DropdownItem** | `packages/ui/src/dropdown.tsx` | Context menu via Radix | `disabled?: boolean` (on DropdownItem) | ✅ `--border-default`, `--bg-primary`, `shadow-muhide-4`, `--text-primary`, `--bg-secondary` |
| 14 | **Kbd** | `packages/ui/src/kbd.tsx` | Keyboard shortcut display | `children: string` | ✅ `--border-default`, `--bg-secondary`, `--text-secondary`, `shadow-muhide-1` |
| 15 | **Sidebar** | `packages/ui/src/sidebar.tsx` | Navigation sidebar with items, children, collapsible | `items: SidebarItem[]`, `collapsed?: boolean`, `onToggle?: () => void` | ✅ `--border-default`, `--bg-primary`, `--muhide-orange`, `--text-muted`, `--text-primary`, `--bg-secondary` |
| 16 | **Layout** / **LayoutHeader** / **LayoutSidebar** / **LayoutContent** | `packages/ui/src/layout.tsx` | Full-page layout shell with header, sidebar, main content | `children: ReactNode`, `className?: string` | ✅ `--border-default`, `--bg-primary`, `z-sticky` |

### Duplicate Watch
- **Card** exists in both `packages/ui/src/card.tsx` (canonical) and `src/components/foundation/card.tsx` (deprecated — see §6). The foundation version has additional `variant`, `padding`, `accent` props missing from the canonical.
- No other UI primitive duplicates found.

---

## 2. Chart Components (`packages/charts/src/`)

| # | Component | File | Purpose | Key Props | Notes |
|---|-----------|------|---------|-----------|-------|
| 17 | **BarChart** | `packages/charts/src/index.tsx` | Vertical bar chart via Recharts | `data: ChartDataPoint[]`, `title?: string`, `height?: number`, `className?: string` | Color mapped from palette or auto-assigned |
| 18 | **LineChart** | `packages/charts/src/index.tsx` | Multi-series line chart | `series: ChartSeries[]`, `title?: string`, `height?: number`, `className?: string` | `ChartSeries = { name, color, data: number[] }` |
| 19 | **PieChart** | `packages/charts/src/index.tsx` | Pie/donut chart with percentage labels | `data: ChartDataPoint[]`, `title?: string`, `className?: string` | Label format: `"{name} {percent}%"` |
| 20 | **MetricCard** | `packages/charts/src/index.tsx` | KPI card with value, label, trend | `label: string`, `value: string`, `trend?: { direction, percentage }`, `icon?: ReactNode` | Hardcoded Tailwind colors (not CSS vars) |

### Issues
- **BarChart** uses `#3B82F6` etc. hardcoded, not `--muhide-*` tokens
- All charts use raw Tailwind `gray-*` colors — not dark-mode CSS variable aware
- Single file export — consider splitting per chart type

---

## 3. Form Components (`packages/forms/src/`)

| # | Component | File | Purpose | Key Props | Notes |
|---|-----------|------|---------|-----------|-------|
| 21 | **FormRenderer** | `packages/forms/src/index.tsx` | Schema-driven form renderer with validation | `definition: FormDefinition`, `form: UseFormReturn`, `onSubmit`, `errors?: FormErrors` | Uses zod + react-hook-form |
| 22 | **FormField** | `packages/forms/src/index.tsx` | Individual field renderer per type | `field: FormFieldDefinition`, `register`, `error?: string` | Supports: string, number, boolean, email, url, date, enum, textarea |
| 23 | **useFormFromDefinition** | `packages/forms/src/index.tsx` | Hook to build zod schema + form from definition | `formDef: FormDefinition`, `options?: UseFormProps` | Returns typed `UseFormReturn` |

### Issues
- Uses hardcoded `blue-500`/`blue-600` instead of `--muhide-orange` tokens
- Not connected to `@salesos/ui` Input/Select primitives (wraps raw HTML)

---

## 4. Icon System (`packages/icons/src/`)

| # | Export | File | Purpose | Notes |
|---|--------|------|---------|-------|
| 24 | **IconSize**, **iconSizeMap**, **IconProps** | `packages/icons/src/index.ts` | Icon size constants and props type | Export maps sizes to pixel values |
| 25 | **85+ lucide-react re-exports** | `packages/icons/src/index.ts` | Curated icon subset for application | All from lucide-react; re-exported for centralized imports |

### Issues
- Pure re-export file — no custom icons or wrapper components
- Consider adding an `<Icon>` component that applies `iconSizeMap` automatically

---

## 5. Schema Renderer (`packages/renderer/src/`)

| # | Component | File | Purpose | Key Props |
|---|-----------|------|---------|-----------|
| 26 | **SchemaRenderer** | `packages/renderer/src/schema-renderer.tsx` | Entry point: render a UI schema definition | `schema: UISchema`, `loading?: boolean`, `error?: string` |
| 27 | **ViewerRenderer** | `packages/renderer/src/viewer-renderer.tsx` | Tabbed entity viewer with action buttons | `entityType: string`, `entityId: string`, `tabs: UISchemaTab[]`, `actions?: UIAction[]` |
| 28 | **TabRenderer** | `packages/renderer/src/tab-renderer.tsx` | Renders a single tab's sections + widgets | `tab: UISchemaTab`, `entityType`, `entityId`, `context` |
| 29 | **SectionRenderer** | `packages/renderer/src/section-renderer.tsx` | Renders a section with grid layout + node renderers | `section: UISchemaSection`, `entityType`, `entityId`, `context` |
| 30 | **WidgetRenderer** | `packages/renderer/src/widget-renderer.tsx` | Card wrapper for a single widget with loading/error states | `widgetId: string`, `loading?: boolean`, `error?: string` |

### UISchema Types (`types.ts`)
- `UISchema` → tabs + actions + context
- `UISchemaTab` → sections + widgetIds
- `UISchemaSection` → columns, widgets, nodes (text/badge/metric/link/list/table)

### Issues
- Hardcoded `blue-600` spinner color in SchemaRenderer
- SectionRenderer's `renderNode` uses `any` types
- No design token integration

---

## 6. Foundation Components (`src/components/foundation/`)

| # | Component | File | Purpose | Key Props | Design Tokens |
|---|-----------|------|---------|-----------|:---:|
| 31 | **AppShell** | `src/components/foundation/app-shell.tsx` | Root application shell with sidebar state, Cmd+K binding, a11y | `children`, `defaultSidebarCollapsed?: boolean` | ✅ `--bg-primary`, `--text-primary` |
| 32 | **Card** (deprecated) | `src/components/foundation/card.tsx` | Legacy Card with variant/accent — `@deprecated` in favor of `@salesos/ui` | `variant: 'default'\|'dark'\|'bordered'`, `padding: 'sm'\|'md'\|'lg'`, `accent: 'orange'\|'amber'\|'blue'\|'green'\|'purple'\|'red'` | ✅ Uses tokens but adds accent variant missing from canonical |
| 33 | **ErrorFallback** | `src/components/foundation/error-boundary.tsx` | Error state UI with retry, details disclosure | `title?: string`, `message?: string`, `onRetry?: () => void`, `showDetails?: boolean`, `errorDetails?: string` | ✅ `--text-primary`, `--text-muted`, `--bg-tertiary`, `--muhide-orange`, `--focus-ring` |
| 34 | **MobileNav** | `src/components/foundation/MobileNav.tsx` | Mobile navigation drawer with fab button | None (reads pathname, i18n) | ✅ `--muhide-orange`, `--bg-primary`, `--border-default`, `--text-primary`, `--text-secondary`, `--bg-secondary` |
| 35 | **LanguageSwitcher** | `src/components/foundation/LanguageSwitcher.tsx` | Ar↔En locale toggle button | `className?: string` | ✅ `--text-muted`, `--text-primary`, `--bg-secondary`, `--border-default`, `--muhide-orange` |

---

## 7. Feature Components (`src/components/`)

| # | Component | File | Purpose | Key Props | Lines |
|---|-----------|------|---------|-----------|:---:|
| 36 | **ExecutiveDashboard** | `src/components/executive-dashboard.tsx` | Top-level KPI dashboard with pipeline health, growth, renewals | None (uses `useExecutiveDashboard` hook) | 282 |
| 37 | **PipelineKanban** | `src/components/pipeline-kanban.tsx` | Drag-and-drop pipeline kanban board with 6 stages | None (uses opportunity queries) | 547 |
| 38 | **CompanyWorkspace** | `src/components/company-workspace.tsx` | Multi-tab company 360 profile with intelligence widgets | `companyId: string` | 301 |
| 39 | **Employee360View** | `src/components/employee-360-view.tsx` | Employee 360 profile with KPI, activity, pipeline, AI coach | `employeeId: string` | 570 |
| 40 | **TimelineWidget** | `src/components/timeline-widget.tsx` | Activity timeline for an entity | `entityType: string`, `entityId: string`, `title?: string`, `limit?: number`, `className?: string` | 133 |
| 41 | **SearchPanel** | `src/components/search-panel.tsx` | Modal full-text search across entities | `open: boolean`, `onClose: () => void` | 154 |
| 42 | **CopilotPanel** | `src/components/copilot-panel.tsx` | AI chat assistant panel with entity context | `open: boolean`, `onClose: () => void`, `entityType?: string`, `entityId?: string`, `context?: Record`, `embedded?: boolean` | 240 |
| 43 | **CommandBar** | `src/components/command-bar.tsx` | Cmd+K command palette with search, categories, keyboard nav | `open: boolean`, `onClose: () => void` | 155 |
| 44 | **Skeleton** / **WidgetSkeleton** | `src/components/skeleton.tsx` | Loading skeleton with variants | `variant: 'text'\|'title'\|'avatar'\|'card'\|'list'`, `lines?: number`, `title?: string` | 99 |
| 45 | **ErrorBoundary** | `src/components/error-boundary.tsx` | Class-based error boundary with retry + i18n | `children`, `fallback?: ReactNode`, `onError?` | 102 |

### Pattern: Container/View
Feature components follow the Container pattern:
- **ExecutiveDashboard** → uses `useExecutiveDashboard()` hook
- **PipelineKanban** → uses `useOpportunities()`, `useCreateOpportunity()`, etc.
- **CompanyWorkspace** → uses `useCompany()`, `useCompany360()`
- **Employee360View** → uses `useEmployee360()`

---

## 8. Workspace Widget SDK (`packages/workspace/src/`)

| # | Component | File | Purpose | Key Props |
|---|-----------|------|---------|-----------|
| 46 | **createWidget** | `packages/workspace/src/create-widget.tsx` | Widget factory — creates a memoized component with lifecycle, telemetry, permissions, feature flags, 4-state renderer | `config: WidgetConfig<T>` (metadata, lifecycle, useData, render, fallback) |
| 47 | **createWorkspaceWidget** | `packages/workspace/src/create-workspace-widget.tsx` | Higher-level factory that connects to workspace context | `config: WorkspaceWidgetConfig`, `useWorkspaceContext`, `widgetSelector`, `overrides` |
| 48 | **createWorkspaceProvider** | `packages/workspace/src/workspace-provider.tsx` | Generic workspace context provider factory | `useData: (props) => { data, isLoading, isError, error, refetch }`, `deriveWidgets` |
| 49 | **WorkspaceGrid** | `packages/workspace/src/workspace-grid.tsx` | CSS Grid layout for widgets | `columns?: number` (default 6), `gap?: string`, `style?: CSSProperties` |
| 50 | **WorkspaceLoading** | `packages/workspace/src/workspace-loading.tsx` | Shimmer skeleton grid matching widget layout | `entries: WorkspaceWidgetEntry[]` |
| 51 | **WorkspaceErrorBoundary** | `packages/workspace/src/workspace-error-boundary.tsx` | Per-widget error boundary with telemetry | `widgetId: string`, `workspaceId?: string`, `fallback?: ReactNode` |
| 52 | **createRegistry** | `packages/workspace/src/workspace-registry.ts` | Registry factory for workspace widgets | — |
| 53 | **deriveStatus** | `packages/workspace/src/derive-status.ts` | Utility: derive WidgetStatus from data | — |

### Widget SDK Key Types (`types.ts`)
- `WidgetStatus: 'ready' \| 'loading' \| 'degraded' \| 'error'`
- `WidgetData<T>: { data, status, lastUpdated, error, refetch }`
- `WidgetRenderContext<T>: { data, status, lastUpdated, metadata, refresh }`
- `WidgetConfig<T>: { metadata, lifecycle?, useData, render, fallback? }`

### Workspace Prebuilt Widgets

| # | Component | File | Purpose | Key Props |
|---|-----------|------|---------|-----------|
| 54 | **RevenueCommandCenter** | `packages/workspace/src/revenue-command-center.tsx` | Revenue ops dashboard with pipeline, forecast, hot accounts, AI decisions | `metrics: RevenueMetrics`, `onViewAll?: (section) => void` |
| 55 | **GlobalActivityFeed** | `packages/workspace/src/global-activity-feed.tsx` | Filterable activity feed with entity/type filters, AI toggle | `events: ActivityEvent[]`, `global?: boolean` |
| 56 | **UniversalInbox** | `packages/workspace/src/universal-inbox.tsx` | Inbox with priority badges, type filters, unread toggle, actionable items | `items: InboxItem[]`, `onItemClick?`, `onAction?` |
| 57 | **AIOperatingAssistant** | `packages/workspace/src/ai-operating-assistant.tsx` | Multi-step workflow assistant with quick actions, step visualization, history | `open: boolean`, `onClose: () => void`, `onExecute?: (query) => Promise<void>` |

### Widget Lifecycle Hooks (`widget-lifecycle.ts`)
| # | Export | Purpose |
|---|--------|---------|
| 58 | **useWidgetLifecycle** | Manages mount/unmount/refresh/error lifecycle callbacks |
| 59 | **widgetTelemetry** | Timer-based telemetry recorder (`startTimer`, `record`) |
| 60 | **setPermissionChecker** / **checkPermissions** | Permission gate for widgets |
| 61 | **setFeatureFlagResolver** / **isFeatureEnabled** | Feature flag gate for widgets |

### Testing Utilities (`testing/`)
| # | Export | Purpose |
|---|--------|---------|
| 62 | **describeWidgetContract** | Test framework for Widget Contract tests |
| 63 | **renderWidget** | Widget render helper for tests |
| 64 | **mockWidgetContext** | Mock context provider |
| 65 | **mockTelemetry** | Mock telemetry recorder |
| 66 | **mockPermissions** | Mock permission checker |
| 67 | **mockFeatureFlags** | Mock feature flag resolver |

---

## 9. Guidance Components (`src/components/guidance/`)

| # | Component | File | Purpose | Key Props |
|---|-----------|------|---------|-----------|
| 68 | **TourProvider** | `guidance/tour/TourProvider.tsx` | Context provider for app tours with progress, persistence | None (wraps tree) |
| 69 | **TourOverlay** | `guidance/tour/TourOverlay.tsx` | Tour step spotlight overlay | (reads tour context) |
| 70 | **CoachMarkProvider** | `guidance/coach-mark/CoachMarkProvider.tsx` | Context provider for coach marks | None |
| 71 | **CoachMarkBubble** | `guidance/coach-mark/CoachMarkBubble.tsx` | Positioned hint bubble anchored to DOM target | `hintId: string`, `target: string` (CSS selector), `message: string`, `tourId?: string` |
| 72 | **CoachMarkRenderer** | `guidance/coach-mark/CoachMarkRenderer.tsx` | Renders active hints from provider state | None |
| 73 | **OnboardingProvider** | `guidance/onboarding/OnboardingProvider.tsx` | Context for onboarding checklist | None |
| 74 | **OnboardingChecklist** | `guidance/onboarding/OnboardingChecklist.tsx` | Onboarding checklist UI | None |
| 75 | **EmptyState** | `guidance/empty-states/EmptyState.tsx` | Generic empty state with icon, title, description | (variants per context) |
| 76 | **EmptyAnalytics** / **EmptyMeetings** / **EmptyPipeline** / **EmptyNBA** / **EmptyRAG** / **EmptyWorkflows** | `guidance/empty-states/` | Domain-specific empty states | (contextual) |

### Tour Definitions (`guidance/tour/tours/`)
| # | Tour | File | Steps |
|---|------|------|-------|
| 77 | `welcome` | `guidance/tour/tours/welcome.ts` | — |
| 78 | `pipeline` | `guidance/tour/tours/pipeline.ts` | — |
| 79 | `workflow` | `guidance/tour/tours/workflow.ts` | — |
| 80 | `nba` | `guidance/tour/tours/nba.ts` | — |
| 81 | `rag` | `guidance/tour/tours/rag.ts` | — |

---

## 10. Design Language (`packages/design-language/src/`)

| # | Module | File | Purpose |
|---|--------|------|---------|
| 82 | **color** | `design-language/src/color.ts` | MUHIDE color palette tokens |
| 83 | **typography** | `design-language/src/typography.ts` | Type scale and font families |
| 84 | **spacing** | `design-language/src/spacing.ts` | Spacing scale tokens |
| 85 | **elevation** | `design-language/src/elevation.ts` | Shadow/elevation tokens |
| 86 | **motion** | `design-language/src/motion.ts` | Animation duration/easing tokens |
| 87 | **animation** | `design-language/src/animation.ts` | Keyframe animation definitions |
| 88 | **layout** | `design-language/src/layout.ts` | Layout constants |
| 89 | **components** | `design-language/src/components.ts` | Component-level token overrides |
| 90 | **states** | `design-language/src/states.ts` | Component state tokens |
| 91 | **ai** | `design-language/src/ai.ts` | AI-specific tokens and AI_ACTIONS |
| 92 | **timeline** | `design-language/src/timeline.ts` | Timeline domain tokens |
| 93 | **workspace** | `design-language/src/workspace.ts` | Workspace domain tokens |
| 94 | **search-commands** | `design-language/src/search-commands.ts` | Search command definitions |
| 95 | **principles** | `design-language/src/principles.ts` | Design principles constants |
| 96 | **accessibility** | `design-language/src/accessibility.ts` | Accessibility constants |

---

## 11. Component Usage Map

| Imported By | Components Used |
|-------------|----------------|
| **executive-dashboard.tsx** | Card, CardContent, CardHeader, Badge, cn |
| **pipeline-kanban.tsx** | Badge, Button, Input, ModalContent, ModalTrigger, cn, Dialog |
| **company-workspace.tsx** | Avatar, cn, Tabs, TabsList, Tab, TabsPanel |
| **employee-360-view.tsx** | Avatar, Card, CardContent, CardHeader, Badge, cn, Tabs, TabsList, Tab, TabsPanel |
| **timeline-widget.tsx** | Card, CardContent, CardHeader, cn |
| **search-panel.tsx** | cn, Spinner |
| **copilot-panel.tsx** | cn, Spinner |
| **command-bar.tsx** | cn, Search |
| **Workspace widgets** | Card, CardHeader, CardContent, Spinner, Badge, cn, MetricCard, BarChart |

---

## 12. Duplicate & Gap Analysis

### Duplicates
1. **Card**: `packages/ui/src/card.tsx` (canonical) vs `src/components/foundation/card.tsx` (deprecated). Foundation version has `accent`/`padding`/`variant` props not in canonical. **Action**: Migrate accent variant to canonical or remove foundation version.
2. **ErrorBoundary**: `src/components/error-boundary.tsx` (class, app-level) vs `packages/workspace/src/workspace-error-boundary.tsx` (widget-specific). These serve different purposes — acceptable.
3. **Skeleton**: `src/components/skeleton.tsx` (variants) vs inline skeleton markup in 4 feature components. **Action**: Feature components should use Skeleton from `src/components/`.

### Gaps
1. **Design token adoption**: Charts package uses `gray-*` hardcoded colors, not CSS variables. Forms package uses `blue-500` instead of `--muhide-orange`.
2. **No DataTable** component: `@salesos/ui` Table is basic — no sorting, filtering, pagination built-in.
3. **No DatePicker**: Missing from forms and UI packages.
4. **No Combobox / Autocomplete**: SearchPanel is modal-only; no inline autocomplete component.
5. **No Drawer**: Sidebar and MobileNav are the only slide-in panels; no generic Drawer component.
6. **No EmptyState in `@salesos/ui`**: Empty states are in `guidance/empty-states/` — not exported from the UI package.

---

## 13. Summary

| Category | Count | Files | Design Token Compliant |
|----------|:-----:|-------|:---------------------:|
| UI Primitives | 16 | `packages/ui/src/` | ✅ All |
| Chart Components | 4 | `packages/charts/src/` | ❌ Hardcoded colors |
| Form Components | 3 | `packages/forms/src/` | ❌ Hardcoded blue |
| Icon System | 2 | `packages/icons/src/` | N/A (lucide re-exports) |
| Schema Renderer | 5 | `packages/renderer/src/` | ⚠️ Partial |
| Foundation | 5 | `src/components/foundation/` | ✅ All |
| Feature Components | 10 | `src/components/` | ✅ All |
| Workspace Widget SDK | 23 | `packages/workspace/src/` | ⚠️ Mixed (inline styles in create-widget) |
| Guidance | 15 | `src/components/guidance/` | ✅ All |
| Design Language | 15 | `packages/design-language/src/` | N/A (source of truth) |
| **Total** | **98** | — | — |
