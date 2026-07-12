# Entity Resolution API

> **حلّ الهويات — كشف الدوال المكررة ودمجها بدقة عالية**

Base path: `/api/v1/entity-resolution`

---

## Overview

The Entity Resolution API detects duplicate companies and contacts across your data using **pg_trgm fuzzy matching**. It identifies potential duplicates, scores them by confidence, and merges records while preserving the most complete data.

**Merge Strategy:** Preserve the oldest record as the primary; enrich it from the newest record's fields.

---

## Match Entities

```
POST /api/v1/entity-resolution/match
```

Find matching entities by company name, CR number, or other identifiers.

**Permissions:** `entity-resolution:read`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Company name, CR number, or search text |
| `entity_type` | string | Yes | `company` or `contact` |
| `threshold` | number | No | Minimum confidence score (0–1). Default: `0.7` |
| `limit` | integer | No | Max results to return. Default: `10`, Max: `50` |

### Example Request

```bash
curl -X POST "https://api.salesos.sa/api/v1/entity-resolution/match" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "شركة الرياض للتكنولوجيا",
    "entity_type": "company",
    "threshold": 0.8,
    "limit": 5
  }'
```

### Example Response

```json
{
  "matches": [
    {
      "entity_id": "comp_01HXYZ123456",
      "name": "شركة الرياض للتكنولوجيا",
      "cr_number": "1010893201",
      "confidence": 0.96,
      "match_reasons": ["name_trigram:0.92", "cr_exact:1.0"],
      "created_at": "2025-11-20T08:00:00.000Z"
    },
    {
      "entity_id": "comp_01HXYZ789012",
      "name": "الرياض للتكنولوجيا المحدودة",
      "cr_number": "1010893201",
      "confidence": 0.88,
      "match_reasons": ["name_trigram:0.79", "cr_exact:1.0"],
      "created_at": "2026-01-05T12:30:00.000Z"
    }
  ],
  "query": "شركة الرياض للتكنولوجيا",
  "total_matches": 2
}
```

---

## Merge Entities

```
POST /api/v1/entity-resolution/merge
```

Merge duplicate entities into a single canonical record. The **oldest record** is preserved as the primary and enriched with data from the **newest record**.

**Permissions:** `entity-resolution:write`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `primary_id` | string | Yes | Entity ID to keep as the primary record |
| `merge_id` | string | Yes | Entity ID to merge into the primary |
| `field_strategy` | object | No | Per-field override: `"primary"`, `"merge"`, or `"newest"` |

### Example Request

```bash
curl -X POST "https://api.salesos.sa/api/v1/entity-resolution/merge" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_id": "comp_01HXYZ123456",
    "merge_id": "comp_01HXYZ789012",
    "field_strategy": {
      "phone": "newest",
      "email": "newest",
      "address": "primary"
    }
  }'
```

### Example Response

```json
{
  "merged_entity": {
    "entity_id": "comp_01HXYZ123456",
    "name": "شركة الرياض للتكنولوجيا",
    "cr_number": "1010893201",
    "phone": "+966501234567",
    "email": "info@riyadh-tech.sa",
    "address": "الرياض، حي العليا",
    "merged_from": ["comp_01HXYZ789012"],
    "merged_at": "2026-07-12T10:15:00.000Z",
    "fields_updated": ["phone", "email"]
  },
  "merged_count": 1
}
```

---

## Get Merge Candidates

```
GET /api/v1/entity-resolution/candidates
```

Retrieve potential duplicate entities that are candidates for merging.

**Permissions:** `entity-resolution:read`

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `entity_type` | string | — | `company` or `contact` (required) |
| `min_confidence` | number | `0.7` | Minimum confidence score |
| `max_confidence` | number | `1.0` | Maximum confidence score |
| `page` | integer | `1` | Page number |
| `page_size` | integer | `20` | Results per page (max: `100`) |

### Example Request

```bash
curl -X GET "https://api.salesos.sa/api/v1/entity-resolution/candidates?entity_type=company&min_confidence=0.8&page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

### Example Response

```json
{
  "candidates": [
    {
      "pair": {
        "entity_a": {
          "id": "comp_01HXYZ123456",
          "name": "شركة الرياض للتكنولوجيا"
        },
        "entity_b": {
          "id": "comp_01HXYZ789012",
          "name": "الرياض للتكنولوجيا المحدودة"
        }
      },
      "confidence": 0.96,
      "match_reasons": ["name_trigram:0.92", "cr_exact:1.0"],
      "recommended_action": "merge"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 14,
    "total_pages": 2
  }
}
```

---

## Matching Algorithm

| Component | Description |
|-----------|-------------|
| **pg_trgm** | Trigram-based fuzzy matching on text fields |
| **CR Number** | Exact match on Commercial Registration number |
| **Arabic Normalization** | Normalizes Arabic text before comparison (diacritics, whitespace, Alef variants) |
| **Confidence Score** | Weighted average of all match signals (0–1 scale) |

### Confidence Thresholds

| Score | Interpretation |
|-------|----------------|
| 0.9–1.0 | Very high — likely exact duplicate |
| 0.7–0.9 | High — probable duplicate, review recommended |
| 0.5–0.7 | Medium — possible match, manual review required |
| 0.0–0.5 | Low — unlikely to be a duplicate |

---

## Related

| Resource | Link |
|----------|------|
| Hybrid Search API | [Search](search.md) |
| Feature Store API | [Feature Store](feature-store.md) |
| Knowledge Graph API | [Knowledge Graph](knowledge-graph.md) |
| Data Fabric Pipeline | [Data Fabric](data-fabric.md) |
