# Knowledge Graph API

> **الرسم البياني للمعرفة — ربط الكيانات والعلاقات في شبكة ذكية**

Base path: `/api/v1/graph`

---

## Overview

The Knowledge Graph API maps relationships between companies, contacts, and deals using a **Neo4j-backed graph store** with automatic SQL fallback for high availability. Relationships are typed, weighted, and support traversal queries.

---

## Get Entity Graph

```
GET /api/v1/graph/{entity_type}/{entity_id}
```

Retrieve the full graph neighborhood for an entity, including direct relationships and their connected entities.

**Permissions:** `graph:read`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `entity_type` | string | `company`, `contact`, or `deal` |
| `entity_id` | string | Entity identifier |

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `depth` | integer | `1` | Traversal depth (1–3) |
| `relationship_types` | string | — | Comma-separated types to filter |
| `limit` | integer | `50` | Max nodes to return (max: `200`) |

### Example Request

```bash
curl -X GET "https://api.salesos.sa/api/v1/graph/company/comp_01HXYZ123456?depth=2&limit=30" \
  -H "Authorization: Bearer <token>"
```

### Example Response

```json
{
  "entity": {
    "id": "comp_01HXYZ123456",
    "type": "company",
    "name": "شركة الرياض للتكنولوجيا"
  },
  "nodes": [
    {
      "id": "comp_01HXYZ123456",
      "type": "company",
      "name": "شركة الرياض للتكنولوجيا"
    },
    {
      "id": "comp_01HXYZ789012",
      "type": "company",
      "name": "شركة جدة للبرمجيات"
    },
    {
      "id": "cont_01HXYZ345678",
      "type": "contact",
      "name": "محمد العلي"
    }
  ],
  "relationships": [
    {
      "id": "rel_001",
      "type": "SUPPLIER",
      "source": "comp_01HXYZ789012",
      "target": "comp_01HXYZ123456",
      "weight": 0.9,
      "created_at": "2026-03-15T10:00:00.000Z"
    },
    {
      "id": "rel_002",
      "type": "OWNS",
      "source": "cont_01HXYZ345678",
      "target": "comp_01HXYZ123456",
      "weight": 1.0,
      "created_at": "2025-11-20T08:00:00.000Z"
    }
  ],
  "total_nodes": 3,
  "total_relationships": 2
}
```

---

## Get Relationships

```
GET /api/v1/graph/relationships/{entity_type}/{entity_id}
```

List all relationships for a specific entity.

**Permissions:** `graph:read`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `entity_type` | string | `company`, `contact`, or `deal` |
| `entity_id` | string | Entity identifier |

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | — | Filter by relationship type |
| `direction` | string | `both` | `incoming`, `outgoing`, or `both` |
| `min_weight` | number | `0` | Minimum relationship weight |
| `page` | integer | `1` | Page number |
| `page_size` | integer | `20` | Results per page (max: `100`) |

### Example Request

```bash
curl -X GET "https://api.salesos.sa/api/v1/graph/relationships/company/comp_01HXYZ123456?type=SUPPLIER&direction=outgoing" \
  -H "Authorization: Bearer <token>"
```

### Example Response

```json
{
  "relationships": [
    {
      "id": "rel_001",
      "type": "SUPPLIER",
      "source": {
        "id": "comp_01HXYZ789012",
        "type": "company",
        "name": "شركة جدة للبرمجيات"
      },
      "target": {
        "id": "comp_01HXYZ123456",
        "type": "company",
        "name": "شركة الرياض للتكنولوجيا"
      },
      "weight": 0.9,
      "metadata": {
        "since": "2026-03-15",
        "contract_value": 500000
      },
      "created_at": "2026-03-15T10:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

## Create Relationship

```
POST /api/v1/graph/relationships
```

Create a new relationship between two entities.

**Permissions:** `graph:write`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | string | Yes | Source entity ID |
| `target_id` | string | Yes | Target entity ID |
| `type` | string | Yes | Relationship type (see below) |
| `weight` | number | No | Confidence weight (0–1). Default: `1.0` |
| `metadata` | object | No | Arbitrary key-value metadata |

### Example Request

```bash
curl -X POST "https://api.salesos.sa/api/v1/graph/relationships" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "comp_01HXYZ123456",
    "target_id": "comp_01HXYZ999999",
    "type": "PARTNER",
    "weight": 0.85,
    "metadata": {
      "partnership_type": "technology",
      "since": "2026-07-01"
    }
  }'
```

### Example Response

```json
{
  "relationship": {
    "id": "rel_003",
    "type": "PARTNER",
    "source": {
      "id": "comp_01HXYZ123456",
      "name": "شركة الرياض للتكنولوجيا"
    },
    "target": {
      "id": "comp_01HXYZ999999",
      "name": "شركة الدمام للحلول"
    },
    "weight": 0.85,
    "metadata": {
      "partnership_type": "technology",
      "since": "2026-07-01"
    },
    "created_at": "2026-07-12T12:00:00.000Z"
  }
}
```

---

## Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| `OWNS` | Ownership or control | Contact owns Company |
| `SUPPLIER` | Vendor/supplier relationship | Company A supplies Company B |
| `CUSTOMER` | Client/customer relationship | Company A is a customer of Company B |
| `COMPETITOR` | Competitive relationship | Two companies in the same market |
| `PARTNER` | Strategic partnership | Joint venture or alliance |
| `INVESTOR` | Investment relationship | Investor funds Company |

---

## Backend

| Component | Details |
|-----------|---------|
| **Primary** | Neo4j graph database |
| **Fallback** | PostgreSQL relational tables |
| **Consistency** | Neo4j is source of truth; SQL is read-replica |
| **Latency** | Neo4j: < 50ms p95; SQL fallback: < 200ms p95 |

---

## Related

| Resource | Link |
|----------|------|
| Entity Resolution API | [Entity Resolution](entity-resolution.md) |
| Feature Store API | [Feature Store](feature-store.md) |
| Data Fabric Pipeline | [Data Fabric](data-fabric.md) |
| Search API | [Search](search.md) |
