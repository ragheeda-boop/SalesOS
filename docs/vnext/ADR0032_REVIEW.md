# ADR-0032 Review: Widget SDK Reconciliation

> **Reviewer**: Engineering OS — Chief Engineering Officer & Architecture Governance Lead
> **Date**: 2026-07-16
> **Reference**: ADR-0032 (Proposed), ADR-003 (Frozen), PROJECT_BIBLE §7.7, D-011
> **PRC Gate**: G-1 (Architecture Review — P0 Blocker)

---

## Executive Summary

| Question | Answer |
|----------|--------|
| Does a Dual Widget SDK problem exist? | ✅ **Confirmed** |
| Does ADR-0032 correctly identify the root cause? | ✅ **Yes** |
| Should ADR-0032 be approved? | ✅ **Yes — with refinements** |
| Does this violate ADR-003 or D-011? | ❌ **No** — surface remains frozen; relocation + consolidation only |
| Does this align with ARCHITECTURE_VNEXT.md? | ✅ **Yes** — establishes `@salesos/widget-sdk` package |

---

## 1. SDK Comparison

### Dashboard SDK — `src/features/dashboard/sdk/`

| Dimension | Details |
|-----------|---------|
| **Purpose** | Widget factory for the Executive Dashboard |
| **Architecture** | Container/View pattern via factory functions |
| **Public APIs** | `createWidget()`, `createDashboardWidget()`, `createDecisionEnabledWidget()`, `useWidgetLifecycle()`, `widgetTelemetry`, `setPermissionChecker/checkPermissions`, `setFeatureFlagResolver/isFeatureEnabled` |
| **Types** | `WidgetStatus`, `WidgetPriority`, `WidgetCategory`, `WidgetFeatureTier`, `WidgetFeatureFlag`, `WidgetMetadata`, `WidgetLifecycle`, `WidgetData`, `WidgetRenderContext`, `WidgetConfig`, plus Decision types (`DecisionContextType`, `DecisionFactor`, `DecisionContextData`, `NBAFeedItem`, `NBAFeedResponse`, `DecisionWidgetRenderContext`, `DecisionWidgetConfig`) |
| **Factories** | `createWidget()` — generic; `createDashboardWidget()` — dashboard-context-aware; `createDecisionEnabledWidget()` — decision-enabled |
| **Registration** | Via `widget-config.ts` registry; widgets registered by ID with config |
| **Lifecycle** | `useWidgetLifecycle()` — mount/unmount/refresh/error/statusChange hooks |
| **Dependencies** | `@salesos/ui` (Skeleton, useToast), CSS variables (`--border-default`, `--bg-primary`, `--text-muted`, `--muhide-orange`, `--danger-*`) |
| **Testing** | `describeWidgetContract()` — WidgetContract.tsx; `createWidgetContractTest()` — contract-test-utils.ts; `renderWidget()`, `createMockWidget()`, mock permissions/flags/telemetry |
| **Consumers** | 7 dashboard widgets: AIBrief, MarketPulse, IntelligenceFeed, RecentActivity, DecisionQueue, CompanyHealth, Pipeline; plus self-test |
| **UI Quality** | Uses `@salesos/ui` Skeleton component; CSS variables for theming/dark mode; `useToast()` integration |
| **Code Quality** | `import { Skeleton, useToast } from '@salesos/ui'` — proper component library usage |

### Workspace SDK — `packages/workspace/`

| Dimension | Details |
|-----------|---------|
| **Purpose** | Widget factory + workspace infrastructure for Company/Employee/Revenue workspaces |
| **Architecture** | Container/View pattern + Workspace Provider + Grid layout engine |
| **Public APIs** | Same as Dashboard SDK PLUS: `createWorkspaceWidget()`, `WorkspaceGrid`, `WorkspaceRenderer`, `WorkspaceProvider`/`createWorkspaceProvider()`, `WorkspaceErrorBoundary`, `WorkspaceLoading`, `createRegistry()`, `deriveStatus()`, plus components: `GlobalActivityFeed`, `UniversalInbox`, `RevenueCommandCenter`, `AIOperatingAssistant` |
| **Types** | Same core types as Dashboard SDK PLUS: `WorkspaceWidgetEntry`, `WorkspaceContextValue` |
| **Factories** | `createWidget()` — generic (forked implementation); `createWorkspaceWidget()` — workspace-context-aware |
| **Registration** | Via `workspace-registry.ts` — `createRegistry()` with typed entries |
| **Lifecycle** | `useWidgetLifecycle()` — logically identical to Dashboard SDK version |
| **Dependencies** | `@salesos/ui`, `@salesos/icons`, `@salesos/charts`, `@salesos/runtime`, `@salesos/hooks`, `@salesos/design-language`, `@salesos/renderer` |
| **Testing** | `describeWidgetContract()` — WidgetContract.tsx (standalone fork); `renderWidget()`, `createMockWidget()`/`createEmptyWidget()`, `TelemetrySpy`, mock permissions/flags |
| **Consumers** | ~36 widgets: company-intelligence (9), employee-intelligence (6), revenue-execution (18+); plus E2E tests, analytics |
| **UI Quality** | Inline styles (`#e5e7eb`, `#fff`, `#fca5a5`) — no CSS variables; custom spinner instead of `@salesos/ui` Skeleton; Arabic labels built into STATUS_LABEL |
| **Code Quality** | No `@salesos/ui` component usage in `createWidget()`; hardcoded colors break dark mode |

### Duplicated Code

| Module | Dashboard SDK | Workspace SDK | Delta |
|--------|--------------|---------------|-------|
| `createWidget()` | 279 lines — uses CSS vars, Skeleton, useToast | 281 lines — inline styles, custom spinner, Arabic labels | Logically identical; implementation differs |
| `types.ts` | 118 lines (incl. Decision types) | 75 lines (no Decision types) | Core widget types identical; Decision types unique to Dashboard |
| `widget-lifecycle.ts` | ✅ | ✅ | Identical logic |
| `widget-telemetry.ts` | ✅ | ✅ | Identical logic |
| `widget-permissions.ts` | ✅ | ✅ | Identical logic |
| `widget-feature-flags.ts` | ✅ | ✅ | Identical logic |
| `testing/WidgetContract.tsx` | 161 lines (10 tests) | 161 lines (10 tests) | Near-identical contract test suites |
| `testing/renderWidget.tsx` | ✅ | ✅ | Near-identical |
| `testing/mockWidgetContext.ts` | ✅ | ✅ | Near-identical (workspace adds `createEmptyWidget()`) |
| `testing/mockPermissions.ts` | ✅ | ✅ | Identical |
| `testing/mockFeatureFlags.ts` | ✅ | ✅ | Workspace adds `mockFeatureFlagsCustom()` |
| `testing/mockTelemetry.ts` | — | ✅ | Unique to Workspace SDK |

### Unique (Non-duplicated) Workspace SDK Assets

These are NOT duplicated and should REMAIN in the workspace package:

| Asset | Purpose | Lines |
|-------|---------|-------|
| `createWorkspaceWidget.tsx` | Workspace-context-aware wrapper | 43 |
| `workspace-provider.tsx` + `createWorkspaceProvider()` | Workspace context provider | ~100 |
| `workspace-grid.tsx` | Grid layout engine | ~80 |
| `workspace-error-boundary.tsx` | Error boundary for workspace | ~50 |
| `workspace-loading.tsx` | Loading state | ~30 |
| `workspace-registry.ts` | Widget registry | ~60 |
| `renderer.tsx` | Workspace renderer | ~80 |
| `generator.ts` | Workspace generation | ~100 |
| `presets.ts` | Workspace presets | ~80 |
| `derive-status.ts` | Status derivation utility | ~20 |
| `GlobalActivityFeed` | Component | ~150 |
| `UniversalInbox` | Component | ~120 |
| `RevenueCommandCenter` | Component | ~100 |
| `AIOperatingAssistant` | Component | ~100 |

---

## 2. Option Analysis

### Option A: Dashboard SDK as Single Source of Truth ✅ (Recommended)

Canonical SDK = Dashboard SDK (v1.0 frozen), moved to `packages/widget-sdk/`.  
Workspace SDK becomes consumer; its `createWidget()` and testing utilities deleted.

| Dimension | Assessment |
|-----------|-----------|
| **Advantages** | Respects ADR-003 frozen surface; better UI tech (CSS vars, @salesos/ui); proven test coverage; aligns with ARCHITECTURE_VNEXT.md target state |
| **Disadvantages** | Workspace ~36 consumers need import updates; workspace inline styles would be lost but that's desirable (CSS variables are superior) |
| **Migration complexity** | **Low-Medium** — import path changes only; no logic changes |
| **Risk level** | **Low** — Dashboard SDK is well-tested (7 widgets + contract tests); workspace consumers simply change import source |
| **Backward compatibility** | ✅ Full — API surface unchanged; types match exactly |
| **Performance impact** | ✅ Neutral — same code, different import path |
| **Developer experience** | ⬆️ **Improved** — one import `@salesos/widget-sdk` everywhere; no confusion |
| **Long-term maintainability** | ✅ **High** — single source of truth; DRY; decisions centralized |
| **Impact on PROJECT_BIBLE** | ✅ Aligns with §7.7 and D-011; frozen surface preserved |
| **Impact on ADR-003** | ✅ ADR-003 remains in full effect — consolidation is not an API surface change |

### Option B: Workspace SDK as Single Source of Truth

| Dimension | Assessment |
|-----------|-----------|
| **Advantages** | Workspace SDK has broader consumer base (~36 vs 7) |
| **Disadvantages** | Inline styles regress from CSS variables; loses `@salesos/ui` component integration; loses Decision integration; ADR-003 technically violated (Dashboard SDK was frozen as canonical) |
| **Migration complexity** | **High** — 7 dashboard widgets + Decision integration need rewrite; backwards step in UI quality |
| **Risk level** | **High** — regressing UI quality; losing decision-enabled widgets capability |
| **Backward compatibility** | ⚠️ Partial — widget contracts would need re-verification |
| **Developer experience** | ⬇️ **Worse** — inline styles instead of design system |
| **Long-term maintainability** | ⚠️ **Medium** — but retains workspace infrastructure as non-duplicated value |
| **Impact on PROJECT_BIBLE** | ❌ Conflicts with §7.7 (frozen SDK changes require ADR) |
| **Impact on ADR-003** | ❌ Would require ADR-003 amendment or replacement |

### Option C: Unified Widget SDK V2

| Dimension | Assessment |
|-----------|-----------|
| **Advantages** | Clean slate; best features from both; forward-looking |
| **Disadvantages** | Violates D-011 ("No v1.1"); higher migration effort; reintroduces churn; would require ADR-003 replacement + PROJECT_BIBLE amendment |
| **Migration complexity** | **High** — new package, new imports, new testing, all consumers updated |
| **Risk level** | **Medium-High** — churn during migration; potential regressions |
| **Backward compatibility** | ⚠️ Partial — would require a compatibility shim |
| **Developer experience** | ⬆️ Best long-term but worst during transition |
| **Long-term maintainability** | ✅ **Highest** — purpose-built for consolidated state |
| **Impact on PROJECT_BIBLE** | ❌ Requires amending §7.7 and D-011; replacing ADR-003 |
| **Impact on ADR-003** | ❌ **Supersedes** — frozen surface would be unfrozen for V2 |

### Option D: Alternative Architecture

Not justified. The problem is code duplication, not architectural inadequacy. A headless/plugin-based widget system would be premature over-engineering for the current scale.

---

## 3. Recommendation

### Decision: **APPROVE ADR-0032** (Option A — with refinements)

**Rationale:**

1. **Dual SDK is a verified P0 violation** — ADR-003 explicitly froze the Widget SDK v1.0. The Workspace SDK's standalone `createWidget()` duplicates the frozen surface, violating Engineering Constitution §3.4 and §9.1.

2. **ADR-0032 correctly identifies the solution** — Consolidating to a single canonical SDK eliminates the duplication while preserving the frozen surface.

3. **The Dashboard SDK is the correct canonical choice** because:
   - It uses CSS variables (the design system standard)
   - It integrates `@salesos/ui` components (Skeleton, useToast)
   - It has Decision Platform integration (`createDecisionEnabledWidget()`)
   - It is already documented in `REFERENCE_WIDGET_GUIDE.md`
   - It is the SDK that ADR-003 explicitly froze

4. **This is NOT a v1.1** — Per PROJECT_BIBLE D-011 ("No v1.1"), this consolidation is a relocation + deduplication, not an API surface change. All exported functions keep identical signatures. All types remain unchanged. No existing consumer breaks.

5. **The Workspace SDK's non-duplicated assets are valuable** — `WorkspaceGrid`, `WorkspaceProvider`, workspace components, and workspace-specific widgets remain untouched.

6. **`createWorkspaceWidget()` is a valid extension pattern** — It wraps the canonical `createWidget()` with workspace defaults. This is the approved extension mechanism.

### Refinements to ADR-0032

| # | Refinement | Rationale |
|---|-----------|-----------|
| R1 | **Preserve Arabic labels** — add `STATUS_LABEL` Arabic strings to canonical SDK | Workspace SDK's Arabic labels are a product requirement (Saudi market). The canonical SDK must support bilingual status labels. |
| R2 | **Retain `mockTelemetry.ts` in workspace** — it's a workspace-specific testing utility not present in Dashboard SDK | Workspace SDK's `TelemetrySpy` is unique and valuable; keep it. |
| R3 | **Retain `createEmptyWidget()` in workspace testing** — unique to Workspace SDK | Useful utility; keep in workspace testing package. |
| R4 | **Explicit doc note**: This consolidation is not a v1.1 API surface change | To satisfy D-011 compliance and avoid confusion. |

### Verdict

```
ADR-0032: ✅ APPROVED (with refinements R1-R4)
P0 Blocker VIO-S0-01 (Dual Widget SDK): ✅ RESOLVED (upon implementation)
```

---

## 4. Compliance with Governing Documents

| Document | Relevant Clause | Compliance | Notes |
|----------|----------------|------------|-------|
| Engineering Constitution | §3.4 (Frozen Interface) | ✅ | Frozen surface preserved; no API changes |
| Engineering Constitution | §9.1-9.5 (Widget SDK) | ✅ | Single SDK enforced; Container/View preserved |
| PROJECT_BIBLE | §7.7 (Widget SDK Frozen) | ✅ | Consolidation is relocation, not surface change |
| PROJECT_BIBLE | D-011 (No v1.1) | ✅ | No version bump; no API surface change |
| ARCHITECTURE_VNEXT.md | §Widget SDK Evolution | ✅ | Establishes `@salesos/widget-sdk` package path |
| ADR-003 | Frozen surface | ✅ | Amended (consolidation mandate), not superseded |

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Import path changes break consumers | Medium | Medium | Automated import update script; CI verify |
| Behavioral difference between duplicate implementations | Low | Medium | Contract tests on all widgets post-migration |
| Dev confusion during transition | Medium | Low | Clear migration guide; deprecation warnings |
| Workspace-specific features lost | Low | Medium | R1-R4 refinements preserve them |

---

## 6. Migration Strategy (Summary)

See `docs/vnext/WIDGET_SDK_MIGRATION_PLAN.md` for the complete strategy.

**Phases:**
1. Move Dashboard SDK → `packages/widget-sdk/`
2. Update Dashboard SDK consumers (7 widgets + tests)
3. Delete duplicated modules from Workspace SDK
4. Update Workspace SDK consumers (~36 widgets) to import from `@salesos/widget-sdk`
5. Verify all contract tests pass
6. Add CI enforcement (single `createWidget()` scan)

---

*This review resolves P0 blocker VIO-S0-01. Upon implementation, the Architecture Review gate (G-1) can be re-evaluated.*
