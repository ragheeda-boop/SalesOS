# API Overview

> **نظرة عامة على واجهة API — الاصطلاحات، المصادقة، الأخطاء**

**Base URL:** `https://api.salesos.sa/api/v1`

---

## Conventions

### Authentication

All endpoints require:

| Header | Description |
|--------|-------------|
| `Authorization` | `Bearer <api_key>` or `Bearer <jwt>` |
| `X-Tenant-Id` | Your tenant identifier |

### Content Type

All requests and responses use `application/json`.

### Timestamps

All timestamps are ISO 8601 in UTC: `2026-07-11T14:30:00.000Z`

### Pagination

| Param | Type | Default | Max |
|-------|------|---------|-----|
| `page` | integer | `1` | — |
| `limit` | integer | `20` | `100` |
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

### IDs

All IDs are prefixed for readability: `comp_`, `opp_`, `user_`, `nba_`, `mtg_`, `eml_`.

---

## API Groups

| Group | Base Path | Description |
|-------|-----------|-------------|
| [Opportunities](opportunities.md) | `/revenue/opportunities` | Pipeline and deal management |
| [NBA](nba.md) | `/revenue/opportunities/{id}/nba` | Next Best Action engine |
| [Pipeline](pipeline.md) | `/revenue/pipeline` | Pipeline analytics and metrics |
| [Meetings](meetings.md) | `/revenue/meetings` | Meeting intelligence |
| [Email](email.md) | `/revenue/emails` | Email intelligence |
| [Revenue](revenue.md) | `/revenue/dashboard` | Revenue dashboard |
| [Workflows](workflows.md) | `/workflows` | Workflow engine |
| [RAG](rag.md) | `/rag` | RAG pipeline |
| [Analytics](analytics.md) | `/analytics` | Reports and analytics |
| [Notifications](notifications.md) | `/notifications` | WebSocket + push |
| [Admin](admin.md) | `/admin` | Tenant administration |
| [Audit](audit.md) | `/audit` | Audit logs |
| [SSO](sso.md) | `/auth` | Authentication and SSO |
| Decision | `/decision` | Decision Intelligence Platform |

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
