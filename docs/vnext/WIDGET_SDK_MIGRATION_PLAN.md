# Widget SDK Migration Plan

> **Reference**: ADR-0032 (Approved)
> **Status**: Planned — awaiting executive approval for execution
> **Date**: 2026-07-16

---

## Overview

Consolidate two Widget SDKs into one canonical package at `packages/widget-sdk/`.

### Current State

```
src/features/dashboard/sdk/          ← Dashboard SDK (canonical per ADR-003)
  ├── create-widget.tsx               ← Generic widget factory
  ├── create-dashboard-widget.tsx     ← Dashboard-context factory
  ├── create-decision-widget.tsx      ← Decision-enabled factory
  ├── types.ts                        ← Widget types + Decision types
  ├── widget-lifecycle.ts             ← Lifecycle hooks
  ├── widget-telemetry.ts             ← Telemetry
  ├── widget-permissions.ts           ← Permissions
  ├── widget-feature-flags.ts         ← Feature flags
  ├── testing/                        ← Testing utilities
  ├── contract-test-utils.ts          ← Contract test helper
  ├── index.ts                        ← Public exports
  └── README.md                       ← Documentation

packages/workspace/src/              ← Workspace SDK (duplicate fork)
  ├── create-widget.tsx               ← DUPLICATE ← DELETE
  ├── create-workspace-widget.tsx     ← Extension (thin wrapper) ← RETAIN
  ├── types.ts                        ← DUPLICATE ← DELETE
  ├── widget-lifecycle.ts             ← DUPLICATE ← DELETE
  ├── widget-telemetry.ts             ← DUPLICATE ← DELETE
  ├── widget-permissions.ts           ← DUPLICATE ← DELETE
  ├── widget-feature-flags.ts         ← DUPLICATE ← DELETE
  ├── testing/
  │   ├── WidgetContract.tsx          ← DUPLICATE ← DELETE
  │   ├── renderWidget.tsx            ← DUPLICATE ← DELETE
  │   ├── mockWidgetContext.ts         ← DUPLICATE ← DELETE (keep createEmptyWidget)
  │   ├── mockPermissions.ts          ← DUPLICATE ← DELETE
  │   ├── mockFeatureFlags.ts         ← DUPLICATE ← DELETE
  │   └── mockTelemetry.ts            ← UNIQUE ← RETAIN
  ├── workspace-provider.tsx          ← UNIQUE ← RETAIN
  ├── workspace-grid.tsx              ← UNIQUE ← RETAIN
  ├── workspace-registry.ts           ← UNIQUE ← RETAIN
  ├── workspace-error-boundary.tsx    ← UNIQUE ← RETAIN
  ├── workspace-loading.tsx           ← UNIQUE ← RETAIN
  ├── renderer.tsx                    ← UNIQUE ← RETAIN
  ├── generator.ts                    ← UNIQUE ← RETAIN
  ├── presets.ts                      ← UNIQUE ← RETAIN
  ├── derive-status.ts                ← UNIQUE ← RETAIN
  ├── global-activity-feed.tsx        ← UNIQUE ← RETAIN
  ├── universal-inbox.tsx             ← UNIQUE ← RETAIN
  ├── revenue-command-center.tsx      ← UNIQUE ← RETAIN
  ├── ai-operating-assistant.tsx      ← UNIQUE ← RETAIN
  └── index.ts                        ← UPDATE (remove deleted exports)
```

### Target State

```
packages/widget-sdk/                  ← Canonical Widget SDK (moved from dashboard)
  ├── create-widget.tsx               ← With Arabic labels added (from workspace)
  ├── create-dashboard-widget.tsx     ← Dashboard-context factory
  ├── create-decision-widget.tsx      ← Decision-enabled factory
  ├── types.ts                        ← Widget types + Decision types
  ├── widget-lifecycle.ts             ← Lifecycle hooks
  ├── widget-telemetry.ts             ← Telemetry
  ├── widget-permissions.ts           ← Permissions
  ├── widget-feature-flags.ts         ← Feature flags
  ├── testing/                        ← Testing utilities (consolidated)
  ├── contract-test-utils.ts          ← Contract test helper
  ├── index.ts                        ← Public exports
  ├── package.json                    ← @salesos/widget-sdk
  └── README.md                       ← Documentation

packages/workspace/src/              ← Workspace (consumer, not provider of widget SDK)
  ├── create-workspace-widget.tsx     ← Extension: wraps createWidget() from @salesos/widget-sdk
  ├── workspace-provider.tsx          ← RETAINED
  ├── workspace-grid.tsx              ← RETAINED
  ├── workspace-registry.ts           ← RETAINED
  ├── workspace-error-boundary.tsx    ← RETAINED
  ├── workspace-loading.tsx           ← RETAINED
  ├── renderer.tsx                    ← RETAINED
  ├── generator.ts                    ← RETAINED
  ├── presets.ts                      ← RETAINED
  ├── derive-status.ts                ← RETAINED
  ├── testing/
  │   └── mockTelemetry.ts            ← RETAINED (workspace-specific)
  ├── [components].tsx                ← RETAINED
  ├── index.ts                        ← UPDATED (no longer exports createWidget etc.)
  └── package.json                    ← ADD @salesos/widget-sdk as dependency
```

---

## Migration Phases

### Phase 1: Create `packages/widget-sdk/` (0.5d)

**Action**: Copy `src/features/dashboard/sdk/` → `packages/widget-sdk/src/`

**Files**:
| Source | Target |
|--------|--------|
| `src/features/dashboard/sdk/create-widget.tsx` | `packages/widget-sdk/src/create-widget.tsx` |
| `src/features/dashboard/sdk/create-dashboard-widget.tsx` | `packages/widget-sdk/src/create-dashboard-widget.tsx` |
| `src/features/dashboard/sdk/create-decision-widget.tsx` | `packages/widget-sdk/src/create-decision-widget.tsx` |
| `src/features/dashboard/sdk/types.ts` | `packages/widget-sdk/src/types.ts` |
| `src/features/dashboard/sdk/widget-lifecycle.ts` | `packages/widget-sdk/src/widget-lifecycle.ts` |
| `src/features/dashboard/sdk/widget-telemetry.ts` | `packages/widget-sdk/src/widget-telemetry.ts` |
| `src/features/dashboard/sdk/widget-permissions.ts` | `packages/widget-sdk/src/widget-permissions.ts` |
| `src/features/dashboard/sdk/widget-feature-flags.ts` | `packages/widget-sdk/src/widget-feature-flags.ts` |
| `src/features/dashboard/sdk/testing/` | `packages/widget-sdk/src/testing/` |
| `src/features/dashboard/sdk/contract-test-utils.ts` | `packages/widget-sdk/src/contract-test-utils.ts` |
| `src/features/dashboard/sdk/index.ts` | `packages/widget-sdk/src/index.ts` |
| `src/features/dashboard/sdk/README.md` | `packages/widget-sdk/README.md` |

**Add Arabic labels** to `packages/widget-sdk/src/create-widget.tsx`:
- Import `STATUS_LABEL` and `STATUS_COLOR` (from Workspace SDK's version)
- These are bilingual labels required for Saudi market; keep them in the canonical SDK

**Create `package.json`**:
```json
{
  "name": "@salesos/widget-sdk",
  "version": "1.0.0",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "dependencies": {
    "react": "^19.0",
    "@salesos/ui": "*",
    "@salesos/design-language": "*"
  }
}
```

**Verify**: `npx tsc --noEmit` passes for the new package.

### Phase 2: Update Dashboard SDK Consumers (0.5d)

**Action**: Update 7 dashboard widgets + related tests to import from `@salesos/widget-sdk`

**Consumers to update**:

| File | Old Import | New Import |
|------|-----------|------------|
| `src/features/dashboard/widgets/ai-brief/AIBriefContainer.tsx` | `'../../sdk'` | `'@salesos/widget-sdk'` |
| `src/features/dashboard/widgets/market-pulse/MarketPulseContainer.tsx` | `'../../sdk'` | `'@salesos/widget-sdk'` |
| `src/features/dashboard/widgets/intelligence-feed/IntelligenceFeedContainer.tsx` | `'../../sdk'` | `'@salesos/widget-sdk'` |
| `src/features/dashboard/widgets/recent-activity/RecentActivityContainer.tsx` | `'../../sdk'` | `'@salesos/widget-sdk'` |
| `src/features/dashboard/widgets/decision-queue/DecisionQueueContainer.tsx` | `'../../sdk'` | `'@salesos/widget-sdk'` |
| `src/features/dashboard/widgets/company-health/CompanyHealthContainer.tsx` | `'../../sdk'` | `'@salesos/widget-sdk'` |
| `src/features/dashboard/widgets/pipeline/PipelineContainer.tsx` | `'../../sdk'` | `'@salesos/widget-sdk'` |
| 7x `__tests__/*.test.tsx` files | `'../../../sdk/testing'` | `'@salesos/widget-sdk/testing'` |

**Also update SDK-internal imports** (within the SDK itself — relative paths stay):
- No changes needed — internal imports remain relative

**Verify**: All 7 dashboard widget tests pass.

### Phase 3: Update Workspace SDK — Remove Duplicates (0.5d)

**Action**: Delete duplicated files from `packages/workspace/src/`

**Files to DELETE**:
- `packages/workspace/src/create-widget.tsx` (replaced by `@salesos/widget-sdk`)
- `packages/workspace/src/types.ts` (replaced by `@salesos/widget-sdk`)
- `packages/workspace/src/widget-lifecycle.ts` (replaced by `@salesos/widget-sdk`)
- `packages/workspace/src/widget-telemetry.ts` (replaced by `@salesos/widget-sdk`)
- `packages/workspace/src/widget-permissions.ts` (replaced by `@salesos/widget-sdk`)
- `packages/workspace/src/widget-feature-flags.ts` (replaced by `@salesos/widget-sdk`)
- `packages/workspace/src/testing/WidgetContract.tsx` (replaced by `@salesos/widget-sdk/testing`)
- `packages/workspace/src/testing/renderWidget.tsx` (replaced by `@salesos/widget-sdk/testing`)
- `packages/workspace/src/testing/mockWidgetContext.ts` (replaced)
- `packages/workspace/src/testing/mockPermissions.ts` (replaced)
- `packages/workspace/src/testing/mockFeatureFlags.ts` (replaced)

**Files to UPDATE**:
- `packages/workspace/src/create-workspace-widget.tsx` — change import from `'./create-widget'` to `'@salesos/widget-sdk'`
- `packages/workspace/src/index.ts` — remove exports for deleted files; keep workspace-unique exports
- `packages/workspace/src/testing/index.ts` — keep only `mockTelemetry.ts` export (workspace-specific)

**Package dependencies**:
- Add `"@salesos/widget-sdk": "*"` to `packages/workspace/package.json`

### Phase 4: Update Workspace SDK Consumers (1d)

**Action**: Update ~36 workspace widget imports

**Pattern**: All workspace widgets import from `@salesos/workspace`:
```typescript
import { createWidget } from '@salesos/workspace'
// Change to:
import { createWidget } from '@salesos/widget-sdk'
```

```typescript
import { createWorkspaceWidget } from '@salesos/workspace'
// This stays the same — createWorkspaceWidget is exported from @salesos/workspace
```

**Consumers to update** (37 files):

| Feature | Files | Change |
|---------|-------|--------|
| company-intelligence (9) | SmartTimeline, SignalsFeed, DecisionMakers, BuyingJourney, CompanyDNA, RelationshipGraph, AIRecommendation, DocumentIntelligence, GovernmentIntelligence, GoldenRecord | `createWidget` import → `@salesos/widget-sdk` |
| employee-intelligence (6) | KPIWidget, ActivityIntelligence, EmployeeProfile, EmployeePortfolio, CalendarIntelligence, EmailIntelligence, AICoach | `createWorkspaceWidget` stays; `createWidget` → `@salesos/widget-sdk` |
| revenue-execution (18+) | Territory, Churn, Expansion, Pipeline, MultiWorkspace, API, Task, MCP, RevenueTimeline, Security, NBA, OpportunityDetail, Meeting, RevenueHealth, OpportunityList, Marketplace, Email, Playbook, Forecast | `createWidget` import → `@salesos/widget-sdk` |
| Other | AnalyticsContainer, company-intelligence-provider, EmployeeWorkspace, company-intelligence-layout, end-to-end test | Varied imports → `@salesos/widget-sdk` |

### Phase 5: Update Testing Infrastructure (0.5d)

**Action**: All widget tests that import `describeWidgetContract` change to `@salesos/widget-sdk`

| Current Import | New Import |
|---------------|------------|
| `from '../../../sdk/testing'` (dashboard widgets) | `from '@salesos/widget-sdk/testing'` |
| `from '@salesos/workspace'` (testing re-exports) | `from '@salesos/widget-sdk/testing'` |

### Phase 6: Add CI Enforcement (0.5d)

**Add CI checks**:
1. **Duplicate `createWidget()` scan** — ensure only one export exists in the codebase
2. **Import restriction** — ESLint rule: workspace widgets must import `createWidget` from `@salesos/widget-sdk`, not from `@salesos/workspace`
3. **File existence check** — `packages/workspace/src/create-widget.tsx` must not exist
4. **Import path audit** — no widget imports from `features/dashboard/sdk/`

### Phase 7: Clean Up (0.5d)

**Action**: Post-migration cleanup
1. Remove `src/features/dashboard/sdk/` directory (no longer needed)
2. Update `tsconfig.json` paths if needed
3. Update any build configuration referencing old paths
4. Run full test suite to verify zero regressions
5. Update REFERENCE_WIDGET_GUIDE.md with new import paths

---

## Affected Packages

| Package | Impact | Action |
|---------|--------|--------|
| `packages/widget-sdk` (NEW) | Created | New canonical SDK package |
| `packages/workspace` | Modified | Remove duplicated files; add dependency |
| `src/features/dashboard/sdk` | DELETED | Moved to `packages/widget-sdk` |
| `src/features/dashboard/widgets/*` | Modified | Import path changes (7 files) |
| `src/features/company-intelligence/widgets/*` | Modified | Import path changes (9 files) |
| `src/features/employee-intelligence/widgets/*` | Modified | Import path changes (6 files) |
| `src/features/revenue-execution/widgets/*` | Modified | Import path changes (18+ files) |

---

## Affected APIs

No API changes. All exported functions and types retain identical signatures:
- `createWidget<T>(config: WidgetConfig<T>): ComponentType` — unchanged
- `createDashboardWidget<T>(id, overrides)` — unchanged
- `createDecisionEnabledWidget<T>(id, overrides)` — unchanged
- `describeWidgetContract<T>(cfg)` — unchanged
- All types (`WidgetStatus`, `WidgetConfig`, `WidgetMetadata`, etc.) — unchanged

---

## Compatibility Layer

Not needed. The migration is purely an import path change. All consumers update their import source in one phase; there is no transition period where both SDKs coexist.

**Exception**: During the window between Phase 2 (dashboard done) and Phase 4 (workspace done), the workspace widgets still import from `@salesos/workspace`, which re-exports from the deleted files. To handle this, either:
1. Execute Phases 3-4 atomically (preferred — risk: moderate timing), or
2. Add temporary re-exports in `@salesos/workspace` that forward to `@salesos/widget-sdk`

Option 2 is safer:
```typescript
// packages/workspace/src/index.ts — temporary re-exports
export { createWidget, ... } from '@salesos/widget-sdk'
```
These re-exports are removed after all consumers are updated.

---

## Rollback Strategy

If migration causes issues:

1. **Revert Phase 1**: Delete `packages/widget-sdk/`, restore `src/features/dashboard/sdk/`
2. **Revert Phase 2-3**: Restore deleted workspace files via git checkout
3. **Revert Phase 4**: Revert import changes via `git revert`
4. **Total rollback time**: ~30 minutes (all changes in working tree)

**Condition for rollback**: >5 failing tests directly caused by the migration (not pre-existing failures).

---

## Validation Plan

| Check | Tool | Criteria |
|-------|------|----------|
| TypeScript compilation | `npx tsc --noEmit` | 0 errors |
| Lint | `npx eslint` | 0 errors |
| Unit tests | `npx jest` / `pytest` | 100% pass rate |
| Widget contract tests | `describeWidgetContract` suites | All 10+ suites pass |
| Import audit | Custom script | No imports from old paths |
| Duplicate scan | Custom script | Exactly 1 `createWidget()` export |
| E2E tests | Playwright | All critical paths pass |

---

## Timeline

| Phase | Effort | Dependencies | Can parallelize? |
|-------|--------|-------------|-----------------|
| P1: Create `packages/widget-sdk/` | 0.5d | None | Yes |
| P2: Update dashboard consumers | 0.5d | P1 | With P3 |
| P3: Remove workspace duplicates | 0.5d | P1 | With P2 |
| P4: Update workspace consumers | 1d | P3 | No (after P3) |
| P5: Update testing infrastructure | 0.5d | P2, P4 | No |
| P6: Add CI enforcement | 0.5d | P5 | No |
| P7: Clean up | 0.5d | P5 | No |

**Total**: ~4 days (can be 2.5 days with P2+P3 parallelized)

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Import resolution fails for new package | Low | High | Test with `npx tsc --noEmit` in CI |
| Workspace consumers miss import update | Medium | Medium | Automated grep scan; CI import audit |
| Behavioral diff between old/new `createWidget()` | Low | Medium | Contract tests verify identical behavior |
| Workspace widgets use `@salesos/workspace` re-exports | Low | Low | Remove re-exports after Phase 4; CI enforces direct import |
| Arabic labels lost in canonical SDK | Low | Low | R1 refinement explicitly preserves them |

---

*Plan approved by Engineering OS. Awaiting executive authorization to execute.*
