# SalesOS Plugin SDK

> Define extension interfaces for building third-party plugins on the SalesOS platform.

## Installation

```bash
npm install @salesos/plugin-sdk
```

## Quick Start

```typescript
import { buildManifest, PluginRunner, ApiClient } from '@salesos/plugin-sdk'
import type { PluginHooks, PluginContext, PluginDefinition } from '@salesos/plugin-sdk'

// 1. Define your plugin
const definition: PluginDefinition = {
  name: 'my-plugin',
  version: '1.0.0',
  description: 'Integrates with external CRM',
  author: { name: 'ACME Corp', email: 'dev@acme.com' },
  capabilities: ['data-source', 'webhook'],
  permissions: ['companies:read', 'contacts:read'],
  dependencies: [],
}

// 2. Build manifest
const manifest = buildManifest('my-plugin-v1', definition, 'dist/index.js')

// 3. Implement hooks
const hooks: PluginHooks = {
  onActivate: async (ctx: PluginContext) => {
    console.log(`Plugin activated for tenant ${ctx.tenantId}`)
  },
  onDeactivate: async (ctx: PluginContext) => {
    console.log('Plugin deactivated')
  },
  onEvent: async (ctx: PluginContext, event) => {
    console.log('Received event:', event.type)
  },
  onError: async (ctx: PluginContext, error) => {
    console.error('Plugin error:', error.message)
  },
}

// 4. Create runner and API client
const ctx: PluginContext = {
  tenantId: 'tenant-123',
  userId: 'user-456',
  pluginId: manifest.id,
  instanceId: 'inst-789',
  config: {},
  apiBaseUrl: 'https://api.salesos.sa/api/v1',
  apiKey: process.env.SALESOS_API_KEY!,
}

const runner = new PluginRunner(hooks, ctx)
const api = ApiClient.fromContext(ctx)

// 5. Activate
await runner.activate()

// 6. Use the API
const companies = await api.get('/companies', { limit: 10, offset: 0 })
```

## Core Concepts

### Plugin Manifests

Every plugin declares a manifest that describes its identity, capabilities, permissions, and resource limits. The Platform Runtime validates the manifest before loading the plugin.

### Lifecycle Hooks

| Hook | Called When |
|------|-------------|
| `onInstall` | Plugin first installed for a tenant |
| `onActivate` | Plugin enabled and loaded |
| `onDeactivate` | Plugin disabled or unloaded |
| `onUninstall` | Plugin removed from tenant |
| `onConfigChange` | Plugin configuration updated |
| `onEvent` | A subscribed domain event fires |
| `onError` | An error occurs within the plugin |
| `onHealthCheck` | Platform pings for health status |

### API Client

The `ApiClient` provides a typed HTTP client for plugin-to-platform communication. It handles:

- **Authentication**: Automatically injects `Authorization: Bearer` header
- **Rate Limiting**: Enforces per-second rate limits with backoff
- **Retries**: Exponential backoff for 429, 5xx, and network errors
- **Timeout**: Configurable request timeout (default: 10s)

### Plugin Context

Each plugin receives a `PluginContext` at runtime containing:

- `tenantId` / `userId` — scoped identity
- `pluginId` / `instanceId` — plugin identification
- `config` — plugin-level configuration
- `apiBaseUrl` / `apiKey` — platform API access

### Capabilities

| Capability | Description |
|------------|-------------|
| `widget` | Provides a workspace widget |
| `workflow` | Provides a workflow action or trigger |
| `data-source` | Provides an external data source |
| `webhook` | Registers webhooks for platform events |
| `dashboard-card` | Provides a dashboard card |
| `search-provider` | Provides a custom search provider |
| `notification-channel` | Provides a notification channel |

## Best Practices

1. **Declare minimal permissions** — request only what your plugin needs
2. **Handle errors gracefully** — implement `onError` to catch and log issues
3. **Use idempotent handlers** — events may be delivered more than once
4. **Keep startup fast** — `onActivate` should complete in under 5 seconds
5. **Validate config schema** — define `configSchema` for structured configs
6. **Clean up on deactivate** — close connections, flush buffers in `onDeactivate`
7. **Report health** — implement `onHealthCheck` so the platform can monitor your plugin

## Error Handling

```typescript
import { ApiError } from '@salesos/plugin-sdk'

try {
  const result = await api.get('/companies')
} catch (err) {
  if (err instanceof ApiError) {
    if (err.isRateLimited()) {
      // Back off and retry later
    } else if (err.isUnauthorized()) {
      // Re-authenticate
    }
  }
}
```

## Validation

```typescript
import { validateManifest } from '@salesos/plugin-sdk'

const result = validateManifest(manifest)
if (!result.valid) {
  console.error('Manifest errors:', result.errors)
}
```

## Plugin API Interface

Plugins that don't use the `ApiClient` directly can use the higher-level `PluginAPI` interface for common operations:

```typescript
interface PluginAPI {
  query<T>(endpoint: string, params?: Record<string, unknown>): Promise<T>
  create<T>(endpoint: string, data: Record<string, unknown>): Promise<T>
  update<T>(endpoint: string, id: string, data: Record<string, unknown>): Promise<T>
  delete<T>(endpoint: string, id: string): Promise<T>
  getConfig<T>(): T
  updateConfig(config: Record<string, unknown>): Promise<void>
  getStorage<T>(key: string): Promise<T | null>
  setStorage(key: string, value: unknown): Promise<void>
  deleteStorage(key: string): Promise<void>
  publishEvent(eventType: string, payload: Record<string, unknown>): Promise<void>
  subscribeToEvent(eventType: string, handler: Function): () => void
  checkPermission(permission: string): Promise<boolean>
  log(level: 'info' | 'warn' | 'error', message: string, data?: Record<string, unknown>): void
  reportMetric(name: string, value: number, tags?: Record<string, unknown>): void
}
```

## Development

```bash
npm run build    # Compile TypeScript
npm run dev      # Watch mode
npm run typecheck # Type-check without emitting
```
