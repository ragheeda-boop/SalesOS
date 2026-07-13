# Design System & UX Fixes — Execution Report

**Date**: 2026-07-13  
**Audit ID**: 04-design-ux-fixes  
**Status**: COMPLETE

---

## 1. Backend Design Token Migration (DD-001) — COMPLETE

**File**: `salesos/backend/design_tokens/__init__.py`

### Color Palette Changes
| Token | Old Value | New Value |
|-------|-----------|-----------|
| primary | `#2563EB` (blue-600) | `#F57C1E` (MUHIDE Orange) |
| primary_light | `#3B82F6` (blue-500) | `#FFA04A` (orange-400) |
| primary_dark | `#1D4ED8` (blue-700) | `#D4660F` (orange-600) |
| neutral_50-950 | Zinc scale (`#FAFAFA` → `#09090B`) | Warm gray scale (`#F7F6F4` → `#1A1714`) |
| surface_secondary | `#F4F4F5` | `#F7F6F4` |
| surface_tertiary | `#E4E4E7` | `#EDEBE6` |
| border | `#E4E4E7` | `#D9D5CD` |
| border_strong | `#D4D4D8` | `#BFB9AD` |
| text_primary | `#09090B` | `#26231E` |
| text_secondary | `#52525B` | `#706A5D` |
| text_tertiary | `#A1A1AA` | `#A59E90` |
| text_disabled | `#D4D4D8` | `#BFB9AD` |
| chart_1-6 | Blue/green palette | Orange/green/warm palette |

### Typography Changes
| Token | Old | New |
|-------|-----|-----|
| font_family_arabic | `'Noto Sans Arabic', 'Tahoma'` | `'IBM Plex Sans Arabic'` |
| font_family_english | `'Inter', -apple-system...` | `'IBM Plex Sans', -apple-system...` |
| font_family_display | *(missing)* | `'Viga', 'IBM Plex Sans Arabic'` |
| font_family_mono | `'JetBrains Mono', 'Cairo'` | `'IBM Plex Mono'` |
| Font scale | 12-36px (xs-4xl) | 11-32px to match frontend |

### Other Token Changes
- **Radius**: Updated to match frontend (2px, 6px, 8px, 12px, 16px)
- **Elevation**: Updated to MUHIDE shadow palette (warm-shadow colors)
- **Spacing**: Unchanged (already aligned)

---

## 2. CSS Variable Cleanup (DD-002) — COMPLETE

**File**: `salesos/frontend/src/app/globals.css`

### Missing Variables Added

| Variable | Light Value | Dark Value | Used By |
|----------|-------------|------------|---------|
| `--surface-default` | `#FFFFFF` | `#151214` | Surface.tsx |
| `--surface-dark` | `#151214` | `#26231E` | Surface.tsx |
| `--surface-glass` | `rgba(255,255,255,0.8)` | `rgba(21,18,20,0.8)` | Surface.tsx |
| `--shadow-card` | `0 1px 3px rgba(...)` | `0 1px 3px rgba(...)` | Surface.tsx |
| `--border-subtle` | `#D9D5CD` | `#3D3932` | Surface.tsx, Divider.tsx |
| `--border-muted` | `#EDEBE6` | `#26231E` | Divider.tsx |
| `--border-strong` | `#706A5D` | `#8B8475` | Divider.tsx |
| `--border` | `#D9D5CD` | `#3D3932` | Widget spinner, etc. |
| `--sidebar-width` | `256px` | *(same)* | globals.css `.sidebar` |
| `--focus-ring` | `#2196F3` | `#64B5F6` | Global focus-visible |

### Verification
All `var(--` references in foundation components now have corresponding `--` definitions in globals.css.

---

## 3. Duplicate Component Consolidation — COMPLETE

### Identified Duplicates
| Component | Foundation (duplicate) | Canonical (packages/ui/) |
|-----------|------------------------|--------------------------|
| Card | `src/components/foundation/card.tsx` | `packages/ui/src/card.tsx` |
| Badge | `src/components/foundation/badge.tsx` | `packages/ui/src/badge.tsx` |
| Sidebar | `src/components/foundation/sidebar.tsx` | `packages/ui/src/sidebar.tsx` |

### Actions Taken
- Added `@deprecated` JSDoc to all 3 foundation components with migration notes
- Foundation Card already uses `bg-[var(--bg-primary)]` (fixed in dark mode task)
- Foundation Badge uses `@salesos/ui` CSS variable pattern

---

## 4. Dark Mode Fixes — COMPLETE

### Hardcoded Backgrounds Fixed

| File | Line | Old | New |
|------|------|-----|-----|
| `command-bar.tsx` | 133 | `bg-white` | `bg-[var(--bg-primary)]` |
| `header.tsx` | 35 | `bg-white` | `bg-[var(--bg-primary)]` |
| `header.tsx` | 72 | `bg-white` (kbd) | `bg-[var(--bg-primary)]` |
| `workspace-layout.tsx` | 20 | `bg-white` | `bg-[var(--bg-primary)]` |
| `card.tsx` | 13,15 | `bg-white` | `bg-[var(--bg-primary)]` |
| `metric.tsx` | 45,56 | `bg-white` | `bg-[var(--bg-primary)]` |

### Text-Muted/Text-Secondary Swap Fix

| Mode | `--text-secondary` | `--text-muted` |
|------|-------------------|----------------|
| Light (unchanged) | `#706A5D` | `#A59E90` |
| Dark (BEFORE) | `#A59E90` (was muted in light!) | `#706A5D` (was secondary in light!) |
| Dark (AFTER) | `#8B8475` (neutral-500) | `#565147` (neutral-700) |

The values were effectively swapped between light and dark modes, causing inconsistent visual hierarchy. Fixed with properly ordered neutral-500/700 values.

---

## 5. Focus Ring Consistency — COMPLETE

**File**: `salesos/frontend/src/app/globals.css`

Added global focus-visible rule using the accessibility standard blue (`#2196F3`) rather than the brand orange:

```css
*:focus-visible {
  outline: 2px solid var(--focus-ring, #2196F3);
  outline-offset: 2px;
  border-radius: 2px;
}
```

- **`--focus-ring`**: `#2196F3` (light) / `#64B5F6` (dark) — WCAG AA compliant
- The previous codebase had no consistent focus ring; components used `outline-none` without replacement focus indicators.
- This rule ensures ALL focusable elements get a visible focus indicator for keyboard navigation.

### Foundation Components Checked
| Component | Focus Ring Status |
|-----------|-------------------|
| command-bar.tsx | Uses `outline-none` on input → now gets global focus ring |
| All interactive elements | Did not have explicit focus:ring → now covered by global rule |

---

## 6. Widget Contract Tests — VERIFIED EXISTING

The three widgets specified (Mission Center, Intelligence Feed, Decision Queue) already have comprehensive `describeWidgetContract()` tests following the WidgetTemplate pattern.

### Test Coverage Summary

| Widget | File | Contract Tests | View Tests | Total |
|--------|------|----------------|------------|-------|
| Mission Center | `mission-center/__tests__/MissionCenter.test.tsx` | ✅ (lines 19-40) | 13 sections | 420 lines |
| Intelligence Feed | `intelligence-feed/__tests__/IntelligenceFeed.test.tsx` | ✅ (lines 37-60) | 7 sections | 239 lines |
| Decision Queue | `decision-queue/__tests__/DecisionQueue.test.tsx` | ✅ (lines 26-41) | 8 sections | 172 lines |

### Contract Test Coverage Areas
All three widgets pass:
- [x] 1. Rendering (title, children in ready state, fallback for permissions/flags)
- [x] 2. Widget States (loading, ready, degraded, error)
- [x] 3. Permissions (granted → render, denied → hide)
- [x] 4. Feature Flags (enabled → render, disabled → hide)
- [x] 5. Accessibility (refresh aria-label, loading role, error role, retry button)
- [x] 6. Interaction (retry refetch, refresh refetch)

### SDK Test Infrastructure
- `WidgetContract.tsx` — reusable contract test framework with 22 test cases
- All three widgets import from `@/features/dashboard/sdk/testing`

---

## Files Modified

| # | File | Changes |
|---|------|---------|
| 1 | `salesos/backend/design_tokens/__init__.py` | Full MUHIDE palette migration (colors, fonts, radii, shadows) |
| 2 | `salesos/frontend/src/app/globals.css` | +10 CSS variables, dark mode values, global focus-visible, text swap fix |
| 3 | `salesos/frontend/src/components/foundation/command-bar.tsx` | `bg-white` → `bg-[var(--bg-primary)]` |
| 4 | `salesos/frontend/src/components/foundation/header.tsx` | `bg-white` → `bg-[var(--bg-primary)]` (x2) |
| 5 | `salesos/frontend/src/components/foundation/workspace-layout.tsx` | `bg-white` → `bg-[var(--bg-primary)]` |
| 6 | `salesos/frontend/src/components/foundation/card.tsx` | `bg-white` → `bg-[var(--bg-primary)]` + `@deprecated` JSDoc |
| 7 | `salesos/frontend/src/components/foundation/badge.tsx` | `@deprecated` JSDoc |
| 8 | `salesos/frontend/src/components/foundation/sidebar.tsx` | `@deprecated` JSDoc |
| 9 | `salesos/frontend/src/components/foundation/metric.tsx` | `bg-white` → `bg-[var(--bg-primary)]` (x2) |
| 10 | `salesos/frontend/src/components/foundation/__tests__/card.test.tsx` | Updated test expectations for bg class changes |

---

## Verification Checklist

- [x] Backend ColorPalette now uses `#F57C1E` primary
- [x] Backend font families use IBM Plex Sans + Arabic
- [x] All `var(--` references resolved in global CSS
- [x] Foundation Card, Badge, Sidebar marked `@deprecated`
- [x] Zero `bg-white` hardcoded in foundation components
- [x] Dark mode `--text-secondary` and `--text-muted` properly ordered
- [x] Global focus-visible uses blue (`#2196F3`) per accessibility spec
- [x] Mission Center, Intelligence Feed, Decision Queue have contract tests
- [x] All modified files saved
