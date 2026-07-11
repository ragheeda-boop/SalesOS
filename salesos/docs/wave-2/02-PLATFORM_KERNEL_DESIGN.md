# Platform Kernel Design

> **الهدف:** تصميم `packages/platform/` كـ Platform Kernel — نقطة التجميع الرسمية لكل Shared Runtime
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Phase 2 — Platform Kernel

---

## Design Philosophy

`packages/platform/` is **not** a barrel package. It is the **Platform Kernel** — the shared runtime that every SalesOS package and application depends on. It owns cross-cutting concerns only: telemetry, permissions, feature flags, events, contracts, and testing utilities.

### Ownership Rules

| Layer | Owns | Does Not Own |
|-------|------|-------------|
| **kernel/** | Platform bootstrap, registry, lifecycle | Business logic, UI components |
| **shared/** | Cross-cutting concerns (telemetry, permissions, events) | Implementation details |
| **contracts/** | Type definitions, interfaces, DTOs | Runtime logic, API implementations |
| **testing/** | Test utilities, mocks, factories | Test data, test cases |

---

## Structure

```text
packages/platform/

kernel/
    platform.ts          — Platform bootstrap: init order, dependency resolution
    registry.ts          — Global registry: widgets, commands, capabilities
    lifecycle.ts         — Lifecycle hooks: onMount, onUnmount, onError, onConfigChange

shared/
    telemetry/
        index.ts
        metrics.ts       — Metric recording, counters, histograms
        trace.ts         — Distributed tracing context
        performance.ts   — Performance observers, marks, measures
    permissions/
        index.ts
        resolver.ts      — PermissionResolver interface + default
        types.ts         — Resource, Action, Permission types
    feature-flags/
        index.ts
        resolver.ts      — FeatureFlagResolver interface + default
        types.ts         — WidgetFeatureFlag, WidgetFeatureTier
    cache/
        index.ts
        memory-cache.ts  — In-memory cache with TTL
        types.ts         — CacheEntry, CacheOptions
    config/
        index.ts
        runtime-config.ts — Runtime configuration provider
        types.ts         — ConfigValue, ConfigSource
    events/
        index.ts
        event-bus.ts     — EventBus interface
        types.ts         — DomainEvent, EventHandler, EventSubscription
    utils/
        index.ts
        id.ts            — ID generation (UUID, short IDs)
        time.ts          — Time utilities (format, relative, duration)

contracts/
    workspace/
        index.ts
        widget.ts        — WidgetContract, WidgetMetadata, WidgetConfig
        permissions.ts   — WorkspacePermission, ResourceAction
        provider.ts      — WorkspaceProviderConfig
    search/
        index.ts
        query.ts         — SearchQuery, SearchFilter, SearchSort
        result.ts        — SearchResult, SearchResultItem, SearchFacet
        entity.ts        — SearchEntityType, SearchEntity
    widgets/
        index.ts
        types.ts         — WidgetStatus, WidgetData, WidgetRenderContext
        lifecycle.ts     — LifecycleHook, LifecycleEvent
    ai/
        index.ts
        recommendation.ts — Recommendation, Evidence, Confidence, Alternative
        decision.ts      — Decision, DecisionPipeline, DecisionOutcome
        score.ts         — Score, ScoringFactor, WeightedScore
        risk.ts          — Risk, RiskLevel, RiskFactor
    revenue/
        index.ts
        opportunity.ts   — Opportunity, OpportunityStage, OpportunityHealth
        pipeline.ts      — Pipeline, PipelineStage, PipelineMetrics
        meeting.ts       — Meeting, MeetingIntelligence, MeetingAction
        email.ts         — Email, EmailIntelligence, EmailAction
        nba.ts           — NextBestAction, NBASource, NBAStatus
        playbook.ts      — Playbook, PlaybookStep, PlaybookTrigger
        goal.ts          — RevenueGoal, GoalPeriod, GoalStatus

testing/
    index.ts
    mock-workspace.ts    — createMockWorkspaceContext, createMockWidget
    mock-recommendation.ts — createMockRecommendation, createMockEvidence
    test-utils.ts       — renderWithProviders, createMockRouter
    factories.ts        — Entity factories: createMockOpportunity, createMockPipeline
```

---

## Module Responsibilities

### kernel/

```typescript
// platform.ts — Platform bootstrap
interface PlatformConfig {
  permissions: PermissionResolver
  featureFlags: FeatureFlagResolver
  telemetry?: TelemetryProvider
  cache?: CacheProvider
}

export function createPlatform(config: PlatformConfig): Platform
// Initializes all shared modules in dependency order:
// 1. Cache (no deps)
// 2. Config (no deps)
// 3. Telemetry (no deps)
// 4. Permissions (no deps)
// 5. Feature Flags (depends on Config)
// 6. Events (depends on Telemetry)
// Returns: Platform instance with all modules accessible
```

```typescript
// registry.ts — Global registry
export class Registry {
  registerWidget(id: string, widget: WidgetDefinition): void
  getWidget(id: string): WidgetDefinition | undefined
  getAllWidgets(): WidgetDefinition[]
  registerCommand(id: string, command: CommandDefinition): void
  executeCommand(id: string, context: CommandContext): Promise<CommandResult>
}
```

```typescript
// lifecycle.ts — Lifecycle management
export interface LifecycleHooks {
  onMount?: () => void | Promise<void>
  onUnmount?: () => void | Promise<void>
  onError?: (error: Error) => void
  onConfigChange?: (config: Record<string, unknown>) => void
}

export function useLifecycle(id: string, hooks: LifecycleHooks): void
```

### shared/telemetry/

- **Metrics:** `recordMetric(name, value, tags?)`, `incrementCounter(name, tags?)`, `recordHistogram(name, value, tags?)`
- **Trace:** `createTraceSpan(name, context?)`, `setTraceAttribute(key, value)`, `endTraceSpan()`
- **Performance:** `mark(name)`, `measure(name, startMark, endMark)`, `getPerformanceEntries()`

All telemetry is **pluggable**. Default implementation is no-op. Production injects OpenTelemetry or Datadog provider.

### shared/permissions/

- **`PermissionResolver`** interface: `hasPermission(resource: string, action: string, context?: PermissionContext): boolean`
- **`createPermissionResolver(permissions: Permission[])`** — creates resolver from static permission list
- Default resolver is **permissive** (returns `true` for everything)

### shared/feature-flags/

- **`FeatureFlagResolver`** interface: `isEnabled(flag: FeatureFlag): boolean`
- **`createFeatureFlagResolver(flags: Record<string, boolean | FeatureFlagConfig>)`** — static resolver
- **`TieredFeatureFlagResolver`** — checks user tier against flag's required tier
- Default resolver returns `true` for all flags

### shared/cache/

- **`MemoryCache<T>`** — in-memory cache with TTL support
- **`createCache<T>(options: CacheOptions)`** — factory with configurable TTL, max size
- **`getOrSet<T>(key, factory, ttl?)`** — composite get+set with async factory function

### shared/events/

- **`EventBus`** interface: `emit(event: DomainEvent)`, `on(type, handler)`, `off(type, handler)`
- **`createEventBus()`** — in-process event bus
- Designed to wrap `EventRuntime` on the backend side

### contracts/ — Strongly Typed Interfaces

Every contract module exports:
- **TypeScript interfaces** for frontend
- **Pydantic models / TypeScript DTOs** for backend (dual source of truth)
- **JSON Schemas** for cross-boundary validation

**Example: contracts/revenue/nba.ts**

```typescript
export interface NextBestAction {
  id: string
  opportunityId: string
  action: string
  reason: string
  evidence: Evidence[]
  confidence: number
  source: NBASource
  alternatives: Alternative[]
  expectedImpact: Impact
  expectedRevenue?: number
  potentialRisk?: Risk[]
  dueBy?: string
  status: NBAStatus
  createdAt: string
  updatedAt: string
}
```

---

## Dependency Graph

```
packages/platform/

kernel/        (zero deps — bootstrap only)
  │
  ├── shared/cache/        (zero deps)
  ├── shared/config/       (zero deps)
  ├── shared/telemetry/    (zero deps)
  ├── shared/permissions/   (zero deps)
  ├── shared/feature-flags/ (depends on: config)
  ├── shared/events/       (depends on: telemetry)
  └── shared/utils/        (zero deps)
       │
       └── contracts/      (depends on: utils)
            │
            └── testing/   (depends on: contracts)
```

---

## Migration Plan

| Step | Action | Files Affected |
|------|--------|----------------|
| 1 | Create `packages/platform/` directory structure | New |
| 2 | Move contracts from `@salesos/workspace` to `packages/platform/contracts` | workspace/src/types.ts → platform/contracts/workspace/ |
| 3 | Move telemetry from `@salesos/workspace` to `platform/shared/telemetry` | workspace/src/widget-telemetry.ts → platform/shared/telemetry/ |
| 4 | Move permissions from `@salesos/workspace` to `platform/shared/permissions` | workspace/src/widget-permissions.ts → platform/shared/permissions/ |
| 5 | Move feature flags from `@salesos/workspace` to `platform/shared/feature-flags` | workspace/src/widget-feature-flags.ts → platform/shared/feature-flags/ |
| 6 | Create platform/contracts/ai and platform/contracts/revenue | New — Wave 2 contracts |
| 7 | Create platform/testing utilities | New — merges workspace/testing + search/testing |
| 8 | Update imports across `@salesos/workspace` and `@salesos/search` | Gradual — preserve backward compatibility via barrel re-exports |
| 9 | Publish `@salesos/platform` | Independent from `@salesos/workspace` — phased migration |

### Phase 1 (Sprint 5.0)
- Create directory structure
- Create `contracts/ai/` and `contracts/revenue/` (needed for NBA)
- No migration of existing packages yet

### Phase 2 (Sprint 5)
- Migrate `workspace/testing` → `platform/testing`
- Begin moving contracts

### Phase 3 (Sprint 6+)
- Migrate telemetry, permissions, feature flags
- Update workspace and search SDKs to re-export from platform

---

*Platform Kernel Design complete. Ready for Phase 3: NBA Architecture.*
