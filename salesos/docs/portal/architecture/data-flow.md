# Data Flow Architecture

> **تدفق البيانات — كيف تنتقل البيانات عبر النظام**

This document traces how data flows through SalesOS — from ingestion to intelligence to action.

---

## 1. Company Data Ingestion Flow

```
Government Sources (Balady, Taqeem, Waseel, ZATCA, MCI)
      │
      ▼
┌──────────────────────────────────────────────┐
│           Ingestion Service                    │
│  • Parse CR numbers, extract fields           │
│  • Normalize Arabic text                      │
│  • Detect format (JSON, XML, PDF)             │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           Entity Resolution                    │
│  • Match against existing records             │
│  • Merge duplicates → Golden Record           │
│  • Publish company.created / company.merged   │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│  PostgreSQL     │  │   Neo4j          │
│  Companies      │  │   Graph Nodes    │
│  Licenses       │  │   Relationships  │
│  Contacts       │  │                  │
└─────────────────┘  └──────────────────┘
          │                 │
          └────┬────────────┘
               ▼
┌──────────────────────────────────────────────┐
│           Search Index                        │
│  • Company name (AR/EN)                      │
│  • CR number, city, activity                 │
│  • Full-text search                          │
└──────────────────────────────────────────────┘
```

## 2. Signal Processing Flow

```
Signal Sources
  │
  ├── Government Updates (Daily)
  │   └── License expiry, status changes
  ├── News / Social Media (Real-time)
  │   └── Hiring, expansion, contracts
  ├── User Activity (Real-time)
  │   └── Email, meetings, calls
  └── External APIs (On-demand)
      └── Company enrichment
      │
      ▼
┌──────────────────────────────────────────────┐
│           Signal Runtime                       │
│  • Normalize signal format                    │
│  • Classify type & severity                   │
│  • Publish to Kafka (signal.detected)         │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│  Scoring Engine  │  │   NBA Engine     │
│  • Update scores  │  │   • Re-evaluate  │
│  • Recompute DNA │  │   • New NBA      │
└─────────────────┘  └──────────────────┘
```

## 3. Decision Evaluation Flow (NBA / Decision Platform)

```
DecisionContext (tenant, actor, entity, metadata)
      │
      ▼
┌─────────────────────────────────────────────┐
│ Step 1: Collect Evidence                     │
│   • Signals, DNA, Timeline, Search          │
│   • Deduplicate, rank by confidence         │
│   • Apply freshness decay                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 2: Apply Rules                         │
│   • 7+ built-in business rules              │
│   • Customer rules (customizable)            │
│   • Conflict detection & resolution          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 3: Compute Scores                      │
│   • 8 score types (company, intent, risk..) │
│   • Weighted factor computation             │
│   • Confidence estimation                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 4: Generate Recommendation             │
│   • Evaluate 8 action types                 │
│   • Score + rank actions                    │
│   • Assess risks                            │
│   • Select primary + 3 alternatives         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 5: Build Explainability                │
│   • why, whyNow, whyThisAction              │
│   • whyNotAlternative per alternative       │
│   • Bilingual (AR/EN)                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
            DecisionResult
```

## 4. Event-Driven Flow (Kafka)

```
Service A (Producer)
      │
      ├── Emits DomainEvent to Kafka topic
      │     e.g., "salesos.opportunity.stage_changed.v1"
      │
      ▼
┌──────────────────────────────────────────────┐
│              Kafka Cluster                     │
│  • 3 brokers, 8 partitions per topic         │
│  • Schema Registry (Avro)                    │
│  • Configurable retention (7-90 days)         │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ Consumer Group   │  │ Consumer Group    │
│ nba-engine       │  │ workflow-engine   │
│ (4 consumers)    │  │ (2 consumers)     │
└─────────────────┘  └──────────────────┘
          │                 │
          ▼                 ▼
  Re-evaluate NBA    Trigger workflow
  for opportunity    (DAG execution)
```

## 5. RAG Query Flow

```
User Query (Arabic or English)
      │
      ▼
┌──────────────────────────────────────────────┐
│     1. Embed Query                           │
│        multilingual-e5 → 1024-dim vector     │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ 2a. Vector       │  │ 2b. Keyword       │
│ Search (pgvector)│  │ Search (BM25)     │
│ Cosine sim       │  │ PostgreSQL FTS    │
└────────┬────────┘  └────────┬─────────┘
         └────────┬──────────┘
                  ▼
┌──────────────────────────────────────────────┐
│     3. Reciprocal Rank Fusion (RRF)           │
│        Combine & rerank results               │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│     4. Context Assembly                       │
│        Token-aware, priority-ranked           │
│        Max 6000 tokens                        │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│     5. LLM Generation                        │
│        GPT-4o-mini with citations            │
│        Citation verification                 │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
          Response + Citations
```

## 6. Analytics Flow

```
Operational DB (PostgreSQL)
      │
      │  hourly / daily ETL
      ▼
┌──────────────────────────────────────────────┐
│              Data Warehouse                    │
│  • Separate PostgreSQL instance              │
│  • Star schema (dimensions + facts)          │
│  • Materialized cubes                        │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ Standard Reports │  │ Custom Reports   │
│ • Pipeline       │  │ • Builder UI     │
│ • Team           │  │ • Dynamic SQL    │
│ • Forecast       │  │ • Export (PDF/CSV)│
└─────────────────┘  └──────────────────┘
```

## Key Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Eventual Consistency** | Read models may lag writes by < 1 second |
| **Idempotency** | All event handlers are idempotent |
| **At-Least-Once Delivery** | Consumers deduplicate where needed |
| **Exactly-Once** | For opportunity stage changes and workflow execution |
| **Fail Degraded** | Missing sources lower confidence, don't crash |
| **Tenant Isolation** | Every query includes `tenantId` filter |

## Related Documents

| Document | Link |
|----------|------|
| Domain Events Catalog | [Domain Driven Design](../../docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md#12-domain-events-catalog) |
| Decision Platform Data Flow | [Decision Platform Blueprint](../../docs/DECISION_PLATFORM_BLUEPRINT.md#3-data-flow) |
| Kafka Event Design | [Kafka Architecture](../../docs/wave-3/05-KAFKA_EVENT_BUS.md) |
| RAG Pipeline | [RAG Architecture](../../docs/wave-3/02-AI_RAG_ARCHITECTURE.md) |
