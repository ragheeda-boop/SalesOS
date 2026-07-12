# Feature Store API

> **مخزن الميزات — تخزين واسترجاع سمات الكيانات بالوقت الحقيقي**

Base path: `/api/v1/features`

---

## Overview

The Feature Store provides a centralized repository for entity features used by scoring engines, ML models, and decision pipelines. Features are stored per entity with support for multiple data types, time-to-live (TTL) expiry, and versioning.

---

## Get Entity Features

```
GET /api/v1/features/{entity_type}/{entity_id}
```

Retrieve all features for a specific entity.

**Permissions:** `features:read`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `entity_type` | string | `company`, `contact`, or `deal` |
| `entity_id` | string | Entity identifier (e.g., `comp_01HXYZ123456`) |

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `feature_names` | string | — | Comma-separated feature names to filter |
| `include_expired` | boolean | `false` | Include features past their TTL |

### Example Request

```bash
curl -X GET "https://api.salesos.sa/api/v1/features/company/comp_01HXYZ123456?feature_names=revenue_score,risk_tier" \
  -H "Authorization: Bearer <token>"
```

### Example Response

```json
{
  "entity_id": "comp_01HXYZ123456",
  "entity_type": "company",
  "features": [
    {
      "name": "revenue_score",
      "type": "numeric",
      "value": 87.5,
      "updated_at": "2026-07-12T08:00:00.000Z",
      "expires_at": null,
      "source": "scoring_engine"
    },
    {
      "name": "risk_tier",
      "type": "categorical",
      "value": "low",
      "updated_at": "2026-07-10T14:30:00.000Z",
      "expires_at": "2026-07-24T14:30:00.000Z",
      "source": "decision_platform"
    }
  ],
  "total_features": 2
}
```

---

## Store / Update Features

```
POST /api/v1/features/{entity_type}
```

Store or update one or more features for entities of a given type.

**Permissions:** `features:write`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `entity_type` | string | `company`, `contact`, or `deal` |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | string | Yes | Entity identifier |
| `features` | array | Yes | Array of feature objects |

#### Feature Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Feature name (snake_case) |
| `type` | string | Yes | `numeric`, `categorical`, `text`, `embedding`, or `datetime` |
| `value` | any | Yes | Feature value matching the declared type |
| `ttl_hours` | integer | No | Hours until feature expires (omit for permanent) |
| `source` | string | No | Origin system (default: `api`) |

### Example Request

```bash
curl -X POST "https://api.salesos.sa/api/v1/features/company" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "comp_01HXYZ123456",
    "features": [
      {
        "name": "annual_revenue",
        "type": "numeric",
        "value": 15000000,
        "ttl_hours": 720,
        "source": "enrichment_pipeline"
      },
      {
        "name": "industry_segment",
        "type": "categorical",
        "value": "technology",
        "source": "manual"
      },
      {
        "name": "company_description",
        "type": "text",
        "value": "Leading provider of enterprise software solutions in Saudi Arabia",
        "ttl_hours": 168
      },
      {
        "name": "last_contact",
        "type": "datetime",
        "value": "2026-07-10T09:15:00.000Z",
        "source": "email_intelligence"
      }
    ]
  }'
```

### Example Response

```json
{
  "entity_id": "comp_01HXYZ123456",
  "entity_type": "company",
  "features_stored": 4,
  "features_updated": 1,
  "stored_at": "2026-07-12T11:00:00.000Z"
}
```

---

## Remove a Feature

```
DELETE /api/v1/features/{entity_type}/{entity_id}/{feature_name}
```

Remove a specific feature from an entity.

**Permissions:** `features:write`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `entity_type` | string | `company`, `contact`, or `deal` |
| `entity_id` | string | Entity identifier |
| `feature_name` | string | Name of the feature to delete |

### Example Request

```bash
curl -X DELETE "https://api.salesos.sa/api/v1/features/company/comp_01HXYZ123456/annual_revenue" \
  -H "Authorization: Bearer <token>"
```

### Example Response

```json
{
  "deleted": true,
  "entity_id": "comp_01HXYZ123456",
  "feature_name": "annual_revenue",
  "deleted_at": "2026-07-12T11:30:00.000Z"
}
```

---

## Feature Types

| Type | Value Format | Example |
|------|-------------|---------|
| `numeric` | number | `87.5`, `15000000` |
| `categorical` | string | `"low"`, `"technology"`, `"enterprise"` |
| `text` | string | `"Leading provider of enterprise software"` |
| `embedding` | array of floats | `[0.021, -0.134, 0.891, ...]` (768–1536 dims) |
| `datetime` | ISO 8601 string | `"2026-07-12T08:00:00.000Z"` |

---

## TTL Expiry

Features with a `ttl_hours` value automatically expire and are excluded from results after the configured period. To retrieve expired features, pass `include_expired=true` as a query parameter.

| TTL | Use Case |
|-----|----------|
| 24h (168h) | Short-lived signals: email open, page visit |
| 7d (168h) | Weekly metrics: engagement score, activity |
| 30d (720h) | Monthly aggregates: revenue, deal count |
| No TTL | Permanent: industry, founding year, CR number |

---

## Related

| Resource | Link |
|----------|------|
| Entity Resolution API | [Entity Resolution](entity-resolution.md) |
| Knowledge Graph API | [Knowledge Graph](knowledge-graph.md) |
| Data Fabric Pipeline | [Data Fabric](data-fabric.md) |
| Search API | [Search](search.md) |
