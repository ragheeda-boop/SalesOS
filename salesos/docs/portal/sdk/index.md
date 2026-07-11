# SalesOS SDK Reference

> TypeScript and Python SDK packages for building on the SalesOS platform.

## Which SDK to Use

| You want to... | Use this SDK | Language |
|---|---|---|
| Build a dashboard widget | `@salesos/workspace` (Widget SDK) | TypeScript |
| Create a reusable visual component | `@salesos/workspace` (Widget SDK) | TypeScript |
| Search companies, contacts, documents | `@salesos/search` (Search SDK) | TypeScript / Python |
| Read/write platform entities | `backend.sdk` (Python SDK) | Python |
| Publish/subscribe to domain events | `backend.sdk.events` (Python SDK) | Python |
| Evaluate decisions and recommendations | `@salesos/decision-platform` | TypeScript |
| Score entities (intent, revenue, risk) | `@salesos/decision-platform` | TypeScript |
| Extend the platform with a plugin | `@salesos/plugin-sdk` | TypeScript |
| Manage permissions and RBAC | `backend.sdk.permissions` (Python SDK) | Python |
| Cache data with Redis | `backend.sdk.cache` (Python SDK) | Python |
| Use telemetry and tracing | `backend.sdk.telemetry` (Python SDK) | Python |

## SDK Packages

| Package | Source | Description |
|---|---|---|
| `@salesos/workspace` | `frontend/src/features/dashboard/sdk/` | Widget SDK v1.0 — compose dashboard widgets |
| `@salesos/search` | `frontend/src/features/search/sdk/` | Hybrid search across all entity types |
| `@salesos/decision-platform` | `packages/platform/decision/` | Decision intelligence, scoring, NBA |
| `@salesos/plugin-sdk` | `packages/plugin-sdk/` | Plugin extension interfaces |
| `@salesos/design-language` | `packages/design-language/` | MUHIDE tokens, components, icons |
| `salesos-sdk` (Python) | `backend/sdk/` | Core Python SDK — entities, events, cache, search |

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Workspace (TypeScript)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Widget SDK    │  │ Search SDK   │  │ Plugin SDK     │ │
│  │ (createWidget)│  │ (SearchSvc)  │  │ (PluginRunner) │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘ │
└─────────┼─────────────────┼──────────────────┼───────────┘
          │                 │                  │
┌─────────┼─────────────────┼──────────────────┼───────────┐
│         │          Backend (Python)           │          │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌───────┴────────┐ │
│  │ Platform SDK  │  │ Search SDK   │  │ Plugin SDK     │ │
│  │ (events,      │  │ (FT, vector) │  │ (PluginBuilder)│ │
│  │  permissions) │  │              │  │                │ │
│  └──────────────┘  └──────────────┘  └────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐│
│  │ Decision Platform (TypeScript)                       ││
│  │ DecisionEngine │ ScoringEngine │ FeedbackEngine      ││
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

## Authentication

All SDKs authenticate using API keys passed via the `Authorization: Bearer` header.

**Python:**
```python
from sdk import sdk_settings
# SDK settings auto-loaded from .env or environment
```

**TypeScript:**
```typescript
const api = ApiClient.fromContext({
  apiBaseUrl: 'https://api.salesos.sa/api/v1',
  apiKey: process.env.SALESOS_API_KEY!,
  // ...
})
```

## API Base URL

```
Production:  https://api.salesos.sa/api/v1
Staging:     https://staging.api.salesos.sa/api/v1
Local:       http://localhost:8000/api/v1
```

## Versioning

| SDK | Current Version | Status |
|-----|----------------|--------|
| Widget SDK | v1.0 | 🧊 Feature Freeze |
| Search SDK | v1.0 | Stable |
| Decision Platform | v1.0 | Stable |
| Plugin SDK | v0.1 | Beta |
| Python SDK | v1.0 | Stable |

## Documentation Pages

| Doc | Description |
|-----|-------------|
| [Widget SDK](workspace-sdk.md) | `createDashboardWidget`, `createWidget`, lifecycle, permissions |
| [Search SDK](search-sdk.md) | Full-text, vector, hybrid search; Arabic support |
| [Platform SDK](platform-sdk.md) | Event bus, telemetry, cache, permissions, config |
| [Decision SDK](decision-sdk.md) | DecisionEngine, ScoringEngine, NBA, feedback |
