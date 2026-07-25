# EMPLOYEE 360 — COMPLETE ENGINEERING AUDIT

**Date:** 2026-07-25  
**Auditor:** Automated reverse-engineering across frontend, backend, database, permissions, tests  
**Status:** Read-only audit — no modifications made  
**Scope:** 82 files analyzed across 6 layers

---

# 1. PRODUCT VISION

## What is Employee 360?

Employee 360 is a **signal-driven workforce intelligence module** within SalesOS that provides a unified view of any employee's activities, performance scoring, timeline of actions, and AI coaching recommendations. It is accessible at two routes:

- `/employees/me` — self-service view for individual employees
- `/employees/[id]` — manager/admin view to inspect any employee

It is **not** a traditional HR system. There is no employee table — employees are simply `User` records in the `users` table (`salesos/backend/app/modules/identity/models.py:22`). The module layers **signals, scoring, and performance analytics** on top of the existing identity model.

## Business Objective

Provide sales managers and executives with **data-driven visibility** into rep activity, engagement, and performance — enabling coaching, risk detection, and workload balancing without requiring manual reporting.

## Target Users

| Role | Permission | Capability |
|------|-----------|------------|
| Admin | `employee.*` (all CRUD) | View any employee 360, bulk edit/delete, export |
| Manager | No `employee.*` permission | **Cannot access Employee 360** (permission gap) |
| User/Sales Rep | No `employee.*` permission | **Cannot access Employee 360** (permission gap) |

**Critical finding:** The `manager` role does NOT have `employee` permissions in `sdk/permissions.py:91-103`. Only `admin` role has `employee.*` and `employee-360.*` permissions. This means **managers cannot view their team members' 360 views** — a significant product gap.

## Problems Solved

1. Replaces manual activity tracking with automated signal collection from CRM, timeline, and workflow sources
2. Provides objective scoring (0-100) based on signal volume, recency, diversity, and completion rate
3. Detects at-risk employees via declining signals, low engagement, and score decline flags
4. Surfaces AI coaching actions based on pipeline health, win rate, and signal diversity

## Primary Workflows

1. **Self-check:** Rep navigates to `/employees/me` to see their own stats, score, and coach recommendations
2. **Manager review:** Admin navigates to `/employees/[id]` to inspect a rep's activity, signals breakdown, timeline, and performance vs peers
3. **List + bulk:** Admin views employee list at `/employees`, filters by role/name, bulk edits, exports CSV
4. **Signal collection:** System (or manual trigger via `POST /employees/{id}/signals/collect`) pulls signals from CRM, timeline, and workflow sources
5. **Analytics dashboard:** `/analytics/employees` shows aggregate metrics: headcount, avg score, score distribution, department breakdown

## KPIs (as surfaced in the UI)

| KPI | Source | Current State |
|-----|--------|---------------|
| Revenue | `EmployeeKPIs.revenue` from portfolio pipeline | Implemented |
| Pipeline value | `EmployeeKPIs.pipeline` | Implemented |
| Win rate | Won/(Won+Lost) | Implemented |
| Response rate | From ADR-012 Activity Intelligence `reply_rate` | Implemented |
| Follow-up rate | From ADR-012 Activity Intelligence `follow_up_rate` | Implemented |
| Activities count | `ActivityIntelligence.total` | Implemented |
| Productivity | `activities / 30` | Implemented (crude) |
| Forecast | `EmployeeKPIs.forecast` | Schema exists, always 0 |
| Signal volume score | From scoring engine | Implemented |
| Signal diversity score | From scoring engine | Implemented |
| Completion rate | From scoring engine | Implemented |
| Signal count | From signals summary | Implemented |

## User Value

- Sales reps see their own activity quantified with an objective score
- Reps receive AI-generated coaching actions (pipeline empty, low win rate, low diversity, declining signals)
- Managers can identify struggling reps before pipeline impact

## Company Value

- Data-driven sales coaching replaces gut-feel management
- Early warning on disengaged reps via risk flags
- Objective basis for performance reviews
- Single source of truth for rep activity across CRM, meetings, emails, and tasks

---

# 2. UX ARCHITECTURE

## Route Map

| Route | Component | Description |
|-------|-----------|-------------|
| `/employees` | `EmployeesPage` (`employees/page.tsx`, 749 lines) | Employee list with search, filter, bulk operations |
| `/employees/me` | `Employee360Page` with `employeeId={currentUserId}` | Self-service 360 view |
| `/employees/[id]` | `Employee360Page` with `employeeId={id}` | Admin 360 view |
| `/analytics/employees` | `EmployeesAnalyticsPage` | Aggregate analytics dashboard |

## Screen 1: Employee List (`/employees`)

### Components:
- **Search bar** — debounced text search (name, email) with 400ms debounce
- **Filters** — department dropdown (Sales, Marketing, Engineering, Support, Finance, HR, Operations), role dropdown (Executive, Manager, Sales Rep, Engineer, Analyst, Admin), signal min/max range
- **DataTable** — TanStack React Table with columns: checkbox, Name, Email, Role, Department, Signals, Score, Trend, Actions
- **Bulk operations toolbar** — Select All, Edit (modal for role/department/status), Export CSV, Delete (confirmation modal)
- **Pagination** — Cursor-based with Previous/Next navigation

### States:
- **Loading:** 10-row skeleton table
- **Empty:** "No employees found" + hint about team members being added
- **No search results:** Specific "No employees match your search" message
- **Error:** `ErrorFallback` component with retry
- **Bulk edit modal:** Edit form for role, department, status
- **Bulk delete modal:** Confirmation with warning text, count display

### Expandable Row:
- Clicking a row toggles an expanded view showing signals dashboard (signal type breakdown, source breakdown, trend) and score detail (trend, confidence, factors)

---

## Screen 2: Employee 360 (`/employees/me` and `/employees/[id]`)

### Layout: 5-tab interface

```
┌─────────────────────────────────────────────────┐
│ [Overview] [Signals] [Scoring] [Timeline] [Performance] │
├─────────────────────────────────────────────────┤
│              Tab Content Panel                   │
└─────────────────────────────────────────────────┘
```

**Tab bar:** Custom `Tabs` component from `@salesos/ui`. Active tab highlighted with `--muhide-orange` background tint. Icons: User, Activity, Brain, Clock, TrendingUp (lucide-react).

### Tab 1: Overview

**Loading State:** `OverviewSkeleton()` — 3 skeleton blocks (large profile card, 4 stat boxes, activity feed)

**Components:**
1. **ProfileCard** — gradient banner (info to purple to orange), Avatar (lg, 80px, initials fallback), full name (Arabic or English), role, email, active/inactive badge, phone link, email link, manager info, team avatars (up to 5 + overflow count)

2. **QuickStatsRow** — 2x2 grid of StatBoxes:
   - Total Signals (info color, Activity icon)
   - Current Score (purple, Brain icon)
   - Risk Level (dynamic color: high=red, medium=yellow, low=green, Shield icon)
   - Tenure (neutral, Clock icon, shows created_at month/year)

3. **RecentActivityFeed** — last 5 timeline events as a vertical timeline with connecting lines, action icons, source badges, relative timestamps ("5m ago", "2h ago", "3d ago")

**Error State:** Full-page `EmptyState` with User icon, error message, "Back" button via `window.history.back()`

### Tab 2: Signals

**Components:**
- **Signals by Type** — horizontal bar chart (svg bars) showing each signal type as label + bar + count
- **Signals by Source** — same format for source breakdown
- **Signal Trend (7 days)** — mini bar chart showing daily signal counts for last 7 days

**Loading:** 3 skeleton cards (3-column grid)
**Empty:** "No signals" + hint
**Error:** `ErrorFallback` with retry

### Tab 3: Scoring

**Components:**
- **Gauge Card** — SVG donut gauge (100px, 42px radius, 8px stroke), score text centered, trend icon (up/down/stable), confidence bar
- **Factors Card** — dual-source:
  - If Decision Platform scores exist: shows DP score factors (up to 6) with "Decision Platform" badge
  - If domain score only: shows 4 factors (Signal Volume, Recency, Diversity, Completion Rate) with horizontal bars

**Loading:** 2 skeleton cards
**Empty:** "No score available" + hint
**Error:** `ErrorFallback` with retry

### Tab 4: Timeline

**Components:**
- **Filter toggle button** with active filter count badge
- **Filter panel** (expandable card):
  - Source chips: crm, timeline, workflow, email, calendar, manual (multi-select)
  - Type chips: 9 signal types (multi-select)
  - Date range: From/To native date inputs
  - Apply button
- **Event list** — vertical timeline with connecting lines, per-event icon (color-coded per action type), title, source badge, actor, relative timestamp
- **"Load more" button** — cursor-based pagination (loads next page, appends to existing list)
- **"All events loaded"** end-of-list indicator
- **Clear filters** link (orange, with X icon)

**Loading:** Animated pulse skeleton with 5 timeline entries
**Empty (no events):** "No timeline events"
**Empty (with filters):** "No timeline events" + "Try different filters" hint
**Error:** `ErrorFallback` with retry

### Tab 5: Performance

**Components:**
- **Score Trend** — SVG line chart (400x150) with gradient fill, data points, date labels at bottom, trend direction icon (up/down/stable)
- **Peer Comparison** — 4 horizontal bar comparisons (Overall Score, Signal Volume, Diversity, Completion Rate) showing "You" (orange bar) vs "Dept Avg" (gray bar) with percentage values
- **Risk Flags** — colored cards per flag:
  - High severity: red bg, AlertTriangle icon, "danger" badge
  - Medium: yellow bg, Target icon, "warning" badge
  - Low: green bg, CheckCircle icon, "success" badge
- **Factors Breakdown** — same as scoring factors (4 bars)

**Loading:** 3 skeleton cards (2-column + 1 full-width)
**Empty:** "No performance data" + hint
**Error:** `ErrorFallback` with retry

---

## Screen 3: Employee Analytics (`/analytics/employees`)

### Components:
- **Metric cards** (4-card grid): Total Employees, Active Employees, Avg Score (+trend arrow), Avg Signals (+trend arrow)
- **BarChart** — Score by Department
- **PieChart** — Score Distribution (4 ranges: 90-100, 70-89, 50-69, 0-49)
- **LineChart** — Score Trend over time
- **Top Performers** — ranked list with rank badges (gold/silver/bronze for top 3)
- **Department Breakdown table** — Headcount, Avg Score, Performance bar
- **Date range selector** — 7d / 30d / 90d toggle
- **Export/Share bar**

### States:
- **Loading:** Animated pulse skeleton (4 metric cards + 2 chart placeholders)
- **Error:** "Failed to load employee analytics" + Retry button

### Architecture Issue:
The analytics page uses a **direct `useState` + `useEffect` + `api.get()` pattern** (lines 64-100) rather than React Query hooks. This is inconsistent with the rest of the module.

---

# 3. UI HIERARCHY

```
Employee 360 Page
├── Tab Navigation Bar
│   ├── Overview Tab (User icon)
│   ├── Signals Tab (Activity icon)
│   ├── Scoring Tab (Brain icon)
│   ├── Timeline Tab (Clock icon)
│   └── Performance Tab (TrendingUp icon)
│
├── [Overview Tab]
│   ├── ProfileCard
│   │   ├── Gradient Banner (info → purple → orange)
│   │   ├── Avatar (80px, initials fallback)
│   │   ├── Name (Arabic/English)
│   │   ├── Role + Email
│   │   ├── Active/Inactive Badge
│   │   ├── Phone link
│   │   ├── Email link
│   │   ├── Manager info (if exists)
│   │   └── Team avatars (max 5 + overflow count)
│   ├── QuickStatsRow
│   │   ├── Total Signals StatBox
│   │   ├── Current Score StatBox
│   │   ├── Risk Level StatBox
│   │   └── Tenure StatBox
│   └── RecentActivityFeed (Card)
│       └── Timeline entries (max 5)
│           ├── Color-coded icon circle
│           ├── Connecting line
│           ├── Event title
│           └── Source badge + relative time
│
├── [Signals Tab]
│   ├── Signals by Type Card
│   │   └── Horizontal bars (label + bar + count)
│   ├── Signals by Source Card
│   │   └── Horizontal bars (label + bar + count)
│   └── Signal Trend Card
│       └── Daily count bars (7 days)
│
├── [Scoring Tab]
│   ├── Gauge Card
│   │   ├── SVG donut chart (0-100)
│   │   ├── Score number (centered)
│   │   ├── Trend icon (up/down/stable)
│   │   └── Confidence bar
│   └── Factors Card
│       ├── Decision Platform factors (if available)
│       │   └── Score bars (0-100%)
│       └── Domain score factors (fallback)
│           └── Contribution bars
│
├── [Timeline Tab]
│   ├── Header bar
│   │   ├── Title
│   │   ├── Clear Filters link (conditional)
│   │   └── Filter toggle button (with active count badge)
│   ├── Filter Panel (expandable)
│   │   ├── Source multi-select chips
│   │   ├── Type multi-select chips
│   │   ├── Date From/To inputs
│   │   └── Apply button
│   ├── Event List
│   │   └── Timeline entries
│   │       ├── Color-coded icon circle
│   │       ├── Connecting line
│   │       ├── Event title
│   │       └── Source badge + actor + relative time
│   ├── Load More button (cursor pagination)
│   └── "All events loaded" indicator
│
└── [Performance Tab]
    ├── Score Trend Card
    │   ├── SVG line chart (30-day)
    │   ├── Gradient fill area
    │   ├── Data point circles
    │   └── Date labels
    ├── Peer Comparison Card
    │   └── 4 metric bars (You vs Dept Avg)
    ├── Risk Flags Card (conditional)
    │   └── Severity-coded flag cards
    └── Factors Breakdown Card (conditional)
        └── Contribution bars
```

---

# 4. VISUAL DESIGN

## Design Tokens

### Primary brand identity
- **Brand:** `--muhide-orange: #F57C1E`
- Source: `packages/design-language/src/semantic-tokens.ts`, `packages/design-system/src/tokens.ts`

### Color System (semantic tokens)
| Token | Purpose |
|-------|---------|
| `--bg-primary` | Main card/container background |
| `--bg-secondary` | Secondary surface |
| `--bg-tertiary` | Skeleton loading, subtle backgrounds |
| `--text-primary` | Headings, key values |
| `--text-secondary` | Secondary text, labels |
| `--text-muted` | Subtle info, metadata |
| `--text-disabled` | Placeholder, "no data" indicators |
| `--border-default` | Card borders, dividers |
| `--border-subtle` | Softer borders |

### Status/Semantic Colors (Tailwind-based)
| Color | Token | Use |
|-------|-------|-----|
| Success | `success-50/100/500/600/700` | Active badges, completed actions, low risk |
| Warning | `warning-50/100/500/600/700` | Medium risk, task items |
| Danger | `danger-50/100/500/600/700` | High risk, error states |
| Info | `info-50/100/500/600/700` | Signal counts, informational elements |
| Purple | `purple-600`, `chart-purple` | Score gauge, decision platform indicators |
| Orange | `--muhide-orange` | Active tab, chart lines, KPI bars |

### Chart Colors (12 colors from semantic-tokens.ts)
Used in analytics page charts (BarChart, PieChart, LineChart from `@salesos/charts`)

## Typography

| Element | Size | Weight | Class |
|---------|------|--------|-------|
| Page title (h1) | `text-xl` (20px) | `font-bold` | Employee name |
| Section headers | `text-sm` (14px) | `font-semibold` | Card titles |
| Body text | `text-sm` (14px) | `font-medium` | Event titles, labels |
| Meta/reduced text | `text-xs` (12px) | normal | Timestamps, source badges |
| Micro text | `text-[10px]` | various | Stat labels, badge text, chart labels |
| Stat values | `text-lg` (18px) | `font-bold` | Signal counts, score |
| Gauge value | `text-3xl` (30px) | `font-bold` | Score donut center |

## Spacing & Grid
- Container: `space-y-4` (16px vertical gap between major sections)
- Stats grid: `grid grid-cols-2 md:grid-cols-4 gap-3` (12px gap)
- Cards: `rounded-xl` (12px border radius)
- StatBoxes: `rounded-xl p-3` (12px padding)
- Tabs: `rounded-xl border border-[--border-default] px-2 py-1`
- Tab items: `rounded-lg px-3 py-2`
- Timeline gaps: `gap-3 pb-4`

## Shadows
- Profile avatar: `shadow-muhide-3`
- Profile card: `shadow-muhide-1`

## Avatars
- Profile: 80x80px (lg), `text-xl`, 4px white border
- Team members: 24x24px (sm), `text-[8px]`, 2px white border
- Overflow badge: 24x24px circle, `text-[8px]`

## Badges
- Status: "success" variant for active, "default" for inactive
- Score: Color-coded (green ≥70, yellow ≥40, red <40)
- Source in timeline: "default" variant, `text-[10px]`
- Risk severity: danger/warning/success, `text-[10px]`

## Icons
- Library: `lucide-react` (exclusively)
- Size: `h-4 w-4` for tab/icons, `h-5 w-5` for stat boxes, `h-8 w-8` for empty states, `h-10 w-10` for large empty states, `h-12 w-12` for error page

## Responsiveness
- Stat grid: 2 cols mobile → 4 cols desktop (`grid-cols-2 md:grid-cols-4`)
- Signals grid: 1 col mobile → 3 cols desktop (`grid-cols-1 md:grid-cols-3`)
- Scoring grid: 1 col → 3 cols
- Performance grid: 1 col → 2 cols
- Tab labels: hidden on small screens (`hidden sm:inline`)
- Profile: flex-wrap layout for header items

## Dark Mode
- All component styles include dark mode variants:
  - `dark:bg-danger-900/20`, `dark:bg-warning-900/20`, `dark:bg-success-900/20`
  - `dark:text-info-400`, `dark:text-success-400`, `dark:text-warning-400`, `dark:text-danger-400`
  - `dark:bg-neutral-700` for hover states
  - `dark:bg-[var(--bg-primary)]/20` for score background
- Full dark mode support via CSS variables and Tailwind dark: prefix

## Animations
- No explicit animations defined
- Skeleton loading uses `animate-pulse` (Tailwind)
- Tab transitions use `transition-colors`
- No page transitions, no micro-animations on data changes

## Accessibility
- Tab navigation uses `role="tablist"` and `role="tab"` (verified by E2E tests)
- Icons have no aria-labels (potential gap)
- Form inputs have labels
- SVG charts have no accessible alternatives (no `<title>`, no `<desc>`)
- "Back" action uses `window.history.back()` (no `Link` for proper routing)

---

# 5. FRONTEND ARCHITECTURE

## Routes (Next.js App Router)

| Path | File | Route Group |
|------|------|-------------|
| `/employees` | `app/(dashboard)/employees/page.tsx` | Dashboard layout |
| `/employees/me` | `app/(dashboard)/employees/me/page.tsx` | Dashboard layout |
| `/employees/[id]` | `app/(dashboard)/employees/[id]/page.tsx` | Dashboard layout |
| `/analytics/employees` | `app/(dashboard)/analytics/employees/page.tsx` | Dashboard layout |

## Navigation Registration
`app/(dashboard)/layout.tsx:35` registers two sidebar items:
- `{ href: "/employees", key: "nav.employees", icon: UserCheck }`
- `{ href: "/employees/me", key: "nav.profile", icon: User }`

## Component Tree

```
Employee360Page (1004 lines, client component)
├── Tabs (@salesos/ui) — controlled state, 5 tabs
│   ├── OverviewTab
│   │   ├── ProfileCard
│   │   ├── QuickStatsRow
│   │   │   └── StatBox (×4)
│   │   └── RecentActivityFeed
│   │       └── Timeline entries (max 5)
│   ├── SignalsTab
│   │   ├── Signals by Type Card
│   │   ├── Signals by Source Card
│   │   └── Signal Trend Card
│   ├── ScoringTab
│   │   ├── Gauge Card (SVG donut)
│   │   └── Factors Card
│   ├── TimelineTab
│   │   ├── Filter Panel (conditional)
│   │   ├── Event List (infinite-ish scroll)
│   │   └── Load More button
│   └── PerformanceTab
│       ├── Score Trend Card (SVG line)
│       ├── Peer Comparison Card
│       ├── Risk Flags Card
│       └── Factors Card
└── (Error state: EmptyState with back button)
```

## Hooks

| Hook | File | Query Key |
|------|------|-----------|
| `useEmployee360(id)` | `employeeQueries.ts:22` | `["employees", "detail", id]` |
| `useMy360()` | `employeeQueries.ts:31` | `["employees", "me"]` |
| `useEmployeeSearch(params)` | `employeeQueries.ts:39` | `["employees", "list", filters]` |
| `useEmployeeSignals(employeeId)` | `employeeQueries.ts:47` | `["employees", "signals", id]` |
| `useEmployeeScore(employeeId)` | `employeeQueries.ts:56` | `["employees", "score", id]` |
| `useEmployeeTimeline(employeeId, params)` | `employeeQueries.ts:65` | `["employees", "timeline", id, params]` |
| `useEmployeePerformance(employeeId)` | `employeeQueries.ts:74` | `["employees", "performance", id]` |
| `useBulkEditEmployees()` | `employeeQueries.ts:83` | mutation, invalidates `employeeKeys.lists()` |
| `useBulkDeleteEmployees()` | `employeeQueries.ts:95` | mutation, invalidates `employeeKeys.lists()` |
| `useExportEmployees()` | `employeeQueries.ts:107` | mutation |

## External Hook Dependencies
- `useDecisionScores(employeeId, 'employee')` — used in ScoringTab for Decision Platform scores (`lib/decisionQueries.ts`)

## React Query Configuration
| Setting | Value |
|---------|-------|
| staleTime (360, signals, score, performance) | 30 seconds |
| staleTime (search, timeline) | 15 seconds |
| gcTime | Default (5 min) |
| refetchOnWindowFocus | Default (true) |
| retry | Default (3) |

## Pagination
- Employee list: Keyset cursor pagination via `sdk/pagination.py` (decoded/encoded UUID+timestamp cursors)
- Timeline: Same keyset cursor pagination, client appends pages (no true infinite scroll — manual "Load More" button)
- Performance/signals/score: Non-paginated (always fetches full dataset for the employee)

## Charts
- Signals tab: **Custom SVG inline** (bars and donut) — NOT using `@salesos/charts`
- Scoring tab: **Custom SVG donut** (inline SVG with circle stroke-dasharray)
- Performance tab: **Custom SVG line chart** (inline SVG with polyline + gradient)
- Analytics page: Uses `@salesos/charts` library (BarChart, PieChart, LineChart, MetricCard)

**Key observation:** The Employee 360 page uses hand-rolled SVG charts rather than the shared `@salesos/charts` package, creating an inconsistency.

## Libraries
- `@salesos/ui` — Tabs, Skeleton, EmptyState, Badge, Avatar, Card, Button, DataTable, Modal, Input, Select, useToast
- `@salesos/charts` — BarChart, LineChart, PieChart, MetricCard (analytics page only)
- `@salesos/hooks` — useDebounce
- `@salesos/decision-platform` — Score type
- `@tanstack/react-query` — useQuery, useMutation, useQueryClient
- `@tanstack/react-table` — ColumnDef
- `lucide-react` — Icons
- `next/navigation` — useRouter, useSearchParams

## Suspense / Loading
- No React `<Suspense>` boundaries used
- Loading state handled inline within each tab sub-component via `isLoading` checks

## Optimistic Updates
- **Not implemented.** Bulk edit/delete invalidates query cache after server response, no optimistic UI.

## Infinite Scroll / Virtualization
- **Not implemented.** Timeline uses manual "Load More" button. No virtualization for large lists.

---

# 6. COMPONENT INVENTORY

## Core Components

### 1. `Employee360Page`
- **File:** `components/employee-360-page.tsx:934`
- **Purpose:** Top-level page component for Employee 360 view
- **Props:** `{ employeeId: string }`
- **Children:** Tabs with 5 tab panels
- **Dependencies:** useEmployee360, Tabs from @salesos/ui
- **Complexity:** HIGH — 1004 lines, 5 sub-components inline, handles routing, error, loading states
- **Performance:** Fetches employee 360 data via React Query; each tab lazily fetches its own data
- **Reuse:** Not reusable — specific to Employee 360 page

### 2. `ProfileCard`
- **File:** `employee-360-page.tsx:94`
- **Purpose:** Employee profile header with avatar, name, contact info, team
- **Props:** `{ data: Employee360Response, t: i18n function }`
- **Complexity:** MEDIUM — handles Arabic/English name fallback, active/inactive badge, conditional phone/email links, team avatar overflow
- **Performance:** Stateless display component

### 3. `QuickStatsRow`
- **File:** `employee-360-page.tsx:171`
- **Purpose:** 4-up stat boxes for signals, score, risk, tenure
- **Props:** `{ data, signals, scoreData }`
- **Complexity:** LOW — calculates risk level from score, passes to StatBox
- **Performance:** No concerns

### 4. `StatBox`
- **File:** `employee-360-page.tsx:70`
- **Purpose:** Reusable stat display with icon, label, value
- **Props:** `{ icon, label, value, color }`
- **Complexity:** LOW
- **Reuse:** HIGH — used 4× in QuickStatsRow, reusable across the app

### 5. `RecentActivityFeed`
- **File:** `employee-360-page.tsx:191`
- **Purpose:** Last 5 timeline events for overview tab
- **Props:** `{ employeeId: string }`
- **Complexity:** MEDIUM — loading skeleton, empty state, timeline rendering
- **Performance:** Fetches timeline with page_size=5, no virtualization

### 6. `OverviewTab`
- **File:** `employee-360-page.tsx:264`
- **Purpose:** Composes ProfileCard + QuickStatsRow + RecentActivityFeed
- **Props:** `{ employeeId, data }`
- **Complexity:** LOW — composition only

### 7. `OverviewSkeleton`
- **File:** `employee-360-page.tsx:82`
- **Purpose:** Loading skeleton for overview tab
- **Complexity:** LOW

### 8. `SignalsTab`
- **File:** `employee-360-page.tsx:280`
- **Purpose:** Signal breakdown by type, source, trend
- **Props:** `{ employeeId }`
- **Complexity:** MEDIUM — 3 cards with inline SVG bars
- **States:** loading (3 skeleton cards), error (ErrorFallback), empty (EmptyState), data (3-column grid)

### 9. `ScoringTab`
- **File:** `employee-360-page.tsx:387`
- **Purpose:** Score gauge + factor breakdown
- **Props:** `{ employeeId }`
- **External data:** Fetches both `useEmployeeScore` and `useDecisionScores`
- **Complexity:** HIGH — dual data sources, SVG gauge computation, fallback logic
- **Performance:** Two independent queries may cause double render

### 10. `TimelineTab`
- **File:** `employee-360-page.tsx:516`
- **Purpose:** Filterable event timeline with cursor pagination
- **Props:** `{ employeeId }`
- **Complexity:** HIGH — filter state management (5 filter dimensions), cursor stack tracking, append-on-load-more pattern
- **Performance:** Maintains full event list in state (`allEvents`), no virtualization — O(n) memory for large timelines
- **Known issue:** VIO-6 (direct `api` fetch pattern documented in gates)

### 11. `PerformanceTab`
- **File:** `employee-360-page.tsx:729`
- **Purpose:** Score trend chart, peer comparison, risk flags
- **Props:** `{ employeeId }`
- **Complexity:** HIGH — inline SVG line chart with gradient, max-score normalization, trend direction calculation, risk flag severity mapping
- **Performance:** No concerns at current data sizes

### 12. `ScoreBadge`
- **File:** `employee-360-page.tsx:58`
- **Purpose:** Color-coded score display (<40 red, <70 yellow, ≥70 green)
- **Props:** `{ score: number | null }`
- **Complexity:** LOW
- **Reuse:** HIGH — duplicated in both `employee-360-page.tsx` and `employees/page.tsx`

### 13. `formatRelativeTime()`
- **File:** `employee-360-page.tsx:46`
- **Purpose:** Relative timestamp formatting
- **Complexity:** LOW
- **Reuse:** HIGH — should be extracted to a shared utility

### 14. `EmployeesPage`
- **File:** `app/(dashboard)/employees/page.tsx` (749 lines)
- **Purpose:** Employee list with search, filter, bulk operations
- **Complexity:** VERY HIGH — 749 lines, DataTable, modals, filters, expandable rows, pagination, bulk operations
- **Performance:** Uses `useDebounce` for search, cursor pagination

### 15. `EmployeesAnalyticsPage`
- **File:** `app/(dashboard)/analytics/employees/page.tsx` (340 lines)
- **Purpose:** Aggregate employee analytics
- **Complexity:** MEDIUM — uses direct state rather than React Query
- **Architecture issue:** Bypasses `useEmployeeSearch` hook, makes raw `api.get()` call

---

# 7. STATE MANAGEMENT

## Global State
- **Tenant ID:** `getTenantId()` from `hooks/useTenant` — included in every API call header
- **Auth/User:** Via FastAPI `Depends(get_current_user_id)` on backend
- **I18n:** `useTranslation()` from `lib/i18n` — provides `t()` function

## Local State (within `Employee360Page`)
| State | Type | Scope |
|-------|------|-------|
| `activeTab` | `TabId` | Tab navigation |
| `filters` | `EmployeeTimelineParams` | Timeline params |
| `showFilters` | `boolean` | Timeline filter panel visibility |
| `selectedSources` | `string[]` | Timeline source filter |
| `selectedTypes` | `string[]` | Timeline type filter |
| `dateFrom` / `dateTo` | `string` | Timeline date range |
| `allEvents` | `Event[]` | Accumulated timeline events (load more) |
| `cursorStack` | `string[]` | Previous cursors for navigation |

## Local State (within `EmployeesPage`)
| State | Type | Scope |
|-------|------|-------|
| `searchQuery` | `string` | Debounced search input |
| `departmentFilter` | `string` | Department dropdown |
| `roleFilter` | `string` | Role dropdown |
| `signalMin` / `signalMax` | `string` | Signal range |
| `cursor` / `cursors` | `string \| null` / `string[]` | Pagination |
| `selectedIds` | `Set<string>` | Bulk selection |
| `selectAllAcross` | `boolean` | Select-all across pages |
| `bulkEditOpen` / `bulkDeleteOpen` | `boolean` | Modal visibility |
| `expandedRow` | `string \| null` | Expanded row ID |

## Server State (React Query)
All employee data flows through React Query with the following cache strategy:

| Query | Cache Key Pattern | staleTime |
|-------|------------------|-----------|
| Employee 360 | `["employees", "detail", id]` | 30s |
| My 360 | `["employees", "me"]` | 30s |
| Employee list | `["employees", "list", filters]` | 15s |
| Signals | `["employees", "signals", id]` | 30s |
| Score | `["employees", "score", id]` | 30s |
| Timeline | `["employees", "timeline", id, params]` | 15s |
| Performance | `["employees", "performance", id]` | 30s |

## Derived State
- `gaugeScore`: Computed from domain score OR Decision Platform scores (ScoringTab:422)
- `gaugeColor`: Derived from gaugeScore thresholds (ScoringTab:423)
- `riskLevel`: Derived from score (<40 high, <70 medium, else low) (QuickStatsRow:177)
- `hasActiveFilters`: Computed from filter arrays (TimelineTab:573)
- `trendDirIcon`: Computed from score_trend_direction (PerformanceTab:762)

## Memoization
- `queryParams`: `useMemo` in TimelineTab (line 528) — depends on filters, sources, types, dates
- No other explicit memoization (no `React.memo`, no `useCallback` for handlers passed to children)

## Query Invalidation
- `useBulkEditEmployees()` — on success, invalidates `employeeKeys.lists()` (all employee list queries)
- `useBulkDeleteEmployees()` — on success, invalidates `employeeKeys.lists()`
- No automatic invalidation of detail queries after mutation (score compute, signal collect)

## Realtime Updates
- **Not implemented.** No WebSocket, Server-Sent Events, or polling. All data is stale until next query refetch cycle (15-30s).

---

# 8. API MAPPING

## Endpoint Inventory

### A. Employee 360 Module (`app/modules/employee_360/router.py`)

| # | Method | Endpoint | Handler | Auth | Permission |
|---|--------|----------|---------|------|------------|
| 1 | GET | `/api/v1/employees/me/360` | `my_employee_360` | Bearer + Tenant | `employee.READ` |
| 2 | GET | `/api/v1/employees/{employee_id}/360` | `employee_360` | Bearer + Tenant | `employee.READ` |

**Response (1&2):** `Employee360Response`
```json
{
  "profile": { "id", "full_name", "full_name_ar", "email", "role", "phone", "avatar_url", "is_active", "tenant_id", "created_at", "team": [], "manager": null },
  "portfolio": { "companies": [], "contacts": [], "pipeline": [], "revenue": 0, "contracts": [], "projects": [] },
  "calendar_intelligence": { "today_count", "week_count", "month_count", "total_hours", "avg_duration_minutes", "unique_companies_met", "upcoming": [] },
  "email_intelligence": { "sent", "received", "replies", "avg_response_hours", "top_contacts": [], "top_companies": [] },
  "activity_intelligence": { "meetings", "emails", "calls", "tasks", "notes", "documents", "total", "recent": [] },
  "kpis": { "revenue", "pipeline", "win_rate", "response_rate", "follow_up_rate", "activities", "productivity", "forecast", "signal_volume_score", "diversity_score", "completion_rate", "signal_count" },
  "ai_coach": [ { "type", "title", "description", "priority", "target_id", "target_type" } ],
  "signals": { "signals": { "total_signals", "by_source": {}, "by_type": {}, "recent_signals": [] }, "score": null },
  "timeline": { "events": [], "total": 0, "next_cursor": null },
  "performance": { "trend": { "current_score", "previous_score", "delta", "direction", "period_days" }, "peer_comparison": { "employee_score", "department_average", "percentile", "above_average" }, "risk_flags": [] }
}
```

**Error handling:** Both endpoints wrap service calls in try/except, returning degraded `Employee360Response` with empty defaults on failure (not HTTP 500).

### B. Employee Domain (`domains/employee/router.py`)

| # | Method | Endpoint | Handler | Auth | Permission |
|---|--------|----------|---------|------|------------|
| 3 | POST | `/api/v1/employees/{employee_id}/signals/collect` | `collect_employee_signals` | Bearer + Tenant | `employee.READ` |
| 4 | GET | `/api/v1/employees/{employee_id}/signals` | `list_employee_signals` | Bearer + Tenant | `employee.READ` |
| 5 | POST | `/api/v1/employees/{employee_id}/score` | `compute_employee_score` | Bearer + Tenant | `employee.READ` |
| 6 | GET | `/api/v1/employees/{employee_id}/score` | `get_employee_score` | Bearer + Tenant | `employee.READ` |
| 7 | GET | `/api/v1/employees/{employee_id}/timeline` | `employee_timeline` | Bearer + Tenant | `employee.READ` |
| 8 | GET | `/api/v1/employees/{employee_id}/performance` | `get_employee_performance` | Bearer + Tenant | `employee.READ` |
| 9 | PATCH | `/api/v1/employees/bulk` | `bulk_update_employees` | Bearer + Tenant | `employee.UPDATE` |
| 10 | DELETE | `/api/v1/employees/bulk` | `bulk_delete_employees` | Bearer + Tenant | `employee.DELETE` |
| 11 | GET | `/api/v1/employees/export` | `export_employees` | Bearer + Tenant | `employee.READ` |
| 12 | GET | `/api/v1/employees` | `list_employees` | Bearer + Tenant | `employee.READ` |

#### Endpoint 3: POST `/employees/{id}/signals/collect`
- **Request:** Path param `employee_id`; no body
- **Response:** `{ "collected": N, "employee_id": "..." }`
- **Logic:** Runs `SignalPipeline.collect_for_employee()` (CRM → timeline → workflow)

#### Endpoint 4: GET `/employees/{id}/signals`
- **Query params:** `source` (str, optional), `signal_type` (str, optional), `since` (datetime, optional), `until` (datetime, optional), `limit` (int, 1-200, default 50), `cursor` (str, optional)
- **Response:** `EmployeeSignalsSummaryResponse`
```json
{
  "by_type": [ { "type": "email_sent", "count": 45, "label": "Email Sent" } ],
  "by_source": [ { "source": "crm", "count": 120, "label": "CRM" } ],
  "trend": [ { "date": "2026-07-25", "count": 5 } ],
  "total": 0
}
```
- **Pagination:** Cursor-based (keyset)
- **Trend:** Computed from last 30 days of signals

#### Endpoint 5: POST `/employees/{id}/score`
- **Request:** No body
- **Response:** `EmployeeScoreDetailResponse` (computes and persists new score)
```json
{ "score": 78.5, "trend": "up", "confidence": 85, "factors": [ { "name": "signal_volume", "contribution": 30, ... } ] }
```

#### Endpoint 6: GET `/employees/{id}/score`
- **Response:** Same as POST, but reads latest from DB (does NOT recompute)
- **Fallback:** Returns zeroed score if no data exists

#### Endpoint 7: GET `/employees/{id}/timeline`
- **Query params:** `source` (str, optional, comma-separated), `signal_type` (str, optional), `from` (datetime), `to` (datetime), `limit` (1-100, default 20), `cursor` (str)
- **Response:** `EmployeeTimelineDataResponse`
```json
{
  "events": [ { "id", "action", "title", "source", "source_label", "timestamp", "actor", "entity_type", "entity_id", "metadata" } ],
  "next_cursor": null,
  "has_next": false,
  "total": 0
}
```
- **Pagination:** Keyset cursor (timestamp-based)
- **Note:** Frontend sends source/type as CSV strings; backend treats them as single string filter — **potential bug** (multi-select not supported at API level)

#### Endpoint 8: GET `/employees/{id}/performance`
- **Response:** `EmployeePerformanceResponse`
```json
{
  "score_trend": [ { "date": "2026-07-25", "score": 72.5 } ],
  "peer_comparison": [ { "metric": "overall", "employee_value": 75.0, "department_avg": 62.3, "label": "Overall Score" } ],
  "risk_flags": [ { "type": "declining_signals", "label": "Declining Activity", "severity": "high", "description": "..." } ],
  "factors": [ ... ],
  "current_score": 75.0,
  "score_trend_direction": "up",
  "department": "sales_rep"
}
```
- **Note:** `department` field is a **mapping of `user.role`** (router.py:297), not a true department — the `users` table has no department column

#### Endpoint 9: PATCH `/employees/bulk`
- **Request body:** `{ "employee_ids": ["uuid1", "uuid2"], "updates": { "role": "...", "is_active": true } }`
- **Response:** `{ "updated": N, "failed": N, "errors": [] }`
- **Validation:** Only `role` and `is_active` allowed

#### Endpoint 10: DELETE `/employees/bulk`
- **Request body:** `{ "employee_ids": ["uuid1", "uuid2"] }`
- **Response:** `{ "deleted": N }`
- **Logic:** Soft-delete (sets `is_active = False`)

#### Endpoint 11: GET `/employees/export`
- **Query params:** `format` (csv), `fields` (comma-separated), `employee_ids` (optional comma-separated)
- **Response:** CSV file download

#### Endpoint 12: GET `/employees`
- **Query params:** `q` (search), `role`, `is_active`, `limit` (1-100, default 20), `cursor`
- **Response:** `CursorResponse` with employee list
- **Pagination:** Keyset cursor on `created_at DESC`

### C. Work Intelligence Module (`app/modules/work_intelligence/router.py`)

| # | Method | Endpoint | Auth | Permission |
|---|--------|----------|------|------------|
| 13 | GET | `/api/v1/work-intelligence/{employee_id}` | Bearer + Tenant | `work-intelligence.READ` |
| 14 | GET | `/api/v1/work-intelligence/me` | Bearer + Tenant | `work-intelligence.READ` |

**Note:** Only `admin` role has `work-intelligence` permission (not manager or user).

---

## Authentication & Authorization Summary

| Component | Mechanism |
|-----------|-----------|
| Auth type | Bearer token (JWT) |
| Tenant isolation | `X-Tenant-Id` header; `Depends(get_current_tenant_id)` on all endpoints |
| User identity | `Depends(get_current_user_id)` |
| Permission check | `Depends(require_permission_dep("employee", PermissionAction.READ))` |
| RBAC registry | `sdk/permissions.py:PermissionRegistry` |
| Role hierarchy | `{"admin": 3, "manager": 2, "user": 1, "api": 1, "auditor": 0}` |

---

# 9. BACKEND FLOW

## Full Request Trace: `GET /api/v1/employees/{id}/360`

```
HTTP Request
  │
  ├─ FastAPI Middleware Stack
  │   ├─ CORS middleware
  │   ├─ Auth middleware (JWT validation)
  │   └─ Tenant middleware (X-Tenant-Id)
  │
  ├─ Router: app/modules/employee_360/router.py:52
  │   └─ employee_360()
  │       ├─ Depends(get_current_tenant_id) → tenant_id
  │       ├─ Depends(get_db_session) → AsyncSession
  │       └─ require_permission_dep("employee", PermissionAction.READ)
  │
  ├─ Service: Employee360Service.get_360(user_id, tenant_id)
  │   │
  │   ├─ _get_profile(user_id, tenant_id)
  │   │   ├─ SELECT FROM users WHERE id = ? AND tenant_id = ?
  │   │   ├─ Raises NotFoundError("User", user_id) if missing
  │   │   ├─ SELECT FROM users WHERE tenant_id = ? AND is_active = TRUE (LIMIT 50)
  │   │   └─ Returns EmployeeProfile with team (first 10, excluding self), manager=None
  │   │
  │   ├─ _get_portfolio(tenant_id, user_id)
  │   │   ├─ PostgresOpportunityRepository.query(OpportunityQuery(owner_id=user_id))
  │   │   │   └─ Returns pipeline items (opportunities with value, stage, company)
  │   │   ├─ SELECT FROM contacts WHERE tenant_id = ? (LIMIT 50)
  │   │   ├─ SELECT FROM companies WHERE tenant_id = ? (LIMIT 50)
  │   │   ├─ Computes total_revenue = sum(pipeline.value for status in ["closed_won", "won"])
  │   │   └─ Returns EmployeePortfolio (companies, contacts, pipeline, revenue, contracts=[], projects=[])
  │   │
  │   ├─ _get_activity_intelligence(tenant_id, user_id)
  │   │   ├─ activity_runtime.get_by_actor(actor=user_id, tenant_id, limit=50)
  │   │   ├─ Classifies actions by prefix: meeting_*, email_*, call_*, task_*, note_*, document_*/file_*
  │   │   └─ Returns ActivityIntelligence with counts + recent 20 items
  │   │
  │   ├─ _compute_kpis(portfolio, activity)
  │   │   ├─ pipeline = sum of non-won/lost opportunity values
  │   │   ├─ win_rate = won / (won + lost)
  │   │   ├─ productivity = activity.total / 30
  │   │   └─ Returns EmployeeKPIs (revenue, pipeline, win_rate, activities, productivity)
  │   │
  │   ├─ _get_signals_data(user_id, tenant_id)
  │   │   ├─ signal_repo.get_summary(user_id, tenant_id)
  │   │   │   └─ SELECT * FROM employee_signals WHERE employee_id=? AND tenant_id=?
  │   │   │   └─ Aggregates by_source, by_type dicts
  │   │   └─ signal_repo.get_latest_score(user_id, tenant_id)
  │   │       └─ SELECT * FROM employee_scores WHERE ... ORDER BY generated_at DESC LIMIT 1
  │   │
  │   ├─ _get_timeline(user_id, tenant_id)
  │   │   └─ signal_repo.get_by_employee(user_id, tenant_id, limit=10)
  │   │       └─ SELECT * FROM employee_signals WHERE ... ORDER BY timestamp DESC LIMIT 11
  │   │
  │   ├─ _get_performance(user_id, tenant_id, signal_data)
  │   │   ├─ Creates EmployeeScore from signal_data (if available)
  │   │   ├─ Fetches all signals (limit=500)
  │   │   ├─ EmployeePerformanceEngine.compute_performance()
  │   │   │   ├─ _compute_trend(): Compares current vs 30-day-ago score
  │   │   │   ├─ _compute_peer_comparison(): Averages scores of same-role users
  │   │   │   └─ _compute_risk_flags(): 14-day decline, 7-day engagement, score direction
  │   │   └─ Returns PerformanceInsights
  │   │
  │   ├─ [ADR-012] Calendar & Email Intelligence
  │   │   ├─ Lazy imports: CalendarEngine, EmailEngine, EngagementEngine
  │   │   ├─ EngagementEngine.get_relationship_health(user_id, tenant_id)
  │   │   └─ Maps metrics to CalendarIntelligence + EmailIntelligence
  │   │
  │   ├─ _generate_coach_actions(portfolio, kpis, performance)
  │   │   ├─ Pipeline empty → "Build your pipeline" (high)
  │   │   ├─ Win rate < 0.3 → "Improve win rate" (medium)
  │   │   ├─ Low signal diversity → "Diversify your activity types" (medium)
  │   │   ├─ Declining signals flag → "Activity dropping" (high)
  │   │   ├─ Low engagement flag → "Increase engagement" (medium)
  │   │   └─ Fallback → "You're on track" (low)
  │   │
  │   └─ Assembles and returns Employee360Response
  │
  └─ FastAPI serializes to JSON → HTTP 200 response
```

## Events / Notifications / Audit Logs
- **Not implemented.** No Celery tasks, no background jobs, no webhook triggers, no audit log entries specific to Employee 360 actions.
- The only "event" infrastructure is the `SUPPORTED_EVENTS` list in `webhooks/schemas.py` which includes `"employee.updated"` but this is a **stub** — no actual webhook emission code exists.

---

# 10. DATABASE MODEL

## Tables

### `users` (identity module)
Primary employee identity table. **There is no separate `employees` table.**

| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID (PK) | NOT NULL | Employee unique ID |
| tenant_id | UUID (FK→tenants.id) | NOT NULL, INDEX | Multi-tenant isolation |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Login + identity |
| password_hash | VARCHAR(255) | NOT NULL | Hashed |
| full_name | VARCHAR(255) | NOT NULL | Employee display name |
| full_name_ar | VARCHAR(255) | NULLABLE | Arabic name |
| role | VARCHAR(50) | DEFAULT 'user' | Free-text role (also serves as RBAC role) |
| is_active | BOOLEAN | DEFAULT true | Soft-delete flag |
| is_verified | BOOLEAN | DEFAULT false | Email verification |
| avatar_url | VARCHAR(500) | NULLABLE | Profile picture |
| phone | VARCHAR(30) | NULLABLE | Contact number |
| preferences | JSONB | DEFAULT {} | User preferences |
| last_login_at | TIMESTAMPTZ | NULLABLE | Last login |
| failed_attempts | INTEGER | DEFAULT 0 | Login brute-force protection |
| locked_until | TIMESTAMPTZ | NULLABLE | Account lockout |
| created_at | TIMESTAMPTZ | DEFAULT now() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT now() | Record update |

**Critical observation:** No `department` column exists on `users`. The frontend `EmployeeListItem.department` field and backend `EmployeePerformanceResponse.department` field both map to `user.role` as a workaround (`router.py:297`).

### `employee_signals`
| Column | Type | Constraints | Index |
|--------|------|------------|-------|
| id | UUID (PK) | NOT NULL | Primary |
| employee_id | UUID | NOT NULL | INDEX |
| tenant_id | UUID | NOT NULL | INDEX |
| signal_type | VARCHAR(50) | NOT NULL | INDEX (`ix_employee_signals_type`) |
| source | VARCHAR(30) | NOT NULL | INDEX (`ix_employee_signals_source`) |
| metadata | JSONB | DEFAULT {} | — |
| timestamp | TIMESTAMPTZ | NOT NULL | INDEX (`ix_employee_signals_timestamp`) |
| created_at | TIMESTAMPTZ | DEFAULT now() | — |

**Composite indexes:**
- `ix_employee_signals_tenant_employee` ON (`tenant_id`, `employee_id`)

**Missing indexes / concerns:**
- No index on `(tenant_id, employee_id, timestamp DESC)` — the most common query pattern
- No index on `(tenant_id, employee_id, source)` for filtered queries
- No index on `(tenant_id, employee_id, signal_type)` for filtered queries
- **No foreign key constraints** to `users.id` or `tenants.id` — purely implicit UUID matching

### `employee_scores`
| Column | Type | Constraints | Index |
|--------|------|------------|-------|
| id | UUID (PK) | NOT NULL | Primary |
| employee_id | UUID | NOT NULL | INDEX |
| tenant_id | UUID | NOT NULL | INDEX |
| overall_score | FLOAT | DEFAULT 0.0 | — |
| signal_volume_score | FLOAT | DEFAULT 0.0 | — |
| recency_score | FLOAT | DEFAULT 0.0 | — |
| diversity_score | FLOAT | DEFAULT 0.0 | — |
| completion_rate | FLOAT | DEFAULT 0.0 | — |
| confidence_interval_low | FLOAT | DEFAULT 0.0 | — |
| confidence_interval_high | FLOAT | DEFAULT 0.0 | — |
| signal_count | INTEGER | DEFAULT 0 | — |
| generated_at | TIMESTAMPTZ | DEFAULT now() | — |

**Composite indexes:**
- `ix_employee_scores_tenant_employee` ON (`tenant_id`, `employee_id`)

**Missing indexes / concerns:**
- Query pattern `WHERE employee_id=? AND tenant_id=? ORDER BY generated_at DESC LIMIT 1` would benefit from `(employee_id, tenant_id, generated_at DESC)` index
- No index on `generated_at` for time-range queries
- **No partition strategy** — scores grow indefinitely
- **No foreign key constraints**

## Relationships
- `employee_signals.employee_id` → `users.id` (implicit, no FK)
- `employee_signals.tenant_id` → `tenants.id` (implicit, no FK)
- `employee_scores.employee_id` → `users.id` (implicit, no FK)
- `employee_scores.tenant_id` → `tenants.id` (implicit, no FK)

## Views / Materialized Views
- **None.** All aggregations computed in-memory by repository layer.

## Performance Issues
1. `get_summary()` loads ALL signals for an employee into memory to compute counts (`postgres_repo.py:113-147`) — **O(n) memory for large signal volumes**
2. Peer comparison in `performance._get_peer_scores()` does N+1 per-user queries without batching
3. Score computation in `_build_score_detail` fetches up to 500 signals and re-runs scoring algebra in Python
4. Timeline `get_by_employee` with keyset cursor does `LIMIT limit+1` for has_next detection — standard but could be optimized with window functions
5. No connection pooling configuration visible in employee module

---

# 11. EMPLOYEE TIMELINE ENGINE

## Architecture

The timeline engine aggregates employee signals from three distinct sources into a unified chronological feed.

### Signal Sources

```
┌──────────────────────────────────────────────────────┐
│                  SignalPipeline                        │
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ CRM Activity │  │   Timeline   │  │   Workflow   │ │
│  │   Runtime    │  │   Recorder   │  │   Service    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│         ▼                 ▼                 ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ deal_assigned│  │meeting_comp. │  │workflow_comp.│ │
│  │ contact_mod. │  │ call_comp.   │  │              │ │
│  │              │  │ email_sent   │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                        │
│         └────────────────┬────────────────┘            │
│                          ▼                              │
│              employee_signals table                     │
└──────────────────────────────────────────────────────┘
```

### Collection Flow (`signals.py:SignalPipeline.collect_for_employee()`)

1. **CRM collection** (`_collect_crm_signals`): Queries `activity_runtime` for actions matching "opportunity"/"deal" → `DEAL_ASSIGNED` or "contact" → `CONTACT_MODIFIED`
2. **Timeline collection** (`_collect_timeline_signals`): Queries `timeline_recorder.get_by_actor()`; maps event_type prefixes to signal types ("meeting"→`MEETING_COMPLETED`, "call"→`CALL_COMPLETED`, "email"→`EMAIL_SENT`)
3. **Workflow collection** (`_collect_workflow_signals`): Queries `workflow_service.get_executions_by_actor()`; maps completed executions → `WORKFLOW_COMPLETED`
4. **Batch persistence:** All collected signals saved via `save_many()` → `db.add_all()`

### Trigger Mechanisms
- **Manual:** `POST /api/v1/employees/{id}/signals/collect` — explicit API call
- **Automatic:** **Not implemented** — no cron job, no event-driven hook, no webhook handler

### Ordering
- All signals ordered by `timestamp DESC` in queries
- Keyset cursor pagination on `(timestamp, id)` for stable ordering

### Aggregation
- `get_summary()`: In-memory aggregation of all employee signals into `by_source` and `by_type` counts
- Signal trend: In-memory computation of daily counts for last 30 days (`_compute_signal_trend`)

### Deduplication
- **Not implemented.** If a signal is collected twice (e.g., manual trigger re-runs), duplicate rows are inserted. No unique constraint on `(employee_id, signal_type, source, timestamp)`.

### Scoring
- **Not implemented for timeline filtering.** No relevance scoring, no prioritization of events.

### Filtering (API level)
- `source`: Single string filter (not array — frontend multi-select limitation)
- `signal_type`: Single string filter
- `since`/`until`: DateTime range

### Search
- **Not implemented.** Full-text search on timeline metadata does not exist.

### Realtime Updates
- **Not implemented.** No push mechanism. Client relies on React Query staleTime (15s).

---

# 12. CALENDAR INTELLIGENCE

## Current Implementation

**Status:** Basic integration via ADR-012 Activity Intelligence engine. Minimal metrics surfaced.

### What exists:

1. **`CalendarIntelligence` schema** (`employee_360/schemas.py:41-48`): 7 fields
   - `today_count`, `week_count`, `month_count`, `total_hours`, `avg_duration_minutes`, `unique_companies_met`, `upcoming: list[dict]`

2. **Data source:** Lazy import of `CalendarEngine` from `intelligence.activity_intelligence.engine.calendar_engine` in `Employee360Service.get_360()` (lines 64-92)

3. **Metric mapping** from EngagementEngine:
   - `meeting_count.value` → `today_count`
   - `communication_velocity.value` → `week_count`
   - `meeting_hours.value` → `total_hours`
   - `month_count`, `avg_duration_minutes`, `unique_companies_met` → always 0 (not mapped)
   - `upcoming` → always empty list

4. **Work Intelligence** (`work_intelligence/service.py`): Separate engine provides meeting load analysis:
   - `meetings_today`, `meetings_this_week`, `meetings_this_month`, `avg_meetings_per_day`, `total_meeting_hours_this_week`
   - `overbooked` flag (meeting_hours > 16/week)
   - Arabic recommendation text

### What is NOT implemented:

| Feature | Status |
|---------|--------|
| Google Calendar integration (OAuth) | Not implemented |
| Microsoft Outlook/Exchange integration | Not implemented |
| ICS feed support | Not implemented |
| Zoom integration | Not implemented |
| Google Meet integration | Not implemented |
| Teams integration | Not implemented |
| Calendly integration | Not implemented |
| Recurring meeting handling | Not implemented |
| Cancelled meeting tracking | Not implemented |
| Timezone awareness | Not implemented |
| Webhook-based sync | Not implemented |
| Incremental sync | Not implemented |
| Token lifecycle management | Not implemented |
| Meeting effectiveness score | Not implemented |
| Focus time calculation | Basic implementation (work_intelligence) |
| Meeting heatmap | Not implemented |
| External vs Internal classification | Not implemented |
| Response rate | Not implemented |
| Average attendees | Not implemented |
| Calendar utilization % | Not implemented |

### Recommended Architecture (Production-Grade)

```
┌─────────────────────────────────────────────────────────┐
│                   Calendar Intelligence                   │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Google       │  │ Microsoft     │  │ ICS / CalDAV   │  │
│  │ Calendar API │  │ Graph API     │  │ Parser         │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬─────────┘  │
│         │                 │                  │             │
│         ▼                 ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Calendar Sync Engine                     │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │ OAuth    │  │ Token    │  │ Incremental Sync │   │  │
│  │  │ Flow     │  │ Rotation │  │ (syncToken/delta)│   │  │
│  │  └─────────┘  └──────────┘  └──────────────────┘   │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │         Meeting Normalizer                     │   │  │
│  │  │  • Recurring expansion                        │   │  │
│  │  │  • Timezone normalization to UTC              │   │  │
│  │  │  • Cancelled/declined filtering               │   │  │
│  │  │  • Attendee extraction & dedup               │   │  │
│  │  │  • External vs Internal classification        │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                                │
│                           ▼                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              employee_calendar_events table            │  │
│  │  • id, employee_id, tenant_id, provider, event_id     │  │
│  │  • title, start_utc, end_utc, timezone, duration_mins │  │
│  │  • is_recurring, recurrence_rule, is_cancelled        │  │
│  │  • attendees_count, is_internal, conference_link      │  │
│  │  • organizer_email, response_status                   │  │
│  │  • last_synced_at                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                           │                                │
│                           ▼                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Calendar KPIs (Daily Materialized View)      │  │
│  │  • Meetings today/this week/this month                 │  │
│  │  • Total meeting hours                                 │  │
│  │  • Average duration                                    │  │
│  │  • Unique companies met                                │  │
│  │  • External vs Internal ratio                         │  │
│  │  • Focus time (8h - meeting time)                     │  │
│  │  • Calendar utilization %                             │  │
│  │  • Meeting heatmap (hour-of-day × day-of-week)        │  │
│  │  • Response rate (accepted / total)                   │  │
│  │  • Average attendees                                   │  │
│  │  • Cancellation rate                                   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Sync Strategy (Recommended)

1. **OAuth flow:** Per-employee OAuth 2.0 authorization with `offline` access type
2. **Scopes (Google):** `https://www.googleapis.com/auth/calendar.readonly`, `https://www.googleapis.com/auth/calendar.events.readonly`
3. **Scopes (Microsoft Graph):** `Calendars.Read`, `Calendars.Read.Shared`
4. **Token lifecycle:** Encrypted storage, automatic refresh via refresh token, rotation on expiry
5. **Initial sync:** Full calendar pull (last 90 days + future 90 days)
6. **Incremental sync:** Google `syncToken` / Microsoft `delta` query every 15 minutes via Celery Beat
7. **Webhook:** Google Calendar push notifications / Microsoft Graph webhook subscriptions for near-realtime updates
8. **Conflict handling:** Last-write-wins with `last_synced_at` timestamp, provider-side as source of truth
9. **Recurring meetings:** Expansion via RRULE library (e.g., `dateutil.rrule`), store expanded instances for 90-day window

---

# 13. EMAIL INTELLIGENCE

## Current Implementation

**Status:** Basic integration via ADR-012 Activity Intelligence engine.

### What exists:

1. **`EmailIntelligence` schema** (`employee_360/schemas.py:51-57`): 6 fields
   - `sent`, `received`, `replies`, `avg_response_hours`, `top_contacts: list[dict]`, `top_companies: list[dict]`

2. **Data source:** Lazy import of `EmailEngine` from `intelligence.activity_intelligence.engine.email_engine` (lines 64-92)

3. **Metric mapping:**
   - `email_count_sent.value` → `sent`
   - `email_count_received.value` → `received`
   - `reply_rate.value * 100` → `replies`
   - `response_time_avg.value` → `avg_response_hours`
   - `top_contacts`, `top_companies` → always empty lists (not mapped)

### What is NOT implemented:

| Feature | Status |
|---------|--------|
| Google Workspace (Gmail) integration | Not implemented |
| Microsoft 365 (Outlook) integration | Not implemented |
| Exchange integration | Not implemented |
| IMAP/SMTP support | Not implemented |
| Email volume by customer | Not implemented |
| Email volume by opportunity | Not implemented |
| Daily/weekly/monthly volume trends | Not implemented |
| Peak hours analysis | Not implemented |
| Response SLA tracking | Not implemented |
| AI email summary | Not implemented |
| Communication score | Not implemented |
| Inbox health score | Not implemented |
| Relationship score | Not implemented |
| Open conversations tracking | Not implemented |
| Unread email count | Not implemented |
| Customer conversation detection | Not implemented |
| Internal vs External classification | Not implemented |

### Recommended Architecture (Production-Grade)

```
┌─────────────────────────────────────────────────────────┐
│                   Email Intelligence                      │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Gmail API   │  │ MS Graph     │  │ SMTP/IMAP      │  │
│  │             │  │ (Outlook)    │  │                │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬─────────┘  │
│         └──────────────────┼──────────────────┘            │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Email Sync Engine                         │  │
│  │  • OAuth flow per provider                            │  │
│  │  • Gmail: History.list() for incremental changes      │  │
│  │  • MS Graph: /messages delta query                    │  │
│  │  • Webhook: Gmail push / Graph subscriptions          │  │
│  │  • Header parsing (Message-ID, In-Reply-To,           │  │
│  │    References for threading)                          │  │
│  └─────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              employee_email_events table               │  │
│  │  • id, employee_id, tenant_id                         │  │
│  │  • provider, provider_message_id, thread_id           │  │
│  │  • direction (sent/received)                           │  │
│  │  • from_address, to_addresses[], cc[], bcc[]          │  │
│  │  • subject, has_attachments, is_internal              │  │
│  │  • timestamp_utc, response_time_seconds               │  │
│  │  • related_company_id, related_contact_id             │  │
│  │  • related_opportunity_id                             │  │
│  └─────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Email KPIs (Materialized View)               │  │
│  │  • Sent count (today/week/month)                      │  │
│  │  • Received count                                     │  │
│  │  • Reply rate                                         │  │
│  │  • Average response time (P50/P90)                    │  │
│  │  • Unread count                                       │  │
│  │  • Open conversations                                 │  │
│  │  • Customer conversations                             │  │
│  │  • Internal vs External ratio                         │  │
│  │  • Volume by hour-of-day (peak hours)                 │  │
│  │  • Volume trend (daily/weekly/monthly)                │  │
│  │  • Response SLA compliance %                          │  │
│  │  • Top contacts by volume                             │  │
│  │  • Top companies by volume                            │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### AI Summary Integration (Recommended)
- On email ingestion, queue async AI summary generation
- Produce 1-2 sentence summary per email thread
- Extract action items from email bodies
- Detect sentiment (positive/neutral/negative)
- Flag urgent/important emails

---

# 14. CRM ACTIVITY INTELLIGENCE

## Current Implementation

The `ActivityIntelligence` schema captures 6 activity types:

| Activity Type | Detection Method | Source |
|---------------|-----------------|--------|
| Meetings | Action prefix `meeting_*` | `activity_runtime.get_by_actor()` |
| Emails | Action prefix `email_*` | `activity_runtime.get_by_actor()` |
| Calls | Action prefix `call_*` | `activity_runtime.get_by_actor()` |
| Tasks | Action prefix `task_*` | `activity_runtime.get_by_actor()` |
| Notes | Action prefix `note_*` | `activity_runtime.get_by_actor()` |
| Documents | Action prefix `document_*` / `file_*` | `activity_runtime.get_by_actor()` |

### What is tracked:
- `ActivityIntelligence.total` — total activity count from runtime
- `ActivityIntelligence.recent` — last 20 activity items (raw dicts)

### What is NOT tracked:

| Activity | Status |
|----------|--------|
| Deals created/closed | Not in employee 360 context |
| Quotes generated | Not implemented |
| Contracts signed | Schema has `contracts` field but always empty |
| Pipeline stage movements | Not implemented |
| Approvals | Signal type `APPROVAL_COMPLETED` exists: used in signals, not activity counts |
| Comments | Not implemented |
| Mentions | Not implemented |
| Logins | `last_login_at` exists on User model: not surfaced in 360 |
| Searches | Not implemented |
| Exports | Not implemented |
| Downloads | Not implemented |
| Customer visits | Not implemented |
| Location check-ins | Not implemented |
| WhatsApp interactions | Not implemented |
| LinkedIn interactions | Not implemented |

### Implementation Gap Analysis
The activity intelligence is **fully dependent on a single `activity_runtime` abstraction**. If the runtime doesn't have data for a given category, it returns 0. There's no direct database querying for activity data — everything flows through the runtime proxy.

---

# 15. PRODUCTIVITY INTELLIGENCE

## Current Implementation

### Scoring Engine Formula (`scoring.py`)

The `EmployeeScoringEngine` computes a 0.0-1.0 score:

```
overall_score = 0.30 × signal_volume + 0.25 × recency + 0.20 × diversity + 0.25 × completion_rate
```

| Factor | Formula | Description |
|--------|---------|-------------|
| Signal Volume | `min(signal_count / 100, 1.0)` | 100 signals = perfect volume |
| Recency | `max(0, 1.0 - days_since_last_signal / 90)` | Most recent signal freshness |
| Diversity | `0.6 × type_diversity + 0.4 × source_diversity` | `type_diversity = min(unique_types / 6, 1.0)`, `source_diversity = min(unique_sources / 3, 1.0)` |
| Completion Rate | `completed / total_workflow_signals` (or 0.5 if any completed) | Workflow completion ratio |

**Confidence Intervals:**
| Sample Size (n) | Margin |
|----------------|--------|
| n < 5 | ±0.25 |
| n < 20 | ±0.15 |
| n < 50 | ±0.10 |
| n ≥ 50 | ±0.05 |

### KPIs Computed (`service.py:_compute_kpis`)

| KPI | Formula | Status |
|-----|---------|--------|
| Revenue | Sum of pipeline values where status in ["closed_won", "won"] | Implemented |
| Pipeline | Sum of pipeline values excluding won/lost | Implemented |
| Win Rate | `won / (won + lost)` | Implemented |
| Activities | `activity_runtime.total` | Implemented |
| Productivity | `activities / 30` | Crude — linear division of 30-day period |
| Response Rate | From ADR-012 `reply_rate` metric | Implemented |
| Follow-up Rate | From ADR-012 `follow_up_rate` | Implemented |
| Forecast | Always 0.0 | Schema exists, no computation |

### Work Intelligence Engine (`work_intelligence/service.py`)

Separate module providing:

| Metric | Formula |
|--------|---------|
| Time Allocation | Meeting: 1.0h/item, Email: 0.25h/item, Call: 0.5h/item, Task: 0.5h/item |
| Focus Hours | `max(0, 5 × 30 - total_tracked)` |
| Meeting Load | Counts today/this week/this month |
| Overbooked | `meeting_hours_this_week > 16` (8h × 2) |
| Activity Score | `0.30 × volume + 0.25 × variety + 0.25 × recency + 0.20 × consistency` |
| Activity Grade | Arabic labels: ممتاز/جيد/متوسط/ضعيف/منخفض جدًا |

### What is NOT implemented:

| KPI | Status |
|-----|--------|
| Tasks completed (count) | Not tracked separately |
| Tasks overdue | Not implemented |
| Task completion % | Not implemented — `completion_rate` is signal-level, not task-level |
| Focus score | Work intelligence has `focus_hours` but no 0-100 score |
| Productivity score (0-100) | `productivity = activities/30` — not normalized |
| AI productivity index | Not implemented |
| Engagement score | Low engagement flag exists but no composite 0-100 score |
| Customer touchpoints | Not implemented |
| Workload score | Not implemented |
| Burnout indicator | Not implemented |
| Daily/weekly/monthly activity breakdown | ActivityIntelligence only gives totals |

---

# 16. AI LAYER

## Current Implementation

### AI Coach (`service.py:_generate_coach_actions`)

Rule-based engine producing coaching actions:

| Trigger | Action | Priority |
|---------|--------|----------|
| Pipeline = 0 AND Revenue = 0 | "Build your pipeline" | high |
| Win rate < 0.3 AND > 0 | "Improve win rate" | medium |
| Signal diversity < 0.3 AND signal_count > 0 | "Diversify your activity types" | medium |
| Performance risk flag: declining_signals (high severity) | "Activity dropping" | high |
| Performance risk flag: low_engagement (high/medium) | "Increase engagement" | medium |
| No triggers matched | "You're on track" | low |

### Decision Platform Integration (`ScoringTab`)
- Uses `useDecisionScores(employeeId, 'employee')` from `@/lib/decisionQueries`
- Displays Decision Platform scores as alternative factor breakdown
- Fallback to domain scores if DP scores unavailable
- `@salesos/decision-platform` package: referenced for `Score` type

### Activity Intelligence ADR-012 Integration
- Lazy imports of `CalendarEngine`, `EmailEngine`, `EngagementEngine` from `intelligence.activity_intelligence`
- Metrics mapped to `CalendarIntelligence` and `EmailIntelligence`
- Falls back gracefully if imports fail

### What is NOT implemented:

| AI Feature | Status |
|------------|--------|
| Meeting summaries | Not implemented |
| Email summaries | Not implemented |
| AI action item extraction | Not implemented |
| Follow-up suggestions | Not implemented |
| Risk detection (ML-based) | Not implemented — rules-based only |
| Relationship health scoring | ADR-012 integration exists but not surfaced in Coach |
| Sales coaching (ML) | Not implemented |
| Performance coaching (ML) | Not implemented |
| Customer sentiment analysis | Not implemented |
| Employee behavior insights | Not implemented |
| Recommended next actions (ML) | Rules-based only (see coach above) |
| Predictive workload | Not implemented |
| AI Assistant chat integration | Not implemented |
| Natural language query | Not implemented |
| Anomaly detection | Only rule-based decline detection |

### AI Coach Limitations
- **Static rules** — no ML, no personalization, no learning from outcomes
- **No action tracking** — no way to know if coach actions were followed
- **No prioritization across multiple triggers** — multiple actions generated independently
- **No tenure-aware coaching** — same advice for new hires and veterans
- **No industry/role context** — generic advice only

---

# 17. SECURITY

## Permissions Matrix

| Resource | Admin | Manager | User (Rep) | API | Auditor |
|----------|-------|---------|------------|-----|---------|
| `employee.*` (all CRUD) | Full | **None** | **None** | None | None |
| `employee-360.*` | Yes | No | No | No | No |
| `work-intelligence.READ` | Yes | No | No | No | No |

**Critical gap:** Manager role cannot view Employee 360 for their team. Only admin can. This makes Employee 360 effectively unusable for sales managers — the primary intended user.

## RBAC Implementation
- Central registry: `sdk/permissions.py:PermissionRegistry`
- Role hierarchy: `{"admin": 3, "manager": 2, "user": 1, "api": 1, "auditor": 0}`
- Permission check: `require_permission_dep("employee", PermissionAction.READ)` on every route
- Default roles hardcoded in `permissions.py:84-120`, not in database

## Tenant Isolation
- Every query includes `tenant_id = Depends(get_current_tenant_id)` extracted from JWT
- All database queries filter by `tenant_id`
- `X-Tenant-Id` header used by frontend API client
- No cross-tenant data leakage path identified

## PII
- The `users` table stores: full_name, email, phone, avatar_url
- Employee 360 exposes: full_name, email, phone, role, activity data, scores
- **No data classification labels** on PII fields
- **No PII-specific access controls** — anyone with `employee.READ` sees all profile fields
- **No data masking or redaction** for sensitive fields (phone/email are fully visible)

## Audit Logging
- **Not implemented** for Employee 360 specifically
- No audit trail for: who viewed which employee 360, who ran score computations, who bulk edited/deleted
- The general audit infrastructure exists elsewhere but is not wired to employee endpoints

## GDPR Readiness
- No data retention policy for signals or scores
- No right-to-be-forgotten endpoint (bulk delete is soft-delete only: sets `is_active=False`)
- No data export per individual beyond CSV export (which exports all employees)
- No consent management for activity tracking
- No purpose limitation documentation

## SOC2 Considerations
- No audit trail for data access
- No change management logging
- No MFA enforcement for sensitive operations
- No session timeout enforcement visible at the employee module level

## Encryption
- Passwords: Hashed via `password_hash` (assumed bcrypt based on identity module)
- Data at rest: No field-level encryption for PII
- Data in transit: HTTPS (assumed from production config)
- No TLS configuration visible within employee module

## OAuth Security (Calendar/Email — Not Implemented)
- No OAuth flows implemented
- No token storage mechanism
- No scope documentation

---

# 18. PERFORMANCE

## Render Cost

| Component | Lines | Complexity | Render Concern |
|-----------|-------|------------|----------------|
| `Employee360Page` | 1004 | High | 5 tabs, each fetches independently |
| `EmployeesPage` | 749 | Very High | DataTable with expandable rows, modals |
| `EmployeesAnalyticsPage` | 340 | Medium | Direct state management, manual `useEffect` fetch |
| `TimelineTab` | 211 | High | Accumulates all events in state, no virtualization |
| `PerformanceTab` | 198 | High | Inline SVG computation on every render |

## Large Lists
- **Employee list:** Cursor-paginated with `limit` (1-100), default 20. OK for typical tenant sizes.
- **Signals list:** Non-paginated — all signals loaded into memory in `get_summary()`. Potentially problematic for high-activity employees.
- **Timeline events:** Client-side accumulation — `allEvents` state array grows unbounded with "Load More". No virtualization.

## Virtualization
- **Not implemented anywhere.** No `react-window`, `react-virtuoso`, or similar.

## Query Cost

| Query | Concern |
|-------|---------|
| `get_summary()` | Loads ALL employee_signals for count — O(n) data transfer |
| `get_by_employee(limit=500)` | Used in score compute and performance — 500 rows per call |
| `_get_peer_scores()` | N queries: 1 for user, 1 for peer IDs, 1 for peer scores — no JOIN |
| `_get_profile()` | Fetches 50 team members — always runs, even when `team` slice is 10 |
| `get_360()` orchestration | 8+ independent DB calls for a single page load |

## API Latency

The `get_360()` service method makes these sequential-ish calls:
1. `_get_profile()` — 2 queries
2. `_get_portfolio()` — 3 queries (opportunities, contacts, companies)
3. `_get_activity_intelligence()` — 1 runtime call
4. `_get_signals_data()` — 2 queries (summary + latest score)
5. `_get_timeline()` — 1 query
6. `_get_performance()` — 2-3 queries (signals + score + peer scores)

Total: ~12 database operations per page load. Several are sequential dependencies but opportunities, contacts, and companies could be parallelized.

## Bundle Size
- `employee-360-page.tsx` — 1004 lines, likely ~30KB uncompiled
- `employees/page.tsx` — 749 lines, likely ~25KB uncompiled
- `employeeQueries.ts` — 113 lines, small
- `api/employee.ts` — 120 lines, small
- `api/types/employee.ts` — 218 lines, small

## Recommendations
1. **Parallelize independent queries** in `get_360()` — contacts, companies, signals can run concurrently
2. **Use SQL aggregations** for `get_summary()` instead of loading all rows
3. **Add database-level JOIN** for peer scores instead of N+1 queries
4. **Virtualize timeline** for employees with >1,000 events
5. **Memoize chart computations** in PerformanceTab and ScoringTab
6. **Lazy-load tabs** — only fetch tab data when tab is activated, not on page load
7. **Add composite indexes** for common query patterns

---

# 19. MISSING ENTERPRISE FEATURES

## Benchmark Comparison

| Feature | Salesforce | HubSpot | MS Dynamics | Zoho | Rippling | Workday | SAP SF | SalesOS |
|---------|-----------|---------|-------------|------|----------|---------|--------|---------|
| **Core Profile** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** |
| **Activity Timeline** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** (basic) |
| **Performance Scoring** | Yes (Einstein) | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** (rules) |
| **Calendar Integration** | Yes | Yes | Yes | Yes | No | No | No | **Partial** (stub) |
| **Email Analytics** | Yes | Yes | Yes | Yes | No | No | No | **Partial** (stub) |
| **Pipeline View** | Yes | Yes | Yes | Yes | No | No | No | **Yes** (portfolio) |
| **Goals/Quotas** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **No** |
| **1:1 Meeting Notes** | Yes (Quip) | No | Yes | No | Yes | Yes | Yes | **No** |
| **Career Path** | No | No | No | No | Yes | Yes | Yes | **No** |
| **Compensation** | No | No | No | No | Yes | Yes | Yes | **No** |
| **Time Off** | No | No | No | No | Yes | Yes | Yes | **No** |
| **Org Chart** | Yes (limited) | No | Yes | No | Yes | Yes | Yes | **No** |
| **Skills Matrix** | No | No | No | No | Yes | Yes | Yes | **No** |
| **Peer Feedback** | No | No | No | No | Yes | Yes | Yes | **No** |
| **OKRs** | No | No | No | No | Yes | Yes | Yes | **No** |
| **Manager Dashboard** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **No** (manager can't access) |
| **Team View** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **No** |
| **Bulk Operations** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** (basic) |
| **CSV Export** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** |
| **API** | Yes (REST) | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** (REST) |
| **Webhooks** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Stub** |
| **Audit Trail** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **No** |
| **GDPR Tools** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **No** |
| **Role-Based Access** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Partial** (manager gap) |
| **Mobile App** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **No** |
| **AI/ML Insights** | Yes (Einstein) | Yes (Breeze) | Yes (Copilot) | Yes (Zia) | No | Yes | Yes | **Rules only** |
| **Real-time Updates** | Yes | Yes | Yes | Yes | No | Yes | Yes | **No** |
| **Multi-language** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** (EN/AR) |
| **Dark Mode** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Yes** |

## Top 10 Missing Enterprise Features

1. **Manager access to team 360** — Manager role has no `employee` permission. Critical blocker.
2. **Calendar/Email integrations** — ADR-012 stubs exist but no OAuth flows, sync, or rich analytics
3. **Goals and quotas** — No way to set targets and measure against them
4. **Org chart** — No hierarchical team visualization
5. **Audit trail** — No logging for who accessed what employee data
6. **Real-time updates** — No push notifications, websockets, or polling
7. **Mobile support** — No mobile app or responsive-optimized mobile views
8. **GDPR/Compliance tools** — No data retention, consent, or deletion workflows
9. **Department management** — No `department` column on users table; role is used as proxy
10. **AI/ML insights** — Coach is purely rules-based, no learning or personalization

---

# 20. FINAL ASSESSMENT

## Scores

| Category | Score | Rationale |
|----------|-------|-----------|
| **UX** | 65/100 | 5-tab interface is clean but no mobile optimization, no real-time updates, charts are basic SVGs, empty states are good, loading states are good |
| **UI** | 70/100 | Consistent design tokens, dark mode support, nice profile card, but inline SVGs are primitive (no `@salesos/charts`), no micro-animations, RTL support included |
| **Architecture** | 60/100 | Clean DDD separation (domain vs module), repository pattern, but manager permission gap, no event-driven architecture, lazy imports are fragile, analytics page bypasses hooks |
| **Scalability** | 40/100 | In-memory aggregations, no database-level summaries, N+1 queries in performance engine, no partitioning, no caching layer beyond React Query, no background job framework |
| **Security** | 48/100 | RBAC exists but manager role blocked, no audit logging, no PII masking, soft-delete only, no GDPR tools, no field-level encryption |
| **Performance** | 50/100 | Cursor pagination is good, but no virtualization, all-signals loading for summary, sequential DB calls in get_360, no lazy loading of tabs |
| **Maintainability** | 55/100 | 1004-line monolithic component, inlined chart SVGs, duplicated ScoreBadge, duplicated formatRelativeTime, inline scoring math in router, direct DB queries mixed with repository pattern |
| **Enterprise Readiness** | 35/100 | Missing calendar/email integrations, no goals, no org chart, no audit, no mobile, no GDPR, no real-time — not suitable for enterprise deployment |
| **AI Readiness** | 25/100 | Only rules-based coaching, no ML, no NLP, no recommendations, no sentiment, no anomaly detection beyond simple thresholds |

### **Overall Score: 50/100** — Production NO-GO

Currently classified as "production no-go" per GA engineering audit (Production Readiness 38, Security 48). This audit confirms that assessment.

---

## Top 20 Improvements

1. **P0: Grant manager role `employee.READ` permission** — Unblock primary user persona
2. **P0: Add `department` column to `users` table** — Replace role-as-department workaround
3. **P0: Implement audit logging** — Track all employee data access and mutations
4. **P0: Add composite DB indexes** — `(tenant_id, employee_id, timestamp DESC)` on employee_signals
5. **P1: Build calendar OAuth integration** — Google Calendar + Microsoft Graph
6. **P1: Build email OAuth integration** — Gmail + Outlook sync
7. **P1: Add SQL-level aggregation** — Replace in-memory `get_summary()` with `COUNT`/`GROUP BY` queries
8. **P1: Split 1004-line component** — Extract tabs into separate files, extract chart components
9. **P1: Use `@salesos/charts` consistently** — Replace inline SVGs with shared chart library
10. **P1: Implement goals/quotas** — Set targets, track attainment %, surface in 360
11. **P2: Virtualize timeline** — Use `react-virtuoso` for employees with >500 events
12. **P2: Add lazy tab loading** — Fetch tab data on first activation, not on page load
13. **P2: Parallelize get_360() queries** — Use `asyncio.gather()` for independent DB calls
14. **P2: Add webhook infrastructure** — Emit `employee.scored`, `employee.signal_collected` events
15. **P2: Build org chart visualization** — Hierarchical team view using manager relationships
16. **P2: Add real-time updates** — WebSocket or SSE for live signal/timeline updates
17. **P3: Add AI email/meeting summaries** — Integrate with LLM for auto-summarization
18. **P3: Build mobile-responsive views** — Optimize Employee 360 for mobile form factors
19. **P3: Implement ML-based scoring** — Replace rule-based coach with trained model
20. **P3: Add GDPR tools** — Data retention policies, right-to-erasure, consent management

## Quick Wins (Week 1-2)

1. Grant manager role employee permissions (1 line change in `permissions.py`)
2. Fix multi-select timeline filters (pass arrays to backend, parse CSV in backend)
3. Extract `ScoreBadge` and `formatRelativeTime` into shared utilities
4. Add `asyncio.gather` to parallelize profile/portfolio/signals queries
5. Add `(tenant_id, employee_id, timestamp DESC)` composite index via migration

## High Impact Improvements (Month 1-2)

1. Calendar + Email integration (ADR-012 already has engine stubs — wire them fully)
2. Department column migration + schema update across frontend/backend
3. Audit logging middleware for employee endpoints
4. Tab lazy-loading in Employee360Page
5. Replace inline SVGs with `@salesos/charts` for consistency

## Production Blockers (Before GA)

1. Manager cannot access team employee 360 (no permission)
2. No audit trail for sensitive employee data access
3. In-memory aggregation will fail under load (10K+ signals per employee)
4. No department column — data model is objectively wrong
5. Security score of 48 is below production threshold
6. No GDPR/data retention mechanism

## Future Roadmap (6-12 Months)

### Phase 1: Foundation Hardening (Month 1-2)
- Permissions fix, department column, audit logging, index optimization
- Split monolith component, extract shared utilities

### Phase 2: Integration Layer (Month 3-4)
- Calendar sync (Google + Microsoft)
- Email sync (Gmail + Outlook)
- Webhook infrastructure for real-time updates

### Phase 3: Intelligence Layer (Month 5-6)
- ML-based scoring with feedback loop
- AI email/meeting summarization
- Anomaly detection for engagement patterns
- Personalized coaching recommendations

### Phase 4: Enterprise Features (Month 7-9)
- Goals/quotas management with attainment tracking
- Org chart with team performance rollup
- Manager dashboard with team 360 aggregate view
- GDPR compliance toolkit

### Phase 5: Platform Maturity (Month 10-12)
- Mobile app support
- Public API with rate limiting and documentation
- Multi-language expansion
- SOC2 certification support

---

## Appendix: File Inventory

### Backend — 14 files
```
salesos/backend/app/modules/employee_360/__init__.py
salesos/backend/app/modules/employee_360/router.py          (75 lines, 2 endpoints)
salesos/backend/app/modules/employee_360/service.py          (385 lines, Employee360Service)
salesos/backend/app/modules/employee_360/schemas.py          (160 lines, 15 schemas)
salesos/backend/domains/employee/__init__.py
salesos/backend/domains/employee/router.py                   (677 lines, 10 endpoints)
salesos/backend/domains/employee/models.py                    (61 lines, dataclasses + enums)
salesos/backend/domains/employee/schemas.py                   (182 lines, 18 schemas)
salesos/backend/domains/employee/repository.py                 (ABC interface)
salesos/backend/domains/employee/postgres_repo.py             (199 lines, impl)
salesos/backend/domains/employee/db_models.py                  (47 lines, 2 ORM models)
salesos/backend/domains/employee/signals.py                    (195 lines, SignalPipeline)
salesos/backend/domains/employee/scoring.py                    (159 lines, ScoringEngine)
salesos/backend/domains/employee/performance.py                (242 lines, PerformanceEngine)
salesos/backend/app/modules/work_intelligence/service.py       (263 lines, WorkIntelligenceEngine)
salesos/backend/app/modules/work_intelligence/schemas.py        (49 lines, 4 schemas)
```

### Frontend — 8 files
```
salesos/frontend/src/components/employee-360-page.tsx          (1004 lines)
salesos/frontend/src/lib/api/types/employee.ts                 (218 lines, 20+ interfaces)
salesos/frontend/src/lib/api/employee.ts                       (120 lines, 10 API functions)
salesos/frontend/src/lib/hooks/employeeQueries.ts              (113 lines, 10 hooks)
salesos/frontend/src/lib/queryKeys.ts                          (employeeKeys, lines 32-43)
salesos/frontend/src/app/(dashboard)/employees/page.tsx        (749 lines)
salesos/frontend/src/app/(dashboard)/employees/me/page.tsx
salesos/frontend/src/app/(dashboard)/employees/[id]/page.tsx
salesos/frontend/src/app/(dashboard)/analytics/employees/page.tsx (340 lines)
```

### Database — 2 tables
```
employee_signals — 9 columns, 4 indexes, 0 foreign keys
employee_scores  — 12 columns, 1 index, 0 foreign keys
```

### Tests — 10 files
```
salesos/backend/tests/unit/test_employee_360_service.py
salesos/backend/tests/e2e/test_employee_360.py
salesos/backend/domains/employee/tests/test_employee360.py
salesos/backend/domains/employee/tests/test_signals.py
salesos/backend/domains/employee/tests/test_scoring.py
salesos/backend/domains/employee/tests/test_performance.py
salesos/backend/domains/employee/tests/test_pagination.py
salesos/backend/domains/employee/tests/test_bulk_operations.py
salesos/frontend/src/lib/hooks/__tests__/employeeQueries.test.tsx
salesos/frontend/e2e/12-employee-360.spec.ts
```

### i18n — 44 emp360 keys + 92 employee keys (EN + AR)
```
salesos/frontend/src/lib/i18n/en.json  (lines 957-1000)
salesos/frontend/src/lib/i18n/ar.json  (mirrored)
```

---

*End of audit. Report generated from reverse-engineering 82 source files. No modifications made.*
