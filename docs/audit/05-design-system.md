# SalesOS Design System Reverse-Engineering Audit

> **Audit date:** 2026-07-13  
> **Auditor:** Design System Architect (read-only)  
> **Scope:** Full design system across design-language, ui, icons, foundation components, tailwind config, globals.css, renderer, WidgetTemplate, and backend design_tokens  

---

## Table of Contents

1. [Design Token Catalog](#1-design-token-catalog)
2. [Typography System](#2-typography-system)
3. [Spacing & Layout System](#3-spacing--layout-system)
4. [Complete Component Library Inventory](#4-complete-component-library-inventory)
5. [Component API Contracts & Props](#5-component-api-contracts--props)
6. [RTL Architecture & Implementation Quality](#6-rtl-architecture--implementation-quality)
7. [Dark Mode / Theme System](#7-dark-mode--theme-system)
8. [Responsive Rules & Breakpoints](#8-responsive-rules--breakpoints)
9. [Interaction Patterns](#9-interaction-patterns)
10. [Design Consistency Score](#10-design-consistency-score)
11. [Design Debt Register](#11-design-debt-register)
12. [Widget SDK Design Analysis](#12-widget-sdk-design-analysis)

---

## 1. Design Token Catalog

### 1.1 Brand Colors

| Token | Hex | Source | Purpose |
|-------|-----|--------|---------|
| `--muhide-orange` | `#F57C1E` | globals.css:20 | Primary brand color, CTA buttons, focus rings, active states |
| `--muhide-ink` | `#151214` | globals.css:21 | Dark background (sidebar, tooltips), shadow multiplier |
| `--muhide-espresso` | `#403D38` | globals.css:22 | Secondary dark tone, mid-weight accents |
| `--muhide-sand` | `#CCC6BA` | globals.css:23 | Warm taupe, decorative elements |
| `--muhide-paper` | `#FAFAFA` | globals.css:24 | Near-white background surfaces |

### 1.2 Orange Scale (9-step) — Primary

| Step | Hex | Source | Design-language Token |
|------|-----|--------|----------------------|
| 50 | `#FFF3E6` | globals.css:26 | `COLORS.primary[50]` |
| 100 | `#FFE2BF` | globals.css:27 | `COLORS.primary[100]` |
| 200 | `#FFCE99` | globals.css:28 | `COLORS.primary[200]` |
| 300 | `#FFB870` | globals.css:29 | `COLORS.primary[300]` |
| 400 | `#FFA04A` | globals.css:30 | `COLORS.primary[400]` |
| 500 | `#F57C1E` | globals.css:31 | `COLORS.primary[500]` |
| 600 | `#D4660F` | globals.css:32 | `COLORS.primary[600]` |
| 700 | `#B35009` | globals.css:33 | `COLORS.primary[700]` |
| 800 | `#8F3C06` | globals.css:34 | `COLORS.primary[800]` |
| 900 | `#6E2A03` | globals.css:35 | `COLORS.primary[900]` |

### 1.3 Warm Neutral Scale (10-step)

| Step | Hex | Source | Design-language Token |
|------|-----|--------|----------------------|
| 50 | `#F7F6F4` | globals.css:37 | `COLORS.neutral[50]` / `COLORS.secondary[50]` |
| 100 | `#EDEBE6` | globals.css:38 | `COLORS.neutral[100]` |
| 200 | `#D9D5CD` | globals.css:39 | `COLORS.neutral[200]` |
| 300 | `#BFB9AD` | globals.css:40 | `COLORS.neutral[300]` |
| 400 | `#A59E90` | globals.css:41 | `COLORS.neutral[400]` |
| 500 | `#8B8475` | globals.css:42 | `COLORS.neutral[500]` |
| 600 | `#706A5D` | globals.css:43 | `COLORS.neutral[600]` / `COLORS.secondary[600]` |
| 700 | `#565147` | globals.css:44 | `COLORS.neutral[700]` |
| 800 | `#3D3932` | globals.css:45 | `COLORS.neutral[800]` |
| 900 | `#26231E` | globals.css:46 | `COLORS.neutral[900]` |

### 1.4 Functional Colors (10-step each)

#### Success (Green)

| Step | Hex | Design-language Token |
|------|-----|----------------------|
| 50 | `#E8F5E9` | `COLORS.success[50]` |
| 100 | `#C8E6C9` | `COLORS.success[100]` |
| 200 | `#A5D6A7` | `COLORS.success[200]` |
| 300 | `#81C784` | `COLORS.success[300]` |
| 400 | `#66BB6A` | `COLORS.success[400]` |
| 500 | `#4CAF50` | `COLORS.success[500]` |
| 600 | `#388E3C` | `COLORS.success[600]` — used for success badges, active status |
| 700 | `#2E7D32` | `COLORS.success[700]` |
| 800 | `#1B5E20` | `COLORS.success[800]` |
| 900 | `#0D3B0F` | `COLORS.success[900]` |

#### Warning (Amber)

| Step | Hex | Design-language Token |
|------|-----|----------------------|
| 50 | `#FFF8E1` | `COLORS.warning[50]` |
| 500 | `#FFC107` | `COLORS.warning[500]` — pending status |
| 600 | `#FFB300` | `COLORS.warning[600]` — warning badges |
| 700 | `#FFA000` | `COLORS.warning[700]` |
| 800 | `#FF8F00` | `COLORS.warning[800]` |
| 900 | `#E65100` | `COLORS.warning[900]` |

#### Danger (Red)

| Step | Hex | Design-language Token |
|------|-----|----------------------|
| 50 | `#FFEBEE` | `COLORS.danger[50]` |
| 500 | `#F44336` | `COLORS.danger[500]` |
| 600 | `#E53935` | `COLORS.danger[600]` — error states, delete actions |
| 700 | `#D32F2F` | `COLORS.danger[700]` |
| 900 | `#B71C1C` | `COLORS.danger[900]` |

#### Info (Blue)

| Step | Hex | Design-language Token |
|------|-----|----------------------|
| 50 | `#E3F2FD` | `COLORS.info[50]` |
| 500 | `#2196F3` | `COLORS.info[500]` |
| 600 | `#1E88E5` | `COLORS.info[600]` — info badges |
| 700 | `#1976D2` | `COLORS.info[700]` |
| 900 | `#0D47A1` | `COLORS.info[900]` |

### 1.5 Semantic Domain-Specific Colors

The design-language has 18 color palettes for domain-specific usage (color.ts:18-132):

| Semantic Color | Scale Base | Primary Use |
|---------------|-----------|-------------|
| `ai` | Purple (`#F5F3FF` → `#4C1D95`) | AI features, purple badges |
| `search` | Orange (identical to primary) | Search UI elements |
| `command` | Neutral warm | Command palette UI |
| `workspace` | Orange (identical to primary) | Workspace chrome |
| `object` | Orange (identical to primary) | Entity objects |
| `timeline` | Blue (`#E3F2FD` → `#0D47A1`) | Timeline events |
| `signal` | Orange (identical to primary) | Signal cards/indicators |
| `revenue` | Green (`#E8F5E9` → `#0D3B0F`) | Revenue metrics |
| `copilot` | Purple (identical to ai) | Copilot panel |
| `link` | Blue (`#E3F2FD` → `#0D47A1`) | Inline links |
| `brand` | Orange (identical to primary) | Brand elements |

**Issue:** 5 of 11 semantic colors (`search`, `workspace`, `object`, `signal`, `brand`) are identical copies of the primary orange scale. This adds no differentiation value.

### 1.6 Semantic Tokens (CSS Custom Properties)

| Token | Light Value | Dark Value | globals.css |
|-------|------------|------------|-------------|
| `--text-primary` | `#26231E` | `#EDEBE6` | :48, :81 |
| `--text-secondary` | `#706A5D` | `#A59E90` | :49, :82 |
| `--text-muted` | `#A59E90` | `#706A5D` | :50, :83 |
| `--text-disabled` | `#BFB9AD` | `#565147` | :51, :84 |
| `--bg-primary` | `#FFFFFF` | `#151214` | :52, :85 |
| `--bg-secondary` | `#F7F6F4` | `#26231E` | :53, :86 |
| `--bg-tertiary` | `#EDEBE6` | `#3D3932` | :54, :87 |
| `--border-default` | `#D9D5CD` | `#3D3932` | :55, :88 |
| `--border-hover` | `#BFB9AD` | `#565147` | :56, :89 |
| `--border-active` | `#F57C1E` | `#F57C1E` | :57, :90 |
| `--border-disabled` | `#EDEBE6` | `#26231E` | :58, :91 |

**Note:** `--border-active` is constant across light/dark (orange always stands out).

### 1.7 Shadows (Elevation Levels)

| Level | CSS Value | Tailwind Class | Usage |
|-------|----------|----------------|-------|
| 1 | `0 1px 2px rgba(21,18,20,0.06)` | `shadow-muhide-1` | Card default, inputs |
| 2 | `0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)` | `shadow-muhide-2` | Hover cards, tooltips |
| 3 | `0 4px 6px rgba(21,18,20,0.07), 0 2px 4px rgba(21,18,20,0.04)` | `shadow-muhide-3` | Elevated cards |
| 4 | `0 10px 15px rgba(21,18,20,0.08), 0 4px 6px rgba(21,18,20,0.04)` | `shadow-muhide-4` | Dropdowns, modals, toasts |
| 5 | `0 20px 25px rgba(21,18,20,0.10), 0 8px 10px rgba(21,18,20,0.05)` | `shadow-muhide-5` | Command bar |
| 6 | `0 25px 50px rgba(21,18,20,0.16)` | `shadow-muhide-6` | Command bar backdrop, full-screen overlays |

Shadow color: Always `#151214` (muhide-ink), not generic black.

### 1.8 Border Radii

| Token | Value | Tailwind Class | Usage |
|-------|-------|----------------|-------|
| `--radius-sm` | `2px` | `rounded-sm` | Inline KBD, small chips |
| `--radius-md` | `6px` | `rounded-md` | Buttons, inputs, badges |
| `--radius-lg` | `8px` | `rounded-lg` | Cards, dropdowns, sidebar items |
| `--radius-xl` | `12px` | `rounded-xl` | Modals, cards |
| `--radius-2xl` | `16px` | `rounded-2xl` | Large containers |
| `--radius-full` | `9999px` | `rounded-full` | Avatars, badge pills, notification dots |

### 1.9 Z-Index Scale

| Layer | Value | Tailwind Variable | Usage |
|-------|-------|-------------------|-------|
| base | 0 | — | Default stacking |
| dropdown | 10 | `z-dropdown` | Dropdowns, select popups, tooltips |
| sticky | 20 | `z-sticky` | Sticky headers, topbar |
| banner | 30 | `z-banner` | Banners, notification bars |
| overlay | 40 | `z-overlay` | Backdrop overlays, command bar backdrop |
| modal | 50 | `z-modal` | Modal dialogs |
| toast | 60 | `z-toast` | Toast notifications (100px for viewport) |
| command-palette | 70 | — (design-language only) | Command palette in design-language |
| copilot | 80 | — (design-language only) | Copilot panel in design-language |
| max | 9999 | — (design-language only) | Maximum override |

**Gap:** The design-language `elevation.ts:35-46` defines `command-palette: 70`, `copilot: 80`, and `max: 9999` but these are not in `globals.css` or `tailwind.config.ts`. Only `dropdown` through `toast` (10-60) exist in both worlds.

### 1.10 Motion / Easing

| Token | Value | Design-language Source |
|-------|-------|----------------------|
| `ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | motion.ts:12 |
| `ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | motion.ts:13 |
| `ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | motion.ts:14 |
| `duration-fast` | `120ms` | motion.ts:18 |
| `duration-base` | `200ms` | motion.ts:19 |
| `duration-slow` | `400ms` | motion.ts:20 |
| `duration-xslow` | `600ms` | motion.ts:21 |

**Note:** These easing/duration tokens are NOT defined as CSS custom properties in `globals.css`, though they are referenced in foundation components (e.g., sidebar uses `ease-standard` in sidebar.tsx:32).

### 1.11 Shadow Token Naming Inconsistency

| Location | Name |
|----------|------|
| tailwind.config.ts | `shadow-muhide-1` through `shadow-muhide-6` |
| globals.css | Tokens listed in DESIGN_TOKEN_MAPPING.md but NOT as `--shadow-X` CSS variables |
| design-language elevation.ts | `shadowCSS(level)` function generates values |
| foundation components | References `shadow-[var(--shadow-card)]` (surface.tsx:17) — **undefined variable** |

**Critical gap:** `globals.css` does not export `--shadow-1` through `--shadow-6` as CSS custom properties. The shadows are only available via Tailwind classes (`shadow-muhide-1` etc.) or the design-language TS module.

---

## 2. Typography System

### 2.1 Font Families

| Family | CSS Variable | Font Names | globals.css Line |
|--------|-------------|-----------|-----------------|
| Display | `--font-display` | `'Viga', 'IBM Plex Sans Arabic', sans-serif` | :60, tailwind:53 |
| UI (LTR) | `--font-ui` | `'IBM Plex Sans', sans-serif` | :61, tailwind:54 |
| UI (RTL) | `--font-ui-arabic` | `'IBM Plex Sans Arabic', sans-serif` | :62, tailwind:55 |
| Mono | `--font-mono` | `'IBM Plex Mono', monospace` | :63, tailwind:56 |

**Font sources** (`@fontsource` npm packages, globals.css:5-16):
- `@fontsource/viga` — weight 400
- `@fontsource/ibm-plex-sans` — weights 400, 500, 600, 700
- `@fontsource/ibm-plex-sans-arabic` — weights 400, 500, 600, 700
- `@fontsource/ibm-plex-mono` — weights 400, 500, 600

**Design-language FONT_FAMILY (typography.ts:27-32)** uses slightly different values:
```
display: "'Viga', 'IBM Plex Sans Arabic', sans-serif"
english: "'IBM Plex Sans', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif"  ← has system fallbacks
arabic: "'IBM Plex Sans Arabic', sans-serif"
mono: "'IBM Plex Mono', 'SF Mono', monospace"  ← has SF Mono fallback
```

### 2.2 Font Sizes (px → Tailwind)

| Token | px | Tailwind Class | Line-height | Design-language TYPOGRAPHY |
|-------|-----|---------------|-------------|---------------------------|
| xs | 11px | `text-xs` | 1.4 | — (not in TYPOGRAPHY object) |
| sm | 12px | `text-sm` | 1.4 | caption (12px), label (12px) |
| base | 14px | `text-base` | 1.6 | body (14px), h6 (14px), body-sm (13px) |
| lg | 16px | `text-lg` | 1.5 | h5 (16px) |
| xl | 18px | `text-xl` | 1.35 | h4 (18px) |
| 2xl | 20px | `text-2xl` | 1.3 | h3 (20px) |
| 3xl | 24px | `text-3xl` | 1.2 | h2 (24px) |
| 4xl | 32px | `text-4xl` | 1.15 | h1 (32px) |

**Design-language TYPOGRAPHY variants** (typography.ts:12-25):
| Variant | Size | Weight | Line-height | Letter-spacing |
|---------|------|--------|-------------|---------------|
| h1 | 32px | 700 | 1.15 | — |
| h2 | 24px | 600 | 1.2 | — |
| h3 | 20px | 600 | 1.3 | — |
| h4 | 18px | 600 | 1.35 | — |
| h5 | 16px | 600 | 1.4 | — |
| h6 | 14px | 600 | 1.4 | — |
| body | 14px | 400 | 1.6 | — |
| body-sm | 13px | 400 | 1.5 | — |
| caption | 12px | 400 | 1.4 | 0.2 |
| label | 12px | 500 | 1.3 | 0.3 |
| code | 13px | 400 | 1.6 | — |
| kbd | 11px | 500 | 1.3 | — |

**Note:** `body-sm` (13px) has no corresponding Tailwind font size token — `text-sm` is 12px and `text-base` is 14px. This creates a gap in the Tailwind ↔ design-language mapping.

### 2.3 Font Weights

| Weight | Value | Tailwind Class |
|--------|-------|----------------|
| Regular | 400 | `font-normal` |
| Medium | 500 | `font-medium` |
| Semibold | 600 | `font-semibold` |
| Bold | 700 | `font-bold` |

### 2.4 Font Application Rules (globals.css:95-132)

```
body → font-ui (IBM Plex Sans) + font-ui-arabic fallback
h1-h6 → font-display (Viga) + font-ui-arabic fallback
code, pre, kbd → font-mono (IBM Plex Mono)
[dir="rtl"] body → font-ui-arabic first, font-ui fallback
[dir="rtl"] h1-h6 → font-ui-arabic first, font-display fallback
```

---

## 3. Spacing & Layout System

### 3.1 Base Grid Unit

**4px base unit** (spacing.ts). All spacing values are multiples of 4px.

### 3.2 Spacing Scale (spacing.ts:15-33)

| Key | Value | Tailwind Equivalent |
|-----|-------|-------------------|
| 0 | 0px | `gap-0` |
| 1 | 4px | `gap-1` |
| 2 | 8px | `gap-2` |
| 3 | 12px | `gap-3` |
| 4 | 16px | `gap-4` |
| 5 | 20px | `gap-5` |
| 6 | 24px | `gap-6` |
| 8 | 32px | `gap-8` |
| 10 | 40px | `gap-10` |
| 12 | 48px | `gap-12` |
| 16 | 64px | `gap-16` |
| 20 | 80px | `gap-20` |
| 24 | 96px | `gap-24` |
| 32 | 128px | `gap-32` |
| 40 | 160px | `gap-40` |
| 48 | 192px | `gap-48` |
| 64 | 256px | `gap-64` |

### 3.3 Density Presets (spacing.ts:35-48)

| Density | Row | Card | Section | Page | Table | Form | Gutter |
|---------|-----|------|---------|------|-------|------|--------|
| compact | 4px | 6px | 12px | 16px | 4px | 6px | 6px |
| normal | 6px | 12px | 20px | 24px | 6px | 12px | 12px |
| comfortable | 10px | 20px | 32px | 40px | 10px | 20px | 20px |
| spacious | 16px | 32px | 48px | 64px | 16px | 32px | 32px |

**Issue:** These density presets are defined only in `design-language/spacing.ts`. They are not used anywhere in the foundation components. No component consumes `DENSITY` to adjust its internal spacing.

### 3.4 Fixed Layout Constants

| Constant | Value | Source |
|----------|-------|--------|
| sidebar | 256px | `FIXED.sidebar`, `SIDEBAR_WIDTH` in layout.ts |
| sidebar-collapsed | 64px | `FIXED.sidebarCollapsed`, `SIDEBAR_COLLAPSED` |
| topbar | 56px | `FIXED.topbar`, `TOPBAR_HEIGHT` |
| copilot | 384px | `FIXED.copilot` |
| command | 576px | `FIXED.command` |
| modal-sm | 400px | `FIXED.modalSm` |
| modal-md | 560px | `FIXED.modalMd` |
| modal-lg | 720px | `FIXED.modalLg` |

**Tailwind config coverage:** Only `sidebar`, `sidebar-collapsed`, `topbar`, `copilot`, `command` are in tailwind.config.ts spacing. Modal sizes are missing from Tailwind.

### 3.5 Component-Specific Spacing Tokens (components.ts)

| Component | Token | Value | Source |
|-----------|-------|-------|--------|
| Sidebar | itemHeight | 36px | components.ts:44 |
| Sidebar | iconSize | 18px | components.ts:45 |
| Sidebar | padding | 12px | components.ts:46 |
| Topbar | paddingX | 20px | components.ts:52 |
| Command Bar | maxHeight | 480px | components.ts:57 |
| Command Bar | borderRadius | 12px | components.ts:58 |
| Copilot | collapsedWidth | 48px | components.ts:63 |
| Card (default) | padding | 16px | components.ts:13 |
| Card (elevated) | padding | 20px | components.ts:14 |
| Card (all) | borderRadius | 8px | components.ts:13-17 |
| Table (compact) | rowHeight | 40px | components.ts:31 |
| Table (default) | rowHeight | 52px | components.ts:32 |
| Table (comfortable) | rowHeight | 64px | components.ts:33 |

### 3.6 Breakpoints (layout.ts:7-14)

| Token | Width | Tailwind Variant |
|-------|-------|-----------------|
| xs | 480px | `xs:` (custom) |
| sm | 640px | `sm:` |
| md | 768px | `md:` |
| lg | 1024px | `lg:` |
| xl | 1280px | `xl:` |
| 2xl | 1536px | `2xl:` |

### 3.7 Grid System (layout.ts:39-46)

| Property | Value |
|----------|-------|
| columns | 12 |
| gutter | 16px |
| margin | 24px |
| maxWidth | 1440px |
| widgetMinWidth | 240px |
| widgetMaxWidth | 960px |

Column function: 4 cols (<640px), 8 cols (<1024px), 12 cols (≥1024px).

---

## 4. Complete Component Library Inventory

### 4.1 @salesos/ui (17 files, 16 components + 1 utility)

| # | Component | File | Dependencies |
|---|-----------|------|-------------|
| 1 | Button | `button.tsx` | `@radix-ui/react-slot`, `class-variance-authority`, Spinner |
| 2 | Card | `card.tsx` | None (pure Tailwind) |
| 3 | Modal | `modal.tsx` | `@radix-ui/react-dialog`, lucide `X` |
| 4 | Dropdown | `dropdown.tsx` | `@radix-ui/react-dropdown-menu` |
| 5 | Input | `input.tsx` | None (pure HTML + Tailwind) |
| 6 | Select | `select.tsx` | `@radix-ui/react-select`, lucide `ChevronDown` |
| 7 | Table | `table.tsx` | `@tanstack/react-table`, lucide `Loader2` |
| 8 | Tabs | `tabs.tsx` | `@radix-ui/react-tabs` |
| 9 | Sidebar | `sidebar.tsx` | None (pure HTML + Tailwind) |
| 10 | Layout | `layout.tsx` | None |
| 11 | Badge | `badge.tsx` | `class-variance-authority` |
| 12 | Avatar | `avatar.tsx` | `@radix-ui/react-avatar` |
| 13 | Tooltip | `tooltip.tsx` | `@radix-ui/react-tooltip` |
| 14 | Toast | `toast.tsx` | `@radix-ui/react-toast`, `class-variance-authority`, lucide `X` |
| 15 | Spinner | `spinner.tsx` | lucide `Loader2` |
| 16 | Kbd | `kbd.tsx` | None |
| 17 | cn | `utils.ts` | `clsx`, `tailwind-merge` |

### 4.2 Foundation Components (22 files in `src/components/foundation/`)

| # | Component | File | Wraps/Depends On |
|---|-----------|------|-----------------|
| 1 | AppShell | `app-shell.tsx` | Context provider, keyboard shortcuts |
| 2 | Sidebar | `sidebar.tsx` | AppShell context |
| 3 | Header | `header.tsx` | AppShell context |
| 4 | Navigation | `navigation.tsx` | None |
| 5 | WorkspaceLayout | `workspace-layout.tsx` | None |
| 6 | PageLayout | `page-layout.tsx` | None |
| 7 | CommandBar | `command-bar.tsx` | Keyboard navigation, focus management |
| 8 | Typography | `typography.tsx` | `@salesos/design-language` TYPOGRAPHY |
| 9 | Surface | `surface.tsx` | None (references `--surface-*` CSS vars) |
| 10 | Stack | `stack.tsx` | None (flexbox layout) |
| 11 | Grid | `grid.tsx` | None (CSS grid) |
| 12 | Container | `container.tsx` | None |
| 13 | Section | `section.tsx` | Typography, Divider, Stack |
| 14 | Divider | `divider.tsx` | None |
| 15 | Icon | `icon.tsx` | None |
| 16 | Card | `card.tsx` | None (different from @salesos/ui Card) |
| 17 | Badge | `badge.tsx` | None (different from @salesos/ui Badge) |
| 18 | Metric | `metric.tsx` | Typography |
| 19 | Skeleton | `skeleton.tsx` | None |
| 20 | Loading | `loading.tsx` | None |
| 21 | EmptyState | `empty-state.tsx` | None |
| 22 | ErrorBoundary | `error-boundary.tsx` | `useTranslation` (i18n) |
| — | LanguageSwitcher | `LanguageSwitcher.tsx` | `useTranslation` (i18n) |
| — | MobileNav | `MobileNav.tsx` | Next.js Link, lucide icons |

**DUPLICATE COMPONENTS:** Two conflicting implementations exist for Card, Badge, and Sidebar:
- `@salesos/ui` Card/Badge/Sidebar: Simple primitives
- Foundation Card/Badge/Sidebar: Richer feature set with accent colors, domain-specific variants, section-based layout

### 4.3 @salesos/icons

Re-exports 100+ lucide-react icons plus `iconSizeMap`:
- Sizes: sm=14px, md=18px, lg=22px, xl=28px

### 4.4 @salesos/renderer (6 files)

| # | Component | File | Purpose |
|---|-----------|------|---------|
| 1 | SchemaRenderer | `schema-renderer.tsx` | Top-level UISchema → ViewerRenderer |
| 2 | ViewerRenderer | `viewer-renderer.tsx` | Entity viewer with tabs, actions |
| 3 | TabRenderer | `tab-renderer.tsx` | Tab → sections + widgets |
| 4 | SectionRenderer | `section-renderer.tsx` | Section → nodes + widgets |
| 5 | WidgetRenderer | `widget-renderer.tsx` | Widget shell with loading/error states |
| 6 | Types | `types.ts` | UISchema, UISchemaTab, UISchemaSection, UIWidget, UISchemaNode, UIAction |

### 4.5 @salesos/config

Simple constants: `API_BASE_URL`, `DEFAULT_PAGE_SIZE=20`, `SEARCH_DEBOUNCE_MS=400`, `STALE_TIME_MS=10000`, `RETRY_COUNT=1`, `ROUTES`.

### 4.6 Backend Design Tokens (Python)

`salesos/backend/design_tokens/__init__.py` defines:
- `ColorPalette` — OLD blue-based (`#2563EB` primary, zinc/gray neutrals)
- `TypographyTokens` — `Inter` + `Noto Sans Arabic` + `JetBrains Mono`
- `RadiusTokens` — 4px, 8px, 12px, 16px, 9999px
- `ElevationTokens` — generic black shadows
- `SpacingTokens` — same 4px grid
- `IconTokens` — `lucide-react`, sizes 16/20/24/32px
- `MotionTokens` — 150/200/300ms durations
- `BreakpointTokens` — 640/768/1024/1280/1536px
- `DesignTheme` — full theme assembly
- `generate_css_variables()` method
- `THEME_REGISTRY` with tenant-scoped themes

**CRITICAL:** The backend design tokens are NOT in sync with the frontend. Backend uses blue `#2563EB`, zinc neutrals, Inter fonts. Frontend uses orange `#F57C1E`, warm neutrals, IBM Plex fonts. This is a major consistency gap.

---

## 5. Component API Contracts & Props

### 5.1 @salesos/ui Button

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  asChild?: boolean  // Radix Slot for polymorphic rendering
}
// Sizes: sm=8x3(px), md=10x4, lg=12x6 (Tailwind: h-8/h-10/h-12)
// Primary: bg-[var(--muhide-orange)] text-white
// Focus ring: --muhide-orange, disabled: opacity 50%
```

### 5.2 @salesos/ui Card

```typescript
interface CardProps extends HTMLAttributes<HTMLDivElement> {}
// Compound: Card, CardHeader, CardContent, CardFooter
// Default: rounded-xl, border border-default, bg-primary, shadow-muhide-1
// Header: p-6, Content: p-6 pt-0, Footer: flex items-center p-6 pt-0
```

**Note:** No `variant` prop on @salesos/ui Card — it's a single-style component. Foundation Card has `variant` (default/dark/bordered) and `accent` (orange/amber/blue/green/purple/red).

### 5.3 @salesos/ui Modal

```typescript
interface ModalProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children: ReactNode
}
// Compound: Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter
// Content: fixed center, max-w-lg, rounded-xl, bg-primary, shadow-muhide-4
// Overlay: fixed inset-0, z-overlay, bg-black/50
// Close button: absolute top-right, X icon
```

### 5.4 @salesos/ui Dropdown

```typescript
interface DropdownProps { children: ReactNode }
// Compound: Dropdown, DropdownTrigger, DropdownContent, DropdownItem
// Content: z-dropdown, min-w-[200px], rounded-lg, shadow-muhide-4
// Item: cursor-pointer, rounded-md, px-3 py-2, hover:bg-secondary
```

### 5.5 @salesos/ui Input

```typescript
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  leftIcon?: ReactNode
  rightIcon?: ReactNode
}
// Default: h-10, rounded-lg, border border-default
// Focus: ring-2 ring-[--muhide-orange], border-[--muhide-orange]
// Error: border-danger-500, focus:ring-danger-500
// Icons: left=pl-10, right=pr-10
```

### 5.6 @salesos/ui Select

```typescript
interface SelectOptions { label: string; value: string }
interface SelectProps {
  options: SelectOptions[]
  placeholder?: string
  error?: string; className?: string
  value?: string; onChange?: (value: string) => void
}
// Radix-based with animated open/close
```

### 5.7 @salesos/ui Table

```typescript
interface TableProps<TData> {
  columns: ColumnDef<TData>[]  // @tanstack/react-table
  data: TData[]
  loading?: boolean
  onRowClick?: (row: TData) => void
  className?: string
}
// Loading: 5 skeleton rows with animated pulse
// Empty: centered Loader2 spinner + "No results"
// Row: border-b, hover:bg-secondary on clickable rows
// Headers: sticky top-0, bg-secondary
```

### 5.8 @salesos/ui Tabs

```typescript
interface TabsProps {
  value?: string; onValueChange?: (value: string) => void
  defaultValue?: string
  children: ReactNode; className?: string
}
// Compound: Tabs, TabsList, Tab, TabsPanel
// Active tab: border-b-2 border-[--muhide-orange], text-primary
// Inactive: text-muted, hover:text-secondary
// TabsList: inline-flex, border-b border-default
```

**Missing:** No `badge`/`count` prop on Tab, no `variant` (underline/pills/buttons) — all required by COMPONENT_CATALOG.md C-009.

### 5.9 @salesos/ui Sidebar

```typescript
interface SidebarItem {
  icon: ReactNode; label: string; href?: string
  active?: boolean; badge?: number; children?: SidebarItem[]
}
interface SidebarProps {
  items: SidebarItem[]
  collapsed?: boolean
  onToggle?: () => void
  className?: string
}
// Collapsed: w-16, Expanded: w-64
// Active item: bg-[--muhide-orange]/10 text-[--muhide-orange]
// Collapsed tooltip: absolute left-full, z-dropdown
```

**Note:** This is a SIMPLE sidebar. Foundation Sidebar is the richer version with sections, company logo, dark bg.

### 5.10 @salesos/ui Layout

```typescript
// Layout: flex h-screen (full viewport)
// LayoutHeader: sticky top-0, z-sticky, h-14, border-b
// LayoutSidebar: border-r
// LayoutContent: flex-1 overflow-auto p-6
```

### 5.11 @salesos/ui Badge

```typescript
interface BadgeProps {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'outline'
}
// Default: bg-[--muhide-orange]/10 text-[--muhide-orange]
// Pill: rounded-full, px-2.5 py-0.5, text-xs
```

**Note:** Foundation Badge is the richer implementation with `status`, `tier`, `source`, `doc-status`, `intelligence-score` variants.

### 5.12 @salesos/ui Avatar

```typescript
interface AvatarProps {
  src?: string; alt?: string; fallback?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}
// Sizes: sm=8x8, md=10x10, lg=12x12 (Tailwind: h-8/h-10/h-12)
// Fallback: bg-secondary, text-muted, rounded-full
```

### 5.13 @salesos/ui Tooltip

```typescript
interface TooltipProps {
  content: ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  children: ReactNode; className?: string
}
// Content: bg-[--muhide-ink], text-white, text-xs, rounded-md
// Arrow fill matches tooltip bg
```

### 5.14 @salesos/ui Toast

```typescript
interface ToastProps {
  variant?: 'default' | 'success' | 'error'
  title?: string; description?: string
  onClose?: () => void; className?: string
}
// ToastProvider wraps app
// ToastViewport: bottom-right, max-h-screen, p-4, sm:max-w-[420px]
// useToast(): { toast, dismiss }
// Auto-dismiss: 5000ms default
// Max toasts: 5 (sliced)
```

**Missing variant:** `warning` and `info` variants exist in design but toastVariants only has default/success/error.

### 5.15 @salesos/ui Spinner

```typescript
interface SpinnerProps { className?: string }
// Uses lucide Loader2 + animate-spin
// Default color: text-[--text-muted]
```

### 5.16 @salesos/ui Kbd

```typescript
interface KbdProps { children: string }
// h-5, min-w-[20px], rounded, border, bg-secondary
// text-[11px], font-medium, text-secondary
// Uses shadow-muhide-1
```

### 5.17 Foundation Components — Prop Summaries

#### AppShell
```typescript
interface AppShellProps {
  children: ReactNode
  defaultSidebarCollapsed?: boolean  // default: false
}
// Context: { sidebarCollapsed, setSidebarCollapsed, commandOpen, setCommandOpen }
// Keyboard: Cmd/Ctrl+K toggles command palette
```

#### Foundation Sidebar (richer)
```typescript
interface SidebarProps {
  sections: SidebarSection[]      // Each: { id, label, items[] }
  companySection?: SidebarSection // Optional company-specific nav
  companyLogo?: ReactNode
  className?: string
}
// Dark bg: bg-[--muhide-ink] text-white
// Widths: sidebar-collapsed (64px) / sidebar (256px)
// Active item: bg-[--muhide-orange]/20 text-[--muhide-orange]
// Badge: bg-[--muhide-orange]/20
// Transition: duration-200 ease-standard
```

#### Header
```typescript
interface HeaderProps {
  title?: string
  breadcrumbs?: { label: string; href?: string }[]
  searchPlaceholder?: string      // default: "Search anything..."
  onSearchClick?: () => void      // default: opens command palette
  notificationCount?: number
  onNotificationClick?: () => void
  userAvatar?: ReactNode
  userMenu?: ReactNode
  className?: string
  children?: ReactNode
}
// Height: h-topbar (56px), border-b, white bg
// Search: min-w-[180px], bg-secondary, keyboard shortcut display
// Notifications: orange dot, 99+ cap
```

#### Navigation
```typescript
interface NavigationProps {
  sections: NavSection[]   // Each: { id, label?, items[] }
  orientation?: 'vertical' | 'horizontal'   // default: vertical
  size?: 'sm' | 'md' | 'lg'                 // default: md
  variant?: 'default' | 'pills' | 'tabs'    // default: default
  className?: string
}
// Three distinct visual variants with active/inactive/disabled states
// Sizes: sm=7px h, md=9px h, lg=10px h
// Role: navigation, list, listitem
```

#### Typography
```typescript
interface TypographyProps {
  variant?: TYPOGRAPHY variant key  // default: 'body'
  as?: React.ElementType             // polymorphic element
  weight?: 400 | 500 | 600 | 700
  color?: 'primary' | 'secondary' | 'muted' | 'disabled' | 'brand' | 'white'
  truncate?: boolean
  children: ReactNode
}
// Uses design-language TYPOGRAPHY tokens
// Auto-applies font-display to h1-h6, font-sans to body, font-mono to code/kbd
```

#### Stack
```typescript
interface StackProps {
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
  gap?: 0|1|2|3|4|5|6|8|10|12|16|20    // default: 3
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline'
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'
  wrap?: 'wrap' | 'nowrap' | 'wrap-reverse'
  as?: React.ElementType
}
```

#### Grid
```typescript
interface GridProps {
  cols?: 1-12 | { default?; sm?; md?; lg?; xl? }
  gap?: 0|1|2|3|4|5|6|8|10|12            // default: 4
  align?: 'start' | 'center' | 'end' | 'stretch'
  as?: React.ElementType
}
```

#### Container
```typescript
interface ContainerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'  // default: xl
  as?: React.ElementType
}
// Sizes: sm=640px, md=768px, lg=1024px, xl=1280px, full=100%
// Padding: px-4 sm:px-6 lg:px-8, mx-auto
```

#### Surface
```typescript
interface SurfaceProps {
  variant?: 'default' | 'elevated' | 'dark' | 'bordered' | 'glass'
  padding?: 'none' | 'sm' | 'md' | 'lg'    // default: md(20px)
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl'  // default: lg(8px)
  as?: React.ElementType
}
// References --surface-default, --surface-dark, --surface-glass CSS vars
// NOTE: These CSS vars are NOT defined in globals.css
```

#### Foundation Card (foundation/card.tsx)
```typescript
interface CardProps {
  variant?: 'default' | 'dark' | 'bordered'   // default: default
  padding?: 'sm' | 'md' | 'lg'                // default: md(16px)
  accent?: 'orange' | 'amber' | 'blue' | 'green' | 'purple' | 'red'
}
// Accent: border-l-[3px] with color
// Compound: Card, CardHeader, CardContent, CardFooter
// NOT the same as @salesos/ui Card
```

#### Foundation Badge (foundation/badge.tsx)
```typescript
interface BadgeProps {
  variant?: 'status' | 'tier' | 'source' | 'doc-status' | 'intelligence-score' | 'default' | 'outline'
  size?: 'sm' | 'md'
  dot?: boolean
  value?: string | number
}
// Status: active/evaluation/negotiation/pending/signed/confidential
// Source: wathq/balady/najiz/linkedin/manual
// Intelligence-score: color-coded by range (≤30 red, ≤60 amber, ≤80 green, >80 emerald)
```

#### Loading
```typescript
interface LoadingProps {
  variant?: 'spinner' | 'dots' | 'pulse'   // default: spinner
  size?: 'sm' | 'md' | 'lg'                // default: md(24px)
  label?: string
  overlay?: boolean                         // fixed overlay mode
}
// All variants use --muhide-orange color
// motion-reduce:animate-none on all animations
```

#### Skeleton
```typescript
interface SkeletonProps {
  variant?: 'text' | 'title' | 'avatar' | 'card' | 'table-row' | 'chart'
  width?: string | number; height?: string | number
  className?: string
  count?: number   // default: 1
}
// Color: bg-neutral-200, animate-pulse
// motion-reduce:animate-none
```

#### EmptyState
```typescript
interface EmptyStateProps {
  variant?: 'search' | 'signals' | 'timeline' | 'documents' | 'relationships' | 'default'
  title: string; description?: string
  action?: { label: string; onClick: () => void }
}
// SVG icons drawn inline per variant
// Action button: bg-[--muhide-orange], hover:brightness-110
```

#### Metric
```typescript
interface MetricProps {
  value: string | number; label: string
  trend?: 'up' | 'down' | 'flat'
  trendValue?: string
  icon?: ReactNode
  color?: 'default' | 'brand' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md' | 'lg'    // affects value font size
  loading?: boolean
}
// Loading: skeleton placeholder with 3 bars
// Trend: up=↑ green, down=↓ red, flat=→ muted
// Screen reader: "Increased"/"Decreased"/"No change"
```

#### Section
```typescript
interface SectionProps {
  title?: string; description?: string
  actions?: ReactNode
  divider?: boolean    // adds Divider at bottom
  as?: React.ElementType
}
// Title: h4 variant, color primary, aria-labelledby
// Description: body-sm, color muted
```

#### Divider
```typescript
interface DividerProps {
  variant?: 'full' | 'light' | 'dark'
  label?: string    // renders text in middle with lines on both sides
}
// References: --border-subtle, --border-muted, --border-strong CSS vars
// NOTE: --border-subtle and --border-muted are NOT defined in globals.css
```

#### Icon (foundation wrapper)
```typescript
interface IconProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'    // 14/16/20/24px
  color?: 'primary' | 'secondary' | 'muted' | 'brand' | 'white' | 'current'
  children: ReactNode
  label?: string    // when provided: role="img" aria-label
}
```

---

## 6. RTL Architecture & Implementation Quality

### 6.1 Quality Assessment: ★★★★☆ (4/5)

The RTL implementation is comprehensive and well-architected.

### 6.2 Mechanism

The system uses:
1. **HTML `dir` attribute** (`dir="rtl"` / `dir="ltr"`) set on `<html>` via i18n
2. **CSS utility layer** (globals.css:403-554) with `[dir="rtl"]` selectors overriding all directional Tailwind utilities
3. **Arabic font stack** flipping (body → IBM Plex Sans Arabic, headings → IBM Plex Sans Arabic with Viga fallback)
4. **Component-level logic** (e.g., LanguageSwitcher, MobileNav slide animation direction)

### 6.3 Covered CSS Overrides

| Category | Coverage | globals.css Lines |
|----------|----------|-------------------|
| Text alignment (left/right/start/end) | Complete | 404-408 |
| Positioning (left-*/right-*) | 18 utility pairs | 410-420 |
| Margins (ml-*/mr-*, 0→20, auto) | Complete | 422-453 |
| Padding (pl-*/pr-*, 0→20) | Complete | 455-478 |
| Space utilities (space-x-*) | Complete | 480-493 |
| Borders (border-l/r) | 4 widths (0,1,2,4) | 494-501 |
| Border radius (rounded-l/r) | Complete (6 sizes) | 503-514 |
| Transforms (translate-x) | Complete (incl. full, half) | 516-532 |
| Insets (inset-x/y, start/end) | Complete | 534-537 |
| Rotate | 180deg flip | 539 |
| Dividers (divide-x) | 5 widths | 541-545 |
| Float (left/right) | Complete | 547-548 |
| Transform origins | Complete (4 corners) | 550-553 |

### 6.4 RTL-Aware Components

- **LanguageSwitcher**: Toggles `locale` between "ar"/"en", updates `dir` attribute, shows appropriate label
- **MobileNav**: Slide animation direction respects `dir` (RTL → slide-in-right, LTR → slide-in-left), FAB position uses `start-4`/`end-4`
- **Typography**: `typeClass(variant, isRTL)` function exists in design-language but is NOT called in the Typography component
- **Sidebar**: chevron rotation flips with `rotate-180` on collapsed

### 6.5 RTL Gaps

1. **Typography.tsx** ignores the `isRTL` parameter in `typeClass()` — doesn't change font-family to arabic for RTL
2. **CommandBar** shortcuts show `⌘` (Mac-specific) — no Arabic-aware shortcut display
3. **Sidebar** `aria-label="Sidebar"` hardcoded in English
4. **ErrorBoundary** uses i18n `useTranslation()` — proper Arabic support
5. **Empty states** in design-language are all in Arabic, but EmptyState components use English as primary with Arabic fallbacks via Foundation badge variants and missing i18n integration in some places

---

## 7. Dark Mode / Theme System

### 7.1 Mechanism

Dark mode uses Tailwind's `class` strategy (`tailwind.config.ts:10`):

```
darkMode: "class"
```

A `.dark` class on `<html>` triggers the dark mode override block in globals.css:80-93.

### 7.2 Light → Dark Token Map

| Token | Light | Dark | Contrast Ratio |
|-------|-------|------|---------------|
| `--text-primary` | `#26231E` | `#EDEBE6` | Good |
| `--text-secondary` | `#706A5D` | `#A59E90` | Adequate |
| `--text-muted` | `#A59E90` | `#706A5D` | **SWAPS with secondary** |
| `--text-disabled` | `#BFB9AD` | `#565147` | Adequate |
| `--bg-primary` | `#FFFFFF` | `#151214` (muhide-ink) | Good |
| `--bg-secondary` | `#F7F6F4` | `#26231E` (neutral-900) | Good |
| `--bg-tertiary` | `#EDEBE6` | `#3D3932` (neutral-800) | Good |
| `--border-default` | `#D9D5CD` | `#3D3932` | Good |
| `--border-hover` | `#BFB9AD` | `#565147` | Good |
| `--border-active` | `#F57C1E` | `#F57C1E` | Constant |
| `--border-disabled` | `#EDEBE6` | `#26231E` | Good |

### 7.3 Dark Mode Component Coverage

| Component | Dark Support | Mechanism |
|-----------|-------------|----------|
| All @salesos/ui components | ✅ Via CSS variables | All use `var(--bg-primary)`, `var(--text-primary)`, etc. |
| Foundation Sidebar | ✅ Always dark | `bg-[var(--muhide-ink)]` — independent of theme |
| Foundation Header | ⚠️ Partial | `bg-white` hardcoded — does NOT invert in dark mode |
| Foundation CommandBar | ⚠️ Partial | `bg-white` hardcoded — does NOT invert |
| Foundation Card | ✅ | Uses CSS vars + dedicated `variant: 'dark'` |
| Foundation Surface | ✅ | Has `variant: 'dark'` bg |
| WidgetRenderer | ⚠️ Partial | Has hardcoded `dark:` classes alongside CSS vars |
| SectionRenderer | ❌ | Hardcoded `text-gray-700 dark:text-gray-300` — not using design tokens |
| SchemaRenderer | ❌ | Hardcoded `dark:bg-gray-700`, `text-gray-500 dark:text-gray-400` |

**`text-muted` swap issue:** In light mode, muted (`#A59E90`) is lighter than secondary (`#706A5D`). In dark mode, they swap positions — muted (`#706A5D`) is now darker than secondary (`#A59E90`). This breaks the visual hierarchy: muted text should always be the lightest/dimmest, but in dark mode it becomes more prominent than secondary.

### 7.4 Shadow Behavior in Dark Mode

Shadows use `rgba(21,18,20,X)` which becomes invisible on the dark `#151214` background. This is by design — elevation is conveyed through border contrast instead of shadow visibility in dark mode. However, components like DropdownContent and ModalContent that use `shadow-muhide-4` will appear borderless in dark mode because the shadow is invisible.

---

## 8. Responsive Rules & Breakpoints

### 8.1 Breakpoints

| Name | Width | Tailwind | Scope |
|------|-------|----------|-------|
| xs | 480px | — (custom) | design-language only |
| sm | 640px | `sm:` | Mobile landscape |
| md | 768px | `md:` | Tablet |
| lg | 1024px | `lg:` | Small desktop |
| xl | 1280px | `xl:` | Desktop |
| 2xl | 1536px | `2xl:` | Wide desktop |

### 8.2 Responsive Behaviors (globals.css)

#### App Shell (≤767px)
- Flex direction switches to column
- Sidebar becomes fixed bottom tab bar (100% width, auto height, h-56px, horizontal layout)
- Sidebar nav items flex to row, buttons compact (10px font, 20px icons)
- Main content gets 64px bottom padding for tab bar clearance

#### Sidebar (≤767px)
- `.sidebar` hidden entirely (display:none) — replaced by app-shell mobile sidebar

#### Table → Cards (≤639px)
- Responsive tables transform to card layout
- `thead` hidden, `tr` becomes bordered card
- `td` uses `data-label` attribute for label-value pairs
- RTL-aware: labels get `margin-left: 8px` spacing

#### Widget Grid
- 1 col (default/mobile)
- 2 cols (≥640px)
- 3 cols (≥1024px)
- 4 cols (≥1280px)

#### Padding/Margin Reduction (≤639px)
- `.responsive-pad*` classes reduce to 8px
- `.responsive-gap` reduces to 8px
- Headings scale down (h1→18px, h2→16px)
- Body text minimum → 11px

#### Full-Screen Modals (≤639px)
- Dialog content → 100% width/height, no border-radius
- Basically converts modals to full-screen sheets on mobile

#### Workspace Layout (≤767px)
- Flex direction switches to column (sidebar → stack → content)

### 8.3 Zone Visibility Rules (layout.ts:58-63)

| Zone | xs | sm | md | lg+ |
|------|----|----|----|-----|
| Copilot | Hidden | Hidden | Visible | Visible |
| Panel | Hidden | Hidden | Visible | Visible |
| Timeline | Hidden | Visible | Visible | Visible |
| Sidebar | Hidden | Hidden | Visible | Visible |

### 8.4 Grid Columns by Viewport (layout.ts:52-56)

| Width | Columns |
|-------|---------|
| < 640px | 4 |
| < 1024px | 8 |
| ≥ 1024px | 12 |

### 8.5 Component-Specific Responsiveness

| Component | Behavior |
|-----------|---------|
| Button | Sizes adapt (sm: h-8, md: h-10, lg: h-12) — not breakpoint-dependent |
| Modal | Full-screen on mobile (≤639px) via CSS, not component logic |
| CommandBar | Logo hidden on sm (sm:inline), search width adapts |
| Navigation | Horizontal variant for tablet/desktop, vertical with sections for mobile |
| MobileNav | FAB visible only on md:hidden, slide-in drawer on mobile |
| Header | Search button: min-w-[180px] on desktop, compact on mobile |
| Toast viewport | sm:max-w-[420px], full-width on mobile |

---

## 9. Interaction Patterns

### 9.1 Hover States

| Component | Hover Effect | Implementation |
|-----------|-------------|---------------|
| Button (primary) | `hover:bg-orange-600` (darker orange) | Tailwind |
| Button (secondary) | `hover:bg-[var(--bg-tertiary)]` | CSS var |
| Button (outline) | `hover:bg-[var(--bg-secondary)]` | CSS var |
| Button (ghost) | `hover:bg-[var(--bg-secondary)]` | CSS var |
| Button (danger) | `hover:bg-danger-700` | Tailwind class |
| Sidebar item | `hover:bg-white/10` (dark) or `hover:bg-secondary` (light) | CSS var |
| Table row | `hover:bg-[var(--bg-secondary)]` | Conditional (onRowClick prop) |
| Dropdown item | `hover:bg-[var(--bg-secondary)]` | CSS var |
| Select option | `hover:bg-[var(--bg-secondary)]` | CSS var |
| Tab | `hover:text-[var(--text-secondary)]` | CSS var |
| Input | `hover:border` via parent | None — focuses on focus state |
| Card (interactive) | `hoverEffect: 'border'` | Design-language only, not implemented in code |
| Navigation item | `hover:text-primary hover:bg-secondary` | CSS var |
| Tooltip | Appears on hover | Radix |
| Toast close | `hover:text-primary` | CSS var, opacity 0→100 on group hover |
| EmptyState button | `hover:brightness-110` | CSS filter |

### 9.2 Focus States

| Component | Focus Style | Implementation |
|-----------|------------|---------------|
| Button | `focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[--muhide-orange]` | Tailwind |
| Input | `focus:ring-2 focus:ring-[--muhide-orange] focus:border-[--muhide-orange]` | Tailwind |
| Select | `focus:ring-2 focus:ring-[--muhide-orange] focus:border-[--muhide-orange]` | Tailwind |
| CommandBar input | `outline-none` only — no visible focus ring | **MISSING** |
| Toast close | `focus:opacity-100 focus:outline-none focus:ring-2` | Tailwind |
| Kbd | No focus styles | **MISSING** |
| Tabs | Focus handled by Radix | Browser default |

**Accessibility concern:** The design-language `FOCUS` constant (accessibility.ts:2) specifies `ring-blue-500` but components use `ring-[--muhide-orange]`. The accessibility token doesn't match the implementation.

### 9.3 Active / Selected States

| Component | Active Style |
|-----------|-------------|
| Sidebar item | `bg-[var(--muhide-orange)]/20 text-[var(--muhide-orange)] font-medium` |
| Tab | `border-b-2 border-[var(--muhide-orange)] text-[var(--text-primary)]` |
| Navigation (default) | `bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] font-medium` |
| Navigation (pills) | `bg-[var(--muhide-orange)] text-white font-medium` |
| Navigation (tabs) | `text-[var(--muhide-orange)] border-b-[var(--muhide-orange)] font-medium` |
| CommandBar item | `bg-[var(--muhide-orange)]/10 text-[var(--text-primary)]` |

### 9.4 Disabled States

| Component | Disabled Style |
|-----------|---------------|
| Button | `disabled:pointer-events-none disabled:opacity-50` |
| Input | `disabled:cursor-not-allowed disabled:opacity-50` |
| Select | `disabled:cursor-not-allowed disabled:opacity-50` |
| Dropdown item | `data-[disabled]:pointer-events-none data-[disabled]:opacity-50` |
| Navigation item | `opacity-40 cursor-not-allowed pointer-events-none` |

### 9.5 Loading States

| Component | Loading Pattern |
|-----------|----------------|
| Button | Replaces icons with Spinner, disables button |
| Table | 5 skeleton rows with animated pulse bars |
| Metric | 3 skeleton bars (label, value, trend) in placeholder card |
| Skeleton | 6 variants (text/title/avatar/card/table-row/chart), `count` prop for lists |
| Loading | 3 variants (spinner/dots/pulse), optional overlay mode |
| CommandBar | Spinner + "Searching..." centered |
| WidgetRenderer | Card with skeleton header + centered Spinner |

### 9.6 Empty States

| Component | Empty Pattern |
|-----------|--------------|
| Table | Centered Loader2 spinner + "No results" |
| EmptyState | 6 variant icons + title + description + action button |
| CommandBar | Search icon + "No results found." message |
| WidgetTemplate | "لا توجد عناصر بعد" + hint text |
| ErrorBoundary | Warning triangle + title + message + retry button |

### 9.7 Error States

| Component | Error Pattern |
|-----------|--------------|
| Input | Red border (`border-danger-500`) + error message below |
| Select | Red border + error message below |
| CommandBar | Red banner with alert icon + error text |
| WidgetRenderer | Red card with error message |
| SchemaRenderer | Centered red card with error |
| ErrorBoundary | Warning icon + title + message + expandable error details + retry button |
| Toast | `error` variant: red bg/border |
| Metric | Shows value normally (no special error display) — **MISSING** |
| Table | No error state prop — **MISSING** |

---

## 10. Design Consistency Score

### 10.1 Overall Score: 72/100

| Category | Score | Max | Notes |
|----------|-------|-----|-------|
| Color Token Consistency | 14 | 20 | 5 identical semantic palettes, backend out of sync |
| Typography Consistency | 15 | 20 | body-sm (13px) gap in Tailwind, design-language vs globals.css font stacks differ |
| Spacing Consistency | 14 | 15 | DENSITY presets not consumed, modal sizes missing from Tailwind |
| Shadow Consistency | 10 | 15 | No CSS variables exported, backend different system |
| Component Prop Consistency | 8 | 15 | Duplicate Card/Badge/Sidebar implementations, renderer uses hardcoded colors |
| Dark Mode Coverage | 8 | 10 | Header/CommandBar hardcoded white, text-muted swap issue, renderer hardcoded values |
| RTL Coverage | 13 | 15 | Comprehensive CSS layer, some hardcoded English labels |
| Responsive Coverage | 14 | 15 | 4 breakpoint strategies, mobile-first, table→card transform |
| Accessibility | 12 | 15 | Focus ring color inconsistency, some missing focus states, good ARIA overall |
| Token Source of Truth | 5 | 10 | Four parallel token systems (CSS vars, Tailwind, design-language TS, backend Python) |
| Component Completeness | 10 | 10 | 22 foundation + 16 UI + renderer + icons = comprehensive |

**Deductions:**
- -6: No single source of truth for tokens (4 parallel systems)
- -6: Duplicate component implementations without clear hierarchy
- -5: Identical semantic color scales (no differentiation)
- -3: Backend tokens not migrated to MUHIDE
- -3: Hardcoded colors in renderer package
- -2: CSS variables referenced in components but not defined
- -2: Focus ring color mismatch between spec and implementation
- -1: Toast missing warning/info variants

---

## 11. Design Debt Register

### Critical (P0)

| ID | Item | Impact | Location |
|----|------|--------|----------|
| DD-001 | **Backend tokens use old blue palette** (#2563EB primary, zinc neutrals, Inter/Noto Sans Arabic/JetBrains Mono) | Frontend-backend visual divergence for any server-rendered content or CSS generation | `backend/design_tokens/__init__.py` |
| DD-002 | **CSS variables referenced but undefined** — `--surface-default`, `--surface-dark`, `--surface-glass`, `--border-subtle`, `--border-muted`, `--border-strong`, `--shadow-card` | Surface, Divider, and other components reference these but they don't exist in globals.css | `foundation/surface.tsx:15-19`, `foundation/divider.tsx:11-14` |
| DD-003 | **Renderer uses hardcoded Tailwind colors instead of design tokens** — `text-gray-700`, `bg-gray-200`, `text-blue-600`, `dark:text-gray-300` etc. in SchemaRenderer, SectionRenderer, WidgetRenderer | Visual inconsistency with rest of design system | `packages/renderer/src/*.tsx` |
| DD-004 | **Duplicate Card, Badge, Sidebar implementations** — @salesos/ui has simple versions, foundation has rich versions. No documented hierarchy. | Confusion about which to use, visual inconsistency | `ui/src/card.tsx` vs `foundation/card.tsx`, etc. |

### High (P1)

| ID | Item | Impact | Location |
|----|------|--------|----------|
| DD-005 | **text-muted swaps with text-secondary in dark mode** — dark mode muted is darker (more prominent) than dark mode secondary, breaking visual hierarchy | Confusing visual priority in dark mode | `globals.css:83` |
| DD-006 | **5 semantic color scales identical to primary** — search, workspace, object, signal, brand all copy the orange scale exactly | No semantic differentiation, wasted palette entries | `design-language/color.ts:83-132` |
| DD-007 | **body-sm (13px) has no Tailwind equivalent** — design-language defines it but Tailwind has 12px (sm) and 14px (base) only | Gap in typography scale consistency | `design-language/typography.ts:20` |
| DD-008 | **Shadow CSS variables not exposed** — shadows only available via Tailwind `shadow-muhide-*` classes, not as `--shadow-1..6` CSS props | Can't use shadows in inline styles or non-Tailwind contexts | No `--shadow-*` in `globals.css` |
| DD-009 | **DENSITY presets defined but never consumed** — compact/normal/comfortable/spacious spacing presets exist in design-language but no component uses them | Wasted design token effort | `design-language/spacing.ts:35-48` |
| DD-010 | **Z-index design-language vs globals gap** — design-language defines command-palette(70), copilot(80), max(9999) but only dropdown-toast(10-60) exist in CSS/Tailwind | Potential z-index conflicts if copilot/command-palette are ever rendered | `elevation.ts:35-46` vs `globals.css:72-77` |
| DD-011 | **Header bg-white hardcoded** — does not respect dark mode | Header shows white on dark backgrounds | `foundation/header.tsx:35` |
| DD-012 | **CommandBar bg-white hardcoded** — does not respect dark mode | Command palette shows white in dark mode | `foundation/command-bar.tsx:133` |

### Medium (P2)

| ID | Item | Impact | Location |
|----|------|--------|----------|
| DD-013 | **FOCUS ring color in accessibility.ts says blue but components use orange** | Documentation/implementation mismatch | `accessibility.ts:2` vs button.tsx:8 |
| DD-014 | **Table has no error state prop** — only loading (skeleton) and empty (no results) | Can't show error states in tables | `ui/src/table.tsx` |
| DD-015 | **Toast variants missing warning and info** — cva only has default/success/error | Can't show warning/info toasts | `ui/src/toast.tsx:11-17` |
| DD-016 | **Tab has no badge/count prop** — COMPONENT_CATALOG requires it | Extra work to add counts to tabs | `ui/src/tabs.tsx:39-53` |
| DD-017 | **Tabs has no variant prop** — only underline style, but catalog requires pills/buttons variants | Limited tab styling options | `ui/src/tabs.tsx` |
| DD-018 | **CommandBar input has no focus ring** — `outline-none` only | Keyboard users can't see when input is focused | `foundation/command-bar.tsx:149` |
| DD-019 | **Kbd component has no focus styles** | Keyboard hints lack state indication | `ui/src/kbd.tsx` |
| DD-020 | **Metric has no error state** — only loading and loaded | Can't display error metrics | `foundation/metric.tsx` |
| DD-021 | **FONT_FAMILY values differ** — design-language adds system fallbacks (SF Pro Display, SF Mono, -apple-system) but globals.css and tailwind.config.ts don't | Minor typography inconsistency | `typography.ts:27-32` vs `globals.css:60-63` |
| DD-022 | **typeClass(isRTL) parameter ignored** — the function accepts isRTL but never uses it | Dead parameter | `typography.ts:34-37` |
| DD-023 | **Design-language `elevation.ts` shadow level 2 single-layer** — Tailwind config shadow-muhide-2 has two layers (0,1,3 + 0,1,2), but design-language ELEVATION[2] has only one | Different shadow definitions between systems | `elevation.ts:28` vs `tailwind.config.ts:85` |

### Low (P3)

| ID | Item | Impact | Location |
|----|------|--------|----------|
| DD-024 | **Design-language DESIGN_TOKEN_MAPPING.md mentions `--shadow-*` CSS vars that don't exist** | Documentation drift | DESIGN_TOKEN_MAPPING.md:195-200 |
| DD-025 | **Tailwind `spacing.modal-*` missing** — design-language FIXED defines modal-sm/md/lg but Tailwind config doesn't include them | Can't use `w-modal-md` in Tailwind | `design-language/spacing.ts:57-58` vs `tailwind.config.ts:68-74` |
| DD-026 | **Foundation Card `rounded-lg` (8px) vs @salesos/ui Card `rounded-xl` (12px)** | Inconsistent border radius between two Card implementations | `foundation/card.tsx:33` vs `ui/card.tsx:11` |

---

## 12. Widget SDK Design Analysis

### 12.1 Architecture

The Widget system follows a **Container/View pattern**:

```
YourWidgetContainer.tsx  →  createDashboardWidget()  →  SDK handles lifecycle/permissions/telemetry
YourWidgetView.tsx       →  Pure React component      →  No SDK dependency, receives data props
types.ts                 →  Shared type definitions
```

### 12.2 Template Analysis (WidgetTemplate/)

#### Container (`YourWidgetContainer.tsx`)
- Uses `createDashboardWidget<DataType>('widgetId', config)`
- Config includes `metadata: { title, description }` and `render({ data })`
- Minimal boilerplate — the SDK handles all the complexity

#### View (`YourWidgetView.tsx`)
- Pure presentational component
- Three explicit states: **loading** (spinner), **empty** (message + hint), **loaded** (items list)
- No business logic, no API calls, no SDK imports
- Uses CSS variables for theming (`var(--text-primary)`, `var(--text-muted)`, `var(--muhide-orange)`)
- Proper ARIA: `role="region"`, `role="status"`, `aria-live="polite"`, `aria-label` on items
- RTL-aware: Arabic text for labels

#### Types (`types.ts`)
- Clean separation: `ViewProps` (for the View), `Item` (for data items), `Data` (for the data shape)
- Flat, minimal types

### 12.3 Contract Test Pattern

The WidgetTemplate includes a `describeWidgetContract()` test utility that enforces:
1. **Rendering**: Widget renders with data
2. **Loading state**: Shows loading indicator
3. **Degraded state**: Widget handles partial data
4. **Error state**: Widget handles errors
5. **Permissions**: Widget respects permission requirements
6. **Feature flags**: Widget checks feature flags
7. **Accessibility**: Roles, labels, live regions
8. **Empty state**: Meaningful empty state

Contract tests are found in `__tests__/YourWidget.test.tsx` (124 lines) and cover:
- Rendering: item count, all items
- Loading: status role, no list rendering
- Empty: messages, hint text
- Accessibility: region role, list/lisitem roles, aria-labels, aria-live, aria-atomic
- Dark mode: CSS variable usage verification
- Reduced motion: animation class detection

### 12.4 WidgetRenderer (@salesos/renderer)

The `WidgetRenderer` provides a shell with:
- **Loading state**: Card with skeleton header + centered Spinner
- **Error state**: Card with red error card (hardcoded red classes — DD-003)
- **Loaded state**: Card wrapper with `data-widget-id` attribute
- Uses `@salesos/ui` Card, CardHeader, CardContent, Spinner

### 12.5 Widget SDK Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Architecture | ★★★★★ | Clean Container/View separation, SDK handles cross-cutting concerns |
| TypeScript | ★★★★☆ | Well-typed, generic data type, clear interfaces |
| Accessibility | ★★★★☆ | Contract tests enforce ARIA, live regions, roles |
| States coverage | ★★★★☆ | Loading, empty, error all required by contract |
| RTL support | ★★★☆☆ | Template uses Arabic labels, but not tested in contract tests |
| Dark mode | ★★★☆☆ | Uses CSS variables, but no explicit dark mode test |
| Documentation | ★★★★★ | README with setup steps, checklist, standards reference |

### 12.6 Widget SDK Gaps

1. **No `error` state in the template's View** — only loading and empty. Contract tests require it.
2. **No `degraded` state pattern** — how to handle partial data (some widgets load, some fail).
3. **No RTL-specific contract test** — should verify direction swapping.
4. **No dark mode contract test** — should verify CSS variable usage in both themes.
5. **Renderer has color debt** — WidgetRenderer uses hardcoded Tailwind colors (DD-003).

---

## Appendix: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DESIGN TOKEN SOURCES                         │
│  (4 parallel systems with varying synchronization)                  │
├───────────────┬──────────────────┬────────────────┬─────────────────┤
│ globals.css   │ tailwind.config  │ design-language│ backend/Python  │
│ CSS vars      │ Tailwind tokens  │ TS modules     │ design_tokens   │
│ ─────────     │ ─────────────    │ ────────       │ ────────        │
│ 92 tokens     │ 15 export groups │ 16 modules     │ 8 dataclasses   │
│ Light + Dark  │ colors/fonts/    │ colors/motion/ │ colors/typo/    │
│ ✅ MUHIDE     │ shadow/zIndex    │ layout/states  │ radius/shadow/  │
│               │ ✅ MUHIDE        │ ✅ MUHIDE      │ ❌ OLD BLUE     │
├───────────────┴──────────────────┴────────────────┴─────────────────┤
│                          COMPONENT LAYERS                            │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐      │
│  │ @salesos/ui (16)    │  │ Foundation (22)                   │      │
│  │ Button/Card/Modal/  │  │ AppShell/Sidebar/Header/          │      │
│  │ Dropdown/Input/     │  │ Navigation/CommandBar/Typography/ │      │
│  │ Select/Table/Tabs/  │  │ Surface/Stack/Grid/Container/     │      │
│  │ Sidebar/Layout/     │  │ Section/Divider/Icon/Card/Badge/  │      │
│  │ Badge/Avatar/       │  │ Metric/Skeleton/Loading/          │      │
│  │ Tooltip/Toast/      │  │ EmptyState/ErrorBoundary          │      │
│  │ Spinner/Kbd         │  │                                   │      │
│  └─────────────────────┘  └──────────────────────────────────┘      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ @salesos/renderer (5)                                        │    │
│  │ Schema/Viewer/Tab/Section/Widget Renderers                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐      │
│  │ @salesos/icons      │  │ @salesos/config                  │      │
│  │ 100+ lucide icons   │  │ Base URL, routes, page size      │      │
│  └─────────────────────┘  └──────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```
