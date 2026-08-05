# Phase 07: Pending Migration Completion (ADR-100 execution, Phase 4 of 4)

## Date
2026-08-05

## Authority
[`ADR-100: Repository Canonicalization`](../docs/adr/0100-repository-canonicalization.md), Execution Order Phase 4. Preceded by a mandatory Pre-Migration Validation and Migration Impact Report — see `docs/architecture/MIGRATION_IMPACT_REPORT_widget_template.md`.

## Pre-migration validation (summary — full detail in the Impact Report)

Checked: imports, repo-wide references, documentation, build configuration (`tsconfig.json` include/exclude), workspaces (`package.json` workspaces glob), package manager (no `package.json` inside the template), Storybook (`stories` glob), tsconfig path aliases, CI workflow references.

**Result:** zero build-time, CI, or workspace dependency on the template's location in either direction — `salesos/frontend`'s workspace glob (`packages/*`), tsconfig `include`, and Storybook `stories` glob are all scoped relative to `salesos/frontend/` itself and never reached root `WidgetTemplate/` or root `packages/widget-template/` in the first place. The template's own `@/` and `@salesos/ui` imports only ever resolve once copied into `salesos/frontend/src/...`, per its own README's documented workflow — true before and after this move. 8 documentation references found (5 real broken links after move, 3 cosmetic mentions worth annotating for accuracy).

## What did we do?

### Moved: `WidgetTemplate/` → `packages/widget-template/`
All 7 files (`index.ts`, `README.md`, `types.ts`, `YourWidgetContainer.tsx`, `YourWidgetView.tsx`, `__tests__/WidgetTemplate.test.tsx`, `__tests__/YourWidget.test.tsx`) copied and verified byte-identical (`diff -rq` clean) before the empty root `WidgetTemplate/` was deleted.

### Updated (same atomic step, per instruction): 5 real broken references
- `salesos/frontend/docs/REFERENCE_WIDGET_GUIDE.md:603` — relative link `../../../../WidgetTemplate/` → `../../../../packages/widget-template/`
- `salesos/frontend/README.md:69` — `../../WidgetTemplate/` → `../../packages/widget-template/`
- `salesos/frontend/README.md:246` — `../../WidgetTemplate/` → `../../packages/widget-template/`
- `salesos/docs/portal/guides/creating-a-widget.md:22` — `cp -r WidgetTemplate/ ...` → `cp -r packages/widget-template/ ...`
- `salesos/docs/portal/guides/creating-a-widget.md:216` — table path updated

### Annotated (accuracy, not broken links): 3 files
- `salesos/docs/CURRENT_ARCHITECTURE.md:68` — tree-diagram leaf annotated with relocation note (rest of that diagram is separately, pre-existingly stale — not touched)
- `docs/audit/current-state/02-repository-map.md` (2 of 3 occurrences — the third sits inside a fixed-width ASCII box diagram and was left alone to avoid breaking its alignment)
- `docs/audit/current-state/17-current-progress.md:24`

## What did NOT change
- `salesos/frontend/package.json` workspaces glob — unchanged, never referenced this path
- `salesos/frontend/tsconfig.json` `include`/`paths` — unchanged, never referenced this path
- `salesos/frontend/.storybook/main.ts` `stories` glob — unchanged, never referenced this path
- `.github/workflows/*` — zero references before or after
- No code file's import statements were touched — all template imports are relative or app-scoped aliases, unaffected by the template's own location

## ⚠️ Anomaly discovered during post-migration validation (pre-existing, not caused by this phase)

Post-migration `git status` unexpectedly flagged three files as modified that this phase never touched: `salesos/frontend/package.json`, `salesos/frontend/tsconfig.json`, `salesos/frontend/jest.config.js`.

**Investigated and confirmed pre-existing:**
- File mtimes are `2026-08-05 21:14:17` (`package.json`) and `2026-08-05 15:56:57`–`15:57:00` (`tsconfig.json`, `jest.config.js`) — all **hours before** this session began (this session's own first file write is timestamped `22:07:43`). These changes predate any action taken across all four ADR-100 phases.
- `tsconfig.json` and `jest.config.js`: `git diff`/`git diff --raw` show **zero actual content difference** despite `git status` marking them modified — consistent with a stale git index entry (line-ending normalization or similar), not a real change.
- `package.json`: a genuine semantic diff exists — **one field**, `dependencies["@salesos/config"]`, changed from `"workspace:*"` to `"*"`. This is a real, pre-existing anomaly worth separate attention: `"workspace:*"` pins to the local monorepo package; a bare `"*"` would have npm attempt to resolve `@salesos/config` from a registry, which would fail for a private/internal package.

**This was not caused by, and is not part of, this migration.** Flagging it here because it surfaced during the post-migration build-configuration check this phase's validation mandate required — not remediating it, since it's outside Phase 4's scope and outside `salesos/` was supposed to remain untouched by every prior phase. Recommend a separate, dedicated look at `salesos/frontend/package.json`'s `@salesos/config` dependency.

## Post-migration validation

| Check | Result |
|---|---|
| Repository structure | `WidgetTemplate/` absent at root; `packages/widget-template/` present with all 7 files |
| Build configuration | Unaffected by this migration (see anomaly note above for an unrelated pre-existing item) |
| Package discovery | No `package.json` in the template before or after — nothing for npm/workspaces to gain or lose track of |
| Documentation links | All 5 real links re-verified resolving to `packages/widget-template/`; zero remaining references to the old `WidgetTemplate/` path outside historical/governance logs |
| Git status | Scoped to every path this phase touched: 6 modified docs, 1 new report, 1 new directory (`packages/widget-template/`) — exactly matches what was intentionally changed |

## Gate results
- [x] Pre-migration validation: PASS (Impact Report produced before any file operation)
- [x] References updated in the same atomic step: PASS (5 real links + 3 accuracy annotations)
- [x] Repository structure consistent post-migration: PASS
- [x] Build configuration consistent: PASS (pre-existing unrelated anomaly disclosed, not part of this migration)
- [x] Package discovery consistent: PASS
- [x] Documentation links consistent: PASS
- [x] Git status consistent with intended changes only: PASS

## Rollback procedure
```bash
# Restore WidgetTemplate/ at root
mkdir -p WidgetTemplate/__tests__
cp packages/widget-template/*.ts packages/widget-template/*.tsx packages/widget-template/README.md WidgetTemplate/
cp packages/widget-template/__tests__/*.tsx WidgetTemplate/__tests__/
rm -rf packages/widget-template

# Revert the 6 documentation edits
git checkout -- salesos/frontend/README.md salesos/frontend/docs/REFERENCE_WIDGET_GUIDE.md \
  salesos/docs/portal/guides/creating-a-widget.md salesos/docs/CURRENT_ARCHITECTURE.md \
  docs/audit/current-state/02-repository-map.md docs/audit/current-state/17-current-progress.md
```

## Notes
- **All four phases of ADR-100's approved execution order are now complete:** Phase 1 (Safe Cleanup), Phase 2 (Repository Documentation), Phase 3 (Legacy Isolation), Phase 4 (Pending Migration Completion).
- Remaining open items, none blocking: the Railway config conflict and `infrastructure/` disposition (both explicitly deferred, marked in Phase 3), the `salesos/`-internal hygiene items surfaced in the Health Gate (security-audit-report duplicates, `benchmark.db`, `.tmp-*` files), and now this newly surfaced `@salesos/config` dependency anomaly.
- Per explicit prior instruction: **Docker/Bootstrap work does not begin until repository canonicalization is complete.** Repository canonicalization (the four approved phases) is now complete — Docker/Bootstrap work can be considered on request, though the two deferred items above remain open governance questions independent of that.
