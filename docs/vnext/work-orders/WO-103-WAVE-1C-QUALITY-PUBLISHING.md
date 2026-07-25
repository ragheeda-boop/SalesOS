# Work Order WO-103 — Phase 1 Wave 1C: Quality & Publishing

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: WO-101 (Core Components) — components needed for Storybook
> **Priority**: P1

---

## Scope

Testing infrastructure, codemod, package publishing, and form validation.

## Tasks

| # | Task | Effort | Dependency |
|---|------|--------|------------|
| 1 | **CSS variable codemod** — auto-migrate `text-neutral-*` → `var(--text-*)` | 3d | None |
| 2 | **Form validation** — React Hook Form + Zod, `FormField` wrapper | 3d | WO-101 (form components) |
| 3 | **Storybook** — visual documentation for all components | 3d | WO-101 (components) |
| 4 | **a11y tests** — `jest-axe` automated assertions | 1d | WO-101 (components) |
| 5 | **Token package v2.0-alpha** — publish `@salesos/design-language@2.0.0-alpha` | 2d | None |
| 6 | **Visual regression tests** — Playwright screenshot comparison | 1w (partial) | WO-101 + WO-102 |
| 7 | **Form layout primitives** — Form, FormSection, FormRow, FormField | 2d | WO-101 (form components) |

## Assigned Engineer

`frontend-engineer`

## Reviewer

`qa-engineer`

## Deliverables

- Codemod script
- Form validation integration
- Storybook setup
- a11y test suite
- Token package v2.0-alpha
- Visual regression test foundation
- `SPRINT1_WAVE_1C_REPORT.md`

## Quality Gates

| Gate | Criteria |
|------|----------|
| G-1C.1 | Storybook shows all components |
| G-1C.2 | a11y tests pass |
| G-1C.3 | Visual regression compares against baseline |
| G-1C.4 | `@salesos/design-language@2.0.0-alpha` published |
| G-1C.5 | Frontend build succeeds |
| G-1C.6 | Codemod script documented |

---

**Engineering OS**: ✅ Approved
