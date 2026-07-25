# Muhide — SalesOS Platform

> Sales Intelligence Platform for the Saudi Arabian Market
> SalesOS is a domain-driven platform for CRM enrichment, entity resolution, AI-powered search, and revenue intelligence.

---

## Quick Start

```bash
# Start all services
cd salesos
cp .env.example .env
# Edit .env with required secrets (POSTGRES_PASSWORD, JWT_SECRET_KEY, OPENAI_API_KEY)
docker compose up --build

# Open http://localhost:3000
```

---

## Platform Architecture

```
Muhide/
├── salesos/              ★ Main platform (FastAPI + Next.js)
│   ├── backend/          DDD backend — Identity, Company, Search, AI, CRM
│   ├── frontend/         Next.js 15 — Dashboard, Widgets, Copilot
│   ├── infra/            K8s, Terraform, Monitoring, Docker
│   ├── docs/             User guide, admin guide, deployment guide, runbooks
│   └── docker-compose.yml
│
├── docs/                 Product-level docs — ADRs, audits, reports, vNext plans
├── engineering-os/       Engineering OS — governance, agent registry, rules
├── scripts/              Backup, restore, utilities
├── balady_scraper/       Government scraper — engineering offices
├── najiz_scraper/        Government scraper — lawyers
├── rega_scraper/         Government scraper — real estate
└── taqeem_scraper/       Government scraper — valuation
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Radix UI |
| Database | PostgreSQL 16 (pgvector, pg_trgm), Neo4j 5 |
| Cache | Redis 7 |
| Search | Meilisearch + pgvector (hybrid) |
| AI | OpenAI, LangChain, RAG |
| Monitoring | Prometheus, Grafana, Loki, OpenTelemetry |
| Infrastructure | Docker, K8s, Terraform, AWS (me-south-1) |

---

## Domains

| Domain | Description | Status |
|--------|-------------|--------|
| Identity | User auth, JWT, RBAC | 🟢 Live |
| Company | Company profiles, CRUD, enrichment | 🟢 Live |
| Search | Full-text + semantic hybrid search | 🟢 Live |
| CRM | Pipeline management, opportunities | 🟢 Live |
| AI | Copilot, NBA recommendations, RAG | 🟢 Live |
| Entity Resolution | Company deduplication, merging | 🟢 Live |
| Feature Store | Dynamic feature computation | 🟢 Live |
| Knowledge Graph | Entity relationships, graph queries | 🟢 Live |
| Workflow | Automation rules, triggers | 🟢 Live |

---

## Key Documents

| Document | Location |
|----------|----------|
| GA scoreboard (NO-GO) | `docs/audit/ga-engineering-audit/GA_STATUS.md` |
| GA engineering audit | `docs/audit/ga-engineering-audit/README.md` |
| Production plan (Waves 0–14) | `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` |
| Wave 11 soak progress | `docs/audit/ga-engineering-audit/PROGRESS-WAVE11-SOAK.md` |
| Wave 12 deploy/rollback tabletop | `docs/audit/ga-engineering-audit/PROGRESS-WAVE12-TABLETOP.md` |
| Agent essentials | `AGENTS.md` |
| Runbook | `RUNBOOK.md` |
| Deployment Guide | `salesos/docs/deployment_guide.md` |
| API Documentation | `docs/api/OPENAPI.md` |
| ADR Index | `docs/adr/index.md` |
| Engineering Constitution | `engineering-os/ENGINEERING_CONSTITUTION.md` |
| User Guide | `salesos/docs/user_guide.md` |
| Admin Guide | `salesos/docs/admin_guide.md` |
| Production Runbook | `salesos/docs/production_runbook.md` |
| Disaster Recovery Runbook | `docs/ops/DR_RUNBOOK.md` |

---

## Requirements

- Docker 24+ with Docker Compose v2
- Python 3.12+ (for data pipelines)
- Node.js 20+ (for frontend development)
- 8GB+ RAM, 20GB+ disk

---

## License

Proprietary — SalesOS Platform
