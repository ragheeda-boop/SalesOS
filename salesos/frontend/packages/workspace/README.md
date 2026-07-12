# @salesos/workspace

Widget SDK — v1.0 Feature Freeze. The canonical way to build widgets for SalesOS.

## Purpose

Provides `createWidget()`, `createDashboardWidget()`, and `createWorkspaceWidget()` factories along with lifecycle management, permissions, feature flags, and telemetry. All widgets must use this SDK.

## Exports

| Export | Source | Description |
|--------|--------|-------------|
| `createWidget` | `create-widget.tsx` | Generic widget factory |
| `createDashboardWidget` | `create-dashboard-widget.tsx` | Dashboard-specific widget factory |
| `createWorkspaceWidget` | `create-workspace-widget.tsx` | Workspace widget factory |
| `WidgetLifecycle` | `widget-lifecycle.ts` | Lifecycle hooks (mount, update, unmount) |
| `WidgetTelemetry` | `widget-telemetry.ts` | Telemetry and analytics |
| `WidgetPermissions` | `widget-permissions.ts` | Permission checking |
| `WidgetFeatureFlags` | `widget-feature-flags.ts` | Feature flag evaluation |
| `useWidgetRuntime` | `renderer.tsx` | Runtime hook for widget |
| `WorkspaceProvider` | `workspace-provider.tsx` | Root provider |
| `WorkspaceGrid` | `workspace-grid.tsx` | Layout grid |
| `WorkspaceRegistry` | `workspace-registry.ts` | Widget registration |
| `deriveStatus` | `derive-status.ts` | Status derivation |
| `testing/*` | `testing/` | Contract testing utilities |

## Usage

```tsx
import { createDashboardWidget, describeWidgetContract } from '@salesos/workspace'

const MyWidget = createDashboardWidget({
  id: 'my-widget',
  title: 'My Widget',
  component: MyWidgetView,
})

// Contract test
describeWidgetContract('MyWidget', () => ({
  widget: MyWidget,
  states: ['ready', 'loading', 'degraded', 'error'],
}))
```

See [Widget SDK Guide](../docs/REFERENCE_WIDGET_GUIDE.md) for full documentation.
