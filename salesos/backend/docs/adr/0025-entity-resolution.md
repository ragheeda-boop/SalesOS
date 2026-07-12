# ADR-025: Entity Resolution via pg_trgm Fuzzy Matching

**Status:** Accepted  
**Date:** 2026-07-12  
**Deciders:** CTO, Chief Architect, Backend Team  
**Tags:** architecture, data-fabric, entity-resolution, deduplication, postgresql

## Context

SalesOS ingests company and contact data from multiple sources (CR systems, manually entered data, enrichment providers, third-party integrations). This creates duplicate entities across the platform:

- Same company entered with different name variations (e.g., "Samsung Electronics" vs "Samsung Electronics Co., Ltd.")
- Same contact with transliterated Arabic names
- Companies matched by CR number but with different formatting (with/without dashes, leading zeros)
- Merges needed to maintain a single source of truth for relationship graphs, scoring, and AI context

Without entity resolution, the platform produces conflicting intelligence for the same real-world entity, degrading search results, scoring accuracy, and user trust.

## Decision

Implement **Entity Resolution** using PostgreSQL `pg_trgm` extension for fuzzy matching on company names and CR numbers, with a deterministic merge strategy.

### Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Source A (CR)   │     │ Source B (Manual)│     │ Source C (Enrich)│
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Entity Resolution Pipeline                        │
│                                                                      │
│  1. Normalize  →  2. Blocking  →  3. Match  →  4. Merge  →  5. Link │
└──────────────────────────────────────────────────────────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Companies Table │     │ Contacts Table   │     │ Entity Aliases   │
│  (canonical)     │     │ (canonical)      │     │ (lookup)         │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Matching Strategy

| Field | Method | Threshold | Notes |
|-------|--------|-----------|-------|
| Company name | `pg_trgm` similarity | ≥ 0.3 | Trigram-based fuzzy match |
| Company name (Arabic) | Normalized trigram | ≥ 0.3 | Arabic diacritics removed before matching |
| CR number | Exact (normalized) | 1.0 | Strip dashes, spaces, leading zeros |
| Contact name | `pg_trgm` similarity | ≥ 0.4 | Higher threshold for person names |
| Email | Exact (lowercase) | 1.0 | Normalized to lowercase |

### Blocking Rules

To avoid O(n²) comparisons, apply blocking before fuzzy matching:

1. **Country code** — only compare entities in the same country
2. **Entity type** — only compare company-to-company, contact-to-contact
3. **First letter** — same first character of normalized name (Arabic or Latin)

### Merge Strategy

When two entities are matched:

| Rule | Behavior |
|------|----------|
| **Canonical record** | Keep the oldest record (earliest `created_at`) as canonical |
| **Name enrichment** | If newer record has a longer/more complete name, append to `alternate_names` |
| **Data enrichment** | Non-null fields from newer records fill nulls in canonical |
| **Field conflicts** | Canonical wins; conflicts logged in `entity_merge_log` |
| **Relationships** | All relationships from both records are re-pointed to canonical |
| **Soft delete** | Duplicate records are marked `status = 'merged'`, not deleted |

### Database Schema

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE entity_resolution_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    canonical_entity_id UUID NOT NULL,
    duplicate_entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    match_score FLOAT NOT NULL,
    match_method VARCHAR(50) NOT NULL,  -- 'trigram', 'exact_cr', 'manual'
    matched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    merged_at TIMESTAMPTZ,
    merge_status VARCHAR(20) NOT NULL DEFAULT 'pending'  -- pending, merged, rejected
);

CREATE INDEX idx_er_canonical ON entity_resolution_matches(canonical_entity_id);
CREATE INDEX idx_er_duplicate ON entity_resolution_matches(duplicate_entity_id);
CREATE INDEX idx_er_tenant ON entity_resolution_matches(tenant_id);
CREATE INDEX idx_er_status ON entity_resolution_matches(tenant_id, merge_status);

CREATE TABLE entity_merge_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL REFERENCES entity_resolution_matches(id),
    field_name VARCHAR(100) NOT NULL,
    canonical_value JSONB,
    duplicate_value JSONB,
    resolved_value JSONB NOT NULL,
    resolution_reason VARCHAR(50) NOT NULL  -- 'canonical_wins', 'enriched', 'manual'
);
```

### Bulk Operations

```python
# Find potential duplicates for a tenant
async def find_duplicates(
    tenant_id: UUID,
    entity_type: str,
    threshold: float = 0.3,
    batch_size: int = 1000
) -> list[MatchCandidate]:
    """Uses pg_trgm similarity with blocking to find candidate pairs."""

# Merge matched entities
async def merge_entities(
    canonical_id: UUID,
    duplicate_id: UUID,
    tenant_id: UUID
) -> MergeResult:
    """Re-point relationships, enrich canonical, soft-delete duplicate."""
```

## Consequences

### Positive
1. **No external service dependency** — everything runs inside PostgreSQL
2. **ACID guarantees** — merge operations are transactional
3. **Blocking reduces complexity** — O(n) instead of O(n²) comparisons
4. **Arabic support** — pg_trgm handles Arabic text natively with proper collation
5. **Audit trail** — merge_log provides full history of resolution decisions

### Negative
1. **Limited to text similarity** — no ML-based deduplication or entity linking
2. **Threshold tuning required** — different entity types may need different thresholds
3. **Blocking may miss matches** — entities in different countries or with different first letters won't be compared
4. **Single-tenant processing** — cross-tenant resolution not supported (by design)

### Mitigations
- Threshold values are configurable per entity type in the tenant config
- Manual override available via `merge_status = 'manual'` for edge cases
- Future ML-based matching can be added as a second-pass matcher without replacing pg_trgm

## Compliance

- [x] Uses repository pattern — `EntityResolutionRepository` interface in domain, PostgreSQL implementation in infrastructure
- [x] Tenant isolation — all queries scoped by `tenant_id`
- [x] No cross-domain imports — resolution is self-contained within Entity Resolution domain
- [x] Audit logging — every merge logged with before/after values
- [x] Soft delete — merged records retained for 90 days before cleanup
- [x] Automated checks:
  - `pg_trgm` extension exists: `SELECT * FROM pg_extension WHERE extname = 'pg_trgm'`
  - Indexes exist: `SELECT * FROM pg_indexes WHERE tablename = 'entity_resolution_matches'`
  - Match score range validation: `CHECK (match_score >= 0 AND match_score <= 1)`
