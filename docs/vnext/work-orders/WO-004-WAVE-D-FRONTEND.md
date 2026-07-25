# Work Order WO-004 — Wave D: Frontend Stabilization

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependencies**: None (independent of Waves B, C)
> **Priority**: P1 — High

---

## Wave ID

WO-004 / WAVE-D

## Objective

Fix frontend design system issues: token consistency, chart colors, login page, accessibility, deprecated components.

## Scope

Strictly limited to frontend fixes:

1. **DSG-03** — Muted text contrast: update `--text-muted` from `#A59E90` (2.9:1) to `#8C8374` (4.56:1)
2. **DSG-06** — Remove deprecated Foundation Card component after migrating all consumers
3. **DSG-01** — Login page: refactor to use `@salesos/ui` components (Button, Input, Card)
4. **DSG-02** — Chart colors: replace hardcoded `#3B82F6` with MUHIDE `--chart-*` tokens starting with `#F57C1E`
5. **FE-02** — ESLint rule: forbid Tailwind color classes in page components

## Assigned Engineer

`frontend-engineer`

## Assigned Reviewer

`performance-reviewer` (for bundle impact) + `security-reviewer` (a11y is close enough)

## Expected Deliverables

| Deliverable | Description |
|-------------|-------------|
| `--text-muted` updated | Changed from `#A59E90` to `#8C8374` in `globals.css`; all surfaces verified ≥ 4.5:1 |
| Deprecated Card removed | All imports migrated to `@salesos/ui#Card`; Foundation Card deleted |
| Login page refactored | Uses `@salesos/ui` Button, Input, Card; MUHIDE tokens confirmed |
| Chart colors fixed | `--chart-1` through `--chart-12` tokens added; hardcoded `#3B82F6` replaced |
| ESLint rule added | Forbids Tailwind color classes (`text-neutral-*`, `bg-neutral-*`) in page components |
| `SPRINT0_WAVE_D_REPORT.md` | Final report documenting all changes |

## Quality Gates

| Gate | Criteria |
|------|----------|
| G-D.1 | `--text-muted` passes WCAG AA (≥ 4.5:1 contrast) |
| G-D.2 | No imports remain pointing to deprecated `foundation/card.tsx` |
| G-D.3 | Login page uses `@salesos/ui` Button, Input, Card components |
| G-D.4 | Chart colors sequence starts with `#F57C1E` (orange) |
| G-D.5 | ESLint rule catches `text-neutral-*` / `bg-neutral-*` in page files |
| G-D.6 | All existing frontend tests pass |
| G-D.7 | Frontend build succeeds (`npm run build` or equivalent) |

## Stop Condition

Wave D is complete when all deliverables are produced and quality gates pass.

## Constraints

- Do NOT modify backend code
- Do NOT implement new features
- Do NOT touch Agent Runtime, Dashboard, or widget logic
- All changes must be backward-compatible

## Dependencies

None — Wave D is fully independent.

---

**Engineering OS Authorization**: ✅ Approved
