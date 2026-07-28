# SalesOS — Private Governed Institutional Intelligence Platform

> **Version:** `v5.1.0-rc1` | **Status:** Release Candidate 1 | **Engineering:** GO | **Operations:** Pending  
> **Staging:** [`salesos-staging.up.railway.app`](https://salesos-staging.up.railway.app/health)  
> **Production:** [`salesos-production-96c0.up.railway.app`](https://salesos-production-96c0.up.railway.app/health)

SalesOS is a domain-driven sales intelligence platform built for the Saudi Arabian and Middle Eastern markets. It organizes, enriches, and connects company data so sales, procurement, and risk teams can make better decisions faster.

---

## Quick Start

```bash
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
├── salesos/                   ★ Main platform monorepo
│   ├── backend/               FastAPI — Identity, Company, Search, AI, CRM
│   ├── frontend/              Next.js 15 — Dashboard, Widgets, Copilot
│   ├── infra/                 K8s, Terraform, Monitoring, Docker
│   ├── docs/                  User guide, admin guide, deployment, runbooks
│   └── docker-compose.yml     Dev stack (PostgreSQL, Redis, Neo4j, Kafka)
│
├── docs/                      Product docs — ADRs, audits, reports, vNext
├── engineering-os/            Engineering OS — governance, agent registry
├── balady_scraper/            Government scraper — engineering offices
├── najiz_scraper/             Government scraper — lawyers
├── rega_scraper/              Government scraper — real estate
└── taqeem_scraper/            Government scraper — valuation
```

---

## Domains

| Domain | Description | Status |
|--------|-------------|--------|
| Identity | User auth, JWT, RBAC, OAuth 2.0 (Google) | 🟢 Live |
| Company | Company profiles, CRUD, enrichment | 🟢 Live |
| Search | Full-text + semantic hybrid search | 🟢 Live |
| CRM | Pipeline management, opportunities | 🟢 Live |
| AI | Copilot, NBA recommendations, RAG | 🟢 Live |
| Entity Resolution | Company deduplication, merging | 🟢 Live |
| Communication Hub | Gmail/Calendar sync, incremental sync, OAuth | 🟢 Live |
| Activity Intelligence | Email, calendar, engagement analytics | 🟢 Live |
| Knowledge Graph | Entity relationships, graph queries | 🟢 Live |
| Decision Center | NBA decision evaluation, confidence scoring | 🟢 Live |
| Feature Store | Dynamic feature computation | 🟢 Live |
| Workflow | Automation rules, triggers | 🟢 Live |
| Webhooks | Event-driven integrations, SSRF-hardened | 🟢 Live |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Radix UI |
| Database | PostgreSQL 16 (pgvector, pg_trgm), Neo4j 5 |
| Cache / Session | Redis 7 |
| Search | Meilisearch + pgvector (hybrid) |
| AI | OpenAI, LangChain, RAG |
| Event Bus | Kafka (in-memory fallback) |
| Monitoring | Prometheus, Grafana, Loki, OpenTelemetry |
| Deployment | Docker, Railway, K8s, Terraform, AWS (me-south-1) |

---

## Release v5.1.0-rc1

This release candidate includes:

- **Communication Hub** — Gmail sync (incremental via `historyId`), Calendar sync (incremental via `syncToken`), OAuth 2.0 with Google, Fernet-encrypted token storage, key rotation
- **Activity Intelligence** — 6 REST endpoints, 68 tests, zero circular dependencies
- **Security Hardening** — Webhook SSRF pinning, Redis-backed OAuth state store, JWT auth hardening
- **Database** — Alembic migrations 0046–0049 (opportunities, tasks, Google accounts, unique provider event IDs)
- **CI/CD** — 7-stage CI pipeline, staging deploy with smoke tests, automatic rollback, Slack notifications
- **Infrastructure** — Production Docker Compose (Caddy TLS, PgBouncer, backup service), K8s manifests (HPA, PDB, network policies)

**Prerequisite:** Run `alembic upgrade head` for migrations 0046–0049.

---

## Key Documents

| Document | Location |
|----------|----------|
| Release Readiness Report | `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` |
| Production Plan (Waves 0–14) | `docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md` |
| Production Runbook | `salesos/docs/production_runbook.md` |
| Deployment Guide | `salesos/docs/deployment_guide.md` |
| K8s Deployment Runbook | `salesos/infra/k8s/DEPLOYMENT_RUNBOOK.md` |
| API Documentation | `docs/api/OPENAPI.md` |
| ADR Index | `docs/adr/index.md` |
| Agent Essentials | `AGENTS.md` |
| Disaster Recovery | `docs/ops/DR_RUNBOOK.md` |

---

## Requirements

- Docker 24+ with Docker Compose v2
- Python 3.12+ (for data pipelines)
- Node.js 20+ (for frontend development)
- 8GB+ RAM, 20GB+ disk

---

## License

Proprietary — SalesOS Platform
