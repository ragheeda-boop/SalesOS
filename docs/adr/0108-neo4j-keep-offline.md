# ADR-108: Knowledge Graph (Neo4j) — Keep Offline in v1.0

**Status**: ACCEPTED
**Date**: 2026-08-07
**Author**: STAR Audit / Architecture
**Related**: A-02, ADR-101, ADR-102
**Supersedes**: nothing

---

## Context

The STAR audit (A-02) found Neo4j is defined in `docker-compose.yml` but **offline in production**. The GA engineering audit confirmed this. No production traffic uses Neo4j.

Current SalesOS has:
- Neo4j in docker-compose (14 services)
- Knowledge Graph domain with repository pattern
- ADR-028: Knowledge Graph Integration (accepted)
- Fallback to SQL when Neo4j unavailable

No production data flows through Neo4j. The knowledge graph is a "potential" capability, not an operational one.

## Decision

**Keep Neo4j offline in v1.0.** Do not activate.

### Rationale
1. **No production dependency** — SalesOS functions without Neo4j; SQL fallback is working
2. **Operational complexity** — Neo4j adds a 15th service to maintain, monitor, backup
3. **Data consistency** — Dual-write (PostgreSQL + Neo4j) without sync guarantees creates risk
4. **Customer value** — Knowledge graph is a differentiator, not a requirement for GA
5. **Cost** — Neo4j Aura or self-hosted adds infrastructure cost with no immediate ROI

### What stays in v1.0
- Neo4j in docker-compose (for development/experimentation)
- Knowledge Graph repository pattern (code remains)
- SQL fallback (production path)

### What moves to v2.0
- Neo4j activation in production
- Real-time graph sync
- Graph-specific APIs
- Knowledge graph UI

## Consequences

- **Positive:** v1.0 operational complexity reduced; single database (PostgreSQL) for all data
- **Negative:** "Knowledge Graph" capability not available to customers in v1.0
- **Risk:** If competitors ship graph-based intelligence, v2.0 delivery timeline is critical

## Evidence

- A-02: STAR Audit found Neo4j offline
- `salesos/docker-compose.yml` — Neo4j service defined
- `salesos/backend/app/domains/knowledge_graph/` — repository pattern exists
- No production traffic through Neo4j
