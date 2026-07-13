# 17 — Widget Migration to DecisionProvider & SDK Adoption

> Date: 2026-07-13
> Status: ✅ Complete
> Scope: Widget SDK migration, DecisionProvider integration, new widget creation

---

## Executive Summary

Migrated existing dashboard widgets to use `createDecisionEnabledWidget()`, created two new SDK-based widgets (Pipeline, CompanyHealth), and produced comprehensive documentation for future widget development.

---

## Files Created

| File | Purpose |
|------|---------|
| `salesos/docs/WIDGET_MIGRATION_GUIDE.md` | Step-by-step migration guide with before/after examples |
| `salesos/frontend/src/features/dashboard/sdk/README.md` | API reference for all SDK functions |
| `salesos/frontend/src/features/dashboard/widgets/pipeline/PipelineContainer.tsx` | Pipeline widget — decision-enabled |
| `salesos/frontend/src/features/dashboard/widgets/pipeline/PipelineView.tsx` | Pipeline view with stage bars, deal list, virtualization |
| `salesos/frontend/src/features/dashboard/widgets/pipeline/types.ts` | Pipeline types |
| `salesos/frontend/src/features/dashboard/widgets/pipeline/index.ts` | Barrel export |
| `salesos/frontend/src/features/dashboard/widgets/pipeline/__tests__/Pipeline.test.tsx` | Contract + unit tests (15 tests) |
| `salesos/frontend/src/features/dashboard/widgets/company-health/CompanyHealthContainer.tsx` | Company Health widget — decision-enabled |
| `salesos/frontend/src/features/dashboard/widgets/company-health/CompanyHealthView.tsx` | Company Health view with score ring, metrics, alerts |
| `salesos/frontend/src/features/dashboard/widgets/company-health/types.ts` | Company Health types |
| `salesos/frontend/src/features/dashboard/widgets/company-health/index.ts` | Barrel export |
| `salesos/frontend/src/features/dashboard/widgets/company-health/__tests__/CompanyHealth.test.tsx` | Contract + unit tests (17 tests) |

## Files Modified

| File | Change |
|------|--------|
| `widgets/decision-queue/DecisionQueueContainer.tsx` | Migrated from `createDashboardWidget` → `createDecisionEnabledWidget` |
| `widgets/decision-queue/types.ts` | Added `decision`, `nbaItems`, `isDecisionLoading` props |
| `widgets/decision-queue/DecisionQueueView.tsx` | Added skeleton loading, decision summary, NBA items, aria-live |
| `widgets/decision-queue/__tests__/DecisionQueue.test.tsx` | Added DecisionProvider integration tests |
| `_registry/widget-config.ts` | Added `pipeline` and `companyHealth` WidgetId entries |
| `widget-registry.tsx` | Added Pipeline and CompanyHealth to registry with error boundaries |
| `application/dashboard/dashboard.dto.ts` | Added `PipelineDTOData` and `CompanyHealthDTOData` DTOs |

---

## Migration Details

### 1. DecisionQueue Widget — Migrated

**Before:** `createDashboardWidget<DecisionQueueData>('decisionQueue', {...})`
**After:** `createDecisionEnabledWidget<DecisionQueueData>('decisionQueue', {...})`

Added:
- `useDecision: (tenantId) => useCompanyDecision(tenantId)`
- `useNBA: () => useNBAFeed()`
- Skeleton loading state (`SkeletonRows` component)
- Decision summary banner (`DecisionSummary` component)
- NBA items section in view
- `aria-live="polite"` for count updates
- RTL support via CSS variables

### 2. Pipeline Widget — New

- `createDecisionEnabledWidget<PipelineData>('pipeline', {...})`
- Stage progress bars with `role="progressbar"` and aria-valuenow
- Deal list with keyboard navigation
- Virtualization for >50 deals
- Skeleton loading state
- Decision summary + NBA items

### 3. Company Health Widget — New

- `createDecisionEnabledWidget<CompanyHealthData>('companyHealth', {...})`
- SVG score ring with dynamic color
- Health metrics with trend indicators (up/down/stable)
- Alerts with severity levels (critical/warning/info)
- `aria-label` on all interactive elements
- Skeleton loading state
- Decision summary + NBA items

---

## SDK Adoption Status

| Widget | Factory | DecisionProvider | Error Boundary | Contract Tests |
|--------|---------|-----------------|----------------|----------------|
| Mission Center | `createDashboardWidget` | — | ✅ `withErrorBoundary` | ✅ |
| **Decision Queue** | **`createDecisionEnabledWidget`** | **✅ `useCompanyDecision`** | ✅ | ✅ |
| Intelligence Feed | `createDashboardWidget` | — | ✅ | ✅ |
| AI Brief | `createDashboardWidget` | — | ✅ | ✅ |
| Market Pulse | `createDashboardWidget` | — | ✅ | ✅ |
| Recent Activity | `createDashboardWidget` | — | ✅ | ✅ |
| **Pipeline** | **`createDecisionEnabledWidget`** | **✅ `useCompanyDecision`** | ✅ | ✅ |
| **Company Health** | **`createDecisionEnabledWidget`** | **✅ `useCompanyDecision`** | ✅ | ✅ |

**Total widgets:** 8 (6 existing + 2 new)
**Decision-enabled:** 3 (Decision Queue, Pipeline, Company Health)
**All use SDK:** ✅
**All have error boundaries:** ✅
**All have contract tests:** ✅

---

## Accessibility Compliance

| Widget | role="region" | aria-live | keyboard nav | motion-reduce | dark mode | RTL |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| Decision Queue | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pipeline | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Company Health | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Testing

| Metric | Value |
|--------|-------|
| New tests created | ~32 |
| Contract test suites | 2 (Pipeline, Company Health) |
| Existing tests updated | 1 (Decision Queue) |
| Test files modified | 1 |

### Test Coverage Breakdown

**Pipeline tests (15):** Renders stages, counts, deals, probabilities, empty state, role="region", progress bars, click/keyboard interaction, skeleton, motion-reduce

**Company Health tests (17):** Renders score, metrics, values, trends, alerts, empty state, role="region", click/keyboard interaction, skeleton, motion-reduce

**Decision Queue additions (4):** Skeleton loading, decision summary, NBA items, aria-live count

---

## Documentation Created

### WIDGET_MIGRATION_GUIDE.md
- Step-by-step migration checklist (12 steps)
- Before/after code examples (Legacy → SDK, Dashboard → Decision)
- DecisionProvider integration pattern
- Error boundary wrapper pattern
- Accessibility requirements checklist (10 items)
- Testing requirements with contract test examples

### SDK README.md
- API reference for all 8 SDK functions
- Usage examples for each widget type
- DecisionProvider integration guide
- Error handling patterns (SDK + application level)
- Accessibility guide with ARIA patterns
- Performance best practices (virtualization, memoization, telemetry)

---

## Widget Config (New Entries)

```typescript
pipeline: {
  id: 'pipeline',
  gridColumn: 'span 4',
  minHeight: '350px',
  refreshIntervalMs: 60_000,
  staleThresholdMs: 120_000,
},
companyHealth: {
  id: 'companyHealth',
  gridColumn: 'span 3',
  minHeight: '300px',
  refreshIntervalMs: 60_000,
  staleThresholdMs: 120_000,
},
```

---

## Key Patterns Demonstrated

1. **Container/View separation** — All widgets follow SDK pattern
2. **DecisionProvider integration** — `createDecisionEnabledWidget` with `useDecision` + `useNBA`
3. **Skeleton loading** — Dedicated skeleton components for decision-loading states
4. **Error boundaries** — `withErrorBoundary()` in widget-registry
5. **Accessibility** — `role="region"`, `aria-live`, `aria-label`, keyboard nav, motion-reduce
6. **RTL support** — CSS variables and logical properties
7. **Virtualization** — Pipeline deal list virtualizes >50 items

---

## Remaining Work

| Item | Priority | Notes |
|------|----------|-------|
| Mission Center → `createDecisionEnabledWidget` | P2 | Could benefit from decision context |
| Intelligence Feed → `createDecisionEnabledWidget` | P2 | Could show AI-driven signal prioritization |
| AI Brief → `createDecisionEnabledWidget` | P3 | Already has AI, decision context optional |
| Market Pulse → `createDecisionEnabledWidget` | P3 | Market-level decision context |
| Recent Activity → `createDecisionEnabledWidget` | P3 | Activity-level decision context |
| `useNBAFeed` hook implementation | P1 | Currently imported but needs implementation |
| Pipeline/CompanyHealth DTOs wiring | P1 | Backend endpoints needed |

---

*Generated by SalesOS Engineering — Sprint 8 Stabilization*
