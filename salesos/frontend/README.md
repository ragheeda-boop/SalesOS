# SalesOS Frontend

Enterprise Company Intelligence Platform — Next.js monorepo with 12 packages and 4 apps.

## Monorepo Structure

```
frontend/
├── apps/                            # Application shells
│   ├── command-center/              # Executive command center
│   ├── company-workspace/           # Company workspace (per-company)
│   ├── copilot/                     # AI copilot interface
│   └── search/                      # Enterprise search
├── packages/                        # Shared packages
│   ├── ui/                          # @salesos/ui — Foundation components
│   ├── workspace/                   # @salesos/workspace — Widget SDK
│   ├── design-language/             # @salesos/design-language — Tokens, themes
│   ├── hooks/                       # @salesos/hooks — Shared React hooks
│   ├── charts/                      # @salesos/charts — Recharts-based charts
│   ├── runtime/                     # @salesos/runtime — Client runtime
│   ├── config/                      # @salesos/config — Shared config
│   ├── forms/                       # @salesos/forms — Form components
│   ├── icons/                       # @salesos/icons — Icon library
│   ├── platform/                    # @salesos/platform — Platform SDK
│   ├── renderer/                    # @salesos/renderer — Schema-driven UI renderer
│   └── search/                      # @salesos/search — Search UI components
├── src/                             # Application source (dashboard pages, layouts)
│   ├── app/                         # Next.js App Router pages
│   ├── components/                  # Dashboard components and widgets
│   └── application/                 # Application layer (hooks, DTOs, mappers)
├── public/                          # Static assets + MSW service worker
├── server/                          # Custom Next.js server (optional)
├── coverage/                        # Test coverage reports
├── docs/                            # Frontend documentation
├── package.json                     # Root workspace config
├── next.config.js                   # Next.js configuration
├── tailwind.config.ts               # Tailwind CSS theme (MUHIDE tokens)
├── tsconfig.json                    # TypeScript configuration
└── jest.config.js                   # Jest test configuration
```

## Workspace SDK Usage

All widgets use `@salesos/workspace` (Widget SDK v1.0 — Frozen):

```typescript
import { createDashboardWidget } from '@salesos/workspace'

const MyWidget = createDashboardWidget({
  id: 'my-widget',
  title: 'My Widget',
  component: MyWidgetView,
})
```

SDK features:
- `createWidget()` — Generic widget factory
- `createDashboardWidget()` — Dashboard-specific widget factory
- `useWidgetRuntime()` — Runtime hook for widget lifecycle
- `widgetLifecycle` — Lifecycle hooks (mount, update, unmount)
- `widgetTelemetry` — Telemetry and analytics
- `widgetPermissions` — Permission checking
- `widgetFeatureFlags` — Feature flag evaluation

See [Widget SDK Guide](docs/REFERENCE_WIDGET_GUIDE.md) for full documentation.

## Widget Development Workflow

1. **Copy template** — Start from `../../packages/widget-template/`
2. **Define container** — Container uses SDK hooks, manages state, permissions, flags
3. **Define view** — Pure presentational component with typed props
4. **Write contract tests** — Use `describeWidgetContract()` from SDK testing utilities
5. **Test four states** — `ready`, `loading`, `degraded`, `error`
6. **Pass accessibility** — WCAG AA, keyboard nav, ARIA labels, reduced motion

## Component Conventions

- **Container/View Pattern** — Container uses SDK, View is pure component
- **Foundation reuse** — All widgets use `@salesos/ui` components (Card, Stack, Grid, etc.)
- **Design tokens** — Colors, spacing, typography from `@salesos/design-language`
- **Radix primitives** — Use `@radix-ui/*` for accessible primitives (dialog, select, tabs, tooltip, etc.)
- **CSS** — Tailwind CSS with MUHIDE theme tokens
- **Testing** — Jest + React Testing Library + MSW for API mocking

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL |
| `NEXT_PUBLIC_SENTRY_DSN` | Error tracking (optional) |
| `NEXT_PUBLIC_APP_ENV` | Environment name |

Copy `.env.example` to `.env` and fill in values.

## Build and Deploy

```bash
# Development
npm run dev                     # Start dev server on :3000

# Build
npm run build                   # Production build
npm run build:packages          # Build all packages

# Test
npm test                        # Run all tests
npm run test -- --coverage      # Coverage report

# Lint & Typecheck
npm run lint                    # ESLint
npm run typecheck               # TypeScript (tsc --noEmit)

# Storybook
npm run storybook               # Component catalog on :6006

# Specific app
npm run dev:company             # Company Workspace only
npm run dev:search              # Search app only
```

## Consumer Contract Tests

Every API client function in `src/lib/api.ts` has a contract test verifying:
- Response shape matches its TypeScript type
- Correct HTTP method and endpoint are called
- Tenant ID header is attached
- Error codes (401, 403, 422, 4xx, 5xx) are handled correctly
- Paginated response format (offset + cursor)
- Error propagation for network failures and validation errors

```bash
npm test -- --testPathPattern="api.contract"
```

Coverage: **93 API functions covered** across Companies, Contacts, Employees, Opportunities, Activities, Auth, User Profile, Company 360, Admin (tenants, plans, licenses, users, feature flags, jobs, AI costs, health, roles, permissions, config, audit logs), Copilot, Entity Resolution, DLQ, Search, Executive Dashboard, and Tasks.

## Performance Optimization

### Lazy Loading

Heavy components (CommandBar, SearchPanel, CopilotPanel, charts) are loaded via `next/dynamic`:

```typescript
import { LazyCommandBar } from "@/components/lazy-exports"
```

- SSR disabled for all panel components
- Skeleton loading states shown during load
- No impact on initial page load

### Code Splitting

- Dashboard panels are dynamic imports (not statically bundled)
- `experimental.optimizePackageImports` configured for Radix UI and Lucide icons
- `console.log` stripped in production builds (errors/warnings preserved)

### Bundle Analysis

```bash
npm run build
node scripts/analyze-bundle.js
```

- Reports top-20 largest JS assets by page and chunk
- Flags any asset > 100 KB (gzipped equivalent)
- Writes `.next/bundle-report.json` for CI gates
- Run after every build to catch regressions

### Vendor Code Splitting

Webpack `splitChunks` configured in `next.config.js` with cache groups:
- `framework` — React, ReactDOM, Next.js
- `radix` — All `@radix-ui/*` packages
- `charts` — Recharts and charting dependencies
- `commons` — Axios, Zod, CVA, clsx, tailwind-merge

### Optimized Package Imports

Tree-shaking configured via `experimental.optimizePackageImports`:
- `lucide-react`, `recharts`
- All `@radix-ui/*` packages
- `@tanstack/react-table`, `@tanstack/react-query`
- `class-variance-authority`, `tailwind-merge`

## Dashboard Pages

| Route | Description |
|-------|-------------|
| `/dashboard` | Executive dashboard with KPIs |
| `/companies` | Company management with search |
| `/companies/:id` | Company 360° view |
| `/companies/:id/360` | Company 360° detail page |
| `/employees` | Employee management |
| `/employees/me` | Employee 360° (self) |
| `/employees/:id` | Employee 360° (other) |
| `/contacts` | Contact management |
| `/opportunities` | Pipeline & deals |
| `/opportunities/:id` | Opportunity detail |
| `/pipeline` | Kanban pipeline board |
| `/pipeline/analytics` | Pipeline analytics |
| `/revenue` | Revenue intelligence |
| `/revenue/territories` | Territory management |
| `/revenue/quotas` | Quota management |
| `/forecast` | Forecasting |
| `/activities` | Activity timeline |
| `/search` | Unified search |
| `/search/analytics` | Search analytics |
| `/admin` | Admin portal |
| `/admin/tenants` | Tenant management |
| `/admin/flags` | Feature flag management |
| `/admin/audit` | Audit log viewer |
| `/admin/config` | System configuration |
| `/copilot` | AI copilot |
| `/copilot/telemetry` | Copilot telemetry dashboard |
| `/analytics` | Analytics dashboards |
| `/analytics/sales` | Sales analytics |
| `/analytics/revenue` | Revenue analytics |
| `/analytics/pipeline` | Pipeline analytics |
| `/analytics/employees` | Employee analytics |
| `/analytics/automation` | Automation analytics |
| `/analytics/reports/builder` | Custom report builder |
| `/automation` | Workflow automation |
| `/automation/workflows/new` | New workflow |
| `/automation/analytics` | Automation analytics |
| `/knowledge` | Knowledge graph visualization |
| `/knowledge/connectors` | Knowledge connectors |
| `/graph` | Entity relationship graph |
| `/decisions` | Decision center |
| `/decisions/templates` | Decision templates |
| `/monitoring` | System health monitoring |
| `/signals` | Signal intelligence |
| `/rules` | Business rules engine |
| `/rag` | RAG query interface |
| `/ai` | AI prompt templates |
| `/meetings` | Meeting intelligence |
| `/customer-success` | Customer success hub |
| `/marketplace` | App marketplace |
| `/marketplace/:pluginId/config` | Plugin configuration |
| `/settings` | User settings |

## Links

- [Widget SDK Guide](docs/REFERENCE_WIDGET_GUIDE.md)
- [Widget Contract Spec](../application/dashboard/WIDGET_CONTRACT.md)
- [Widget Template](../../packages/widget-template/)
- [ADR-002: Dashboard as Projection](../../engineering-os/adr/ADR-002-executive-intelligence-workspace.md)
- [ADR-003: Widget SDK v1.0 Freeze](../../engineering-os/adr/ADR-003-widget-sdk-v1-freeze.md)
- [Engineering Constitution](../../engineering-os/ENGINEERING_CONSTITUTION.md)
