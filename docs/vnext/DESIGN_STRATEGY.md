# SalesOS Design Strategy — vNext

> **Author**: Design Director
> **Status**: Draft
> **Last Updated**: 2026-07-16
> **Audit Basis**: Design Audit v1.0 (10 findings across 6 domains)

---

## Table of Contents

1. [Design System V2](#1-design-system-v2)
2. [UI Consistency](#2-ui-consistency)
3. [UX Improvements](#3-ux-improvements)
4. [Navigation](#4-navigation)
5. [Information Architecture](#5-information-architecture)
6. [Component Library](#6-component-library)
7. [Charts](#7-charts)
8. [Tables](#8-tables)
9. [Forms](#9-forms)
10. [Responsive](#10-responsive)
11. [Dark Mode](#11-dark-mode)
12. [Accessibility](#12-accessibility)
13. [Interaction Patterns](#13-interaction-patterns)
14. [Prioritized Design Backlog](#14-prioritized-design-backlog)

---

## 1. Design System V2

### Current State

A mature 3-layer design system exists:

| Layer | Location | Contents |
|-------|----------|---------|
| Tokens | `@salesos/design-language` | 16 files — colors, typography, spacing, shadows, breakpoints, animation |
| Components | `@salesos/ui` | 17 components — reusable UI primitives |
| Theme | `tailwind.config.ts` | Tailwind extension with MUHIDE palette |

### V2 Goals

1. **Complete semantic coverage** — all Tailwind utility classes in pages must map to CSS variables, not raw values
2. **Audit-gap closure** — resolve all 10 issues from Design Audit before adding new surfaces
3. **Versioned releases** — `@salesos/design-language@2.0`, `@salesos/ui@2.0` with changelogs
4. **Component count** — expand from 17 to 25+ components
5. **Frozen surface** — lock the token API after V2 to prevent drift

### Token Roadmap

| Token Category | Current | V2 Target | Priority |
|---------------|---------|-----------|----------|
| Color primitives | 10-step palettes (7 hues) | Add tertiary (teal), expand ai/copilot palette | P2 |
| Typography | 8-stop scale (11–48px) | Add 56px, 64px for display; document line-height pairs | P1 |
| Spacing | Tailwind defaults | Custom `--space` scale (4–64px, 4px grid) | P1 |
| Shadows | Basic elevation | 5-level elevation system (`sm`, `md`, `lg`, `xl`, `focus-ring`) | P2 |
| Motion | None centralized | `--duration-*`, `--easing-*` token families | P2 |

### Migration Strategy

- Phase 1: Fix all audit issues (this document sections 2–13)
- Phase 2: Publish `@salesos/design-language@2.0.0-alpha`
- Phase 3: Upgrade `@salesos/ui` to consume V2 tokens
- Phase 4: Migrate page-level code to CSS variables
- Phase 5: Freeze and document

---

## 2. UI Consistency

### Audit Findings

| Finding | Severity | Location | Detail |
|---------|----------|----------|--------|
| CSS variable mismatch | 🔴 High | Login page | Uses `--background`, `--card` (shadcn/ui) instead of MUHIDE `--bg-primary`, `--surface-card` |
| Tailwind bypass | 🟡 Medium | Multiple pages | `text-neutral-900` instead of `var(--text-primary)` |
| Muted text contrast | 🔴 High | Global | `#A59E90` on white = 2.9:1 (needs 4.5:1 for WCAG AA) |
| Duplicate Card | 🟡 Medium | `@salesos/ui` | Deprecated Card component still present alongside current one |
| Chart color mismatch | 🔴 High | `@salesos/charts` | Hardcoded Recharts colors start with `#3B82F6` (blue) instead of `#F57C1E` (orange) |

### Resolution Plan

#### 2.1 Login Page Refactor (P0)

- Replace shadcn/css CSS variables with MUHIDE semantic tokens
- Swap raw `<input>` and `<button>` elements for `@salesos/ui` `Input` and `Button` components
- Audit login page for any other raw HTML elements

#### 2.2 CSS Variable Enforcement (P0)

- Add ESLint rule forbidding Tailwind utility color classes (`text-neutral-*`, `bg-neutral-*`, etc.) in page components
- Require `var(--text-*)`, `var(--bg-*)`, `var(--surface-*)` CSS variables in all page-level code
- Create codemod script to auto-migrate existing usages

#### 2.3 Muted Text Contrast Fix (P0)

- Current: `#A59E90` (light mode muted text)
- Target: minimum `#8C8374` (4.56:1 on white, passes WCAG AA)
- Adjust `--text-muted` token in design-language
- Verify all downstream uses meet 4.5:1 minimum

#### 2.4 Duplicate Card Removal (P1)

- Identify the deprecated Card component
- Remove from `@salesos/ui` exports
- Update any remaining imports across the codebase
- Document breaking change in changelog

#### 2.5 Page Audit (P1)

- Walk every page component and check for:
  - Raw color values (Tailwind classes)
  - Inline styles with hardcoded colors
  - Missing semantic variable usage
- Track in a spreadsheet, fix in priority order

---

## 3. UX Improvements

### Priority Improvements

| Improvement | Impact | Effort | Priority |
|------------|--------|--------|----------|
| Consistent empty states across all domains | High | Medium | P1 |
| Loading skeletons for all data surfaces | High | Medium | P1 |
| Toast/notification system for async operations | High | Low | P1 |
| Keyboard shortcuts reference panel | Medium | Low | P2 |
| Page-level breadcrumbs | Medium | Medium | P2 |
| Unified error state pattern (retry + message) | High | Low | P1 |

### Empty States

Every list, table, and search result must have:

1. **Illustration** — contextual SVG illustration
2. **Title** — what's missing ("No companies found")
3. **Description** — why it might be empty and what to do
4. **Action** — primary CTA ("Add your first company")
5. **Learn more** — link to docs

Implement as `<EmptyState>` component in `@salesos/ui`.

### Loading States

- Every data-fetching surface shows a skeleton matching the final layout
- Use `@salesos/ui` `Skeleton` component (must be added)
- Avoid spinners for content areas — use skeleton patterns
- Spinners acceptable for: auth checks, file uploads, full-page transitions

### Toast / Notification System

- Add `useToast()` hook and `<ToastContainer>` to `@salesos/ui`
- Four variants: success, error, warning, info
- Auto-dismiss for info/success (5s), manual dismiss for error/warning
- Stack multiple toasts, max 5 visible

---

## 4. Navigation

### Current State

- No unified navigation component in `@salesos/ui`
- Pages appear to handle navigation independently

### Proposed Architecture

```
┌─────────────────────────────────────────────┐
│ Top Bar (tenant + user + global search)      │
├──────────┬──────────────────────────────────┤
│ Sidebar  │ Content Area                      │
│ (primary │                                    │
│  nav)    │                                    │
│          │                                    │
│ ──────── │                                    │
│ Footer   │                                    │
│ (context)│                                    │
└──────────┴───────────────────────────────────┘
```

### Components to Design

1. **`<Sidebar>`** — collapsible, nested items, active state, section headers
2. **`<TopBar>`** — breadcrumbs + actions user menu + search trigger
3. **`<Breadcrumbs>`** — auto-generated from route, optional
4. **`<NavItem>`** — icon + label + badge + active indicator

### Navigation Patterns

- Sidebar supports 3 levels of nesting maximum
- Collapse to icon-only on narrow viewports
- Active item follows current route
- Section headers are collapsible groups
- Keyboard: arrow keys to navigate, Enter to activate

---

## 5. Information Architecture

### Current Gaps

- No consistent page hierarchy documented
- No standardized detail page layout
- Action placement inconsistent across pages

### Standardized Page Templates

Design 4 page templates in `@salesos/ui`:

| Template | Use Case | Sections |
|----------|----------|----------|
| ListPage | Search + filter + results | Top bar, filter bar, data table, pagination |
| DetailPage | Single entity view | Back link, header (title + actions), tabs/sections, metadata sidebar |
| DashboardPage | Metric overview | Widget grid, date range selector, export actions |
| FormPage | Data entry | Step indicator (if multi-step), form fields, save/cancel |

### Detail Page Layout

```
[Back to Companies]
─────────────────────────────────────────────
Acme Corp                        [Edit] [Delete]
─── Tabs ───────────────────────────────────
| Overview | Contacts | Deals | Activity |
───────────────────────────────────────────
┌─────────────────────┐ ┌──────────┐
│ Main content area    │ │ Metadata │
│                      │ │ sidebar  │
│                      │ │          │
└─────────────────────┘ └──────────┘
```

### Action Standardization

- Primary actions: top-right of header (Edit, Create, Save)
- Secondary actions: dropdown menu (Export, Duplicate, Archive)
- Destructive actions: always require confirmation dialog
- Bulk actions: top of data table, disabled until selection

---

## 6. Component Library

### Current Inventory: `@salesos/ui` (17 components)

Existing components to preserve and improve (with ARIA, RTL, and reduced motion intact):

- Button, Card, Modal, Dropdown, Tooltip, Badge, Avatar, Spinner, Tabs, Accordion, Alert, Input (basic), Select (basic), Table (basic), Pagination (inline), Toggle, Progress

### Component Gaps (Missing)

| Component | Priority | Reason |
|-----------|----------|--------|
| Checkbox | P0 | Required for all form and table selection |
| Radio Group | P0 | Required for form options |
| Switch | P0 | Required for settings toggles |
| Textarea | P0 | Required for form text input |
| DatePicker | P0 | Required for date ranges and filters |
| Skeleton | P0 | Required for loading states (UX P1) |
| EmptyState | P0 | Required for empty states (UX P1) |
| Toast / ToastContainer | P1 | Notification system |
| Sidebar | P1 | Navigation architecture |
| Breadcrumbs | P1 | Navigation architecture |
| Dialog / Confirm | P1 | Destructive action confirmation |
| Combobox | P1 | Searchable select |
| MultiSelect | P1 | Tag/chip selection |
| FileUpload | P1 | File attachment |
| Pagination (unified) | P1 | Replace inline duplicates |
| Stepper | P2 | Multi-step forms |
| ColorPicker | P2 | Settings/preferences |

### Component Design Principles

1. **Controlled + uncontrolled** — every form component supports both modes
2. **Ref forwarding** — all input components forward refs
3. **Size prop** — `sm`, `md`, `lg` variants
4. **Full error state** — `error`, `errorMessage` props rendering with red border + helper text
5. **Disabled state** — visual + pointer-events disabled
6. **Label + helper text slots** — every input has `label` and `helperText` props
7. **Required indicator** — `required` prop shows asterisk on label

### Component Status Matrix (Target V2)

| Component | Status | ARIA | RTL | Reduced Motion | Tests |
|-----------|--------|------|-----|----------------|-------|
| Button | ✅ Existing | ✅ | ✅ | ✅ | ✅ |
| Input | ✅ Existing (basic) | ✅ | ✅ | ✅ | ✅ |
| Select | ✅ Existing (basic) | ✅ | ✅ | ✅ | ✅ |
| Card | 🔴 Fix duplicate | ✅ | ✅ | ✅ | ✅ |
| Pagination | 🔴 Unify (3+ impls) | ✅ | ✅ | ✅ | ✅ |
| Checkbox | 🆕 Add | 🔲 | 🔲 | 🔲 | 🔲 |
| Radio Group | 🆕 Add | 🔲 | 🔲 | 🔲 | 🔲 |
| Switch | 🆕 Add | 🔲 | 🔲 | 🔲 | 🔲 |
| Textarea | 🆕 Add | 🔲 | 🔲 | 🔲 | 🔲 |
| DatePicker | 🆕 Add | 🔲 | 🔲 | 🔲 | 🔲 |
| Skeleton | 🆕 Add | 🔲 | ✅ | 🔲 | 🔲 |
| EmptyState | 🆕 Add | 🔲 | 🔲 | 🔲 | 🔲 |
| Toast | 🆕 Add | 🔲 | 🔲 | 🔲 | 🔲 |

---

## 7. Charts

### Audit Finding

`@salesos/charts` uses hardcoded Recharts colors starting with `#3B82F6` (blue) instead of the brand primary `#F57C1E` (orange). Chart colors also don't match backend design tokens.

### Root Cause Analysis

- Chart library was built before design token system was finalized
- Colors were chosen independently without coordination with backend token definitions
- No single source of truth for chart color sequences

### Chart Color System Redesign

#### Semantic Chart Palette

```
Chart Sequence (12 colors, cyclical):
  #F57C1E  (orange — primary)
  #22C55E  (green — success)
  #F59E0B  (amber — warning)
  #EF4444  (red — danger)
  #A855F7  (purple — ai/copilot)
  #3B82F6  (blue — info)
  #F97316  (orange-700)
  #16A34A  (green-700)
  #D97706  (amber-700)
  #DC2626  (red-700)
  #9333EA  (purple-700)
  #2563EB  (blue-700)
```

#### Token Alignment

- Export chart colors from `@salesos/design-language` as `--chart-1` through `--chart-12`
- Backend should reference the same token names for API-level color definitions
- `@salesos/charts` must consume `--chart-*` CSS variables, not hardcoded hex values

#### Implementation

1. Add 12 chart color tokens to design-language (light + dark variants)
2. Create `<ChartThemeProvider>` wrapping Recharts with default `--chart-*` mapping
3. Update all chart instances to remove hardcoded palettes
4. Document chart color sequence for backend team reference

---

## 8. Tables

### Current State

- `<Table>` component exists in `@salesos/ui`
- 2+ pages have inline pagination components with different implementations
- No standardized sort, filter, or selection on table rows

### Table Component V2

Build a `<DataTable>` component with:

| Feature | Description | Priority |
|---------|-------------|----------|
| Sortable columns | Click header to sort asc/desc, visual indicator | P0 |
| Row selection | Checkbox column, shift-click for multi-select | P0 |
| Column visibility toggle | Dropdown to show/hide columns | P1 |
| Resizable columns | Drag column borders | P2 |
| Sticky header | Header stays fixed on scroll | P0 |
| Striped rows | Optional alternating background | P1 |
| Row actions | Action menu per row (ellipsis icon) | P0 |
| Footer row | Aggregation (sum, count, avg) | P2 |
| Expandable rows | Click to reveal detail panel | P1 |
| Empty state | Delegates to `<EmptyState>` component | P0 |

### Pagination Standardization

- Replace all inline pagination implementations with `<Pagination>` component
- Unified API:
  ```tsx
  <Pagination
    currentPage={1}
    totalPages={25}
    totalItems={487}
    pageSize={20}
    onPageChange={handlePageChange}
    onPageSizeChange={handlePageSizeChange}
    pageSizeOptions={[10, 20, 50, 100]}
  />
  ```
- Show visible page numbers with ellipsis for large ranges
- Show total count: "Showing 1–20 of 487"
- Keyboard: Left/Right arrows, Home/End

---

## 9. Forms

### Current State

- Basic `Input` and `Select` components exist
- Login page uses raw `<input>` and `<button>` elements (audit finding)
- No form validation library integration
- No form layout primitives

### Form Component Library Plan

#### New Components (from section 6 gaps)

| Component | Purpose |
|-----------|---------|
| Checkbox | Single checkbox with label |
| Radio Group | Mutually exclusive options |
| Switch | Boolean toggle |
| Textarea | Multi-line text input |
| DatePicker | Date selection + range |
| Combobox | Searchable dropdown |
| MultiSelect | Tag/chip multi-select |
| FileUpload | Drag-and-drop + click to upload |

#### Form Layout Primitives

```tsx
<Form>                    // form wrapper, handles onSubmit
  <FormSection label="Basic Info">  // section with heading
    <FormRow>             // 2-column grid row
      <FormField label="Name" required error="Required">
        <Input />
      </FormField>
      <FormField label="Email">
        <Input type="email" />
      </FormField>
    </FormRow>
  </FormSection>
  <FormActions>
    <Button type="submit">Save</Button>
    <Button variant="ghost">Cancel</Button>
  </FormActions>
</Form>
```

#### Validation Integration

- Support React Hook Form + Zod out of the box
- Each form component exposes `error` prop
- `<FormField>` wraps label + input + error message
- Error state: red border + red text below input
- Success state: green border (optional)

#### Login Page Form (P0 Fix)

- Replace raw `<input>` with `@salesos/ui` `Input`
- Replace raw `<button>` with `@salesos/ui` `Button`
- Add form validation with appropriate error messages
- Use `FormField` pattern for label/error consistency
- Switch from shadcn/css variables to MUHIDE tokens

---

## 10. Responsive

### Current State

- RTL support via CSS is preserved and working
- Dark mode via class strategy is implemented
- No documented responsive breakpoint strategy beyond Tailwind defaults

### Breakpoint Strategy

Use Tailwind defaults as the canonical set (already in `tailwind.config.ts`):

| Breakpoint | Width | Target |
|-----------|-------|--------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet portrait |
| `lg` | 1024px | Tablet landscape / small desktop |
| `xl` | 1280px | Desktop |
| `2xl` | 1536px | Large desktop |

### Layout Responsive Behavior

| Component | Mobile (<768px) | Tablet (768–1024px) | Desktop (>1024px) |
|-----------|----------------|---------------------|-------------------|
| Sidebar | Hidden, hamburger trigger | Collapsed (icons only) | Expanded |
| TopBar | Stack vertically | Single row | Single row |
| Detail page | Single column | 2-column | 2-column + sidebar |
| Data table | Card list (horizontal scroll as fallback) | Scrollable table | Full table |
| Filters | Full-screen overlay | Slide-out panel | Inline above table |
| Forms | Single column | Single column | 2-column rows |

### Implementation Rules

1. All new components must be responsive from inception
2. No `overflow-x: scroll` on the `<body>` — contain scroll inside components
3. Touch targets minimum 44×44px on mobile
4. Table horizontal scroll is acceptable but must show gradient indicator
5. Sidebar must have smooth open/close animation (respect reduced motion)

---

## 11. Dark Mode

### Current State

- Dark mode via class strategy on `<html>` is implemented
- Semantic CSS variables exist for light/dark mode
- Not all surfaces have been verified for dark mode completeness

### Dark Mode Verification Checklist

Every component and page must pass:

| Check | Detail |
|-------|--------|
| Background | All `--bg-*` surfaces have dark variants |
| Text | All `--text-*` colors have dark variants |
| Surface | All `--surface-*` (card, modal, sidebar) have dark variants |
| Border | All `--border-*` colors have dark variants |
| Shadow | Shadows darken in dark mode (lower opacity, darker color) |
| Chart colors | Chart sequence has dark mode variants |
| Form inputs | Input backgrounds, borders, focus rings in dark mode |
| Modal overlay | Overlay opacity in dark mode |
| Scrollbars | Dark scrollbars in dark mode |
| Focus rings | Visible contrast in dark mode |

### New Dark Tokens Required

| Token | Light Value | Dark Value |
|-------|------------|------------|
| `--bg-primary` | `#FAFAFA` | `#151214` |
| `--surface-card` | `#FFFFFF` | `#1E1C1F` |
| `--surface-sidebar` | `#F5F4F2` | `#1A181B` |
| `--border-default` | `#CCC6BA` | `#3D393C` |
| `--text-primary` | `#151214` | `#FAFAFA` |
| `--text-muted` | `#8C8374` | `#A59E90` |

### Implementation

- Update `@salesos/design-language` dark token maps
- Create dark mode visual regression test for every component
- Add dark mode toggle to Storybook/story pages
- Verify login page dark mode (currently may not render correctly due to shadcn/css tokens)

---

## 12. Accessibility

### Current State

- ARIA attributes present on all existing `@salesos/ui` components
- Reduced motion support via `@media (prefers-reduced-motion)` is implemented
- Target: WCAG AA

### Audit Gaps

| Finding | WCAG Criterion | Severity |
|---------|---------------|----------|
| Muted text `#A59E90` on white (2.9:1) | 1.4.3 Contrast (Minimum) — AA | 🔴 Fail |
| No Checkbox/Radio/Switch components | 4.1.2 Name, Role, Value | 🟡 Needs audit |
| No DatePicker | 1.3.1 Info and Relationships | 🟡 Needs audit |
| Inline pagination duplicates | 4.1.2 Name, Role, Value | 🟡 Needs audit |
| No form validation error announcements | 4.1.3 Status Messages | 🟡 Needs audit |

### WCAG AA Compliance Plan

#### P0 — Immediate Fix

| Item | Action | Target |
|------|--------|--------|
| Muted text contrast | Update `--text-muted` token | 4.5:1 minimum |
| Focus indicators | Ensure all interactive elements have visible focus ring | 3:1 contrast against adjacent |

#### P1 — Component Audit

| Item | Action | Target |
|------|--------|--------|
| New components (Checkbox, Radio, Switch) | Implement with full ARIA | Spec-compliant |
| Form validation | Error messages use `aria-describedby` + `role="alert"` | Screen reader announcement |
| Modal focus trap | Trap focus within modal when open | WCAG 2.4.3 |
| Skip-to-content link | Add skip navigation link | WCAG 2.4.1 |

#### P2 — Enhanced

| Item | Action | Target |
|------|--------|--------|
| Touch targets | All interactive elements ≥ 44×44px on touch devices | WCAG 2.5.5 |
| Motion toggle | Respect `prefers-reduced-motion` on all animations | WCAG 2.3.3 |
| Status announcements | Toast/notification system uses `aria-live="polite"` | WCAG 4.1.3 |
| PDF/download links | Indicate file type and size in link text | WCAG 2.4.4 |

### Testing

- All new components must pass axe-core automated tests
- Color contrast verified with manual check (not automated alone)
- Keyboard navigation walkthrough for every new page/feature
- Screen reader compatibility (VoiceOver on macOS, NVDA on Windows)

---

## 13. Interaction Patterns

### Pattern Library

Standardize and document these interaction patterns for all teams:

#### 13.1 Instant Search

- 300ms debounce after user stops typing
- Show loading skeleton in results area
- Show "No results" empty state with suggestion
- Preserve search term in URL for share-ability
- Escape key clears search and results

#### 13.2 Bulk Selection

- Checkbox in table header: select all / deselect all
- Shift-click: range selection
- Show count in action bar: "3 selected"
- Bulk actions enable when ≥ 1 selected
- Action bar appears above table (slide-down)

#### 13.3 Confirmation Dialogs

- Destructive actions always require confirmation
- Dialog pattern: title + description + confirm button (red for destructive) + cancel
- Support "Don't ask again" for non-destructive repetitive actions
- Escape key dismisses

#### 13.4 Async Operations

1. User clicks action → button shows loading spinner
2. Success → toast notification, button restores
3. Error → toast with error message, button restores
4. Long operation (>5s) → progress indicator with cancel option

#### 13.5 Inline Editing

- Click to edit on detail pages
- Field becomes editable input
- Enter/Tab to save, Escape to cancel
- Show saved indicator briefly
- Optimistic update with rollback on error

#### 13.6 Filtering

- Filter bar above data tables
- Each filter is a removable chip
- "Clear all" link when filters active
- Filter state persisted in URL query params
- Debounced fetch on filter change (300ms)

#### 13.7 Drag and Drop

- Visual drag handle on sortable items
- Drop target zone highlighs on hover
- Animation during reorder (respect reduced motion)
- Save button to commit, undo within 5 seconds

### Animation Principles

| Property | Duration | Easing | Notes |
|----------|----------|--------|-------|
| Opacity/fade | 200ms | ease-out | Modals, tooltips |
| Transform/position | 300ms | ease-in-out | Sidebar, accordion |
| Height expand | 250ms | ease-out | Collapsible sections |
| Color transitions | 150ms | ease | Hover states, focus |
| Page transitions | 300ms | ease-in-out | Route changes |

All animations must check `prefers-reduced-motion: reduce` and disable or simplify.

---

## 14. Prioritized Design Backlog

Ranked by impact on user experience, accessibility, and consistency.

### P0 — Sprint-Blocking (Must fix before next release)

| # | Item | Section | Effort | Reason |
|---|------|---------|--------|--------|
| 1 | Login page: replace shadcn/css tokens with MUHIDE, swap raw elements for UI components | 2.1, 9.4 | 2 days | First impression, brand consistency |
| 2 | Fix muted text contrast (#A59E90 → #8C8374) | 2.3 | 1 day | WCAG AA failure, legal risk |
| 3 | Remove duplicate Card component | 2.4 | 0.5 day | Code quality, prevents confusion |
| 4 | Add Checkbox, Radio, Switch, Textarea components | 6, 9 | 5 days | Forms cannot ship without these |
| 5 | Fix chart colors to use `--chart-*` tokens starting with orange | 7 | 2 days | Brand consistency, backend alignment |
| 6 | Unify pagination into single component | 8 | 3 days | Consistency, reduces bugs |

### P1 — High Impact (Should fix in vNext)

| # | Item | Section | Effort | Reason |
|---|------|---------|--------|--------|
| 7 | Add Skeleton and EmptyState components | 3, 6 | 3 days | Required for loading/empty UX |
| 8 | ESLint rule: forbid Tailwind color classes in page components | 2.2 | 1 day | Prevents regression |
| 9 | Add DatePicker + Combobox components | 6, 9 | 5 days | Common form patterns |
| 10 | Design and build DataTable with sort, select, sticky header | 8 | 5 days | Core data interaction |
| 11 | Build Sidebar + Breadcrumbs navigation components | 4, 6 | 4 days | Navigation architecture |
| 12 | Add form validation integration (React Hook Form + Zod) | 9 | 3 days | Form quality |
| 13 | Implement toast/notification system | 3, 6 | 2 days | Async feedback |

### P2 — Medium Impact (Plan for next sprint after vNext)

| # | Item | Section | Effort | Reason |
|---|------|---------|--------|--------|
| 14 | Add typography tokens for 56px and 64px sizes | 1 | 1 day | Design system completeness |
| 15 | Add space token scale | 1 | 2 days | Design system completeness |
| 16 | Build FileUpload + MultiSelect components | 6, 9 | 4 days | Form completeness |
| 17 | Add responsive layout templates (List, Detail, Dashboard, Form) | 5 | 5 days | IA consistency |
| 18 | Add column visibility + expandable rows to DataTable | 8 | 3 days | Power user features |
| 19 | Dark mode verification pass across all pages | 11 | 3 days | Dark mode completeness |
| 20 | Add chart color dark mode variants | 11 | 1 day | Dark mode completeness |
| 21 | Build Form, FormSection, FormRow, FormField primitives | 9 | 2 days | Form layout consistency |

### P3 — Polish (Low priority, address opportunistically)

| # | Item | Section | Effort | Reason |
|---|------|---------|--------|--------|
| 22 | Add Stepper component | 6 | 2 days | Nice-to-have for wizards |
| 23 | Add resizable columns to DataTable | 8 | 3 days | Power feature |
| 24 | Add aggregation footer to DataTable | 8 | 2 days | Power feature |
| 25 | Build keyboard shortcuts panel | 3 | 2 days | Power user productivity |
| 26 | Add page-level breadcrumbs | 3, 4 | 2 days | Navigation polish |
| 27 | Add shadow elevation tokens | 1 | 1 day | Visual polish |
| 28 | Add tertiary (teal) color palette | 1 | 1 day | Brand expansion |

### Backlog Summary

| Priority | Items | Total Effort | Impact |
|----------|-------|-------------|--------|
| P0 | 6 | 13.5 days | Brand, accessibility, blocking |
| P1 | 7 | 23 days | UX, consistency, navigation |
| P2 | 7 | 19 days | Completeness, dark mode, polish |
| P3 | 6 | 11 days | Enhancement, power users |
| **Total** | **26** | **66.5 days** | |

---

## Appendix: Quick Wins (Can be done in parallel)

These items have no dependencies and can be picked up immediately:

- Remove deprecated Card component (0.5 day)
- Update `--text-muted` token value (1 day)
- Add ESLint rule for CSS variable enforcement (1 day)
- Add chart color tokens to design-language (1 day)
- Reduce Duplicate pagination — export single component (1 day)

Total quick-win effort: ~4.5 days for 5 items, all P0/P1 impact.
