# SalesOS Design Audit

> Audit date: 2026-07-15
> Scope: `@salesos/design-language`, `@salesos/ui`, `@salesos/charts`, `tailwind.config.ts`, `globals.css`, foundation components, sample pages
> Method: Full file read of all design tokens, UI components, CSS, layout, accessibility, and consistency patterns

---

## 1. Design System

### 1.1 Architecture Overview

SalesOS uses a **three-layer design system**:

| Layer | Package | Purpose |
|-------|---------|---------|
| **Tokens** | `@salesos/design-language` (16 source files) | Single source of truth for all visual tokens |
| **Components** | `@salesos/ui` (17 component files) | Radix-based UI primitives |
| **Charts** | `@salesos/charts` (Recharts wrappers) | Data visualization |
| **Tailwind** | `tailwind.config.ts` + `globals.css` | CSS utility layer bridging tokens to Tailwind |
| **Backend** | `backend/design_tokens/__init__.py` | Python mirror of tokens for server-side rendering / CSS variable generation |

**Status**: The design system is well-structured and consistent across all layers. The `design-language` package exports 15 modules covering colors, typography, spacing, elevation, animation, accessibility, layout, components, states, AI tokens, timeline, workspace, search/commands, and UX principles.

### 1.2 Color System

**Brand Palette** (MUHIDE):

| Token | Value | Usage |
|-------|-------|-------|
| `muhide-orange` | `#F57C1E` | Primary brand color, CTAs, active states |
| `muhide-ink` | `#151214` | Darkest neutral, sidebar bg, text on dark |
| `muhide-espresso` | `#403D38` | Secondary dark neutral |
| `muhide-sand` | `#CCC6BA` | Light neutral accent |
| `muhide-paper` | `#FAFAFA` | Lightest neutral, page bg |

**Semantic Color Palettes** (10-step scales, 50-900):

| Palette | Base | Purpose |
|---------|------|---------|
| `primary` (orange) | `#F57C1E` | Primary actions, links, active states |
| `secondary` (neutral) | `#8B8475` | Neutral backgrounds, borders |
| `success` (green) | `#4CAF50` | Positive states, revenue |
| `warning` (amber) | `#FFC107` | Caution states |
| `danger` (red) | `#F44336` | Error, destructive actions |
| `info` (blue) | `#2196F3` | Focus rings, links, timeline |
| `ai` / `copilot` (purple) | `#8B5CF6` | AI-related features |
| `search` / `workspace` / `object` / `signal` / `brand` | orange | Domain-specific semantic aliases |

**Semantic CSS Variables** (light/dark):

```css
:root {
  --text-primary: #26231E;    --bg-primary: #FFFFFF;
  --text-secondary: #706A5D;  --bg-secondary: #F7F6F4;
  --text-muted: #A59E90;      --bg-tertiary: #EDEBE6;
  --text-disabled: #BFB9AD;   --border-default: #D9D5CD;
  --border-active: #F57C1E;   --focus-ring: #2196F3;
  --surface-glass: rgba(255,255,255,0.8);
}
.dark {
  --bg-primary: #151214;      --text-primary: #EDEBE6;
  --bg-secondary: #26231E;    --border-default: #3D3932;
  --focus-ring: #64B5F6;      --surface-glass: rgba(21,18,20,0.8);
}
```

**Dark mode**: Implemented via `class` strategy (`darkMode: "class"` in Tailwind config). Full dark mode variable overrides in `globals.css`. All UI components use CSS variables that adapt to dark mode.

**Chart colors** (backend tokens):

```python
chart_1: "#F57C1E"  # orange
chart_2: "#4CAF50"  # green
chart_3: "#FFC107"  # amber
chart_4: "#F44336"  # red
chart_5: "#8B5CF6"  # purple
chart_6: "#2196F3"  # blue
```

**Gap**: The `@salesos/charts` package uses hardcoded Recharts colors (`#3B82F6`, `#10B981`, etc.) that do **not** match the backend token chart palette. The chart package COLORS array starts with blue-500 (`#3B82F6`) instead of orange (`#F57C1E`).

### 1.3 Typography

**Font Families**:

| Token | Family | Fallback |
|-------|--------|----------|
| `display` | Viga | IBM Plex Sans Arabic, sans-serif |
| `sans` / `ui` | IBM Plex Sans | sans-serif |
| `arabic` | IBM Plex Sans Arabic | sans-serif |
| `mono` | IBM Plex Mono | monospace |

All fonts loaded via `@fontsource` packages (self-hosted, no Google Fonts dependency). Weights: 400, 500, 600, 700 for text families; 400 for mono.

**Type Scale** (8 stops):

| Token | Size | Line Height | Weight |
|-------|------|-------------|--------|
| `xs` | 11px | 1.4 | 400 |
| `sm` | 12px | 1.4 | 400 |
| `base` | 14px | 1.6 | 400 |
| `lg` | 16px | 1.5 | 400 |
| `xl` | 18px | 1.35 | 600 |
| `2xl` | 20px | 1.3 | 600 |
| `3xl` | 24px | 1.2 | 600 |
| `4xl` | 32px | 1.15 | 700 |

**Typography variants** (design-language): `h1`-`h6`, `body`, `body-sm`, `caption`, `label`, `code`, `kbd` — 12 variants with explicit size, lineHeight, weight, and optional letterSpacing.

**RTL font handling**: CSS variables swap font order for `[dir="rtl"]` — Arabic font takes precedence. Headings in RTL use `IBM Plex Sans Arabic` as primary.

### 1.4 Spacing

**Base unit**: 4px

**Scale** (17 stops): 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160, 192, 256px

**Density presets** (4 modes):

| Density | Row | Card | Section | Page | Table | Form | Gutter |
|---------|-----|------|---------|------|-------|------|--------|
| compact | 4px | 6px | 12px | 16px | 4px | 6px | 6px |
| normal | 6px | 12px | 20px | 24px | 6px | 12px | 12px |
| comfortable | 10px | 20px | 32px | 40px | 10px | 20px | 20px |
| spacious | 16px | 32px | 48px | 64px | 16px | 32px | 32px |

**Fixed dimensions**:

| Token | Value |
|-------|-------|
| `sidebar` | 256px |
| `sidebarCollapsed` | 64px |
| `topbar` | 56px |
| `copilot` | 384px |
| `command` | 576px |
| `modalSm` | 400px |
| `modalMd` | 560px |
| `modalLg` | 720px |

### 1.5 Elevation & Shadows

**7-level shadow scale** (`muhide-1` through `muhide-6`, plus none):

| Token | Shadow |
|-------|--------|
| `muhide-1` | `0 1px 2px rgba(21,18,20,0.06)` |
| `muhide-2` | `0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)` |
| `muhide-3` | `0 4px 6px rgba(21,18,20,0.07), 0 2px 4px rgba(21,18,20,0.04)` |
| `muhide-4` | `0 10px 15px rgba(21,18,20,0.08), 0 4px 6px rgba(21,18,20,0.04)` |
| `muhide-5` | `0 20px 25px rgba(21,18,20,0.10), 0 8px 10px rgba(21,18,20,0.05)` |
| `muhide-6` | `0 25px 50px rgba(21,18,20,0.16)` |

All shadows use the MUHIDE ink color (`#151214`) as the base, creating warm-toned shadows rather than pure black.

### 1.6 Border Radius

| Token | Value |
|-------|-------|
| `sm` | 2px |
| `md` | 6px |
| `lg` | 8px |
| `xl` | 12px |
| `2xl` | 16px |
| `full` | 9999px |

### 1.7 Z-Index Layers

| Layer | Value | Usage |
|-------|-------|-------|
| `base` | 0 | Default |
| `dropdown` | 10 | Dropdowns, tooltips |
| `sticky` | 20 | Sticky headers |
| `banner` | 30 | Banners |
| `overlay` | 40 | Backdrops |
| `modal` | 50 | Modals, dialogs |
| `toast` | 60 | Toast notifications |
| `command-palette` | 70 | Command bar |
| `copilot` | 80 | Copilot panel |
| `max` | 9999 | Emergency |

### 1.8 Animation & Motion

**Motion tokens** (4 speeds):

| Token | Duration | Easing |
|-------|----------|--------|
| `fast` | 120ms | ease-out |
| `base` | 200ms | standard (0.2, 0, 0, 1) |
| `slow` | 400ms | standard |
| `xslow` | 600ms | standard |

**16 animation patterns** defined: `fade-in`, `fade-in-up/down/left/right`, `scale-in`, `slide-in-left/right/up/down`, `expand-in`, `stagger`, `pulse`, `skeleton`.

**Reduced motion support**: `REDUCED_MOTION_FALLBACK` maps every animation pattern to a 100ms fade-in or instant display. CSS `@media (prefers-reduced-motion: reduce)` in `globals.css` kills all animations and transitions with `!important`.

### 1.9 Grid System

```typescript
GRID = {
  columns: 12,
  gutter: 16,
  margin: 24,
  maxWidth: 1440,
  widgetMinWidth: 240,
  widgetMaxWidth: 960,
}
```

**Responsive grid columns**:
- `< 640px`: 4 columns
- `640px - 1023px`: 8 columns
- `>= 1024px`: 12 columns

**Widget grid** (CSS in `globals.css`):
- 1 column (mobile)
- 2 columns (`>= 640px`)
- 3 columns (`>= 1024px`)
- 4 columns (`>= 1280px`)

### 1.10 Component Presets

**Card designs** (5 styles): default, elevated, dark, bordered, interactive — each with defined borderRadius, padding, background, shadow, and hoverEffect.

**Table designs** (3 densities): compact (40px rows), default (52px rows), comfortable (64px rows) — with striped, hoverable, stickyHeader, sortable options.

**Sidebar**: 256px expanded / 64px collapsed, dark background (`#151214`), 36px item height, 18px icons.

**Topbar**: 56px height, white background, `#D9D5CD` border, 20px horizontal padding.

### 1.11 UX Principles

10 formalized UX principles documented in `principles.ts`:
1. Everything searchable
2. Everything linkable
3. Everything explainable
4. Everything auditable
5. Everything actionable
6. Everything contextual
7. Everything composable
8. Never show empty pages
9. AI is always available
10. One click to the next action

---

## 2. Component Library Status

### 2.1 `@salesos/ui` — 17 Components

| Component | Radix-based | CVA variants | `forwardRef` | Status |
|-----------|:-----------:|:------------:|:------------:|--------|
| `Button` | No (Slot) | Yes (5 variants, 3 sizes) | Yes | Complete |
| `Card` (+Header/Content/Footer) | No | No | Yes | Complete |
| `Input` (+label/error/icons) | No | No | Yes | Complete |
| `Select` | Yes | No | Yes | Complete |
| `Modal` (+Trigger/Content/Header/Body/Footer) | Yes | No | Yes | Complete |
| `Dropdown` (+Trigger/Content/Item) | Yes | No | Yes | Complete |
| `Tabs` (+List/Tab/Panel) | Yes | No | Yes | Complete |
| `Table` (TanStack) | No | No | No (function) | Complete |
| `Badge` | No | Yes (6 variants) | No | Complete |
| `Avatar` | Yes | No | Yes | Complete |
| `Tooltip` | Yes | No | Yes | Complete |
| `Toast` (+Provider/Viewport/useToast) | Yes | Yes (3 variants) | Yes | Complete |
| `Spinner` | No | No | No | Complete |
| `Kbd` | No | No | No | Complete |
| `Sidebar` | No | No | No (function) | Complete |
| `Layout` (+Header/Sidebar/Content) | No | No | Yes | Complete |

**Utility**: `cn()` — clsx + tailwind-merge

**Architecture**: All components use CSS variables for theming (`var(--bg-primary)`, `var(--text-primary)`, `var(--border-default)`, `var(--muhide-orange)`). Radix primitives used for accessible interactions (Dialog, Select, Tabs, Toast, Tooltip, DropdownMenu, Avatar).

### 2.2 `@salesos/charts` — 4 Components

| Component | Library | Status |
|-----------|---------|--------|
| `BarChart` | Recharts | Complete |
| `LineChart` | Recharts | Complete |
| `PieChart` | Recharts | Complete |
| `MetricCard` | Custom | Complete |

**Issue**: Chart components use hardcoded Tailwind gray classes (`text-gray-700`, `stroke-gray-200`) instead of CSS variables. The `COLORS` array does not align with the backend chart token palette.

### 2.3 Foundation Components (`src/components/foundation/`)

| Component | Status | Notes |
|-----------|--------|-------|
| `AppShell` | Active | Context provider, route announcer, keyboard shortcuts |
| `Card` | **Deprecated** | Marked `@deprecated`, points to `@salesos/ui` |
| `MobileNav` | Active | FAB + slide-in drawer, RTL-aware |
| `ErrorBoundary` | Active | Wraps with `role="alert"` |
| `LanguageSwitcher` | Active | AR/EN toggle with `aria-label` |

### 2.4 Missing Components

| Component | Status | Notes |
|-----------|--------|-------|
| **Checkbox** | Missing | No checkbox component in `@salesos/ui` |
| **Radio** | Missing | No radio component |
| **Switch** | Missing | No switch/toggle component |
| **Textarea** | Missing | No textarea component |
| **Slider** | Missing | No range slider |
| **DatePicker** | Missing | No date picker component |
| **Popover** | Missing | No popover (only Tooltip) |
| **Accordion** | Missing | No collapsible sections |
| **Breadcrumb** | Missing | No breadcrumb component |
| **Pagination** | Missing | Inline pagination in pages (not componentized) |
| **Skeleton** | Inline only | Used in `src/components/skeleton.tsx`, not in `@salesos/ui` |
| **EmptyState** | Inline only | Used in `src/components/guidance/empty-states/`, not in `@salesos/ui` |
| **ErrorFallback** | Inline only | Used in `src/components/foundation/error-boundary.tsx` |

### 2.5 Icon System

- **Library**: `lucide-react` (standard across all 51 files using icons)
- **Sizes**: 16px (sm), 20px (md), 24px (lg), 32px (xl) — defined in backend tokens
- **Usage**: Consistent — all imports from `lucide-react`, no custom SVG icons except sidebar chevron
- **Icon registry in design-language**: 30+ icons referenced by string name in `ai.ts`, `states.ts`, `search-commands.ts`, `timeline.ts`

---

## 3. Accessibility

### 3.1 WCAG Compliance Level

**Target**: WCAG AA
**Current assessment**: Partial AA compliance with strong foundations but inconsistent application.

### 3.2 ARIA Attributes Usage

**Extensive ARIA usage found** across the codebase (100+ instances):

| Pattern | Example | Coverage |
|---------|---------|----------|
| `role="dialog"` | CommandBar, SearchPanel, CopilotPanel, MobileNav, TourOverlay | Good |
| `role="region"` | Widgets (SmartTimeline, SignalsFeed, TaskView, TerritoryView, RecentActivity) | Good |
| `role="list"` / `role="listitem"` | Search results, metrics, navigation | Good |
| `role="option"` | Search results, command bar items | Good |
| `role="alert"` | ErrorBoundary, SearchError, dashboard error boundary | Good |
| `role="status"` | Loading states, skeleton loaders, coach marks | Good |
| `role="searchbox"` | Search inputs | Good |
| `role="switch"` | Settings toggles | Good |
| `role="group"` | Search result groups, command categories | Good |
| `aria-label` | Buttons, navigation, panels, mobile nav, sidebar | Good |
| `aria-live="polite"` | Route announcer, command palette state, list updates | Good |
| `aria-live="assertive"` | Route announcements | Good |
| `aria-atomic="true"` | Live regions | Good |
| `aria-expanded` | Mobile nav FAB, sidebar toggle | Good |
| `aria-modal="true"` | Mobile nav drawer, tour overlay | Good |
| `aria-selected` | Command bar results | Good |

**ARIA label translations**: Arabic labels used in `accessibility.ts` (`ARIAS` object) and throughout components via `useTranslation()`.

### 3.3 Keyboard Navigation

**Global shortcuts** (defined in `accessibility.ts`):

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl+K` | Quick search |
| `Cmd/Ctrl+Shift+K` | Command palette |
| `Cmd/Ctrl+I` | AI Copilot |
| `Cmd/Ctrl+G` | Quick navigate |
| `Cmd/Ctrl+T` | Toggle theme |
| `Cmd/Ctrl+N` | Notifications |
| `Cmd/Ctrl+/` | Help |
| `Cmd/Ctrl+Shift+C` | Create |
| `Cmd/Ctrl+S` | Save |
| `Escape` | Close |

**Navigation keys**: ArrowDown/Up (next/prev item), Enter (select), ArrowRight/Left (expand/collapse).

**Focus management**:
- Global focus ring: `outline: 2px solid var(--focus-ring)` with `outline-offset: 2px` on `*:focus-visible`
- Button focus: `focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--muhide-orange)]`
- Input focus: `focus:ring-2 focus:ring-[var(--muhide-orange)] focus:border-[var(--muhide-orange)]`
- Modal focus trap: Handled by Radix Dialog
- Dropdown focus: Handled by Radix primitives

**Skip navigation**: `main` element has `id="main-content"` and `tabIndex={-1}` for skip-to-content.

### 3.4 Screen Reader Support

- **Route announcer**: `AppShell` includes a `<div aria-live="assertive">` that announces route changes
- **Command palette state**: `<div aria-live="polite">` announces when command palette opens
- **SR-only text**: `className="sr-only"` used for screen reader only content
- **Skeleton loading**: `role="status"` with Arabic loading text
- **Empty states**: `role="status"` with descriptive text
- **All images**: `img, video { max-width: 100%; height: auto }` in globals.css
- **Lazy loading**: `img[loading="lazy"]` support in CSS

### 3.5 Color Contrast

**Light mode**:
- Primary text (`#26231E`) on white (`#FFFFFF`): ratio ~15.4:1 — AAA
- Secondary text (`#706A5D`) on white: ratio ~5.1:1 — AA
- Muted text (`#A59E90`) on white: ratio ~2.9:1 — **Below AA** (4.5:1 required)
- Orange (`#F57C1E`) on white: ratio ~3.1:1 — **Below AA** for text, OK for large text

**Dark mode**:
- Primary text (`#EDEBE6`) on dark (`#151214`): ratio ~13.8:1 — AAA
- Secondary text (`#8B8475`) on dark: ratio ~4.8:1 — AA
- Muted text (`#565147`) on dark: ratio ~3.5:1 — **Below AA**

**Issues**: Muted text colors (`--text-muted`) fail WCAG AA in both modes. The orange brand color fails AA for normal-size text on white.

### 3.6 Reduced Motion Support

**Comprehensive**:
- CSS `@media (prefers-reduced-motion: reduce)` in `globals.css` disables all animations
- `REDUCED_MOTION_FALLBACK` in `animation.ts` provides fallback styles for each animation pattern
- `.animate-pulse`, `.animate-spin`, `.animate-slide-in-left`, `.animate-slide-in-right` explicitly disabled

### 3.7 RTL Support

**Extensive RTL infrastructure** (534 lines in `globals.css`):

- **Direction-aware utilities**: Full set of RTL overrides for `text-left/right`, `left/right`, `ml/mr`, `pl/pr`, `space-x`, `border-l/r`, `rounded-l/r`, `translate-x`, `float`, `divide-x`, `origin`
- **Font stacking**: `[dir="rtl"]` swaps font families to prioritize Arabic
- **Layout**: `MobileNav` uses `start-4`/`end-4` instead of `left-4`/`right-4`; animation direction adapts to RTL
- **Dashboard layout**: Uses `border-e` (logical property) instead of `border-r`
- **All CSS variables**: Adapt to dark mode but not direction-specific (handled by utility overrides)

---

## 4. Responsive Behavior

### 4.1 Breakpoint Strategy

**6 breakpoints** defined in `layout.ts`:

| Name | Width | Tailwind equivalent |
|------|-------|---------------------|
| `xs` | 480px | (custom, below sm) |
| `sm` | 640px | `sm:` |
| `md` | 768px | `md:` |
| `lg` | 1024px | `lg:` |
| `xl` | 1280px | `xl:` |
| `2xl` | 1536px | `2xl:` |

**Zone visibility by breakpoint**:

| Zone | xs | sm | md+ |
|------|----|----|-----|
| Sidebar | Hidden | Hidden | Visible |
| Copilot | Hidden | Hidden | Visible |
| Panel | Hidden | Hidden | Visible |
| Timeline | Hidden | Visible | Visible |
| Content | Always | Always | Always |

### 4.2 Mobile Navigation

**FAB + Drawer pattern**:
- Fixed bottom-right FAB (48px, orange, `z-30`) — only on `md:hidden`
- Slide-in drawer (288px, max 80vw) with backdrop blur
- Escape key closes, click outside closes
- Route change auto-closes
- RTL-aware slide direction
- `aria-modal="true"`, `role="dialog"`, proper `aria-label`

**Mobile topbar**: Hamburger button visible only on `md:hidden`, with 44px minimum touch target.

### 4.3 Grid System

- Widget grid: CSS Grid with responsive column count (1→2→3→4)
- Content area: `flex-1 overflow-auto` with responsive padding (`p-3 sm:p-4 lg:p-6`)
- Dashboard metrics: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6`
- Search facets: `grid-cols-2 sm:grid-cols-4`

### 4.4 Touch Support

- **Touch targets**: Minimum 44px x 44px on interactive elements (buttons, FAB)
- **Touch action**: `touch-action: manipulation` on all interactive elements (disables double-tap zoom)
- **Pull-to-refresh**: `.pull-to-refresh { overscroll-behavior-y: contain }` on mobile
- **Swipe**: Toast swipe gestures via Radix Toast (`data-[swipe]` attributes)
- **Modal**: Full-screen on mobile (`max-width: 100%; height: 100%; border-radius: 0`)

### 4.5 Responsive Tables

CSS `responsive-card` pattern in `globals.css`:
- Below 640px: tables display as block cards
- `<thead>` hidden
- `<tr>` becomes bordered card with padding
- `<td>` becomes flex row with `justify-content: space-between`
- `data-label` attribute used for column headers via `::before` pseudo-element

### 4.6 Responsive Padding Utilities

Custom utility classes for mobile:
- `.responsive-pad` → 8px padding
- `.responsive-pad-x` / `.responsive-pad-y` → directional 8px
- `.responsive-gap` → 8px gap
- `.responsive-mt` / `.responsive-mb` → 8px margin
- `.responsive-space-y` → 8px between children
- Heading sizes reduced on mobile (`h1: 18px`, `h2: 16px`)

---

## 5. Consistency Problems

### 5.1 Duplicate Card Components

**Two Card implementations exist**:

1. `@salesos/ui/card.tsx` — The canonical implementation (`Card`, `CardHeader`, `CardContent`, `CardFooter`)
2. `src/components/foundation/card.tsx` — **Deprecated** but still present, with different API (`variant`, `padding`, `accent` props)

The deprecated Card uses `rounded-lg` while the canonical uses `rounded-xl`. Different padding defaults. Some pages may still import the deprecated version.

### 5.2 Mixed Styling Approaches

**Three styling patterns coexist**:

1. **CSS variables** (`var(--bg-primary)`, `var(--text-primary)`) — Used in `@salesos/ui` components and foundation components
2. **Tailwind utility classes** (`text-neutral-900`, `bg-white`, `dark:bg-neutral-800`) — Used extensively in page files (companies page, search page, settings page, etc.)
3. **Hybrid** — Some components mix both: `bg-[var(--bg-primary)]` alongside `dark:text-neutral-100`

**Impact**: Pages using Tailwind gray/neutral classes (e.g., `text-neutral-900`) won't automatically adapt if CSS variable values change. The `@salesos/ui` components are themable via CSS variables, but page-level code bypasses this.

### 5.3 Login Page Uses Raw HTML Inputs

`src/app/(auth)/login/page.tsx` uses plain `<input>` and `<button>` elements with inline Tailwind classes instead of `@salesos/ui` `Input` and `Button` components. It references `var(--background)`, `var(--card)`, `var(--border)`, `var(--muted-foreground)` — CSS variables that don't exist in `globals.css` (these appear to be shadcn/ui variable names, not MUHIDE variables).

### 5.4 Search Page Uses Raw Button

`src/app/(dashboard)/search/page.tsx` line 57-63 uses a raw `<button>` with inline classes instead of the `Button` component from `@salesos/ui`. The pagination buttons (lines 156-173) also use raw `<button>` elements.

### 5.5 Chart Colors Mismatch

`@salesos/charts` `COLORS` array:
```typescript
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316']
```

Backend token chart colors:
```python
chart_1: "#F57C1E"  # orange (brand)
chart_2: "#4CAF50"  # green
chart_3: "#FFC107"  # amber
chart_4: "#F44336"  # red
chart_5: "#8B5CF6"  # purple
chart_6: "#2196F3"  # blue
```

Charts start with blue (`#3B82F6`) instead of the brand orange (`#F57C1E`). The palette order and specific colors differ.

### 5.6 Chart Components Use Hardcoded Gray Classes

`@salesos/charts` uses `text-gray-700`, `stroke-gray-200`, `text-gray-500`, `dark:text-gray-300`, `dark:stroke-gray-700` — Tailwind's default gray scale rather than the MUHIDE neutral palette. The `MetricCard` uses `bg-white dark:bg-gray-900` instead of `bg-[var(--bg-primary)]`.

### 5.7 Badge "primary" Variant Maps to Info

In `badge.tsx`, the `primary` variant maps to `bg-info-100 text-info-800` (blue), not the orange brand primary. The `default` variant uses orange. This is semantically confusing — `primary` sounds like it should be the brand color.

### 5.8 Inconsistent Empty State Patterns

Empty states are defined in two places:
1. `design-language/src/states.ts` — Canonical definitions with Arabic text, icons, actions
2. `src/components/guidance/empty-states/` — React components (EmptyWorkflows, EmptyRAG, EmptyPipeline, etc.)

The React components don't consume the design-language token definitions. Each empty state component has its own inline styling and icon choice.

### 5.9 No Pagination Component

Pagination is implemented inline in at least 2 pages (companies, search) with different approaches:
- Companies page: `Button` components with chevron icons
- Search page: Raw `<button>` elements with border styling

### 5.10 Foundation Components Not in UI Package

Several production components live outside `@salesos/ui`:
- `Skeleton` → `src/components/skeleton.tsx`
- `ErrorFallback` → `src/components/foundation/error-boundary.tsx`
- `EmptyState` → `src/components/guidance/empty-states/EmptyState.tsx`
- `CoachMark` → `src/components/guidance/coach-mark/`
- `TourOverlay` → `src/components/guidance/tour/`

These should ideally be in `@salesos/ui` or a separate `@salesos/guidance` package.

### 5.11 Design-Language Type Class Function Has Unused Parameter

`typography.ts:34`: `typeClass(variant, _isRTL)` — the `_isRTL` parameter is declared but never used. The function generates classes without considering RTL.

### 5.12 Semantic Color Duplication

Multiple semantic color names map to the same palette:
- `primary` = `search` = `workspace` = `object` = `signal` = `brand` (all orange)
- `ai` = `copilot` (both purple)
- `timeline` = `link` (both blue)
- `command` = `secondary` = `neutral` (all neutral)

While this provides semantic clarity, 6 identical palettes create maintenance overhead.

---

## 6. Summary Scorecard

| Area | Score | Notes |
|------|-------|-------|
| **Token System** | 9/10 | Comprehensive, well-structured, multi-layer. Minor chart color mismatch. |
| **Component Library** | 7/10 | 17 solid components. Missing checkbox, radio, switch, textarea, datepicker, skeleton. |
| **Dark Mode** | 9/10 | Full CSS variable support, class-based toggle, consistent across components. |
| **RTL Support** | 9/10 | Extensive utility overrides, font stacking, logical properties, animation direction. |
| **Accessibility (ARIA)** | 8/10 | Strong foundations, route announcer, live regions. Some gaps in muted text contrast. |
| **Accessibility (Keyboard)** | 8/10 | Global shortcuts, focus rings, Radix focus traps. Some raw buttons lack focus styles. |
| **Accessibility (Contrast)** | 6/10 | Muted text fails AA. Orange on white fails AA for normal text. |
| **Responsive Design** | 8/10 | Mobile nav, responsive grid, touch targets, table-to-card. Minor inconsistencies. |
| **Consistency** | 6/10 | Duplicate Card, mixed styling approaches, raw HTML in auth pages, chart color drift. |
| **Icon System** | 9/10 | Consistent lucide-react usage, defined sizes, no custom SVGs. |
| **Chart System** | 6/10 | Functional but uses wrong color palette and hardcoded gray classes. |
| **Documentation** | 7/10 | README files exist, token docs in design-language. Missing visual spec / Figma link. |

**Overall Design System Maturity**: **7.5/10** — Strong token foundation and component library with known consistency gaps that should be addressed before GA.

---

## 7. Recommendations

### P0 (Pre-GA)

1. **Fix chart color palette** — Align `@salesos/charts` COLORS with backend tokens
2. **Migrate login page** to `@salesos/ui` components with correct CSS variables
3. **Fix muted text contrast** — Increase `--text-muted` lightness or use for large text only
4. **Remove deprecated Card** — Complete migration to `@salesos/ui/Card`

### P1 (Post-GA)

5. **Add missing form components** — Checkbox, Radio, Switch, Textarea, DatePicker
6. **Standardize page styling** — Migrate all pages to CSS variable pattern (replace `text-neutral-900` with `text-[var(--text-primary)]`)
7. **Componentize pagination** — Create shared `Pagination` component in `@salesos/ui`
8. **Move guidance components** to `@salesos/ui` or `@salesos/guidance` package
9. **Connect empty states** to design-language token definitions
10. **Fix Badge `primary` variant** — Map to orange, not info blue

### P2 (Future)

11. **Add Storybook** for visual component documentation
12. **Add Figma integration** or design tool export (none found)
13. **Automated contrast checking** in CI
14. **Design-language `typeClass` function** — Remove unused `_isRTL` param or implement RTL logic
