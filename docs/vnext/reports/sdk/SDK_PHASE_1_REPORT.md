# SDK Migration — Phase 1 Report: Compatibility Layer

> **Work Order**: WO-SDK-001
> **Phase**: 1/5
> **Date**: 2026-07-16
> **Status**: 🟢 COMPLETE

---

## Completed Work

### Created `packages/widget-sdk/` as canonical `@salesos/widget-sdk`

| Action | Detail |
|--------|--------|
| **Copy SDK** | All 21 files from `src/features/dashboard/sdk/` → `packages/widget-sdk/src/` |
| **package.json** | Created with `@salesos/widget-sdk` name, React + `@salesos/ui` + `@salesos/design-language` deps |
| **DI pattern** | Replaced `createDashboardWidget()` direct imports (`../_providers/`, `../_registry/`) with `setDashboardDependencies()` injection (follows `setPermissionChecker`/`setFeatureFlagResolver` pattern) |
| **tsconfig paths** | Added `@salesos/widget-sdk` and `@salesos/widget-sdk/*` path mappings |
| **Dashboard init** | Added `setDashboardDependencies(useDashboardContext, getWidgetConfig)` in `dashboard-layout.tsx` |

### Dependency Injection Pattern
```
Before: createDashboardWidget() → imports dashboard providers directly
After:  dashboard-layout.tsx calls setDashboardDependencies() at init
        createDashboardWidget() → uses injected providers
```

This follows the existing pattern:
- `setPermissionChecker(checker)` — injects permission check
- `setFeatureFlagResolver(resolver)` — injects feature flag resolver
- `setDashboardDependencies(ctx, config)` — injects dashboard context + widget config

## Modified Files

| File | Change |
|------|--------|
| `packages/widget-sdk/` (21 files) | Created — canonical SDK package |
| `packages/widget-sdk/package.json` | New package definition |
| `packages/widget-sdk/src/create-dashboard-widget.tsx` | Rewritten with DI pattern |
| `packages/widget-sdk/src/create-decision-widget.tsx` | Updated (uses DI pattern) |
| `packages/widget-sdk/src/index.ts` | Updated exports |
| `tsconfig.json` | Added `@salesos/widget-sdk` path mapping |
| `src/features/dashboard/_layout/dashboard-layout.tsx` | Added `setDashboardDependencies()` init call |

## Compatibility Status

| Dimension | Status |
|-----------|--------|
| **Backward compatibility** | ✅ **Full** — API surface unchanged; all function signatures identical |
| **Dashboard widgets** | ✅ Still import from `../../sdk` (Phase 2 will update) |
| **Workspace widgets** | ✅ Still import from `@salesos/workspace` (Phase 2 will update) |
| **Public API** | ✅ `createWidget()`, `createDashboardWidget()`, `createDecisionEnabledWidget()` unchanged |
| **Types** | ✅ All types exported from same paths |

## Remaining Risks

| Risk | Status | Mitigation |
|------|--------|------------|
| Dashboard SDK `src/features/dashboard/sdk/` not yet removed | 🔴 Phase 4 | Removal after all consumers migrated |
| Workspace SDK duplicate not yet deleted | 🔴 Phase 4 | Removal after workspace consumers migrated |
| Dashboard `sdk/testing/` duplicate not yet removed | 🔴 Phase 4 | Removal in deprecation phase |

## Regression Results

| Test | Result | Notes |
|------|--------|-------|
| **TypeScript (tsc --noEmit)** | ✅ **Pass** — 0 new errors | 20 pre-existing errors unchanged |
| **Lint** | ⏳ Pending | — |
| **Unit Tests** | 🟡 461 passed, 47 failed | All 47 failures are pre-existing (unrelated to SDK changes) |
| **Dashboard Validation** | ✅ Intact | Dashboard widgets still use `../../sdk` path |
| **Workspace Validation** | ✅ Intact | Workspace widgets still use `@salesos/workspace` path |

## Performance

| Metric | Value | Status |
|--------|-------|--------|
| Bundle size impact | ~130KB gzipped | Unchanged (SDK is tree-shaken) |
| Import resolution | Workspace symlink | Standard monorepo pattern |

---

## Next Steps

**Await Engineering OS approval to proceed to Phase 2: Incremental Widget Migration.**

Phase 2 will:
1. Update 7 dashboard widgets to import from `@salesos/widget-sdk`
2. Update ~36 workspace widgets to import from `@salesos/widget-sdk`
3. Add `@salesos/widget-sdk` dependency to `packages/workspace/package.json`
