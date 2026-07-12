# @salesos/hooks

Shared React hooks for common frontend concerns.

## Purpose

Provides reusable hooks for runtime features, data access, permissions, theme, localization, and utility functions used across all widgets and pages.

## Exports

| Export | Source | Description |
|--------|--------|-------------|
| `useRuntime` | `use-runtime.ts` | Runtime context access |
| `useSession` | `use-session.ts` | Auth session state |
| `usePermission` | `use-permission.ts` | Permission checking with granular resource scopes |
| `useCache` | `use-cache.ts` | Client-side cache helpers |
| `useRealtime` | `use-realtime.ts` | WebSocket-based real-time data |
| `useOffline` | `use-offline.ts` | Offline state detection |
| `useTheme` | `use-theme.ts` | Theme switching (light/dark) |
| `useAccessibility` | `use-accessibility.ts` | Accessibility preferences |
| `useLocalization` | `use-localization.ts` | i18n and locale (Arabic/English) |
| `useEntity` | `use-entity.ts` | Entity data fetching with React Query |
| `useSchema` | `use-schema.ts` | Schema-driven UI data |
| `useCommand` | `use-command.ts` | Command palette integration |
| `useCollaboration` | `use-collaboration.ts` | Collaborative editing state |
| `useUtils` | `use-utils.ts` | Miscellaneous utilities |

## Usage

```tsx
import { usePermission, useTheme, useEntity } from '@salesos/hooks'

function Example() {
  const { can } = usePermission()
  const { theme, toggleTheme } = useTheme()
  const { data, isLoading } = useEntity('company', id)

  if (!can('read:company')) return <AccessDenied />
  return <div>...</div>
}
```
