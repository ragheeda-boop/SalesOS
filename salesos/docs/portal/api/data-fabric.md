# Data Fabric Pipeline API

> **منسوج البيانات — أنبوب معالجة متكامل يربط كل مكونات Data Fabric**

Base path: `/api/v1/data-fabric`

---

## Overview

The Data Fabric Pipeline orchestrates the full data processing workflow, coordinating Entity Resolution, Hybrid Search, Feature Store, and Knowledge Graph into a single end-to-end pipeline. Trigger a pipeline run for any entity and track its progress through each stage.

---

## Pipeline Stages

| Stage | Description | Components |
|-------|-------------|------------|
| **1. Ingest** | Collect raw data from source systems | CRM, email, web, API |
| **2. Normalize** | Standardize fields, Arabic text normalization | Text normalizer, schema mapper |
| **3. Resolve** | Detect duplicates, merge entities | Entity Resolution (pg_trgm) |
| **4. Enrich** | Enrich with external and computed features | Feature Store, enrichment APIs |
| **5. Store** | Persist enriched features | Feature Store (PostgreSQL) |
| **6. Index** | Build search indices and graph relationships | Hybrid Search + Knowledge Graph |

---

## Trigger Pipeline

```
POST /api/v1/data-fabric/pipeline
```

Start a full Data Fabric pipeline run for an entity.

**Permissions:** `data-fabric:write`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_type` | string | Yes | `company`, `contact`, or `deal` |
| `entity_id` | string | Yes | Entity identifier |
| `source` | string | No | Origin of the request: `api`, `webhook`, `scheduled` (default: `api`) |
| `stages` | array | No | Subset of stages to run (default: all 6 stages) |

### Example Request

```bash
curl -X POST "https://api.salesos.sa/api/v1/data-fabric/pipeline" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "company",
    "entity_id": "comp_01HXYZ123456",
    "source": "api"
  }'
```

### Example Response

```json
{
  "pipeline_id": "pipe_01HXZA123456",
  "status": "started",
  "entity_type": "company",
  "entity_id": "comp_01HXYZ123456",
  "stages": [
    { "name": "ingest", "status": "queued", "started_at": null },
    { "name": "normalize", "status": "queued", "started_at": null },
    { "name": "resolve", "status": "queued", "started_at": null },
    { "name": "enrich", "status": "queued", "started_at": null },
    { "name": "store", "status": "queued", "started_at": null },
    { "name": "index", "status": "queued", "started_at": null }
  ],
  "created_at": "2026-07-12T14:00:00.000Z"
}
```

---

## Check Pipeline Status

```
GET /api/v1/data-fabric/status/{pipeline_id}
```

Get the current status and progress of a pipeline run.

**Permissions:** `data-fabric:read`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `pipeline_id` | string | Pipeline run identifier |

### Example Request

```bash
curl -X GET "https://api.salesos.sa/api/v1/data-fabric/status/pipe_01HXZA123456" \
  -H "Authorization: Bearer <token>"
```

### Example Response

```json
{
  "pipeline_id": "pipe_01HXZA123456",
  "status": "running",
  "entity_type": "company",
  "entity_id": "comp_01HXYZ123456",
  "stages": [
    {
      "name": "ingest",
      "status": "completed",
      "started_at": "2026-07-12T14:00:00.100Z",
      "completed_at": "2026-07-12T14:00:01.200Z",
      "duration_ms": 1100
    },
    {
      "name": "normalize",
      "status": "completed",
      "started_at": "2026-07-12T14:00:01.200Z",
      "completed_at": "2026-07-12T14:00:02.050Z",
      "duration_ms": 850
    },
    {
      "name": "resolve",
      "status": "completed",
      "started_at": "2026-07-12T14:00:02.050Z",
      "completed_at": "2026-07-12T14:00:05.300Z",
      "duration_ms": 3250,
      "output": {
        "duplicates_found": 2,
        "merge_performed": true
      }
    },
    {
      "name": "enrich",
      "status": "running",
      "started_at": "2026-07-12T14:00:05.300Z",
      "completed_at": null
    },
    {
      "name": "store",
      "status": "queued",
      "started_at": null
    },
    {
      "name": "index",
      "status": "queued",
      "started_at": null
    }
  ],
  "started_at": "2026-07-12T14:00:00.100Z",
  "completed_at": null,
  "total_duration_ms": null,
  "progress_pct": 50
}
```

### Completed Pipeline Example

```json
{
  "pipeline_id": "pipe_01HXZA123456",
  "status": "completed",
  "entity_type": "company",
  "entity_id": "comp_01HXYZ123456",
  "stages": [
    { "name": "ingest", "status": "completed", "duration_ms": 1100 },
    { "name": "normalize", "status": "completed", "duration_ms": 850 },
    { "name": "resolve", "status": "completed", "duration_ms": 3250, "output": { "duplicates_found": 2, "merge_performed": true } },
    { "name": "enrich", "status": "completed", "duration_ms": 4500, "output": { "features_added": 12 } },
    { "name": "store", "status": "completed", "duration_ms": 600, "output": { "features_stored": 12 } },
    { "name": "index", "status": "completed", "duration_ms": 1800, "output": { "search_indexed": true, "graph_updated": true } }
  ],
  "started_at": "2026-07-12T14:00:00.100Z",
  "completed_at": "2026-07-12T14:00:12.100Z",
  "total_duration_ms": 12000,
  "progress_pct": 100
}
```

---

## Pipeline Status Values

| Status | Description |
|--------|-------------|
| `started` | Pipeline triggered, stages queued |
| `running` | At least one stage is in progress |
| `completed` | All stages finished successfully |
| `failed` | One or more stages failed |
| `partial` | Some stages completed, some skipped |

### Stage Status Values

| Status | Description |
|--------|-------------|
| `queued` | Waiting to start |
| `running` | Currently processing |
| `completed` | Finished successfully |
| `failed` | Encountered an error |
| `skipped` | Not requested in this run |

---

## Component Integration

| Component | Pipeline Stage | API |
|-----------|---------------|-----|
| Entity Resolution | Resolve | [Entity Resolution](entity-resolution.md) |
| Feature Store | Enrich, Store | [Feature Store](feature-store.md) |
| Hybrid Search | Index | [Search](search.md) |
| Knowledge Graph | Index | [Knowledge Graph](knowledge-graph.md) |

---

## Related

| Resource | Link |
|----------|------|
| Entity Resolution API | [Entity Resolution](entity-resolution.md) |
| Feature Store API | [Feature Store](feature-store.md) |
| Knowledge Graph API | [Knowledge Graph](knowledge-graph.md) |
| Search API | [Search](search.md) |
| v0.2.0 Release Notes | [Release v0.2.0](../releases/v0.2.0.md) |
