# @salesos/runtime

Client-side runtime for workspace, widget, and application orchestration.

## Purpose

Manages client-side state, caching, real-time connections, session, offline support, and accessibility runtime. Used by `@salesos/workspace` and application code.

## Exports

| Export | Source | Description |
|--------|--------|-------------|
| `Runtime` | `runtime.ts` | Core runtime class |
| `SessionRuntime` | `session-runtime.ts` | Session management |
| `CacheRuntime` | `cache-runtime.ts` | Client cache (React Query wrapper) |
| `RealtimeRuntime` | `realtime-runtime.ts` | WebSocket connection manager |
| `OfflineRuntime` | `offline-runtime.ts` | Offline queue and sync |
| `LocalizationRuntime` | `localization-runtime.ts` | i18n and RTL management |
| `AccessibilityRuntime` | `accessibility-runtime.ts` | Accessibility settings (reduced motion, contrast) |
| `CollaborationRuntime` | `collaboration-runtime.ts` | Collaborative state sync |
| `RenderingRuntime` | `rendering-runtime.ts` | Schema-driven rendering |
| `StateRuntime` | `state-runtime.ts` | Global state management |

## Usage

```tsx
import { Runtime, SessionRuntime, CacheRuntime } from '@salesos/runtime'

const runtime = new Runtime({
  session: new SessionRuntime(),
  cache: new CacheRuntime(),
})

await runtime.start()
```
