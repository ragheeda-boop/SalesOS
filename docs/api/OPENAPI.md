# SalesOS API Documentation

> **Audience**: API consumers, integrators
> **Version**: 1.0
> **Last updated**: 2026-07-17

---

## Overview

SalesOS provides a RESTful API at `https://api.salesos.com` (production) or `http://localhost:8000` (development). All endpoints return JSON. The API is versioned via URL prefix `/api/v1/`.

Interactive docs are available at:
- Production: `https://api.salesos.com/docs` (Swagger UI)
- Development: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

FastAPI auto-generates an OpenAPI 3.0 spec at `GET /openapi.json`.

---

## Authentication

All endpoints (except `/health`) require a Bearer JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Obtain Token

```
POST /api/v1/identity/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

Response:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Refresh Token

```
POST /api/v1/identity/refresh
Authorization: Bearer <refresh_token>
```

---

## Core Endpoints

### Identity & Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/identity/register` | Register new user |
| POST | `/api/v1/identity/login` | Login, returns JWT |
| POST | `/api/v1/identity/refresh` | Refresh access token |
| POST | `/api/v1/identity/forgot-password` | Request password reset |
| POST | `/api/v1/identity/reset-password` | Reset password with token |

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/dashboard/summary` | Dashboard KPIs and metrics |
| GET | `/api/v1/dashboard/widgets` | Widget configuration |
| GET | `/api/v1/dashboard/notifications` | User notifications |

### Companies

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/companies` | List/search companies |
| GET | `/api/v1/companies/{id}` | Get company details |
| POST | `/api/v1/companies` | Create company |
| PUT | `/api/v1/companies/{id}` | Update company |
| DELETE | `/api/v1/companies/{id}` | Delete company |

### Search

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/search` | Full-text + semantic hybrid search |
| GET | `/api/v1/search/facets` | Available facet values |
| GET | `/api/v1/search/suggestions` | Autocomplete suggestions |

Supports three strategies: `fulltext`, `semantic`, `hybrid`. Uses RRF (Reciprocal Rank Fusion) for hybrid ranking.

### Entity Resolution

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/entity-resolution/match` | Find matching companies |
| POST | `/api/v1/entity-resolution/merge` | Merge duplicate companies |
| GET | `/api/v1/entity-resolution/candidates/{id}` | Get merge candidates |

### AI Copilot

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/copilot/query` | Ask AI copilot a question |
| GET | `/api/v1/copilot/history` | Copilot conversation history |
| DELETE | `/api/v1/copilot/history` | Clear conversation history |

### NBA (Next Best Action)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/nba/recommendations` | Get NBA recommendations |
| POST | `/api/v1/nba/action` | Record action on recommendation |
| GET | `/api/v1/nba/insights` | NBA analytics insights |

### Pipeline

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/pipeline/summary` | Pipeline overview and totals |
| GET | `/api/v1/pipeline/stages` | Pipeline stages configuration |
| GET | `/api/v1/pipeline/opportunities` | Pipeline opportunities |

### Revenue

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/revenue/dashboard` | Revenue KPIs and metrics |
| GET | `/api/v1/revenue/forecast` | Revenue forecast data |
| GET | `/api/v1/revenue/trends` | Revenue trend analysis |

### Knowledge Graph

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/knowledge-graph/entities` | List graph entities |
| GET | `/api/v1/knowledge-graph/relationships` | List entity relationships |
| POST | `/api/v1/knowledge-graph/query` | Query the knowledge graph |
| GET | `/api/v1/knowledge-graph/company/{id}` | Company subgraph |

### Workflow

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/workflows` | List workflows |
| POST | `/api/v1/workflows` | Create workflow |
| PUT | `/api/v1/workflows/{id}` | Update workflow |
| POST | `/api/v1/workflows/{id}/trigger` | Trigger workflow execution |

### Feature Store

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/feature-store/features` | List available features |
| POST | `/api/v1/feature-store/compute` | Compute features on demand |
| GET | `/api/v1/feature-store/entity/{id}` | Get feature values for entity |

### Data Fabric

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/data-fabric/enrich` | Enrich company data |
| GET | `/api/v1/data-fabric/sources` | List data sources |
| GET | `/api/v1/data-fabric/status/{job_id}` | Check enrichment job status |

### Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/tenants` | List tenants (admin) |
| POST | `/api/v1/admin/tenants` | Create tenant (admin) |
| GET | `/api/v1/admin/users` | List users (admin) |
| GET | `/api/v1/admin/feature-flags` | List feature flags |
| PUT | `/api/v1/admin/feature-flags/{flag}` | Toggle feature flag |
| GET | `/api/v1/admin/sla-report` | SLA compliance report |

### Monitoring & Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | General health check |
| GET | `/health/live` | K8s liveness probe |
| GET | `/health/ready` | K8s readiness probe |
| GET | `/health/detailed` | Full subsystem health |
| GET | `/health/dependencies` | Individual dependency status |
| GET | `/ping` | Simple reachability check |
| GET | `/metrics` | Prometheus-formatted metrics (authed) |
| GET | `/metrics/pool` | DB connection pool stats |
| GET | `/metrics/app` | App-level metrics (WebSocket, cache) |

---

## Pagination

List endpoints support cursor-based pagination:

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Results per page (default 20, max 100) |
| `offset` | integer | Offset from start (default 0) |
| `sort_by` | string | Sort field |
| `sort_order` | string | `asc` or `desc` |

Response includes `total` count and pagination metadata.

---

## Error Handling

All errors return a consistent JSON envelope:

```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "errors": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

HTTP status codes:
- `200` — Success
- `201` — Created
- `400` — Bad request / validation error
- `401` — Unauthenticated
- `403` — Forbidden
- `404` — Not found
- `422` — Unprocessable entity
- `429` — Rate limited
- `500` — Internal server error

---

## Rate Limiting

| Tier | Limit | Scope |
|------|-------|-------|
| Authenticated | 100 requests/min | Per IP |
| Search | 30 requests/min | Per IP |
| Anonymous | 20 requests/min | Per IP |

Rate limit headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. On exceed: `429` with `Retry-After` header.

---

## WebSocket

Real-time notifications available at `/notifications/ws`:

- Requires JWT as query param: `wss://api.salesos.com/notifications/ws?token=<jwt>`
- Supports heartbeat, copilot streaming, and real-time updates
- Protocol: JSON messages with `type`, `payload`, `id` fields
