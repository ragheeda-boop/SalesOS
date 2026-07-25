# Gate G-8: Cross-browser Testing

> **Gate**: G-8 — Cross-browser Testing
> **Owner**: QA Engineer
> **Date**: 2026-07-17
> **Status**: Complete

---

## Verdict

| Criteria | Status |
|----------|--------|
| CSS Compatibility | ✅ PASS — Autoprefixer handles vendor prefixes; no unsupported modern CSS detected |
| JavaScript Compatibility | ✅ PASS — All modern APIs transpiled via Next.js/SWC per browserslist targets |
| Font Rendering | ✅ PASS — Self-hosted @fontsource packages ensure consistent rendering |
| RTL Support | ✅ PASS — Comprehensive RTL utilities + dedicated E2E tests |
| Polyfill Requirements | ✅ PASS — No additional polyfills needed for target browsers |
| Vendor-prefixed CSS | ✅ PASS — Only intentional font-smoothing/text-size-adjust prefixes used |
| CI/CD Multi-browser Coverage | ✅ PASS — Playwright configured for Chromium, Firefox, WebKit, Mobile Safari |

**Overall**: ✅ **PASS** — No blocking cross-browser issues detected.

---

## Browser Compatibility Matrix

| Feature | Chrome 125+ | Firefox 128+ | Safari 17.5+ | Mobile Safari 17+ | Edge 125+ |
|---------|:-----------:|:------------:|:------------:|:-----------------:|:---------:|
| CSS Grid (Tailwind) | ✅ | ✅ | ✅ | ✅ | ✅ |
| CSS Custom Properties | ✅ | ✅ | ✅ | ✅ | ✅ |
| CSS @layer | ✅ | ✅ | ✅ | ✅ | ✅ |
| `overscroll-behavior` | ✅ | ✅ | ✅ (16.0+) | ✅ | ✅ |
| `prefers-reduced-motion` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `touch-action: manipulation` | ✅ | ✅ | ✅ | ✅ | ✅ |
| RTL direction | ✅ | ✅ | ✅ | ✅ | ✅ |
| Optional chaining (`?.`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nullish coalescing (`??`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ResizeObserver` | ✅ | ✅ | ✅ (13.1+) | ✅ | ✅ |
| `Intl.DateTimeFormat("ar-SA")` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `navigator.clipboard.writeText` | ✅ (HTTPS) | ✅ (HTTPS) | ✅ (HTTPS) | ✅ (HTTPS) | ✅ (HTTPS) |
| `navigator.sendBeacon` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `CustomEvent` | ✅ | ✅ | ✅ | ✅ | ✅ |
| WOFF2 fonts | ✅ | ✅ | ✅ | ✅ | ✅ |
| `prefers-color-scheme` (dark mode) | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Findings

### 1. CSS Compatibility
- **CSS Custom Properties** (`--muhide-orange`, `--text-primary`, etc.): Used extensively in `globals.css`. Supported in all modern browsers (Chrome 49+, Firefox 31+, Safari 9.1+, Edge 15+).
- **`@layer` directive**: Used for `base`, `components`, `utilities` layers. Supported in all modern browsers (Safari 15.4+, Chrome 99+, Firefox 97+).
- **`overscroll-behavior-y: contain`**: Used in `.pull-to-refresh` class. Supported in Safari 16.0+. All current target browsers include this.
- **Grid layout**: Extensively used via Tailwind (`grid grid-cols-*`). Fully supported across all target browsers.
- **`touch-action: manipulation`**: Applied globally on interactive elements. Supported since 2015 across all browsers.
- **Vendor prefixes**: Only 3 instances found — all intentional and appropriate:
  - `-webkit-text-size-adjust: 100%` — prevents iOS Safari from auto-scaling text
  - `-webkit-font-smoothing: antialiased` — subpixel rendering on macOS
  - `-moz-osx-font-smoothing: grayscale` — subpixel rendering on macOS Firefox
- **No risky modern CSS** (no container queries, `:has()` selectors, backdrop-filter, or `subgrid` usage).

### 2. JavaScript Compatibility
- **Target**: TypeScript transpilation targets `ES2017` (via `tsconfig.json`), but Next.js/SWC handles actual bundling based on `browserslist` config.
- **Optional chaining (`?.`)**: Used extensively throughout the codebase. Downleveled by SWC during build for target browsers.
- **Nullish coalescing (`??`)**: Widely used. Handled by SWC transpilation.
- **`ResizeObserver`**: Used in `src/app/(dashboard)/graph/page.tsx` for SVG resizing. Supported in Safari 13.1+, Chrome 64+, Firefox 62+. Coverage adequate for target browsers.
- **`Intl.DateTimeFormat("ar-SA")` & `Intl.NumberFormat("ar-SA")`**: Used for Arabic formatting in `i18n` utilities. Supported in all target browsers, though date formatting consistency for `ar-SA` locale can vary slightly — no breaking differences.
- **`navigator.clipboard.writeText`**: Used in settings page for API key copy. Requires HTTPS or localhost; adequate for production.
- **`navigator.sendBeacon`**: Used in monitoring library. Supported in all target browsers.
- **`CustomEvent`**: Used for Copilot, Search, Theme toggle commands. Universally supported.

### 3. Font Rendering
- **Font sources**: All fonts are self-hosted via `@fontsource` npm packages (`@fontsource/viga`, `@fontsource/ibm-plex-sans`, `@fontsource/ibm-plex-sans-arabic`, `@fontsource/ibm-plex-mono`).
- **Font format**: WOFF2 — supported in all modern browsers.
- **Fallback chains**:
  - Body: `var(--font-ui), var(--font-ui-arabic), sans-serif`
  - Headings: `var(--font-display), var(--font-ui-arabic), sans-serif`
  - RTL body: `var(--font-ui-arabic), var(--font-ui), sans-serif`
- **Font loading**: `@import` in CSS rather than `next/font` — fonts are imported via CSS `@fontsource` packages. In dev, Classic MUI-based approach. In production, they'll be bundled with Next.js CSS.
- **Risk**: `@fontsource/ibm-plex-sans-arabic` font family may not have Arabic glyph coverage in certain weights; however, the CSS `font-family` fallback chains are well-designed.

### 4. RTL Support
- **Locale detection**: Inline script in `layout.tsx` reads `localStorage` then falls back to `navigator.language` — immediately sets `dir` and `lang` attributes before first paint (no FOUC).
- **RTL CSS utilities**: Extensive set of custom utilities in `globals.css` covering:
  - Text alignment flips (`text-left` → `right`, `text-right` → `left`)
  - Margin/padding flips (`.ml-*` ↔ `.mr-*`, `.pl-*` ↔ `.pr-*`)
  - Border flips (`.border-l` ↔ `.border-r`)
  - Border radius flips (`.rounded-l` ↔ `.rounded-r`)
  - Transform flips (`.translate-x-*`, `.-translate-x-*`)
  - Float, origin, space, divide, inset utilities
- **Font switching**: RTL layout prefers `IBM Plex Sans Arabic` as primary font.
- **E2E tests**: Dedicated `e2e/09-rtl-layout.spec.ts` validates RTL direction, Arabic text rendering, sidebar labels, and placeholder support.
- **Tailwind RTL**: Tailwind's `start`/`end` utilities could complement the custom RTL approach but are not primary.

### 5. Polyfill Requirements
- **No `core-js`** or polyfill configuration found — not needed given the browserslist targets (`> 0.5%, last 2 versions, Firefox ESR, not dead`).
- **`ResizeObserver`** polyfill not included — all target browsers support it natively.
- **`IntersectionObserver`** used (in graph code) — natively supported in all target browsers.
- **`headers-polyfill`** is a transitive dependency via `msw` (mock service worker), not a runtime polyfill.

### 6. Vendor-prefixed CSS
Only 3 instances found — all appropriate and intentional:

| Location | Prefix | Purpose | Risk |
|----------|--------|---------|------|
| `globals.css:133` | `-webkit-text-size-adjust` | Prevent iOS auto-zoom | None — widely supported |
| `globals.css:139` | `-webkit-font-smoothing` | macOS antialiasing | None — cosmetic only |
| `globals.css:140` | `-moz-osx-font-smoothing` | macOS antialiasing | None — cosmetic only |

Autoprefixer in the PostCSS pipeline handles all other required vendor prefixes automatically.

---

## E2E Playwright Coverage

| Browser Project | Tests | Status |
|----------------|-------|--------|
| Chromium (Desktop Chrome) | 26 e2e specs | ✅ Configured |
| Firefox (Desktop Firefox) | 26 e2e specs | ✅ Configured |
| WebKit (Desktop Safari) | 26 e2e specs | ✅ Configured |
| Mobile Safari (iPhone 14) | 26 e2e specs | ✅ Configured |
| Visual Regression | 6 tests (light + dark) | ✅ Configured |

---

## Recommendations

### Low Priority (P3)
1. **Consider `start`/`end` Tailwind utilities**: The custom RTL utility class approach in `globals.css` works but is verbose. Migrating to Tailwind's built-in `inset-inline-start` / `margin-inline-end` / `padding-inline-start` logical properties would reduce maintenance. Not blocking — existing approach is correct.

2. **Font preloading**: Consider using `next/font` instead of CSS `@import` for font loading. `next/font` provides automatic preloading, reduced CLS, and better caching. Current approach works but may have suboptimal font-loading performance on slow connections.

3. **`navigator.clipboard` HTTPS warning**: The clipboard usage in settings page should check for HTTPS availability and provide a fallback for HTTP (dev environments). Currently not handled.

### No Action Required
- **ResizeObserver polyfill**: Not needed for target browsers. Monitor if users on Safari <13.1 are detected in analytics.
- **RTL approach**: The custom `[dir="rtl"]` utility classes are comprehensive and correct. No changes needed.
- **Vendor prefixing**: Autoprefixer + minimal intentional prefixes = adequate coverage.

---

## CI/CD Integration

Cross-browser testing is integrated into CI via Playwright:
- Branches: PRs trigger multi-browser tests
- Target: Chromium + Firefox + WebKit + Mobile Safari
- Visual regression: Screenshot comparisons for 6 core pages
- RTL tests: Run across all browser projects

No additional pipeline changes required.

---

*Report generated by Engineering OS — Gate G-8*
