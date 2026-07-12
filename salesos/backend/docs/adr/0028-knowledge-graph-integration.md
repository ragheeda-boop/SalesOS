# ADR-028: Knowledge Graph Integration with Neo4j + SQL Fallback

**Status:** Accepted  
**Date:** 2026-07-12  
**Deciders:** CTO, Chief Architect, Backend Team  
**Tags:** architecture, data-fabric, knowledge-graph, neo4j, relationships, graph

## Context

SalesOS needs to model and traverse relationships between entities:

- **Company → Company** — ownership, subsidiaries, suppliers, partners
- **Company → Contact** — employees, board members, advisors
- **Contact → Contact** — reporting lines, referrals, social connections
- **Company → License** — regulatory licenses and permits
- **Deal → Company → Contact** — deal parties and stakeholders

Without a graph representation, relationship queries require expensive JOIN chains and cannot answer questions like:
- "Find all companies in the same ownership group"
- "What is the shortest path between two companies?"
- "Which contacts are within 2 degrees of separation from this company?"

A Knowledge Graph enables natural relationship traversal, community detection, and path analysis.

## Decision

Implement **Knowledge Graph Integration** using Neo4j as the primary graph store with PostgreSQL as fallback for critical paths. Relationship types are defined as a closed enum.

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Knowledge Graph                            │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────────────┐  │
│  │  Neo4j (Primary) │◄────────►│  PostgreSQL (Fallback)    │  │
│  │                  │  dual-   │                           │  │
│  │  - Graph queries │  write   │  - `entity_relationships` │  │
│  │  - Traversal     │          │  - Simple lookups         │  │
│  │  - Path finding  │          │  - Critical path queries  │  │
│  │  - Community det.│          │  - Backup when Neo4j down │  │
│  └────────┬─────────┘          └──────────┬───────────────┘  │
│           │                               │                   │
│           ▼                               ▼                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Graph Service (Unified API)              │   │
│  │                                                       │   │
│  │  get_relationships(entity_id)                        │   │
│  │  find_path(source_id, target_id, max_depth)          │   │
│  │  get_neighbors(entity_id, relationship_type)         │   │
│  │  add_relationship(source, target, type, metadata)    │   │
│  │  get_communities(tenant_id, min_size)                │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Relationship Types (Enum)

```python
class RelationshipType(str, Enum):
    # Company → Company
    OWNS = "OWNS"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    PARTNER = "PARTNER"
    COMPETITOR = "COMPETITOR"

    # Company → Contact
    EMPLOYEE = "EMPLOYEE"
    BOARD_MEMBER = "BOARD_MEMBER"
    ADVISOR = "ADVISOR"
    FOUNDER = "FOUNDER"

    # Contact → Contact
    REPORTS_TO = "REPORTS_TO"
    REFERRED_BY = "REFERRED_BY"
    COLLEAGUE = "COLLEAGUE"

    # Deal → Company/Contact
    DEAL_PARTY = "DEAL_PARTY"
    DEAL_SPONSOR = "DEAL_SPONSOR"
    DEAL_DECISION_MAKER = "DEAL_DECISION_MAKER"

    # Cross-cutting
    RELATED_TO = "RELATED_TO"
    MENTIONED_IN = "MENTIONED_IN"
```

### Neo4j Schema

```cypher
// Company node
CREATE CONSTRAINT company_id IF NOT EXISTS
FOR (c:Company) REQUIRE c.id IS UNIQUE;

CREATE INDEX company_name IF NOT EXISTS
FOR (c:Company) ON (c.name);

// Contact node
CREATE CONSTRAINT contact_id IF NOT EXISTS
FOR (ct:Contact) REQUIRE ct.id IS UNIQUE;

// Relationships
CREATE CONSTRAINT relationship_id IF NOT EXISTS
FOR ()-[r:RELATES_TO]-() REQUIRE r.id IS UNIQUE;

// Example: Company owns subsidiary
MERGE (parent:Company {id: $parent_id})
MERGE (child:Company {id: $child_id})
MERGE (parent)-[:OWNS {
    id: randomUUID(),
    tenant_id: $tenant_id,
    confidence: 0.95,
    source: 'cr_registry',
    created_at: datetime()
}]->(child);
```

### PostgreSQL Fallback Schema

```sql
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    source_entity_type VARCHAR(50) NOT NULL,
    source_entity_id UUID NOT NULL,
    target_entity_type VARCHAR(50) NOT NULL,
    target_entity_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, source_entity_id, target_entity_id, relationship_type)
);

CREATE INDEX idx_er_source ON entity_relationships(tenant_id, source_entity_id);
CREATE INDEX idx_er_target ON entity_relationships(tenant_id, target_entity_id);
CREATE INDEX idx_er_type ON entity_relationships(tenant_id, relationship_type);
```

### Dual-Write Strategy

```python
class KnowledgeGraphService:
    async def add_relationship(
        self,
        tenant_id: UUID,
        source_id: UUID,
        target_id: UUID,
        relationship_type: RelationshipType,
        metadata: dict = {},
        confidence: float = 1.0,
        source: str = "system"
    ) -> Relationship:
        """
        Write to both Neo4j and PostgreSQL.
        Neo4j write is primary; PostgreSQL write is fallback.
        If Neo4j fails, PostgreSQL write still succeeds (eventual consistency).
        """
        rel_id = uuid4()

        # Primary write: Neo4j
        try:
            await self._write_neo4j(
                tenant_id, source_id, target_id,
                relationship_type, metadata, confidence, source, rel_id
            )
        except Neo4jUnavailableError:
            logger.warning(f"Neo4j unavailable, relying on PostgreSQL fallback")
            self._queue_neo4j_retry(rel_id)

        # Fallback write: PostgreSQL (always succeeds if DB is up)
        await self._write_postgres(
            tenant_id, source_id, target_id,
            relationship_type, metadata, confidence, source, rel_id
        )

        return Relationship(id=rel_id, ...)

    async def get_relationships(
        self,
        entity_id: UUID,
        relationship_type: RelationshipType | None = None,
        max_depth: int = 2
    ) -> list[Relationship]:
        """
        Try Neo4j first for graph traversal.
        Fall back to PostgreSQL for simple lookups.
        """
        try:
            return await self._query_neo4j(entity_id, relationship_type, max_depth)
        except Neo4jUnavailableError:
            logger.warning("Neo4j unavailable, falling back to PostgreSQL")
            return await self._query_postgres(entity_id, relationship_type, max_depth)
```

### Graph Traversal Queries

```cypher
// Find all companies in same ownership group (BFS, depth 3)
MATCH path = (start:Company {id: $start_id})-[:OWNS|SUBSIDIARY_OF*1..3]-(related:Company)
WHERE related.id <> $start_id
RETURN related, length(path) AS distance
ORDER BY distance

// Find shortest path between two companies
MATCH path = shortestPath(
    (a:Company {id: $source_id})-[*]-(b:Company {id: $target_id})
)
RETURN path

// Find contacts within 2 degrees of a company
MATCH (c:Company {id: $company_id})-[:EMPLOYEE|FOUNDER|BOARD_MEMBER*1..2]-(ct:Contact)
RETURN ct
LIMIT 50
```

## Consequences

### Positive
1. **Rich graph traversal** — natural language for relationship queries (ownership chains, shortest paths, communities)
2. **Fallback ensures availability** — PostgreSQL provides basic relationship queries even when Neo4j is down
3. **Dual-write consistency** — both stores are updated atomically (Neo4j failure doesn't lose data)
4. **Enum-based relationships** — type safety and discoverability for all relationship types
5. **Confidence scoring** — every relationship tracks how certain we are about it

### Negative
1. **Dual-write complexity** — every write goes to two systems, increasing operational surface
2. **Neo4j operational overhead** — separate database to monitor, back up, and scale
3. **Eventual consistency** — Neo4j retry queue means temporary divergence between stores
4. **Graph query performance** — deep traversals (depth > 5) may be slow on large graphs

### Mitigations
- PostgreSQL fallback covers all critical-path queries (entity details, simple lookups)
- Neo4j retry queue uses exponential backoff with max 3 retries
- Graph depth is capped at 5 for API queries (configurable per endpoint)
- Neo4j connection pooling fixed (context managers used everywhere — see BUG-003 resolution)

## Compliance

- [x] Uses repository pattern — `KnowledgeGraphRepository` interface in domain, Neo4j + PostgreSQL implementations in infrastructure
- [x] Tenant isolation — all queries and writes scoped by `tenant_id`
- [x] No cross-domain imports — Knowledge Graph is consumed by all domains via SDK
- [x] Relationship types are a closed enum — no free-form relationship strings
- [x] Fallback ensures availability — PostgreSQL provides basic queries when Neo4j is down
- [x] Automated checks:
  - Neo4j connectivity: `RETURN 1` query succeeds
  - PostgreSQL fallback table exists: `SELECT * FROM information_schema.tables WHERE table_name = 'entity_relationships'`
  - Relationship types match enum: `SELECT DISTINCT relationship_type FROM entity_relationships WHERE relationship_type NOT IN (...)` returns empty
  - Dual-write consistency: sampling check comparing Neo4j and PostgreSQL relationship counts (weekly)
  - Connection pool health: `neo4j_session.open_count < max_pool_size`
