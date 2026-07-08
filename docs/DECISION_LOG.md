# SalesOS — DECISION LOG

> **سجل القرارات — كل قرار معماري، من اتخذه، لماذا، متى، وما البدائل**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## Decision Template

```
ID:      DEC-{NNN}
Date:    YYYY-MM-DD
Title:   {Brief title}
Author:  {Name}
Status:  Proposed | Accepted | Deprecated | Superseded
Context: {What led to this decision}
Decision: {What was decided}
Rationale: {Why this option was chosen}
Alternatives: {Other options considered}
Consequences: {Impact of this decision}
References: {ADRs, docs, PRs}
```

---

## ARCHITECTURE DECISIONS

### DEC-001: Modular Monolith First, Microservices Later

| Field | Value |
|-------|-------|
| Date | 2026-01-15 |
| Status | ✅ Accepted |
| Context | Team size 5-7, uncertain domain boundaries, need for rapid iteration |
| Decision | Build as modular monolith with strict module boundaries. Extract to microservices when a module needs independent scaling or has a dedicated team |
| Rationale | Monolith simplifies development, deployment, and debugging. Module boundaries preserve the option to extract later |
| Alternatives | Start with microservices (too complex), serverless (vendor lock-in) |
| Consequences | In-process EventBus, cross-module JOINs allowed, need strict import rules |
| References | ADR-001 |

### DEC-002: PostgreSQL as Primary Database

| Field | Value |
|-------|-------|
| Date | 2026-01-20 |
| Status | ✅ Accepted |
| Context | Need ACID compliance, JSON support, full-text search in Arabic/English, vector embeddings |
| Decision | PostgreSQL 16 with pgvector, JSONB, and trigram extensions |
| Rationale | Single database for OLTP + search + embeddings reduces operational complexity |
| Alternatives | MongoDB (no ACID), Elasticsearch (separate search infra), dedicated vector DB (Pinecone, Weaviate) |
| Consequences | Single-node write bottleneck at scale. Read replicas needed above 10M records |
| References | ADR-002 |

### DEC-003: Neo4j for Knowledge Graph

| Field | Value |
|-------|-------|
| Date | 2026-02-01 |
| Status | ✅ Accepted |
| Context | Relationship-heavy queries (company → contact → deal → activity) are inefficient in SQL |
| Decision | Add Neo4j 5.x for graph queries alongside PostgreSQL |
| Rationale | Cypher queries are 10-100x faster for multi-hop traversals. Graph Data Science library for scoring |
| Alternatives | PostgreSQL recursive CTEs (slow at depth >3), Amazon Neptune (vendor lock-in) |
| Consequences | Second database to manage. Eventual consistency between PostgreSQL and Neo4j |
| References | ADR-003 |

### DEC-004: Capability over Module Terminology

| Field | Value |
|-------|-------|
| Date | 2026-06-30 |
| Status | ✅ Accepted |
| Context | "Module" implied a narrow technical component. The platform needs components with full surface area (API, UI, AI, Workflow, Events, Analytics, Permissions, Docs, Tests) |
| Decision | Deprecate "Module". All platform components are now "Capabilities" |
| Rationale | Capability better represents the business product nature. Each capability is independently shippable |
| Alternatives | Keep "Module" (too technical), use "Service" (conflicts with microservices), use "Product" (conflicts with actual products) |
| Consequences | All documentation, code, and conversation must be updated. Old code still uses "module" — migrate over time |
| References | V5 Blueprint, PROJECT_MANIFEST.md |

### DEC-005: Business Intelligence OS over Revenue OS

| Field | Value |
|-------|-------|
| Date | 2026-06-30 |
| Status | ✅ Accepted |
| Context | The platform scope exceeds revenue operations. Revenue is the first capability, not the only one |
| Decision | Position SalesOS as a Business Intelligence Operating System (BIOS) |
| Rationale | Opens TAM beyond sales. Serves marketing, customer success, partner ops, talent intelligence |
| Alternatives | Stay Revenue OS (limited TAM), Enterprise OS (too broad) |
| Consequences | More capabilities to build. Higher TAM. Need to sequence carefully to avoid scope creep |
| References | V4 Blueprint, MASTER_BLUEPRINT.md |

### DEC-006: Four-Layer Architecture

| Field | Value |
|-------|-------|
| Date | 2026-06-30 |
| Status | ✅ Accepted |
| Context | Flat module structure had no hierarchy. Dependencies were unclear. Platform services mixed with business capabilities |
| Decision | Adopt 4-layer architecture: Kernel → Platform Services → Business Capabilities → Applications |
| Rationale | Clear separation of concerns. Each layer has defined responsibilities and dependency direction |
| Alternatives | 3-layer (missing platform services), 5-layer (too many), hexagonal architecture (too abstract) |
| Consequences | All capabilities must be assigned to a layer. Layer violations are architecture errors |
| References | MASTER_BLUEPRINT.md Section 2.2 |

### DEC-007: Digital Twin Every Workspace

| Field | Value |
|-------|-------|
| Date | 2026-06-30 |
| Status | ✅ Accepted |
| Context | Platform knows what happened but not what will happen. Users need predictive intelligence |
| Decision | Every workspace gets a Digital Twin: current state + predictions + risks + scenarios + recommendations |
| Rationale | Transforms system from operational to decision intelligence. Core differentiator |
| Alternatives | Standalone analytics module (too weak), ML-only predictions (no state management) |
| Consequences | Significant new engine (CAP-032). Requires Feature Store, Revenue Graph, and Timeline to function |
| References | MASTER_BLUEPRINT.md Section 14 |

### DEC-008: MCP Server as First-Class API Surface

| Field | Value |
|-------|-------|
| Date | 2026-06-30 |
| Status | ✅ Accepted |
| Context | AI agents are becoming the primary interface to software. REST-only limits SalesOS reach |
| Decision | Add MCP Server alongside REST, GraphQL, and Agent SDK as a first-class API surface |
| Rationale | Makes SalesOS a knowledge source and tool provider for any AI agent ecosystem (Cursor, Copilot, Claude, custom) |
| Alternatives | REST-only (misses AI ecosystem), gRPC (too complex for agents) |
| Consequences | New implementation (CAP-039). All capabilities must eventually expose MCP tools |
| References | MASTER_BLUEPRINT.md Section 7 |

### DEC-009: Arabic-First Interface

| Field | Value |
|-------|-------|
| Date | 2026-06-30 |
| Status | ✅ Accepted |
| Context | Primary market is Saudi Arabia. Users think and work in Arabic |
| Decision | Arabic is the default interface language. English is the translation |
| Rationale | User adoption depends on native language experience. Competitors (HubSpot, Salesforce) are English-first |
| Alternatives | English-first with Arabic translation (competitor approach), bilingual parallel |
| Consequences | RTL layout required for all UI. Arabic NLP pipeline. Search must handle Arabic morphology |
| References | PROJECT_MANIFEST.md, Strategic Principles |

### DEC-010: Measurement Before AI Investment

| Field | Value |
|-------|-------|
| Date | 2026-06-30 |
| Status | ✅ Accepted |
| Context | AI features are expensive and complex. Without measurement, teams build features nobody uses |
| Decision | Every AI feature must have defined success metrics before any code is written |
| Rationale | Prevents AI cost overruns. Ensures AI features solve real problems |
| Alternatives | Build AI features and measure later (risk of waste), skip AI (misses opportunity) |
| Consequences | AI features will take longer to ship. Every PR requires eval results. More upfront design |
| References | AI_CATALOG.md Section 6 |

---

## REJECTED DECISIONS

| ID | Proposal | Rejected Because | Date |
|----|----------|------------------|------|
| REJ-001 | Use Elasticsearch for search | PostgreSQL trigram + pgvector sufficient. Don't add DB #3 yet | 2026-02-10 |
| REJ-002 | Start with microservices | Team too small. Modular monolith provides same benefits with less complexity | 2026-01-15 |
| REJ-003 | Use MongoDB for flexible schema | PostgreSQL JSONB provides the same flexibility with ACID compliance | 2026-01-20 |
| REJ-004 | Build mobile app first | Web app is faster to build and iterate. Mobile is Year 3+ | 2026-03-01 |
| REJ-005 | Use LangChain for AI agents | Custom SDK gives more control. LangChain adds complexity without benefit for current scale | 2026-04-15 |

---

*This decision log records all significant architecture decisions. Every decision is linked to an ADR where applicable. Teams should review relevant decisions before proposing alternatives.*
