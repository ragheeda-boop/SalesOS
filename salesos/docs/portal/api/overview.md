# API Overview

> **SalesOS API Reference — Authentication, Pagination, Errors, Rate Limits**

**Base URL:** `https://api.salesos.sa/api/v1`

---

## Authentication

All endpoints (except `/identity/login`, `/identity/register`, `/health`, `/ping`) require:

| Header | Description |
|--------|-------------|
| `Authorization` | `Bearer <jwt>` or `Bearer <api_key>` |
| `X-Tenant-Id` | Your tenant identifier |

### JWT Tokens

Obtain via `/identity/login` or `/identity/register`. Tokens expire after the interval specified in `expires_in` (default 30 minutes). Use `/identity/refresh` to rotate.

### API Keys

Manage via `/api-keys`. Include as `Bearer <raw_api_key>`.

---

## Content Type

All requests and responses use `application/json` unless noted (file uploads use `multipart/form-data`).

---

## Timestamps

All timestamps are ISO 8601 in UTC: `2026-07-12T14:30:00.000Z`

---

## Pagination

| Param | Type | Default | Max |
|-------|------|---------|-----|
| `page` | integer | `1` | — |
| `limit` / `page_size` | integer | `20` | `100` |
| `offset` | integer | `0` | — |

Paginated responses:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 42,
    "total_pages": 3
  }
}
```

---

## IDs

All IDs are prefixed for readability: `comp_`, `opp_`, `user_`, `nba_`, `mtg_`, `eml_`, `act_`, `rule-`.

---

## Rate Limiting

| Tier | Window | Limit |
|------|--------|-------|
| Auth endpoints | 1 minute | 100 requests |
| Search endpoints | 1 minute | 30 requests |
| Anonymous | 1 minute | 20 requests |

Rate-limited responses include `Retry-After` header.

---

## API Groups

### Identity & Access

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Identity](identity.md) | `/identity` | Registration, login, sessions, password management |
| [SSO](sso.md) | `/auth` | SAML/OIDC single sign-on |
| [API Keys](api-keys.md) | `/api-keys` | API key management |
| [Admin](admin.md) | `/admin` | Tenant, user, billing administration |

### Core Entities

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Companies](companies.md) | `/companies` | Company CRUD, search, 360 view, ingest |
| [Contacts](contacts.md) | `/contacts` | Contact CRUD, search, bulk upsert |
| [Entity Resolution](entity-resolution.md) | `/entity-resolution` | Deduplication and golden records |

### Revenue Execution

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Opportunities](opportunities.md) | `/revenue/opportunities` | Pipeline and deal management |
| [NBA](nba.md) | `/revenue/opportunities/{id}/nba` | Next Best Action engine |
| [Pipeline](pipeline.md) | `/revenue/pipeline` | Pipeline analytics and metrics |
| [Meetings](meetings.md) | `/revenue/meetings` | Meeting intelligence |
| [Email](email.md) | `/revenue/emails` | Email intelligence |
| [Revenue](revenue.md) | `/revenue/dashboard` | Revenue dashboard |
| [Revenue Execution](revenue-execution.md) | `/opportunities`, `/tasks`, `/pipeline` | Opportunities, tasks, pipeline (module) |
| [Commercial](commercial.md) | `/opportunities`, `/pipelines`, `/quotes`, `/proposals`, `/contracts` | Full commercial lifecycle |

### Intelligence & Decision

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Decision Platform](decision-platform.md) | `/decision` | Decision evaluation, recommendations, rules, feedback |
| [Copilot](copilot.md) | `/copilot` | AI copilot agent queries |
| [RAG](rag.md) | `/rag` | RAG pipeline — document ingestion and Q&A |
| [Work Intelligence](work-intelligence.md) | `/work-intelligence` | Employee work analysis |

### Search & Data

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Search](search.md) | `/search` | Hybrid search (full-text + semantic) |
| [Feature Store](feature-store.md) | `/features` | Feature computation and retrieval |
| [Knowledge Graph](knowledge-graph.md) | `/graph` | Graph queries, competitors, paths |
| [Data Fabric](data-fabric.md) | `/data-fabric` | Data ingestion and pipeline |

### Runtime & Platform

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Activity](activity-runtime.md) | `/activities` | Activity recording and querying |
| [Timeline](timeline.md) | `/timeline` | Entity timelines and summaries |
| [Event Runtime](event-runtime.md) | `/event-runtime` | Event bus monitoring and dead letters |
| [Capability Framework](capability-framework.md) | `/capabilities` | Capability registry |
| [UX Runtime](ux-runtime.md) | `/ux` | Navigation, layout, widgets, commands, themes |
| [UI Schema](ui-schema.md) | `/schema` | Dynamic UI schema generation |
| [Form Engine](form-engine.md) | `/forms` | Dynamic form generation and validation |
| [Action Engine](action-engine.md) | `/actions` | Registered action execution |
| [Extension API](extension-api.md) | `/extensions` | Hook points for extensibility |
| [Plugin Sandbox](plugin-sandbox.md) | `/plugins` | Plugin installation and management |

### Monitoring & Operations

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Monitoring](monitoring.md) | `/monitoring` | Client-side metrics ingestion and dashboard |
| [Cache](cache.md) | `/cache` | Redis cache management |
| [Telemetry](telemetry.md) | `/telemetry` | Feature adoption and usage analytics |
| [Audit](audit.md) | `/audit` | Audit logs |
| [Analytics](analytics.md) | `/analytics` | Reports and analytics |

### Workflows & Automation

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Workflows](workflows.md) | `/workflows` | Workflow engine — DAG execution |
| [Notifications](notifications.md) | `/notifications` | WebSocket + push notifications |

### Dashboards

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Dashboard](dashboard.md) | `/dashboard` | Main dashboard aggregation |
| [Executive](executive.md) | `/executive` | Executive dashboard |
| [Employee 360](employee-360.md) | `/employees` | Employee 360 views |

### Import & Integration

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Notion Sync](notion-sync.md) | `/notion` | Import companies from Notion |
| [Excel Import](excel-import.md) | `/import` | Import companies from Excel |

---

## Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": "Additional context"
  }
}
```

### Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid auth |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `AI_TIMEOUT` | 504 | AI reasoning timed out |
| `TENANT_MISMATCH` | 403 | X-Tenant-Id doesn't match JWT |

---

## SDK Packages

| Package | Import | Description |
|---------|--------|-------------|
| Workspace SDK | `@salesos/workspace` | Widget creation, workspace providers |
| Search SDK | `@salesos/search` | Entity search |
| Decision Platform | `@salesos/decision-platform` | Decision engine, scoring, rules |
| Platform Kernel | `@salesos/platform` | Telemetry, permissions, feature flags |

See [SDK Reference](../sdk/workspace-sdk.md) for details.
