# Migration Impact Report — `WidgetTemplate/` → `packages/widget-template/`

**Date:** 2026-08-05
**Authority:** [`ADR-100`](../adr/0100-repository-canonicalization.md), Phase 4 (Pending Migration Completion)
**Status:** Pre-migration validation complete. Migration not yet executed pending this report.

## Validation checklist

| Dimension | Method | Result |
|---|---|---|
| **Imports** | Read all 6 source files (`index.ts`, `types.ts`, `YourWidgetContainer.tsx`, `YourWidgetView.tsx`, 2× `__tests__/*.test.tsx`); checked every `import`/`require` | All internal imports are relative (`./YourWidgetView`, `./types`, `../YourWidgetView`, `../types`) — **location-independent, safe under any move.** Two imports use aliases: `@/features/dashboard/sdk` and `@salesos/ui`. Neither alias resolves from `WidgetTemplate/`'s current root location or from `packages/widget-template/` — see Build Configuration below. |
| **References** (repo-wide) | Grep for literal string `WidgetTemplate` across the full repo | 21 files match. Classified below into Fix Required / No Fix Needed. |
| **Documentation** | Read every doc match in context | 5 files contain **real, resolvable relative-path links or bash commands** that break after the move (Fix Required). 6 files contain bare directory-name mentions in prose/tables/tree diagrams that name the directory but aren't clickable links (Fix Recommended for accuracy, lower severity). Remaining matches are conceptual/historical, no path involved (No Fix Needed). |
| **Build configuration** | Read `salesos/frontend/tsconfig.json` `include`/`exclude`, `jest.config.js` | `tsconfig.json` `include: ["**/*.ts", "**/*.tsx", ...]` is resolved relative to `salesos/frontend/` itself — `WidgetTemplate/` (root) and `packages/widget-template/` (root) are **both outside this scope**, in both the old and new location. **No change in build inclusion either way.** `jest.config.js` has no path referencing `WidgetTemplate`. |
| **Workspaces** | Read `salesos/frontend/package.json` `workspaces` field | `"workspaces": ["packages/*"]` — resolved relative to `salesos/frontend/`, i.e. `salesos/frontend/packages/*`. Root `packages/widget-template/` (the destination) is a **different `packages/` directory entirely** and is not, and was never going to be, part of this workspace glob. No change. |
| **Package manager** | Checked for a `package.json` inside `WidgetTemplate/` | None exists — it is raw template source, not an installable package. Nothing for npm to discover or lose track of in either location. |
| **Storybook** | Read `salesos/frontend/.storybook/main.ts` `stories` glob | Scoped to `../packages/ui/src/**/*.stories.*`, `../packages/charts/src/**/*.stories.*` (relative to `salesos/frontend/`, i.e. `salesos/frontend/packages/*`) — does not reach root `WidgetTemplate/` or root `packages/widget-template/` in either location. No `.stories.tsx` file exists in the template today despite `ARCHITECTURE_BOOK.md` describing one conceptually (pre-existing doc/reality mismatch, not caused by this move — not corrected here, out of scope). |
| **tsconfig paths** | Read `salesos/frontend/tsconfig.json` `paths` | `@/*` → `./src/*`, plus `@salesos/decision-platform`, `@salesos/widget-sdk` aliases — none reference `WidgetTemplate` or `packages/widget-template`. The template's own `@/features/dashboard/sdk` and `@salesos/ui` imports only resolve once the template is **copied into** `salesos/frontend/src/...` (per its own README's documented workflow) — this is true today and remains true after the move. No regression. |
| **CI references** | Grep `.github/workflows/` for `WidgetTemplate` | Zero matches. No CI job references this path. |

## Files requiring update (Fix Required — real broken links after move)

| File | Line(s) | Current | Updated to |
|---|---|---|---|
| `salesos/frontend/docs/REFERENCE_WIDGET_GUIDE.md` | 603 | `[WidgetTemplate](../../../../WidgetTemplate/)` | `[WidgetTemplate](../../../../packages/widget-template/)` |
| `salesos/frontend/README.md` | 69 | `` Start from `../../WidgetTemplate/` `` | `` Start from `../../packages/widget-template/` `` |
| `salesos/frontend/README.md` | 246 | `[Widget Template](../../WidgetTemplate/)` | `[Widget Template](../../packages/widget-template/)` |
| `salesos/docs/portal/guides/creating-a-widget.md` | 22 | `cp -r WidgetTemplate/ src/widgets/company-health/` | `cp -r packages/widget-template/ src/widgets/company-health/` |
| `salesos/docs/portal/guides/creating-a-widget.md` | 216 | `` \| Widget Template \| `WidgetTemplate/` in repository \| `` | `` \| Widget Template \| `packages/widget-template/` in repository \| `` |

## Files updated for accuracy (bare directory-name mentions — not broken links, but now stale)

| File | Line(s) | Action |
|---|---|---|
| `salesos/docs/CURRENT_ARCHITECTURE.md` | 68 | Tree-diagram leaf updated with a relocation note. Rest of that tree diagram is separately stale (still shows `balady_scraper/`, `output/`, `open-design/` at root, pre-dating `migration-log/phase-03.md`) — **not fixed here**, out of scope for this migration's report. |
| `docs/audit/current-state/02-repository-map.md` | 18, 606, 705 | Snapshot audit doc, same treatment as `15-documentation-audit.md` in Phase 2: path annotated with relocation note, original entry preserved for historical accuracy. |
| `docs/audit/current-state/17-current-progress.md` | 24 | Path annotated with relocation note. |

## Files with no fix needed (conceptual mentions, no resolvable path)

`docs/audit/execution/04-design-ux-fixes.md`, `docs/audit/05-design-system.md`, `docs/COMPLIANCE_AUDIT_REPORT.md`, `salesos/docs/ARCHITECTURE_BOOK.md` — all reference "WidgetTemplate" as a naming convention or concept in prose/tables, not as a clickable path. `ARCHITECTURE_BOOK.md` additionally describes a hypothetical file-naming scheme (`WidgetTemplateContainer.tsx`, `WidgetTemplate.stories.tsx`) that doesn't match the actual current files (`YourWidgetContainer.tsx`, no `.stories.tsx`) — a pre-existing doc/reality mismatch unrelated to this move, not corrected here.

Governance/historical files (`migration-log/*`, `REPO_TOPOLOGY_AUDIT.md`, `docs/adr/0100-*.md`, `docs/architecture/LEGACY_ISOLATION_REGISTER.md`, `docs/audit/REPOSITORY_HEALTH_GATE_2026-08-05.md`, `.engineering/*`) are point-in-time records of prior phases or generated content — not live-updated; this migration's own record will be `migration-log/phase-07.md`.

## Conclusion

**References exist.** Per instruction, they will be updated in the same atomic step as the migration itself — no separate commit. Migration is low-risk: zero build-time or CI dependency on the current path in either direction; all breakage is confined to 5 documentation links (real) plus 3 doc mentions (cosmetic accuracy).

**Proceeding with migration.**
