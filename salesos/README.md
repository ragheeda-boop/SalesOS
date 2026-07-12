# SalesOS — Enterprise Company Intelligence Platform

**SalesOS** is a comprehensive, AI-native platform for company intelligence, CRM, data enrichment, and marketplace capabilities. Built for the Saudi Arabian market and designed for global expansion.

## Architecture

```
                       ┌──────────────────────┐
                       │   Marketplace Apps    │
                       ├──────────────────────┤
                       │      AI Agents        │
                       ├──────────────────────┤
                       │   Workflow Engine     │
                       ├──────────────────────┤
                       │  Revenue Workspace    │  ← Wave 2: Unified shell
                       ├──────────────────────┤
                       │  NBA  │ Pipeline │ AI │  ← Wave 2: Decision + Intelligence
                       ├──────────────────────┤
                       │  CRM  │  Search  │ AI │
                       ├──────────────────────┤
                       │  Company  │  Contact  │
                       ├──────────────────────┤
                       │ Entity Resolution │ Feature Store │ Knowledge Graph │
                       ├──────────────────────┤
                       │     Data Lake         │
                       ├──────────────────────┤
                       │  PostgreSQL  │  Neo4j │
                       └──────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 |
| Frontend | Next.js 15, React 19, Tailwind CSS 4 |
| Database | PostgreSQL 16 + pgvector + pg_trgm |
| Graph | Neo4j 5.x (with SQL fallback) |
| Stream | Apache Kafka |
| Cache | Redis 7 |
| Infra | Docker, Kubernetes, Terraform (AWS) |

## Quick Start

```bash
# Clone and start everything
make dev

# Or manually:
docker compose up --build -d

# Backend API: http://localhost:8000/docs
# Frontend:     http://localhost:3000
```

## Data Fabric — v0.2.0

SalesOS v0.2.0 introduces the **Data Fabric** layer — Entity Resolution, Hybrid Search, Feature Store, and Knowledge Graph.

### Data Fabric Components

| Component | Description | Tech |
|-----------|-------------|------|
| **Entity Resolution** | Fuzzy matching + merge strategy for contact/company deduplication | pg_trgm, SQLAlchemy |
| **Hybrid Search** | Full-text (tsvector) + semantic (pgvector) with RRF fusion scoring | PostgreSQL, pgvector |
| **Feature Store** | Centralized feature computation, caching, and versioning | PostgreSQL |
| **Knowledge Graph** | Graph relationships for company/contact networks | Neo4j + SQL fallback |

### Data Fabric Features

- **Entity Resolution** — pg_trgm fuzzy matching with configurable similarity threshold; merge strategy for duplicate records
- **Hybrid Search** — Full-text (GIN-indexed tsvector) + semantic (pgvector embeddings) fused via Reciprocal Rank Fusion (RRF)
- **Feature Store** — 7 feature computers powering scoring, NBA, and analytics
- **Knowledge Graph** — Neo4j graph traversal with SQL fallback for resilience; full-text indexes via `~` operator

---

## Wave 2 — Revenue Execution Platform

SalesOS v0.6.0 introduces the **Revenue Execution Platform**, transforming intelligence into commercial action.

### Wave 2 Components

| Component | Description | API Prefix |
|-----------|-------------|------------|
| **NBA Engine** | Decision pipeline with AI reasoning, explainable recommendations, feedback loop | `/opportunities/{id}/nba` |
| **Opportunity Workspace** | Full lifecycle management with playbooks, deal health tracking | `/opportunities` |
| **Pipeline Intelligence** | Velocity, conversion rates, health map, forecast engine | `/pipeline` |
| **Meeting Intelligence** | Pre-meeting briefs, post-meeting summaries, sentiment analysis | `/meetings` |
| **Email Intelligence** | Sentiment analysis, topic extraction, urgency detection | `/emails` |
| **Revenue Workspace** | Unified executive shell combining all Wave 2 components | `/revenue/dashboard` |

### Key Features

- **Explainable AI** — Every NBA recommendation includes evidence trail, confidence breakdown, and alternatives
- **Hybrid Scoring** — Business rules + LLM reasoning; works without AI key (rule-only fallback)
- **Feedback Loop** — Accept/dismiss recommendations; automatic rule weight adjustment weekly
- **Performance** — NBA < 200ms rule-only, < 3s with AI; all pipeline metrics real-time
- **Health Map** — Traffic light visualization across all open opportunities
- **Meeting Intelligence** — AI-generated briefs and summaries in < 3s
- **Email Intelligence** — Sentiment, topics, urgency from Gmail/Outlook integration
- **Hybrid Search (RRF)** — Full-text + semantic fusion scoring via Reciprocal Rank Fusion
- **Entity Resolution (pg_trgm)** — Fuzzy matching for contact/company deduplication
- **Feature Store** — Centralized feature computation and caching (7 computers)

### API Overview

```
GET  /api/v1/revenue/opportunities              — List opportunities
GET  /api/v1/revenue/opportunities/{id}         — Get opportunity detail
POST /api/v1/revenue/opportunities              — Create opportunity
PUT  /api/v1/revenue/opportunities/{id}         — Update opportunity
PATCH /api/v1/revenue/opportunities/{id}/stage  — Advance/revert stage

GET  /api/v1/revenue/opportunities/{id}/nba     — Get NBA recommendation
POST /api/v1/revenue/opportunities/{id}/nba/refresh — Force recompute
POST /api/v1/revenue/opportunities/{id}/nba/accept  — Accept recommendation
POST /api/v1/revenue/opportunities/{id}/nba/dismiss — Dismiss recommendation
GET  /api/v1/revenue/opportunities/{id}/nba/history — NBA history

GET  /api/v1/revenue/pipeline                  — Pipeline summary
GET  /api/v1/revenue/pipeline/stages           — Stage metrics
GET  /api/v1/revenue/pipeline/health           — Health map
GET  /api/v1/revenue/pipeline/velocity         — Velocity metrics

GET  /api/v1/revenue/meetings                  — List meetings
POST /api/v1/revenue/meetings                  — Create meeting
POST /api/v1/revenue/meetings/{id}/brief       — Generate pre-meeting brief
POST /api/v1/revenue/meetings/{id}/summary     — Generate post-meeting summary

GET  /api/v1/revenue/emails                    — List emails
POST /api/v1/revenue/emails                    — Log email
GET  /api/v1/revenue/emails/{id}/intelligence  — Get email intelligence

GET  /api/v1/revenue/dashboard                 — Revenue dashboard
```

Full API documentation: [`docs/wave-2/11-API_REFERENCE.md`](docs/wave-2/11-API_REFERENCE.md)

---

## Project Structure

```
salesos/
├── backend/
│   ├── app/
│   │   ├── common/         # Shared models, schemas, middleware
│   │   ├── modules/        # Feature modules
│   │   │   ├── identity/   # Auth, users, tenants
│   │   │   ├── company/    # Companies, branches, licenses, contacts
│   │   │   ├── contact/    # Contact management
│   │   │   ├── search/     # Hybrid Search (full-text + semantic + RRF)
│   │   │   ├── entity_resolution/  # ← NEW: Fuzzy matching + merge (pg_trgm)
│   │   │   ├── feature_store/      # ← NEW: Feature computation + caching
│   │   │   ├── data_fabric_runtime/ # ← NEW: Pipeline orchestration + graph sync
│   │   │   ├── revenue/    # ← Wave 2: Opportunities, Pipeline, NBA, Goals
│   │   │   ├── meeting/    # ← Wave 2: Meeting Intelligence
│   │   │   └── email/      # ← Wave 2: Email Intelligence
│   │   └── alembic/        # Database migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/            # Next.js pages
│       ├── components/     # UI components
│       └── lib/            # Utilities, API client
├── infra/
│   ├── docker/             # Docker configs
│   ├── k8s/                # Kubernetes manifests
│   └── terraform/          # Infrastructure as Code
├── docs/
│   └── wave-2/             # ← Wave 2 architecture + release docs
│       ├── 01-REVENUE_EXECUTION_REVIEW.md
│       ├── 02-PLATFORM_KERNEL_DESIGN.md
│       ├── 03-NBA_ARCHITECTURE.md
│       ├── 04-NBA_BLUEPRINT.md
│       ├── 05-NBA_CONTRACTS.md
│       ├── 06-NBA_API_MAPPING.md
│       ├── 07-NBA_COMPONENT_CATALOG.md
│       ├── 08-NBA_IMPLEMENTATION_PLAN.md
│       ├── 09-ARCHITECTURE_VALIDATION_REPORT.md
│       ├── 10-WAVE2_RELEASE_NOTES.md
│       └── 11-API_REFERENCE.md
└── packages/
    └── platform/           # ← Platform Kernel: contracts, testing, shared
```

## Development

```bash
make install    # Install all dependencies
make dev        # Start dev environment
make test       # Run all tests
make lint       # Run linters
make migrate    # Run database migrations
make reset      # Full environment reset
```

## Documentation

Full architecture, implementation blueprint, and operations manuals are in `output/` and `docs/`:

| Document | Description |
|----------|-------------|
| `SALESOS_ENTERPRISE_COMPANY_INTELLIGENCE_ARCHITECTURE.md` | Complete architecture (Phases 1-25, B1-B20) |
| `SALESOS_IMPLEMENTATION_BLUEPRINT.md` | Implementation specs, 15 CTO layers, ERD, API, sprint plan |
| `SALESOS_ENGINEERING_OPERATIONS_MANUAL.md` | ADRs, engineering standards, PRDs, Sprint 1 checklist |
| `SALESOS_PRODUCT_DELIVERY_PLAYBOOK.md` | Roadmap, pricing, DevOps, SRE, onboarding, metrics |
| `docs/wave-2/10-WAVE2_RELEASE_NOTES.md` | Wave 2 detailed release notes |
| `docs/wave-2/11-API_REFERENCE.md` | Wave 2 full API documentation |
| `CHANGELOG.md` | Version history and release notes |

## License

Proprietary — All Rights Reserved.
