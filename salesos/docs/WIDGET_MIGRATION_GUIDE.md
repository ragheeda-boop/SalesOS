# Widget Migration Guide

> الدليل الشامل لترحيل الـ Widgets من Legacy إلى SDK-based مع DecisionProvider

---

## Table of Contents

1. [Overview](#1-overview)
2. [Migration Steps](#2-migration-steps)
3. [Before / After Examples](#3-before--after-examples)
4. [DecisionProvider Integration](#4-decisionprovider-integration)
5. [Error Boundary Wrapper](#5-error-boundary-wrapper)
6. [Accessibility Requirements](#6-accessibility-requirements)
7. [Testing Requirements](#7-testing-requirements)

---

## 1. Overview

### Why Migrate?

| Problem | Solution |
|---------|----------|
| Inconsistent widget patterns | SDK standardizes lifecycle, telemetry, permissions |
| No error isolation | `DashboardErrorBoundary` per-widget |
| Manual loading/error states | SDK handles all 4 states automatically |
| No DecisionProvider integration | `createDecisionEnabledWidget()` wires it up |
| No accessibility standards | SDK enforces WCAG AA compliance |

### Widget SDK Hierarchy

```
createWidget<T>()                  ← Base factory (all features)
  └─ createDashboardWidget<T>()    ← Dashboard context wiring
       └─ createDecisionEnabledWidget<T>()  ← + DecisionProvider + NBA
```

### When to Use Each

| Factory | Use When |
|---------|----------|
| `createWidget()` | Standalone widget, custom data source |
| `createDashboardWidget()` | Dashboard page, reads from DashboardProvider |
| `createDecisionEnabledWidget()` | Dashboard widget that needs decision context/NBA |

---

## 2. Migration Steps

### Step-by-Step Checklist

- [ ] **1. Identify current widget pattern** — Is it legacy (manual) or already SDK-based?
- [ ] **2. Choose the right factory** — `createDashboardWidget` or `createDecisionEnabledWidget`
- [ ] **3. Create `types.ts`** — Define view props and data types
- [ ] **4. Create `View.tsx`** — Pure presentation component
- [ ] **5. Create `Container.tsx`** — Use SDK factory, define metadata
- [ ] **6. Create `index.ts`** — Barrel export
- [ ] **7. Create `__tests__/*.test.tsx`** — Contract tests + unit tests
- [ ] **8. Register in `widget-config.ts`** — Add WidgetId, grid, refresh, stale config
- [ ] **9. Register in `widget-registry.tsx`** — Add to registry with error boundary
- [ ] **10. Add DTO types** — In `dashboard.dto.ts`
- [ ] **11. Run tests** — `npx jest --no-coverage`
- [ ] **12. Run lint/typecheck** — Verify zero regressions

---

## 3. Before / After Examples

### Example A: Legacy Widget → `createDashboardWidget()`

**Before (Legacy — manual state management):**

```tsx
// LegacyWidget.tsx — NO SDK, manual everything
'use client'

import { useState, useEffect } from 'react'

export function LegacyWidget() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/widget-data')
      .then(r => r.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  if (error) return <div>Error: {error.message}</div>
  return <WidgetContent data={data} />
}
```

**After (SDK-based):**

```tsx
// LegacyWidgetContainer.tsx
'use client'

import { createDashboardWidget } from '../../sdk'
import { LegacyWidgetView } from './LegacyWidgetView'
import type { LegacyWidgetData } from './types'

export const LegacyWidget = createDashboardWidget<LegacyWidgetData>('legacyWidget', {
  metadata: {
    title: 'Legacy Widget',
    description: ' migrated from legacy pattern',
    permissions: ['legacy:read'],
    featureFlag: { enabled: true },
  },
  render: ({ data }) => (
    <LegacyWidgetView items={data.items} />
  ),
})
```

```tsx
// LegacyWidgetView.tsx — Pure, no SDK dependency
'use client'

import type { LegacyWidgetViewProps } from './types'

export function LegacyWidgetView({ items }: LegacyWidgetViewProps) {
  if (!items || items.length === 0) {
    return <div role="status">No data available</div>
  }
  return (
    <div role="region" aria-label="Legacy Widget Dashboard">
      {items.map(item => (
        <div key={item.id}>{item.label}</div>
      ))}
    </div>
  )
}
```

### Example B: `createDashboardWidget` → `createDecisionEnabledWidget`

**Before (Dashboard widget, no decision context):**

```tsx
// DecisionQueueContainer.tsx
export const DecisionQueueWidget = createDashboardWidget<DecisionQueueData>('decisionQueue', {
  metadata: { title: '...' },
  render: ({ data }) => (
    <DecisionQueueView items={data.items ?? []} />
  ),
})
```

**After (Decision-enabled):**

```tsx
// DecisionQueueContainer.tsx
import { createDecisionEnabledWidget } from '../../sdk'
import { useCompanyDecision } from '../../../revenue-execution/_providers/DecisionProvider'
import { useNBAFeed } from '../../_hooks/useNBAFeed'

export const DecisionQueueWidget = createDecisionEnabledWidget<DecisionQueueData>('decisionQueue', {
  metadata: {
    title: 'قرارات معلقة',
    description: 'القرارات التي تحتاج إلى اتخاذ إجراء',
    permissions: ['decisions:read'],
    featureFlag: { enabled: true },
  },
  useDecision: (tenantId) => useCompanyDecision(tenantId),
  useNBA: () => useNBAFeed(),
  render: (ctx) => (
    <DecisionQueueView
      items={ctx.data.items ?? []}
      total={ctx.data.total ?? 0}
      decision={ctx.decision}
      nbaItems={ctx.nbaItems}
      isDecisionLoading={ctx.isDecisionLoading}
    />
  ),
})
```

---

## 4. DecisionProvider Integration

### How `createDecisionEnabledWidget` Works

```
┌─────────────────────────────────────────────────┐
│         createDecisionEnabledWidget<T>()         │
│                                                  │
│  1. Calls useDashboardContext() for widget data  │
│  2. Calls useDecision(tenantId, context)         │
│  3. Calls useNBA() if provided                   │
│  4. Builds DecisionWidgetRenderContext<T>        │
│  5. Passes to render() callback                  │
└─────────────────────────────────────────────────┘
```

### Render Context Shape

```typescript
interface DecisionWidgetRenderContext<T> extends WidgetRenderContext<T> {
  decision: DecisionContextData | null   // DecisionProvider context
  nbaItems: NBAFeedItem[]                // Next Best Actions
  isDecisionLoading: boolean             // Decision loading state
}
```

### Required Hooks

| Hook | Source | Purpose |
|------|--------|---------|
| `useDecision` | `DecisionProvider` | Evaluate decision context for the widget |
| `useNBA` (optional) | Custom hook | Fetch NBA feed items for the widget |

### DecisionProvider Setup

Ensure the parent component tree includes `<DecisionProvider>`:

```tsx
// In your page layout
import { DecisionProvider } from '@/features/revenue-execution/_providers/DecisionProvider'

<DashboardProvider>
  <DecisionProvider>
    <DashboardLayout />
  </DecisionProvider>
</DashboardProvider>
```

---

## 5. Error Boundary Wrapper

### Automatic Error Boundaries (SDK)

The SDK's `createWidget()` wraps each widget in error handling:
- Permission denied → renders `fallback` prop
- Feature flag disabled → renders `fallback` prop
- Data error → shows retry state

### Application-Level Error Boundaries

`widget-registry.tsx` wraps each widget with `withErrorBoundary()`:

```tsx
import { withErrorBoundary } from '@/components/error-boundary'

const DecisionQueueBounded = withErrorBoundary(
  DecisionQueueWidget,
  <WidgetFallback title="Decision Queue" />
)
```

### Custom Error Fallback

```tsx
function WidgetFallback({ title }: { title: string }) {
  return (
    <div className="flex h-full items-center justify-center p-4" role="status"
         aria-label={`${title} widget loading error`}>
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

### DashboardErrorBoundary (SDK internal)

Used by `widget-card.tsx` for widget card frames:

```tsx
import { DashboardErrorBoundary } from '../_layout/dashboard-error-boundary'

<DashboardErrorBoundary widgetId="myWidget">
  <WidgetContent />
</DashboardErrorBoundary>
```

---

## 6. Accessibility Requirements

### Mandatory Checklist

| # | Requirement | How to Implement |
|---|-------------|-----------------|
| 1 | `role="region"` with `aria-label` | Root container of View |
| 2 | `role="status"` for loading | SDK provides automatically |
| 3 | `role="alert"` for errors | SDK provides automatically |
| 4 | `aria-live="polite"` for dynamic content | Announce count changes |
| 5 | `aria-atomic="true"` on live regions | Read full content on update |
| 6 | Keyboard navigation | `onKeyDown` handlers for Enter/Space |
| 7 | `focus-visible:ring-2` on interactive elements | Tailwind focus ring |
| 8 | `motion-reduce:transition-none` | Respect reduced motion |
| 9 | Dark mode support | Use CSS variables and `dark:` variants |
| 10 | RTL layout support | Use logical properties, RTL-aware CSS |

### Pattern: aria-live for Count Updates

```tsx
<div aria-live="polite" aria-atomic="true" className="text-xs">
  {count} عنصر
</div>
```

### Pattern: Keyboard Navigation

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
>
  {content}
</div>
```

---

## 7. Testing Requirements

### Contract Tests (Required for All Widgets)

Every widget MUST pass `describeWidgetContract()`:

```tsx
import { describeWidgetContract } from '../../sdk/testing'

describeWidgetContract({
  name: 'MyWidget',
  defaultData: { /* sample data */ },
  config: {
    metadata: {
      id: 'my-widget',
      title: 'My Widget',
      minHeight: '200px',
      permissions: ['widget:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => <MyWidgetView {...data} />,
  },
})
```

### What Contract Tests Cover

| Test Suite | Tests |
|-----------|-------|
| Rendering | Title, region, fallback for denied permission, fallback for disabled feature |
| Widget States | loading, ready, degraded (with data), degraded (no data), error |
| Permissions | Renders when granted, hides when denied |
| Feature Flags | Renders when enabled, hides when disabled |
| Accessibility | aria-label on refresh, role="status" on loading, role="alert" on error, retry button |
| Interaction | Retry calls refetch, refresh calls refetch |

### Unit Tests (Widget-Specific)

```tsx
describe('MyWidgetView', () => {
  it('renders all items', () => { /* ... */ })
  it('shows empty state when no items', () => { /* ... */ })
  it('handles click', () => { /* ... */ })
  it('supports keyboard navigation', () => { /* ... */ })
  it('has descriptive aria-labels', () => { /* ... */ })
  it('has dark mode classes', () => { /* ... */ })
  it('has motion-reduce classes', () => { /* ... */ })
})
```

### Decision Widget Tests

For widgets using `createDecisionEnabledWidget()`:

```tsx
describe('DecisionWidget', () => {
  it('is a valid React component', () => {
    expect(DecisionWidget).toBeDefined()
    expect(typeof DecisionWidget === 'function' || typeof DecisionWidget === 'object').toBe(true)
  })

  it('renders decision context when available', () => { /* ... */ })
  it('renders NBA items when available', () => { /* ... */ })
  it('shows loading when decision is loading', () => { /* ... */ })
})
```

---

## Quick Reference: File Structure

```
widgets/my-widget/
├── index.ts                    # Barrel export
├── MyWidgetContainer.tsx       # Container — SDK factory
├── MyWidgetView.tsx            # View — pure component
├── types.ts                    # View props + data types
└── __tests__/
    └── MyWidget.test.tsx       # Contract + unit tests
```

---

*Last updated: 2026-07-13*
*Version: v1.0*
