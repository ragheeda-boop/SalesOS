# Work Order WO-101 — Phase 1 Wave 1A: Core Components

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 0 (Sprint 0) ✅
> **Priority**: P0

---

## Scope

Build missing `@salesos/ui` form components and unify pagination.

## Tasks

| # | Task | Effort |
|---|------|--------|
| 1 | **Checkbox** — single + indeterminate, ARIA, RTL, error state | 1d |
| 2 | **Radio Group** — mutually exclusive, ARIA, RTL | 1d |
| 3 | **Switch** — boolean toggle, ARIA, RTL | 1d |
| 4 | **Textarea** — multi-line input, resize, ARIA, error state | 1d |
| 5 | **DatePicker** — date + range, keyboard nav, ARIA | 2d |
| 6 | **Pagination** — unify existing 3+ implementations into single component | 1d |
| 7 | Fix Badge `primary` variant to use `#F57C1E` (orange) | 0.5d |

## Assigned Engineer

`frontend-engineer`

## Reviewer

`performance-reviewer` (bundle impact)

## Deliverables

- All 5 form components in `@salesos/ui`
- Single `<Pagination>` component
- Badge fixed
- `SPRINT1_WAVE_1A_REPORT.md`

## Quality Gates

| Gate | Criteria |
|------|----------|
| G-1A.1 | Checkbox, Radio, Switch, Textarea, DatePicker render with ARIA + RTL + error states |
| G-1A.2 | Components are exported from `@salesos/ui` package |
| G-1A.3 | All inline pagination implementations replaced with unified `<Pagination>` |
| G-1A.4 | Badge `primary` shows `#F57C1E` |
| G-1A.5 | Frontend build succeeds |

---

**Engineering OS**: ✅ Approved
