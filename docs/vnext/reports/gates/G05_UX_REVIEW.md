# G-5: UX/UI Consistency Review

> **Gate**: G-5 — UX/UI Consistency Review
> **Reviewer**: Frontend Architect (AI Agent)
> **Date**: 2026-07-17
> **Scope**: Full application UX/UI consistency across all pages
> **Verdict**: 🟡 **CONDITIONAL PASS** — 5 medium issues found, remediation plan below

---

## Executive Summary

The application has a well-architected design system foundation (`@salesos/ui` + `@salesos/design-language`), comprehensive CSS variable system with dark mode, RTL support, and consistent use of shared component patterns across most pages. However, there are inconsistencies where pages bypass shared components in favor of inline/custom patterns, use hardcoded colors instead of CSS variables, and vary in page width constraints.

**Score**: 8.2/10 — structurally sound, needs targeted hardening in 5 areas.

---

## 1. Design System Consistency

### PASS — Pages using `@salesos/ui` components

| Page | Components Used |
|------|----------------|
| Companies | DataTable, Input, Select, Button, Modal, Checkbox, Badge, Combobox, DatePicker, Pagination, Spinner |
| Employees | DataTable, Input, Select, Button, Modal, Badge, Checkbox, Skeleton, EmptyState |
| Decisions | DataTable, Button, Card, Select, Modal, Skeleton, EmptyState, Textarea, DatePicker, Tooltip |
| Settings | Tabs, Tab, TabsPanel, Input, Button, Badge, Card, Spinner |
| Contacts | Input, Badge, Button, Spinner, Modal, Tooltip |
| Login | Card, CardContent, Input, Button |
| Activities | Card, CardContent, CardHeader, Badge, Button, Spinner, Input |
| Search | Input, Spinner, Badge |
| Monitoring | Card, Badge, Spinner |
| Forecast | (no @salesos/ui components aside from cn) |
| Signals | Tabs, TabsList, Tab, TabsPanel |
| Pipeline | Delegates to PipelineWorkspace (feature module) |
| Customer Success | Delegates to CustomerSuccessWorkspace (feature module) |
| Automation | Delegates to AutomationWorkspace (feature module) |

### FINDING: Forecast page does not use `@salesos/ui` components
**Severity**: Medium
**File**: `src/app/(dashboard)/forecast/page.tsx`
**Issue**: The entire Forecast page is built with raw HTML elements (`<div>`, `<p>`, inline styles, `cn()` on plain divs) and does not use any `@salesos/ui` components except `cn`. No Card, no Badge, no Spinner, no Button. The error/loading/empty states are all custom inline implementations.
**Recommendation**: Replace with `Card`, `Skeleton`, `EmptyState`, `Button` components.

### FINDING: Register page does not use `@salesos/ui` components
**Severity**: Medium
**File**: `src/app/(auth)/register/page.tsx`
**Issue**: The Register page uses raw HTML `<form>`, `<input>`, `<p>` elements. No Card, Input, or Button from `@salesos/ui`.
**Recommendation**: Refactor to use `Card`, `CardContent`, `Input`, `Button` components (consistent with Login page pattern).

### FINDING: Signals page uses raw HTML elements for data display
**Severity**: Low
**File**: `src/app/(dashboard)/signals/page.tsx`
**Issue**: The signals marketplace/cards are rendered with raw `<div>` elements instead of `Card` or `EmptyState` components.
**Recommendation**: Use `Card`, `Badge`, `EmptyState` from `@salesos/ui`.

---

## 2. Color System

### PASS — CSS variables defined and used across most pages
The `globals.css` defines comprehensive color tokens:
- Semantic: `--text-primary`, `--text-secondary`, `--text-muted`, `--text-disabled`
- Background: `--bg-primary`, `--bg-secondary`, `--bg-tertiary`
- Border: `--border-default`, `--border-hover`, `--border-active`, etc.
- Brand: `--muhide-orange`
- Charts: `--chart-1` through `--chart-12`
- Surface: `--surface-default`, `--surface-dark`, `--surface-glass`

### FINDING: Hardcoded colors in several pages
**Severity**: Medium
**Page `/decisions`** — `ConfidenceGauge` uses `text-green-600`, `text-yellow-600`, `text-red-600`, `bg-green-500`, `bg-yellow-500`, `bg-red-500` instead of CSS variables. These won't adapt in dark mode.
**Page `/revenue`** — Uses `text-green-600`, `text-red-600`, `bg-green-500`, `bg-amber-500`, `bg-red-500`, `bg-yellow-100`, `bg-gray-100` — no CSS variable usage for semantic colors.
**Page `/monitoring`** — Uses Tailwind semantic classes `bg-success-500`, `bg-warning-500`, `bg-danger-500`, `bg-info-500`, `bg-purple-500`, `text-success-500`, `text-danger-500` — these are not CSS-variable-based and won't adapt properly in dark mode.
**Page `/forecast`** — Uses `text-green-600`, `text-red-600`, `bg-white`, `border-green-200` (dark mode attempted with `dark:border-green-800` but not using CSS variables).
**Page `not-found.tsx`** — Uses `text-neutral-200`, `text-neutral-500` instead of CSS variables.
**Page `loading.tsx`** — Uses `Spinner` component correct but `min-h-[400px]` is hardcoded.
**Recommendation**: Replace all hardcoded semantic colors with CSS variables (`var(--text-primary)`, `var(--text-muted)`, `var(--bg-primary)`, `var(--border-default)`, etc.). Add CSS variables for success/warning/danger/info states and use them consistently.

### FINDING: Inconsistent inline styles in Login page
**Severity**: Low
**File**: `src/app/(auth)/login/page.tsx`
**Issue**: Login page uses inline `style={{ background: 'var(--bg-secondary)' }}` and `style={{ color: 'var(--text-primary)' }}` — while functionally correct, this is inconsistent with the rest of the application which uses className-based CSS variables.
**Recommendation**: Use `className="bg-[var(--bg-secondary)]"` and `className="text-[var(--text-primary)]"` for consistency.

---

## 3. Layout Consistency

### PASS — Consistent layout shell
All pages share the same `DashboardLayout` with:
- Sidebar (collapsible, 256px/64px)
- Header bar (56px)
- Main content area with scroll
- Mobile nav (FAB button + drawer)
- Command bar, search panel, copilot panel (lazy)

### FINDING: Inconsistent page width constraints
**Severity**: Low
| Page | Max Width |
|------|-----------|
| `/search` | `max-w-5xl` |
| `/settings` | `max-w-4xl` |
| `/pipeline` | `max-w-[1600px]` |
| `/companies` | No max-width (uses `space-y-6` padding) |
| `/employees` | No max-width |
| `/decisions` | No max-width |
| `/revenue` | No max-width |

**Recommendation**: Establish a standard page width strategy. Either use a consistent max-width for all pages (e.g. `max-w-7xl` or `max-w-[1600px]`) or reserve max-width for form-heavy pages and use full-width for data-heavy pages. Document the convention.

### FINDING: Content wrapper padding varies
**Severity**: Low
The `<main>` element adds `p-3 sm:p-4 lg:p-6`. Some pages add additional padding inside (`px-6 py-6` in pipeline), while others rely solely on the wrapper padding. This creates uneven spacing when navigating between pages.
**Recommendation**: Standardize on using only the `<main>` element's responsive padding without additional per-page padding.

---

## 4. RTL Support

### PASS — Comprehensive RTL utilities
`globals.css` provides extensive RTL utility overrides (lines 396–547) for:
- Text alignment (`text-left`, `text-right`, `text-start`, `text-end`)
- Positioning (`left-*`, `right-*`, `start-0`, `end-0`)
- Margins/padding (`ml-*`, `mr-*`, `pl-*`, `pr-*`)
- Borders (`border-l`, `border-r`, `rounded-l`, `rounded-r`)
- Transforms (`translate-x-*`, `-translate-x-*`)
- Dividers, floats, origins

### PASS — RTL-aware components
- `LanguageSwitcher` component handles locale toggle
- `MobileNav` uses `dir` for slide animation direction and FAB positioning
- Dashboard layout uses `dir` for slide animations
- Font declarations switch between IBM Plex Sans / IBM Plex Sans Arabic

### FINDING: Hardcoded `right` values in search page
**Severity**: Medium
**File**: `src/app/(dashboard)/search/page.tsx`
**Issue**: Line 94: `className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-neutral-400"` — uses `right-3` which is not RTL-aware. In RTL mode, the icon should be on the left side.
**Recommendation**: Replace with `end-3` (which is overridden in `globals.css` line 530 for `[dir="rtl"] .end-0`). Add `[dir="rtl"] .end-3 { left: 0.75rem; right: auto; }` to globals.css.

### FINDING: Hardcoded `text-right` in decisions page
**Severity**: Low
**File**: `src/app/(dashboard)/decisions/page.tsx`
**Issue**: Line 171: `className="text-xs text-neutral-500 dark:text-neutral-400 w-10 text-right"` — uses `text-right` directly, which is overridden for RTL in globals.css but the approach is fragile.
**Recommendation**: Use `text-end` instead of `text-right` for RTL-safe text alignment.

### FINDING: `formatDate` hardcodes `en-US` in decisions page
**Severity**: Low
**File**: `src/app/(dashboard)/decisions/page.tsx`
**Issue**: Lines 108-109: `new Intl.DateTimeFormat("en-US", ...)`. Should use the current locale from `useTranslation()`.
**Recommendation**: Pass locale from `useTranslation()` to `Intl.DateTimeFormat`.

---

## 5. Loading States

### PASS — Standard loading infrastructure exists
- `@salesos/ui` provides both `Skeleton` and `Spinner` components
- `src/components/skeleton.tsx` provides extended variants (`WidgetSkeleton`, `Skeleton`, custom pulse)
- Global `loading.tsx` centers a `Spinner`
- `DataTable` has built-in `loading` prop with skeleton row display

### PASS — Most data pages implement loading states
- Companies: `DataTable` with `loading={isLoading}`
- Employees: Inline `Skeleton` rows (5 items) when loading
- Decisions: `DataTable` with `loading={isLoading}`
- Settings: `Spinner` in center when profile loading
- Search: `Spinner` in search button while loading
- Activities: `Spinner` centered in card content

### FINDING: Inconsistent skeleton patterns
**Severity**: Low
**File**: `src/app/(dashboard)/revenue/page.tsx` (line 178-194) and `src/app/(dashboard)/forecast/page.tsx`
**Issue**: Revenue and Forecast pages implement custom inline `LoadingSkeleton` components instead of using the shared `Skeleton` from `@salesos/ui` or the custom `WidgetSkeleton` from `@/components/skeleton.tsx`.
**Recommendation**: Replace custom inline skeleton with `Skeleton` (card variant) or `WidgetSkeleton`.

### FINDING: Monitoring page uses bare Spinner + text instead of Skeleton
**Severity**: Low
**File**: `src/app/(dashboard)/monitoring/page.tsx`
**Issue**: Loading state is `padding py-20 text-center text-neutral-500` with `Spinner + "Loading..."` text. No skeleton structure matching the eventual content layout.
**Recommendation**: Use `Skeleton` (card variant) matching the 4-stat-card layout + chart layouts.

---

## 6. Empty States

### PASS — `EmptyState` component and DataTable integration
The `@salesos/ui` `EmptyState` component is well-designed with icon, title, description, action button, and learn-more link. DataTable has built-in `emptyState` prop.

### PASS — Good empty states in major pages
- **Companies**: Uses DataTable's `emptyState` prop with icon, title, description, and conditional action button.
- **Employees**: Uses `EmptyState` from `@salesos/ui` for both "no results" and "no data" states.
- **Decisions**: Uses DataTable's `emptyState` prop with icon, title, description, and conditional action button.
- **Settings**: Uses `EmptyState`-like patterns for missing data in data sources.

### FINDING: Custom inline empty states instead of `EmptyState` component
**Severity**: Medium
**File**: `src/app/(dashboard)/revenue/page.tsx` (lines 196-212)
**Issue**: Revenue dashboard has a custom `EmptyStateComponent` with inline markup, hardcoded English text, and custom button. Should use the shared `EmptyState` component with proper i18n.
**File**: `src/app/(dashboard)/search/page.tsx` (lines 152-156)
**Issue**: Empty search results rendered with inline `<div>` markup, hardcoded classes, and no shared `EmptyState` component.
**File**: `src/app/(dashboard)/monitoring/page.tsx` (lines 114, 120, etc.)
**Issue**: Inline empty state in error section, no EmptyState component.
**File**: `src/app/(dashboard)/activities/page.tsx` (lines 145-154)
**Issue**: Inline empty state UI instead of `EmptyState` component.
**Recommendation**: Use `EmptyState` from `@salesos/ui` consistently across all pages.

### FINDING: No empty state in Signals page
**Severity**: Low
**File**: `src/app/(dashboard)/signals/page.tsx`
**Issue**: When signals/feed/subscriptions lists are empty, no empty state is rendered (data just shows no rows).
**Recommendation**: Add `<EmptyState>` for each tab when data is empty.

---

## 7. Error States

### PASS — Robust error handling infrastructure
- `ErrorBoundary` (class component) with `componentDidCatch`, `sentry:capture` event, and retry
- `ErrorFallback` (functional component) with icon, title, message, retry button, and optional error details panel
- `withErrorBoundary` HOC utility
- `error.tsx` for dashboard route
- Most data pages implement inline error handling

### FINDING: Custom inline error UIs instead of `ErrorFallback`
**Severity**: Medium
**File**: `src/app/(dashboard)/revenue/page.tsx` (lines 308-321)
**Issue**: Inline error display with `AlertTriangle`, `text-red-500` hardcoded colors, and a retry button. Should use `ErrorFallback` component.
**File**: `src/app/(dashboard)/forecast/page.tsx`
**Issue**: Inline error display with hardcoded colors.
**File**: `src/app/(dashboard)/monitoring/page.tsx` (lines 44-46)
**Issue**: Uses inline loading spinner + text for error case.
**File**: `src/app/(dashboard)/activities/page.tsx` (lines 138-144)
**Issue**: Inline error UI custom-built instead of `ErrorFallback`.
**File**: `src/app/(dashboard)/signals/page.tsx`
**Issue**: No explicit error handling in page (errors from API silently caught).
**Recommendation**: Use `ErrorFallback` from `@/components/foundation/error-boundary` consistently across all pages.

### FINDING: Login/Register pages use inline error display
**Severity**: Low
**Files**: `src/app/(auth)/login/page.tsx`, `src/app/(auth)/register/page.tsx`
**Issue**: Error messages displayed via inline `<p>` element with `style={{ color: 'var(--danger-600, #EF4444)' }}`. While functional, this isn't consistent with the rest of the app.
**Recommendation**: Consider extracting a reusable `AuthError` component, or use the `error` prop on `Input` component for field-level errors.

---

## 8. Dark Mode

### PASS — Dark mode infrastructure works
- `.dark` class overrides on `html` element
- Full CSS variable redefinition for dark mode
- `useTheme` hook with light/dark/system support
- `toggle` function available globally
- Most pages use `dark:` Tailwind variants or CSS variables

### PASS — Components use CSS variables for dark mode
UI components from `@salesos/ui` use `var(--bg-primary)`, `var(--text-primary)`, `var(--border-default)` etc., which automatically adapt in dark mode.

### FINDING: Hardcoded colors break dark mode adaptation
**Severity**: Medium
**Details**: All hardcoded color issues listed in Section 2 affect dark mode. Specifically:
- Pages using `text-green-600`, `text-red-600`, `text-yellow-600` (decisions, revenue, monitoring, forecast) will have poor contrast on dark backgrounds.
- `bg-white` in forecast page becomes white on dark mode (should adapt).
- Pages not using CSS variables will appear identical in dark mode with no adaptation.
**Recommendation**: Resolve all hardcoded color issues from Section 2. Add CSS variables for semantic state colors (success, warning, danger, info) and use them everywhere.

### FINDING: No dark mode toggle button in header
**Severity**: Low
**Issue**: The header has a language switcher button but no theme toggle button. Dark mode is only toggled via keyboard event (`salesos:toggle-theme`). New users may not discover this.
**Recommendation**: Add a theme toggle button to the header, next to the LanguageSwitcher.

---

## 9. Navigation

### PASS — Navigation is consistent
- Sidebar renders 26 navigation items from `NAV_KEYS` array
- Active route highlighting with orange accent
- Collapsible sidebar (desktop), FAB + drawer (mobile)
- Mobile nav has responsive subset of 10 most common pages
- All pages use the same `DashboardLayout`

### FINDING: Duplicate nav entry for `/contacts`
**Severity**: Low
**File**: `src/app/(dashboard)/layout.tsx` (lines 21-22)
**Issue**: `/contacts` appears twice in `NAV_KEYS` with the same icon and key. This creates a duplicate sidebar item.
**Recommendation**: Remove the duplicate entry.

### FINDING: `/dashboard` route doesn't exist as directory
**Severity**: Low
**Issue**: The `page.tsx` at `(dashboard)/page.tsx` serves as the dashboard home page, but `NAV_KEYS` references `/dashboard` (line 17). The `pathname.startsWith("/dashboard")` check in the sidebar won't match the root `/`, meaning the dashboard nav item won't show as active when on the dashboard page.
**Recommendation**: Either create a `/dashboard` route directory or update the active check logic.

---

## Summary of Issues (P0-P2)

| ID | Area | Severity | Page | Description |
|----|------|----------|------|-------------|
| UX-01 | Color System | Medium | Multiple | Hardcoded colors (`text-green-600`, `text-red-600`, `bg-white`, etc.) used instead of CSS variables — breaks dark mode |
| UX-02 | Design System | Medium | Forecast | No `@salesos/ui` components used — fully custom implementation |
| UX-03 | Design System | Medium | Register | No `@salesos/ui` components used — fully custom implementation |
| UX-04 | Empty States | Medium | Revenue, Search, Monitoring, Activities, Signals | Custom inline empty states instead of `EmptyState` component |
| UX-05 | Error States | Medium | Revenue, Forecast, Monitoring, Activities, Signals | Custom inline error UIs instead of `ErrorFallback` component |
| UX-06 | Loading States | Low | Revenue, Forecast, Monitoring | Custom inline skeletons instead of `Skeleton` component |
| UX-07 | RTL | Medium | Search | Hardcoded `right-3` not RTL-aware |
| UX-08 | RTL | Low | Decisions | Hardcoded `en-US` locale in date formatting, hardcoded `text-right` |
| UX-09 | Layout | Low | Multiple | Inconsistent page max-width constraints |
| UX-10 | Navigation | Low | Dashboard layout | Duplicate `/contacts` entry, `/dashboard` route mismatch |
| UX-11 | Dark Mode | Low | Dashboard layout | No theme toggle button visible in header |
| UX-12 | Layout | Low | Login page | Uses inline `style={{}}` instead of className pattern |

---

## Verdict: 🟡 CONDITIONAL PASS

**Criteria**:
- ✅ No P0 or Critical issues found
- 🟡 5 Medium issues (UX-01, UX-02/UX-03, UX-04, UX-05, UX-07)
- 7 Low issues (UX-06, UX-08, UX-09, UX-10, UX-11, UX-12)

**Condition**: All 5 Medium issues must be resolved before GA launch. Low issues should be added to the post-launch backlog and addressed in the next sprint.

---

## Remediation Plan

| Priority | Issue | Effort | Owner | Sprint |
|----------|-------|--------|-------|--------|
| P1 | UX-01: Replace hardcoded colors with CSS variables across 7 pages | 1d | Frontend Engineer | Current |
| P1 | UX-02: Refactor Forecast page to use `@salesos/ui` components | 0.5d | Frontend Engineer | Current |
| P1 | UX-03: Refactor Register page to use `@salesos/ui` components | 0.5d | Frontend Engineer | Current |
| P1 | UX-04: Replace inline empty states with `EmptyState` component (5 pages) | 0.5d | Frontend Engineer | Current |
| P1 | UX-05: Replace inline error UIs with `ErrorFallback` component (5 pages) | 0.5d | Frontend Engineer | Current |
| P2 | UX-06: Replace custom skeletons with `Skeleton` component | 0.5d | Frontend Engineer | Next |
| P2 | UX-07: Fix RTL `right-3` in search page | 0.25d | Frontend Engineer | Next |
| P2 | UX-08: Fix locale and alignment in Decisions page | 0.25d | Frontend Engineer | Next |
| P2 | UX-09: Standardize page width constraints | 0.25d | Frontend Architect | Next |
| P2 | UX-10: Fix duplicate nav entries and route mismatch | 0.25d | Frontend Engineer | Next |
| P2 | UX-11: Add theme toggle button to header | 0.5d | Frontend Engineer | Next |
| P2 | UX-12: Normalize Login page className usage | 0.25d | Frontend Engineer | Next |

**Estimated total effort**: 4.5 days
**Blocking GA**: No — all issues are P1/P2, no P0 or Critical
