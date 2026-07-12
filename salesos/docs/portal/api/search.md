# Search API

> **البحث الهجين — بحث كامل النصوص + بحث دلالي بتقنية RRF**

Base path: `/api/v1/search`

---

## Overview

The Search API provides **hybrid search** combining full-text search (PostgreSQL tsvector) with semantic search (pgvector embeddings), fused using **Reciprocal Rank Fusion (RRF)** scoring. It supports Arabic text normalization, company and contact search, faceted filtering, and autocomplete suggestions.

---

## Hybrid Search

```
POST /api/v1/search
```

Execute a hybrid search across all indexed entities.

**Permissions:** `search:read`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | Yes | Search query text (supports Arabic and English) |
| `type` | string | No | Filter by entity type: `company`, `contact`, `deal`, or `all` (default: `all`) |
| `filters` | object | No | Key-value filters (e.g., `{"industry": "technology"}`) |
| `sort` | string | No | Sort order: `relevance` (default), `name`, `created_at` |
| `page` | integer | No | Page number. Default: `1` |
| `page_size` | integer | No | Results per page. Default: `20`, Max: `100` |

### Example Request

```bash
curl -X POST "https://api.salesos.sa/api/v1/search" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "شركات تقنية في الرياض",
    "type": "company",
    "filters": {
      "industry": "technology",
      "employee_count_min": 50
    },
    "sort": "relevance",
    "page": 1,
    "page_size": 10
  }'
```

### Example Response

```json
{
  "results": [
    {
      "entity_id": "comp_01HXYZ123456",
      "entity_type": "company",
      "name": "شركة الرياض للتكنولوجيا",
      "snippet": "Leading provider of <em>enterprise software</em> solutions in <em>Riyadh</em>",
      "score": 0.94,
      "score_breakdown": {
        "full_text": 0.91,
        "semantic": 0.97,
        "rrf_fusion": 0.94
      },
      "highlights": {
        "name": ["<em>التكنولوجيا</em>"],
        "description": ["<em>enterprise software</em> solutions"]
      }
    },
    {
      "entity_id": "comp_01HXYZ789012",
      "entity_type": "company",
      "name": "شركة جدة للبرمجيات",
      "snippet": "Software development company based in <em>Riyadh</em> with focus on <em>technology</em>",
      "score": 0.82,
      "score_breakdown": {
        "full_text": 0.78,
        "semantic": 0.86,
        "rrf_fusion": 0.82
      },
      "highlights": {
        "name": [],
        "description": ["<em>technology</em>"]
      }
    }
  ],
  "query": "شركات تقنية في الرياض",
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 23,
    "total_pages": 3
  },
  "search_metadata": {
    "engine": "hybrid",
    "latency_ms": 120,
    "total_indexed": 4521
  }
}
```

---

## Autocomplete Suggestions

```
GET /api/v1/search/suggest
```

Fast prefix-based autocomplete for search boxes.

**Permissions:** `search:read`

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | Yes | Partial search query (min 2 chars) |
| `type` | string | No | Entity type filter: `company`, `contact`, `deal` |
| `limit` | integer | No | Max suggestions. Default: `5`, Max: `10` |

### Example Request

```bash
curl -X GET "https://api.salesos.sa/api/v1/search/suggest?q=شركة ال&limit=5" \
  -H "Authorization: Bearer <token>"
```

### Example Response

```json
{
  "suggestions": [
    {
      "text": "شركة الرياض للتكنولوجيا",
      "entity_id": "comp_01HXYZ123456",
      "entity_type": "company",
      "match_type": "prefix"
    },
    {
      "text": "شركة الرياض للمقاولات",
      "entity_id": "comp_01HXYZ333333",
      "entity_type": "company",
      "match_type": "prefix"
    },
    {
      "text": "شركة الدمام للحلول",
      "entity_id": "comp_01HXYZ999999",
      "entity_type": "company",
      "match_type": "fuzzy"
    }
  ],
  "query": "شركة ال",
  "total": 3
}
```

---

## Faceted Search

```
POST /api/v1/search/facets
```

Execute a faceted search returning aggregate counts for filtering dimensions.

**Permissions:** `search:read`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `facets` | array | Yes | Array of facet field names |
| `filters` | object | No | Active filters to narrow facet calculation |

### Example Request

```bash
curl -X POST "https://api.salesos.sa/api/v1/search/facets" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "شركات تقنية",
    "facets": ["industry", "city", "employee_count_range"],
    "filters": {}
  }'
```

### Example Response

```json
{
  "query": "شركات تقنية",
  "total_results": 45,
  "facets": {
    "industry": [
      { "value": "technology", "count": 28 },
      { "value": "finance", "count": 9 },
      { "value": "healthcare", "count": 8 }
    ],
    "city": [
      { "value": "الرياض", "count": 31 },
      { "value": "جدة", "count": 9 },
      { "value": "الدمام", "count": 5 }
    ],
    "employee_count_range": [
      { "value": "1-50", "count": 12 },
      { "value": "51-200", "count": 20 },
      { "value": "201-1000", "count": 10 },
      { "value": "1000+", "count": 3 }
    ]
  }
}
```

---

## Search Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Full-text** | PostgreSQL tsvector + GIN index | Keyword matching, phrase search |
| **Semantic** | pgvector (HNSW) | Meaning-based similarity search |
| **Fusion** | Reciprocal Rank Fusion (RRF) | Combines scores from both engines |
| **Arabic** | Custom normalizer | Diacritics, Alef variants, whitespace normalization |

### RRF Scoring Formula

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

Where `k = 60` (standard constant) and `rank_i(d)` is the rank of document `d` in result list `i`.

---

## Arabic Text Normalization

| Normalization | Before | After |
|---------------|--------|-------|
| Alef variants | أ, إ, آ | ا |
| Diacritics | مَكْتَبَة | مكتبة |
| Whitespace | الرياضِ   التكنولوجيا | الرياض التكنولوجيا |
| Ta Marbuta | مدرسة | مدرسه |

---

## Pagination

| Param | Type | Default | Max |
|-------|------|---------|-----|
| `page` | integer | `1` | — |
| `page_size` | integer | `20` | `100` |

The `max_page_size` guard rejects requests with `page_size > 100`.

---

## Related

| Resource | Link |
|----------|------|
| Entity Resolution API | [Entity Resolution](entity-resolution.md) |
| Feature Store API | [Feature Store](feature-store.md) |
| Knowledge Graph API | [Knowledge Graph](knowledge-graph.md) |
| Data Fabric Pipeline | [Data Fabric](data-fabric.md) |
