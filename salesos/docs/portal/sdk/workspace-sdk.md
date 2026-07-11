# Workspace SDK Reference

> **Widget SDK v1.0 — بناء واجهات مساحة العمل和工作ة**

Package: `@salesos/workspace` | Status: **Frozen** | Version: v1.0.0

The Workspace SDK provides the foundation for building all SalesOS workspace widgets. It follows the **Container/View Pattern** — Containers use the SDK, Views are pure components.

---

## Installation

```bash
npm install @salesos/workspace
```

---

## createDashboardWidget

Creates a full-size dashboard widget with loading, error, and permission states.

```typescript
import { createDashboardWidget } from '@salesos/workspace'

interface MyWidgetData {
  total: number
  items: string[]
}

const MyWidget = createDashboardWidget<MyWidgetData>({
  id: 'my-analytics-widget',
  title: 'My Analytics',
  description: 'Custom analytics widget',
  defaultSize: { w: 4, h: 3 },
  permissions: ['analytics:read'],
  featureFlag: 'ff_analytics_widget',

  async fetchData(ctx) {
    const response = await ctx.api.get('/analytics/summary')
    return response.data
  },

  render(data) {
    return (
      <div className="widget-analytics">
        <h3>{data.total} items</h3>
        <ul>{data.items.map(i => <li>{i}</li>)}</ul>
      </div>
    )
  },
})
```

---

## createWorkspaceWidget

Creates a workspace-scoped widget with access to workspace context.

```typescript
import { createWorkspaceWidget } from '@salesos/workspace'

const OpportunityTimeline = createWorkspaceWidget({
  id: 'opportunity-timeline',
  title: 'Timeline',
  workspace: 'opportunity',
  permissions: ['opportunity:read'],

  render({ workspace, api, user }) {
    return <TimelineView opportunityId={workspace.id} />
  },
})
```

---

## createWidget

Creates a reusable widget component used across multiple contexts.

```typescript
import { createWidget } from '@salesos/workspace'

const ScoreBadge = createWidget({
  id: 'score-badge',
  defaultSize: { w: 1, h: 1 },

  render({ value, label, variant }) {
    return <Badge value={value} label={label} variant={variant} />
  },
})
```

---

## Hooks

| Hook | Signature | Description |
|------|-----------|-------------|
| `useWorkspaceContext` | `() => WorkspaceContext` | Current workspace context |
| `usePermission` | `(resource, action) => boolean` | Check user permission |
| `useFeatureFlag` | `(flag) => boolean` | Check feature flag |
| `useDecision` | `(context) => DecisionResult` | Evaluate decision |
| `useFeedback` | `(decisionId) => { submit, stats }` | Submit feedback |
| `useLifecycle` | `(id, hooks) => void` | Component lifecycle |

---

## Workspace Providers

```typescript
import { createWorkspaceProvider } from '@salesos/workspace'

const OpportunityProvider = createWorkspaceProvider({
  id: 'opportunity',
  fetchData: async (ctx) => {
    const [opp, activities, nba] = await Promise.all([
      ctx.api.get(`/opportunities/${ctx.id}`),
      ctx.api.get(`/opportunities/${ctx.id}/activities`),
      ctx.api.get(`/opportunities/${ctx.id}/nba`),
    ])
    return { opportunity: opp, activities, nba }
  },
})
```

---

## Contract Tests

Every widget should include contract tests:

```typescript
import { describeWidgetContract } from '@salesos/workspace/testing'

describeWidgetContract({
  component: MyWidget,
  name: 'My Analytics Widget',
  scenarios: [
    { name: 'loading', state: { status: 'loading' } },
    { name: 'ready', state: { status: 'ready', data: { total: 42 } } },
    { name: 'error', state: { status: 'error', error: 'Failed to load' } },
    { name: 'no-permission', state: { status: 'no-permission' } },
    { name: 'feature-disabled', state: { status: 'feature-disabled' } },
  ],
})
```

---

## Widget Lifecycle

```
onMount → permission check → feature flag check → fetchData → render
                                                      │
                                              ┌───────┴───────┐
                                              ▼               ▼
                                          Success          Error
                                              │               │
                                              ▼               ▼
                                          render(data)   render error state
                                              │
                                              ▼
                                          onUnmount → cleanup
```

---

## Widget States

Every widget handles four states:

1. **loading** — Skeleton/spinner while data loads
2. **ready** — Normal rendered state with data
3. **degraded** — Partial data or stale cache
4. **error** — Error state with retry option

---

## Related

| Resource | Link |
|----------|------|
| Creating a Widget Guide | [Guide](../guides/creating-a-widget.md) |
| Widget SDK Reference | [REFERENCE_WIDGET_GUIDE.md](../../../engineering-os/REFERENCE_WIDGET_GUIDE.md) (if exists) |
| Platform SDK | [Platform SDK](platform-sdk.md) |
