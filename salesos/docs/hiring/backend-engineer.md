# Backend Engineer — SalesOS

> SalesOS Engineering Team · Saudi Arabia (Remote OK)

---

## About SalesOS

SalesOS is an AI-native enterprise intelligence platform serving the Saudi Arabian market. We operate a modular monolith architecture with strict domain boundaries (DDD), PostgreSQL, Neo4j, FastAPI, and Python 3.12. Our platform handles company intelligence, CRM, data enrichment, decision engines, and revenue execution.

## Role

You will design and implement backend services across our bounded contexts — Identity, Company, Search, Scoring, CRM, AI, Timeline, Workflow, Revenue, and Data Fabric. You will work within our modular monolith architecture, respecting domain boundaries and contributing to our high-coverage test suite.

## Requirements

### Must-Have

- **Python 3.12+** — production experience, not just scripts
- **FastAPI** — building REST APIs with dependency injection, middleware, async handlers
- **SQLAlchemy 2.0** — ORM models, query building, migrations with Alembic
- **PostgreSQL** — schema design, indexing (GIN, GiST), query optimization, extensions (pg_trgm, pgvector)
- **DDD fundamentals** — bounded contexts, repository pattern, domain events, anti-corruption layers
- **Testing** — pytest, coverage-driven development, InMemory repositories for unit tests
- **Git** — branching strategy, PR reviews, conventional commits

### Nice-to-Have

- **Redis** — caching, rate limiting, session management
- **Neo4j / Cypher** — graph database queries and modeling
- **Kafka / event streaming** — durable event bus, dead-letter queues
- **Docker** — containerized development and deployment
- **RBAC / security** — JWT auth, CSRF protection, input validation
- **Arabic text processing** — normalization, full-text search, RTL considerations

## Architecture Context

Our backend follows these principles (enforced via automated checks):

| Principle | Implementation |
|-----------|---------------|
| Repository Pattern | Interface in domain, PostgreSQL impl in infrastructure |
| No Cross-Domain Imports | SDK-only communication between bounded contexts |
| Frozen Interfaces | Widget SDK v1.0 frozen; changes require ADR |
| ADR Governance | Architecture Decision Records for all structural changes |
| Test Coverage | Minimum 85% unit test coverage per domain |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI, Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 + pgvector + pg_trgm |
| Graph | Neo4j 5.x (SQL fallback) |
| Cache | Redis 7 |
| Queue | Kafka (planned), in-process event bus (current) |
| Testing | pytest, coverage, InMemory repositories |
| Linting | Ruff, mypy (strict) |
| CI/CD | GitHub Actions |

## Responsibilities

1. Design and implement domain services within bounded contexts
2. Write repository interfaces and PostgreSQL implementations
3. Build and maintain Alembic database migrations
4. Create comprehensive test suites (unit, integration)
5. Participate in architecture reviews and ADR authoring
6. Monitor and optimize API performance (p95 < 500ms target)
7. Contribute to security hardening (RBAC, rate limiting, input validation)
8. Collaborate with frontend engineers on API contracts

## What We Offer

- Work on a greenfield platform with modern architecture decisions documented in ADRs
- High test coverage culture (93% overall, 85% minimum enforced)
- Modular monolith — deployment simplicity without distributed system overhead
- Clear career path: Backend → Domain Architect → Chief Architect
- Competitive compensation aligned with Saudi market

## Interview Process

1. **Technical Screening** — Python + SQL + FastAPI coding challenge (1 hour)
2. **Architecture Discussion** — DDD patterns, repository pattern, modular monolith trade-offs (1 hour)
3. **Code Review** — Review a real SalesOS PR and discuss trade-offs (45 min)
4. **Team Fit** — Meet the engineering team (30 min)
5. **Offer** — Within 48 hours of final interview

---

*SalesOS is an equal opportunity employer. We value diversity and inclusion.*
