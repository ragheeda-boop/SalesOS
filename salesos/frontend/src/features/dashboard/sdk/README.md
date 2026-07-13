# Widget SDK

> مكتبة بناء Widgets في SalesOS Dashboard — v1.0 Frozen

---

## Table of Contents

1. [API Reference](#1-api-reference)
2. [Usage Examples](#2-usage-examples)
3. [DecisionProvider Integration](#3-decisionprovider-integration)
4. [Error Handling Patterns](#4-error-handling-patterns)
5. [Accessibility Guide](#5-accessibility-guide)
6. [Performance Best Practices](#6-performance-best-practices)

---

## 1. API Reference

### `createWidget<T>(config: WidgetConfig<T>): ComponentType`

Base factory for creating any widget. Handles:
- Lifecycle (mount/unmount/refresh/error/status-change)
- Telemetry (mounted/loaded/failed/refreshed/unmounted)
- Permissions check
- Feature flag check
- Loading / Error / Degraded / Ready states

```typescript
interface WidgetConfig<T> {
  metadata: WidgetMetadata
  lifecycle?: WidgetLifecycle
  useData: () => WidgetData<T>
  render: (ctx: WidgetRenderContext<T>) => React.ReactNode
  fallback?: React.ReactNode
}

interface WidgetMetadata {
  id: string
  title: string
  description?: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
  category?: 'metrics' | 'signals' | 'decisions' | 'intelligence' | 'activity'
  icon?: string
  permissions?: string[]
  refreshInterval?: number
  staleThreshold?: number
  featureFlag?: WidgetFeatureFlag
  gridColumn?: string
  minHeight?: string
}

interface WidgetRenderContext<T> {
  data: T
  status: WidgetStatus
  lastUpdated: string | null
  metadata: WidgetMetadata
  refresh: () => void
}
```

### `createDashboardWidget<T>(id, overrides): ComponentType`

Dashboard-specific factory. Automatically wires up `DashboardContext`:

```typescript
function createDashboardWidget<T>(
  id: WidgetId,
  overrides: {
    metadata?: Partial<WidgetMetadata>
    lifecycle?: WidgetLifecycle
    fallback?: React.ReactNode
    render: (ctx: WidgetRenderContext<T>) => React.ReactNode
  }
): ComponentType
```

### `createDecisionEnabledWidget<T>(id, overrides): ComponentType`

Decision-enabled factory. Extends `createDashboardWidget` with DecisionProvider context:

```typescript
function createDecisionEnabledWidget<T>(
  id: WidgetId,
  overrides: {
    metadata?: Partial<WidgetMetadata>
    lifecycle?: WidgetLifecycle
    fallback?: React.ReactNode
    useDecision: (tenantId: string, context?: Record<string, string>) => DecisionContextData | null
    useNBA?: () => NBAFeedItem[]
    render: (ctx: DecisionWidgetRenderContext<T>) => React.ReactNode
  }
): ComponentType

interface DecisionWidgetRenderContext<T> extends WidgetRenderContext<T> {
  decision: DecisionContextData | null
  nbaItems: NBAFeedItem[]
  isDecisionLoading: boolean
}
```

### `useWidgetLifecycle(id, metadata, status, hooks)`

Hook for lifecycle events (used internally by `createWidget`):

```typescript
function useWidgetLifecycle(
  id: string,
  metadata: WidgetMetadata,
  status: WidgetStatus,
  hooks?: WidgetLifecycle
): { notifyRefresh: () => void; notifyError: (error: Error) => void }
```

### `widgetTelemetry`

Telemetry recorder for widget events:

| Method | Description |
|--------|-------------|
| `record(type, widgetId, extra?)` | Record a telemetry event |
| `startTimer(widgetId)` | Start a performance timer |
| `getAll()` | Get all recorded events |
| `clear()` | Clear the event log |

### `checkPermissions(required?)`

Check if user has required permissions:

```typescript
function checkPermissions(required?: string[]): boolean
// true if all required permissions are granted, or if none required
```

### `isFeatureEnabled(flag?)`

Check if a feature flag is enabled:

```typescript
function isFeatureEnabled(flag?: WidgetFeatureFlag): boolean
// true if no flag, or flag.enabled && resolver.isEnabled(flag)
```

### `setPermissionChecker(checker)` / `setFeatureFlagResolver(resolver)`

Configure the permission checker and feature flag resolver (call once at app init):

```typescript
setPermissionChecker({ hasPermission: (p) => userPermissions.includes(p) })
setFeatureFlagResolver({ isEnabled: (f) => featureFlags[f.tier ?? 'enabled'] })
```

---

## 2. Usage Examples

### Basic Dashboard Widget

```tsx
// widgets/my-widget/MyWidgetContainer.tsx
'use client'

import { createDashboardWidget } from '../../sdk'
import { MyWidgetView } from './MyWidgetView'
import type { MyWidgetData } from './types'

export const MyWidget = createDashboardWidget<MyWidgetData>('myWidget', {
  metadata: {
    title: 'My Widget',
    description: 'Widget description',
    permissions: ['mywidget:read'],
    featureFlag: { enabled: true },
  },
  render: ({ data, refresh }) => (
    <MyWidgetView items={data.items} count={data.count} />
  ),
})
```

### Decision-Enabled Widget

```tsx
// widgets/my-decision-widget/MyDecisionWidgetContainer.tsx
'use client'

import { createDecisionEnabledWidget } from '../../sdk'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { MyDecisionWidgetView } from './MyDecisionWidgetView'

export const MyDecisionWidget = createDecisionEnabledWidget<MyData>('myWidget', {
  metadata: {
    title: 'My Decision Widget',
    permissions: ['decisions:read'],
  },
  useDecision: (tenantId) => useCompanyDecision(tenantId),
  useNBA: () => useNBAFeed(),
  render: (ctx) => (
    <MyDecisionWidgetView
      data={ctx.data}
      decision={ctx.decision}
      nbaItems={ctx.nbaItems}
      isDecisionLoading={ctx.isDecisionLoading}
    />
  ),
})
```

### Pure View Component

```tsx
// widgets/my-widget/MyWidgetView.tsx
'use client'

import type { MyWidgetViewProps } from './types'

export function MyWidgetView({ items, count }: MyWidgetViewProps) {
  if (!items || items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <p className="text-sm text-[var(--text-muted)]">No items yet</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="My Widget Dashboard" className="space-y-2">
      <div aria-live="polite" aria-atomic="true" className="text-xs text-[var(--text-muted)]">
        {count} items
      </div>
      <div role="list" aria-label="Widget items" className="space-y-1">
        {items.map((item) => (
          <div key={item.id} role="listitem" className="rounded-lg px-3 py-2 text-sm">
            {item.label}
          </div>
        ))}
      </div>
    </div>
  )
}
```

---

## 3. DecisionProvider Integration

### Setup

Wrap your dashboard in `DecisionProvider`:

```tsx
// In your page layout
import { DecisionProvider } from '@/features/revenue-execution/_providers/DecisionProvider'

<DashboardProvider>
  <DecisionProvider>
    <DashboardLayout />
  </DecisionProvider>
</DashboardProvider>
```

### Available Decision Hooks

| Hook | Purpose |
|------|---------|
| `useDecision()` | Full decision context (evaluate, scores, history, feedback) |
| `useCompanyDecision(tenantId)` | Company-specific decision context |

### Decision Context Shape

```typescript
interface DecisionContextData {
  context_type: 'company' | 'revenue' | 'pipeline' | 'dashboard'
  factors: DecisionFactor[]
  confidence: number
  summary: string
  generated_at: string
}

interface DecisionFactor {
  name: string
  value: number
  weight: number
  description: string
}
```

### NBA Feed

```typescript
interface NBAFeedItem {
  id: string
  decision_id?: string
  company_id: string
  company_name: string
  action: string
  reason: string
  confidence: number
  confidence_label: 'high' | 'medium' | 'low'
  priority: number
  source: string
  status: string
  created_at: string
}
```

---

## 4. Error Handling Patterns

### SDK-Level Error Handling

The SDK handles 4 states automatically:

| State | SDK Behavior |
|-------|-------------|
| `loading` | Shows spinner with `role="status"` |
| `ready` | Renders content |
| `degraded` | Renders content at 50% opacity + warning overlay |
| `error` | Shows error message with retry button, `role="alert"` |

### Application-Level Error Boundaries

```tsx
// widget-registry.tsx
import { withErrorBoundary } from '@/components/error-boundary'

const MyWidgetBounded = withErrorBoundary(
  MyWidget,
  <WidgetFallback title="My Widget" />
)
```

### Custom Fallback

```tsx
function WidgetFallback({ title }: { title: string }) {
  return (
    <div className="flex h-full items-center justify-center p-4" role="status">
      <div className="text-center">
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs text-neutral-500">
          حدث خطأ في تحميل هذا المكون
        </p>
      </div>
    </div>
  )
}
```

### Lifecycle Error Callback

```tsx
const MyWidget = createDashboardWidget('myWidget', {
  lifecycle: {
    onError: ({ id, error }) => {
      console.error(`Widget ${id} failed:`, error.message)
      // Report to monitoring service
    },
  },
  // ...
})
```

---

## 5. Accessibility Guide

### Required ARIA Attributes

| Element | Attribute | Value |
|---------|-----------|-------|
| Root container | `role="region"` | `aria-label` with widget name |
| Loading state | `role="status"` | `aria-label="Loading"` |
| Error state | `role="alert"` | Automatic from SDK |
| Live updates | `aria-live="polite"` | On count/summary elements |
| Live atomic | `aria-atomic="true"` | On live regions |
| Interactive items | `role="button"` | With `tabIndex={0}` |
| Item lists | `role="list"` | With `aria-label` |
| List items | `role="listitem"` | Direct children of list |

### Keyboard Navigation

All interactive elements must support Enter and Space:

```tsx
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }}
/>
```

### Reduced Motion

```tsx
<div className="transition-colors motion-reduce:transition-none">
  {content}
</div>
```

### Dark Mode

```tsx
<div className="bg-[var(--bg-secondary)] dark:bg-dark-secondary">
  {content}
</div>
```

### RTL Support

Use CSS variables and logical properties:

```tsx
<div className="px-3 py-2 text-sm">
  {/* px-3 maps to padding-inline-start/end in RTL */}
</div>
```

---

## 6. Performance Best Practices

### Virtualization

For lists > 50 items, use virtualization:

```tsx
import { useVirtualizer } from '@tanstack/react-virtual'

function VirtualizedList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null)
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
  })

  return (
    <div ref={parentRef} style={{ overflow: 'auto', height: '300px' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: virtualRow.start,
              height: virtualRow.size,
            }}
          >
            {items[virtualRow.index].label}
          </div>
        ))}
      </div>
    </div>
  )
}
```

### Memoization

- View components should be pure — no state, no side effects
- Use `React.memo()` on list item components
- Use `useCallback` for event handlers
- Use `useMemo` for expensive computations

### Telemetry Performance

The SDK uses `performance.mark()` and `performance.measure()` for timing. These are:
- Non-blocking
- Available in all modern browsers
- Zero-cost when not supported (polyfill-free)

### Refresh Intervals

Configure in `widget-config.ts`:

| Widget | Refresh | Stale |
|--------|---------|-------|
| Mission Center | 60s | 120s |
| Decision Queue | 60s | 120s |
| Intelligence Feed | 30s | 60s |
| AI Brief | 120s | 300s |
| Market Pulse | 60s | 120s |
| Recent Activity | 30s | 60s |

---

*Last updated: 2026-07-13*
*Version: v1.0 — Frozen*
