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
                       │  CRM  │  Search  │ AI │
                       ├──────────────────────┤
                       │  Company  │  Contact  │
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
| Database | PostgreSQL 16 + pgvector |
| Graph | Neo4j 5.x |
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

## Project Structure

```
salesos/
├── backend/
│   ├── app/
│   │   ├── common/         # Shared models, schemas, middleware
│   │   ├── modules/        # Feature modules
│   │   │   ├── identity/   # Auth, users, tenants
│   │   │   ├── company/    # Companies, branches, licenses, contacts
│   │   │   ├── contact/
│   │   │   └── search/
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
└── docs/
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

Full architecture, implementation blueprint, and operations manuals are in `output/`:

| Document | Description |
|----------|-------------|
| `SALESOS_ENTERPRISE_COMPANY_INTELLIGENCE_ARCHITECTURE.md` | Complete architecture (Phases 1-25, B1-B20) |
| `SALESOS_IMPLEMENTATION_BLUEPRINT.md` | Implementation specs, 15 CTO layers, ERD, API, sprint plan |
| `SALESOS_ENGINEERING_OPERATIONS_MANUAL.md` | ADRs, engineering standards, PRDs, Sprint 1 checklist |
| `SALESOS_PRODUCT_DELIVERY_PLAYBOOK.md` | Roadmap, pricing, DevOps, SRE, onboarding, metrics |

## License

Proprietary — All Rights Reserved.
