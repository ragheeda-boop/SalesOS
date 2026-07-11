# System Architecture Overview

> **نظرة عامة على البنية المعمارية للنظام**

SalesOS follows a **Domain-Driven Design (DDD)** with **CQRS** and **Event-Driven** architecture. The system is organized into 13 bounded contexts across 3 waves of development.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Dashboard │ │Workspace │ │Widgets   │ │NBA UI    │ │Admin     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                          API Gateway (Kong)                          │
│  Auth → Rate Limit → Route → Log → Cache                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                       Application Layer (FastAPI)                    │
│                                                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────────┐  │
│  │Company Intel│ │CRM / Revenue│ │AI / RAG     │ │Decision       │  │
│  │Services     │ │Services     │ │Services     │ │Platform       │  │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └───────┬───────┘  │
└─────────┼───────────────┼───────────────┼────────────────┼──────────┘
          │               │               │                │
┌─────────▼───────────────▼───────────────▼────────────────▼──────────┐
│                          Domain Layer                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │Company │ │Identity│ │CRM     │ │Scoring │ │Workflow│ │AI      │  │
│  │        │ │        │ │        │ │        │ │        │ │        │  │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘  │
│      └──────────┼──────────┼──────────┼──────────┼──────────┘       │
└─────────────────┼──────────┼──────────┼──────────┼──────────────────┘
                  │          │          │          │
┌─────────────────▼──────────▼──────────▼──────────▼──────────────────┐
│                        Infrastructure Layer                           │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │PostgreSQL│ │  Neo4j   │ │  Redis   │ │  Kafka   │ │  S3/MinIO│  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

| Layer | Responsibility | Tech |
|-------|---------------|------|
| **Presentation** | React components, widgets, dashboards | Next.js, Widget SDK |
| **API Gateway** | Authentication, rate limiting, routing | Kong / Nginx |
| **Application** | HTTP endpoints, use-case orchestration | FastAPI (Python) |
| **Domain** | Business logic, aggregates, entities | Pure Python |
| **Infrastructure** | Data persistence, messaging, caching | PostgreSQL, Neo4j, Redis, Kafka |

---

## Key Architectural Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-DDD-01 | Aggregates as consistency boundaries | Atomic changes within Company aggregates |
| ADR-DDD-02 | Event sourcing for Entity Resolution only | Full audit trail for merge/split decisions |
| ADR-DDD-03 | Domain events via Kafka | Cross-context communication with replay |
| ADR-DDD-04 | CQRS — read/write models separated | Optimized for query vs command performance |
| ADR-W3-001 | pgvector for vector store | Zero new infrastructure, transactional consistency |
| ADR-W3-003 | Apache Kafka for event bus | Exactly-once semantics, scalability |
| ADR-W3-004 | Custom lightweight DAG engine | Sales-specific workflows, integrated UI |

Full ADR catalog: [Wave 3 Architecture Decisions](../../docs/wave-3/07-ARCHITECTURE_DECISIONS.md)

---

## Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Backend | Python / FastAPI | 3.12 / 0.110+ |
| Frontend | React / Next.js | 18 / 14+ |
| Database (Primary) | PostgreSQL (pgvector) | 16 |
| Graph Database | Neo4j | 5 |
| Cache | Redis | 7 |
| Event Bus | Apache Kafka | 3.x |
| Search | PostgreSQL FTS / Typesense | — |
| Containerization | Docker / Kubernetes | — |
| CI/CD | GitHub Actions | — |
| Monitoring | Prometheus + Grafana | — |
| SDK | TypeScript | 5.x |
| Design Tokens | CSS Variables | MUHIDE palette |

---

## Domain Map

```
┌────────────────────────────────────────────────────────────┐
│                     Identity (BC-01)                        │
│  Tenants, Users, Roles, Permissions, SSO                  │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│                 Company Intelligence (BC-02) [CORE]         │
│  Companies, Branches, Licenses, Contacts, Signals         │
└────┬───────────────┬───────────────┬───────────────────────┘
     │               │               │
     ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────────────┐
│ CRM      │  │ Scoring  │  │ Knowledge Graph  │
│ (BC-04)  │  │ (BC-06)  │  │ (BC-08)          │
│          │  │          │  │                  │
│ Opps,    │  │ Company  │  │ Nodes, Edges,    │
│ Pipeline │  │ Scores   │  │ Relationships    │
└──────────┘  └──────────┘  └──────────────────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│                  AI Platform (BC-09)                        │
│  Agents, Queries, RAG, Embeddings                         │
└────────────────────┬───────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│               Workflow Engine (BC-10)                       │
│  Automations, Triggers, Actions, Execution Traces         │
└───────────────────────────────────────────────────────────┘
```

---

## Performance Budgets

| Operation | Budget |
|-----------|--------|
| API response (simple) | < 100ms p95 |
| API response (complex) | < 500ms p95 |
| Search query | < 300ms p95 |
| NBA evaluation (rule-only) | < 200ms |
| NBA evaluation (with AI) | < 3s |
| RAG retrieval | < 200ms p95 |
| Workflow execution start | < 1s from trigger |
| Dashboard load | < 2s |
| Report generation | < 30s |

---

## Related Documents

| Document | Link |
|----------|------|
| Full DDD Specification | [Domain Driven Design](../../docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md) |
| Platform Kernel Design | [Platform Kernel](../../docs/wave-2/02-PLATFORM_KERNEL_DESIGN.md) |
| Wave 3 Architecture | [Wave 3 Overview](../../docs/wave-3/01-WAVE3_OVERVIEW.md) |
| Decision Platform | [Decision Platform Architecture](../../docs/DECISION_PLATFORM_ARCHITECTURE.md) |
