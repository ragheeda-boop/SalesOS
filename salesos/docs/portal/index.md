# SalesOS Documentation Portal

> **منصة ذكاء المبيعات — Sales Intelligence Platform for the Middle East**
>
> Base URL: `https://api.salesos.sa` | Status: Production | Version: v0.9.0

SalesOS is a domain-driven sales intelligence platform purpose-built for the Saudi Arabian and Middle Eastern markets. It organizes and enriches company data so sales, procurement, and risk teams can make better decisions faster.

---

## Quick Links

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started/quickstart.md) | 5-minute quickstart guide |
| [API Reference](api/overview.md) | Complete API documentation |
| [Architecture](architecture/overview.md) | System architecture & domain model |
| [SDK Reference](sdk/workspace-sdk.md) | TypeScript SDK documentation |
| [Deployment Guide](deployment/docker.md) | Docker & production deployment |
| [Guides & Tutorials](guides/creating-a-widget.md) | Step-by-step tutorials |
| [Release Notes](releases/v0.9.md) | Version history & changelog |
| [FAQ](faq/index.md) | Frequently asked questions |

---

## Platform Overview

```
                         SalesOS Platform
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   Wave 1                Wave 2                Wave 3
Company Intel.      Revenue Execution      AI & Automation
        │                     │                     │
  ┌─────┴──────┐      ┌───────┴───────┐      ┌──────┴──────┐
  │ Companies  │      │ Opportunities │      │  RAG/AI     │
  │ Contacts   │      │ NBA Engine    │      │  Workflows  │
  │ Licenses   │      │ Pipeline      │      │  Analytics  │
  │ Search     │      │ Meetings      │      │  Kafka Bus  │
  │ DNA/Scores │      │ Email Intel   │      │  Warehouse  │
  └────────────┘      └───────────────┘      └─────────────┘
```

### Waves

| Wave | Version | Focus | Status |
|------|---------|-------|--------|
| Wave 1 | v0.5 | Company Intelligence — data ingestion, enrichment, search | ✅ Production |
| Wave 2 | v0.6–v0.8 | Revenue Execution — NBA, pipeline, meetings, email | ✅ Production |
| Wave 3 | v0.9 | AI & Automation — RAG, workflows, analytics, Kafka | 🟡 In Progress |

### Core Capabilities

| Capability | Description |
|-----------|-------------|
| **Company Intelligence** | Golden records for 100M+ companies with CR numbers, licenses, contacts |
| **Entity Resolution** | Deduplication and merging across 10+ government and commercial sources |
| **NBA Engine** | Decision intelligence pipeline generating explainable next-best actions |
| **Pipeline Management** | Full opportunity lifecycle from qualification to close |
| **Meeting Intelligence** | AI-powered pre-meeting briefs and post-meeting summaries |
| **Email Intelligence** | Sentiment analysis, topic extraction, urgency detection |
| **RAG Pipeline** | Retrieval-augmented generation over company documents |
| **Workflow Automation** | Event-driven DAG engine for sales process automation |
| **Widget SDK v1.0** | Composable workspace widgets with contract testing |

---

## Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Domain-Driven** | 13 bounded contexts, each with its own repository and language |
| **CQRS** | Separate read and write models optimized for their use case |
| **Event-Driven** | All domain changes published via Kafka with Schema Registry |
| **Tenant-Isolated** | Every query scoped by `tenantId` — zero cross-tenant leakage |
| **Explainable AI** | Every recommendation exposes why, why now, why this action |
| **Widget SDK** | All dashboards built via SDK — no direct context access in views |

---

## API Base Paths

| Service | Base Path | Version |
|---------|-----------|---------|
| Company Intelligence | `/api/v1/companies` | v1 |
| Identity & Access | `/api/v1/auth` | v1 |
| CRM / Revenue | `/api/v1/revenue` | v1 |
| Decision Platform | `/api/v1/decision` | v1 |
| Search | `/api/v1/search` | v1 |
| Workflow | `/api/v1/workflows` | v1 |
| Analytics | `/api/v1/analytics` | v1 |

---

## SDK Packages

| Package | Description |
|---------|-------------|
| `@salesos/workspace` | Widget SDK v1.0 — create workspace widgets |
| `@salesos/search` | Search SDK — hybrid search across all entities |
| `@salesos/decision-platform` | Decision Intelligence Platform SDK |
| `@salesos/design-language` | MUHIDE design tokens and components |
| `@salesos/platform` | Platform kernel — telemetry, permissions, feature flags |

---

## Support

| Channel | Contact |
|---------|---------|
| Email | `support@salesos.sa` |
| Documentation | [docs.salesos.sa](https://docs.salesos.sa) |
| Status | [status.salesos.sa](https://status.salesos.sa) |
| Saudi Business Hours | Sat–Thu, 9:00–18:00 AST |

---

*SalesOS Documentation Portal — v0.9.0 | آخر تحديث: 2026-07-11*
