# ADR-027: Feature Store for Entity-Level Features

**Status:** Accepted  
**Date:** 2026-07-12  
**Deciders:** CTO, Chief Architect, AI Engineer  
**Tags:** architecture, data-fabric, feature-store, ml, ai, enrichment

## Context

SalesOS uses features (computed signals, scores, and enrichment data) across multiple domains:

- **Scoring domain** — company health scores, contact engagement scores
- **AI domain** — entity embeddings, sentiment scores, classification labels
- **Enrichment domain** — industry classification, company size estimates, technology stack detection
- **CRM domain** — deal probability, pipeline velocity, conversion signals

These features are currently scattered across domain-specific tables, leading to:
- Duplicate computation — the same enrichment run by multiple consumers
- Inconsistent feature versions — scoring and AI use different enrichment snapshots
- No TTL management — stale features persist indefinitely
- No bulk operations — enrichment providers update one entity at a time

## Decision

Implement a **Feature Store** as a PostgreSQL-backed key-value store with entity-type partitioning, TTL expiry, and bulk operations.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Feature Store                              │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Scoring     │  │  AI          │  │  Enrichment      │  │
│  │  Features    │  │  Features    │  │  Features        │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘  │
│         │                 │                  │               │
│         ▼                 ▼                  ▼               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Feature Store (PostgreSQL)                │   │
│  │                                                       │   │
│  │  features table (partitioned by entity_type)          │   │
│  │  ├── entity_type + entity_id + feature_key            │   │
│  │  ├── value (JSONB)                                   │   │
│  │  ├── version (integer, auto-increment)               │   │
│  │  ├── source (string — who computed this)             │   │
│  │  ├── ttl_seconds (integer, NULL = never expires)     │   │
│  │  ├── created_at, expires_at                          │   │
│  │  └── metadata (JSONB)                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Bulk Operations Layer                                │   │
│  │  ├── upsert_batch (100+ entities at once)            │   │
│  │  ├── get_batch (fetch features for entity list)      │   │
│  │  ├── expire_stale (background job)                   │   │
│  │  └── snapshot (versioned feature export)             │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    feature_key VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    source VARCHAR(100) NOT NULL,
    ttl_seconds INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',

    UNIQUE(tenant_id, entity_type, entity_id, feature_key)
);

CREATE INDEX idx_features_entity ON features(tenant_id, entity_type, entity_id);
CREATE INDEX idx_features_key ON features(tenant_id, feature_key);
CREATE INDEX idx_features_expires ON features(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_features_source ON features(tenant_id, source);

-- Partitioning by entity_type for query performance
-- (optional, enabled when feature volume exceeds 1M rows per type)
```

### Feature API

```python
class FeatureStore:
    async def get(
        self,
        tenant_id: UUID,
        entity_type: str,
        entity_id: UUID,
        feature_key: str
    ) -> Feature | None:
        """Get a single feature. Returns None if expired or missing."""

    async def get_batch(
        self,
        tenant_id: UUID,
        entity_type: str,
        entity_ids: list[UUID],
        feature_keys: list[str] | None = None
    ) -> dict[UUID, dict[str, Feature]]:
        """Bulk fetch features for multiple entities."""

    async def upsert(
        self,
        tenant_id: UUID,
        entity_type: str,
        entity_id: UUID,
        feature_key: str,
        value: Any,
        source: str,
        ttl_seconds: int | None = None,
        metadata: dict = {}
    ) -> Feature:
        """Write or update a feature. Increments version on update."""

    async def upsert_batch(
        self,
        tenant_id: UUID,
        features: list[FeatureInput]
    ) -> int:
        """Bulk upsert features. Returns count of features written."""
        # Uses PostgreSQL COPY or INSERT ... ON CONFLICT for performance

    async def expire_stale(self, tenant_id: UUID | None = None) -> int:
        """Delete features past their TTL. Run as background job."""

    async def snapshot(
        self,
        tenant_id: UUID,
        entity_type: str,
        entity_id: UUID
    ) -> dict[str, Any]:
        """Get all current (non-expired) features as a dict."""
```

### TTL Strategy

| Feature Category | TTL | Rationale |
|-----------------|-----|-----------|
| Enrichment data | 30 days | External data changes slowly |
| AI embeddings | 90 days | Re-computed on significant changes |
| Scoring signals | 7 days | Scores should reflect recent state |
| Classification labels | 30 days | Stable but updated periodically |
| Manual annotations | None | User-entered data never expires |

### Background Cleanup

```python
# Scheduled every hour via cron or task queue
async def cleanup_expired_features():
    """Delete features where expires_at < NOW()."""
    result = await db.execute("""
        DELETE FROM features
        WHERE expires_at IS NOT NULL
          AND expires_at < NOW()
    """)
    logger.info(f"Expired {result.rowcount} stale features")
```

## Consequences

### Positive
1. **Single source of truth** for all entity-level features across domains
2. **Version tracking** — every feature update is versioned, enabling rollback and audit
3. **TTL management** — stale features are automatically cleaned up
4. **Bulk operations** — enrichment providers can update hundreds of entities in one call
5. **Uses existing PostgreSQL** — no new infrastructure dependency
6. **Source tracking** — every feature records who/what computed it

### Negative
1. **Not optimized for high-frequency writes** — PostgreSQL JSONB is not a write-optimized KV store
2. **No real-time streaming** — features are written synchronously (not event-driven)
3. **Version bloat** — historical versions are not purged (only current + last N retained)
4. **Single-node limitation** — no horizontal scaling for feature writes (mitigated by partitioning)

### Mitigations
- For high-frequency use cases (e.g., real-time scoring), use in-memory cache in front of Feature Store
- Batch upsert uses PostgreSQL `INSERT ... ON CONFLICT` for write efficiency
- Version history is retained for 30 days, then old versions are pruned
- Feature Store is a read-heavy workload (write:read ratio ~1:100), which PostgreSQL handles well

## Compliance

- [x] Uses repository pattern — `FeatureStoreRepository` interface in domain, PostgreSQL implementation in infrastructure
- [x] Tenant isolation — all queries scoped by `tenant_id`
- [x] No cross-domain imports — Feature Store is domain-agnostic (consumed by all domains)
- [x] Entity type partitioning — query performance maintained as data grows
- [x] TTL expiry — stale features are automatically cleaned up
- [x] Automated checks:
  - Features table exists: `SELECT * FROM information_schema.tables WHERE table_name = 'features'`
  - Unique constraint enforced: `SELECT conname FROM pg_constraint WHERE conrelid = 'features'::regclass AND contype = 'u'`
  - Indexes exist: `SELECT * FROM pg_indexes WHERE tablename = 'features'`
  - TTL cleanup job running: `SELECT last_run FROM cron_jobs WHERE name = 'expire_features'`
  - No expired features older than 7 days: `SELECT COUNT(*) FROM features WHERE expires_at < NOW() - INTERVAL '7 days'`
