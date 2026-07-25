# Accessibility Audit — Baseline

Sources: [10-design-audit](../../audit/current-state/10-design-audit.md), [DESIGN_STRATEGY](../../vnext/DESIGN_STRATEGY.md), Wave 13 crawl (`no_h1`).

**Target:** WCAG **2.2 AA**. Current: **gaps known** — not AA certified.

## Critical

| Issue | Detail | Fix in Program |
|-------|--------|----------------|
| Muted text contrast | `#A59E90` on white ≈ 2.9:1 | Token ≥ 4.5:1 (`design-system/accessibility.md`) |
| Missing h1 | 17 routes in crawl | PageHeader required |
| Login token mismatch | shadcn vars vs MUHIDE | DS V3 auth screens |

## High

| Issue | Fix |
|-------|-----|
| Focus rings must use `--focus-ring` consistently | DS foundations |
| Keyboard nav for data tables incomplete | Data Grid keyboard spec |
| Reduced motion not systematized | Motion System |
| Screen reader labels on icon-only controls | Component a11y rules |

## RTL / LTR

RTL support exists in legacy CSS — must remain first-class in v3 shell (dir attribute, logical properties, mirrored nav).

## Checklist for Design QA

- [ ] Contrast AA for text/icons
- [ ] Visible focus
- [ ] Skip link
- [ ] Landmark regions
- [ ] Form errors associated with inputs
- [ ] Dialog focus trap
- [ ] `prefers-reduced-motion`
- [ ] RTL smoke on shell + grid
