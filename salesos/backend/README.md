# SalesOS Backend

Enterprise Company Intelligence Platform — FastAPI-based modular monolith.

## Project Structure

```
backend/
├── app/                    # Application layer (FastAPI app, routers, modules)
│   ├── alembic/            # Database migrations (Alembic)
│   ├── application/        # CQRS application layer (dashboard, etc.)
│   ├── common/             # Shared middleware, metrics, logging
│   ├── modules/            # Domain modules (company, identity, search, etc.)
│   ├── routers/            # API route definitions
│   ├── config.py           # Environment-based configuration
│   ├── database.py         # Database session management
│   └── main.py             # FastAPI app factory + lifespan
├── domains/                # Domain layer (DDD — search, timeline, scoring, AI, etc.)
│   ├── search/             # Hybrid search (full-text + semantic)
│   ├── timeline/           # Universal timeline service
│   ├── scoring/            # Intelligence scoring engine
│   ├── decision/           # Decision context and recommendations
│   ├── ai/                 # Prompt registry, evaluation, generation
│   ├── commercial/         # Pipeline, opportunity, quote, contract
│   ├── revenue/            # Forecasting and analytics
│   └── workflow/           # Workflow automation engine
├── runtime/                # Runtime services (event bus, feature store, KG, etc.)
├── sdk/                    # SDK — cross-domain communication layer
├── demo/                   # Demo data seeders and generators
├── intelligence/           # Intelligence pipeline (enrichment, NLP)
├── tests/                  # Root test suite (unit + integration)
├── benchmarks/             # Performance benchmarks
├── migrations/             # SQL migration scripts (v0.1 legacy)
├── conftest.py             # Shared test fixtures
├── pyproject.toml          # Poetry config + tool settings
├── alembic.ini             # Alembic configuration
└── Dockerfile              # Container image
```

### Module Index

| Module | Location | Description |
|--------|----------|-------------|
| Identity | `app/modules/identity/` | Authentication, authorization, SSO |
| Company | `app/modules/company/` | Company profiles and management |
| Contact | `app/modules/contact/` | Contact management |
| Search | `app/modules/search/` | Search API and orchestration |
| Entity Resolution | `app/modules/entity_resolution/` | Entity matching and dedup |
| Executive | `app/modules/executive/` | Executive dashboard data |
| Dashboard | `app/application/dashboard/` | Aggregated dashboard projection |
| Decision | `app/modules/decision/` | Decision platform engine |
| Revenue Execution | `app/modules/revenue_execution/` | Revenue execution platform |
| Employee 360 | `app/modules/employee_360/` | Employee intelligence |
| Work Intelligence | `app/modules/work_intelligence/` | Activity and work patterns |
| Notion Sync | `app/modules/notion_sync/` | Notion integration |
| Excel Import | `app/modules/excel_import/` | Excel file import |
| Cache | `app/modules/cache/` | Cache management |
| Admin | `app/modules/admin/` | Admin panel |
| Audit | `app/modules/audit/` | Audit logging |
| API Keys | `app/modules/api_keys/` | API key management |
| SSO | `app/modules/sso/` | Single sign-on |
| Telemetry | `app/modules/telemetry/` | Customer telemetry |
| Monitoring | `app/modules/monitoring/` | Health monitoring |
| Tenant | `app/modules/tenant/` | Multi-tenant management |
| Demo Mode | `app/modules/demo_mode/` | Demo environment isolation |

## How to Add a New Module

1. **Create module package** — `app/modules/{name}/` with `__init__.py`, `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py`
2. **Define domain models** — SQLAlchemy models in `models.py` with table in `{name}` schema
3. **Create repository interface** — Abstract repository class in `repository.py`
4. **Implement repository** — SQLAlchemy implementation in `repository.py`
5. **Create service** — Business logic in `service.py`, depends on repository interface
6. **Create router** — FastAPI router in `router.py` with auth dependency
7. **Register router** — Add to `register_routers()` in `app/main.py`
8. **Add migration** — Create Alembic migration in `app/alembic/versions/`
9. **Write tests** — `app/modules/{name}/tests/` with InMemoryRepository
10. **Register module** — Add to `modules/registry.py` if it needs lifecycle hooks

## Repository Pattern Conventions

- **Repository interface** defined in domain layer (abstract class)
- **Implementation** in infrastructure layer (SQLAlchemy, PostgreSQL)
- **InMemoryRepository** in tests for deterministic, fast tests
- Services depend on repository interface — never on concrete implementation

```python
# domain/repository.py (interface)
class CompanyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Company | None: ...

# infrastructure/repository.py (implementation)
class PostgresCompanyRepository(CompanyRepository):
    def __init__(self, session: AsyncSession): ...

# tests/inmemory_repository.py (test double)
class InMemoryCompanyRepository(CompanyRepository):
    def __init__(self): self._companies: dict[UUID, Company] = {}
```

## Test Patterns

- **Deterministic** — no network calls, no shared state between tests
- **Fast** — each test < 1 second
- **InMemoryRepository** — replaces real DB for unit tests
- **Pytest fixtures** — use `conftest.py` for shared setup
- **Coverage target** — 85% unit test coverage

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific module tests
pytest app/modules/company/tests/
```

## Environment Setup

```bash
# Copy environment file
cp .env.example .env

# Install dependencies (Poetry)
poetry install

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# Or with Docker
docker compose up -d
```

Required environment variables (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `POSTGRES_*` | PostgreSQL connection |
| `REDIS_URL` | Redis cache connection |
| `OPENAI_API_KEY` | OpenAI for embeddings and AI features |
| `JWT_SECRET` | JWT signing key |
| `NEO4J_*` | Neo4j graph database (optional) |
| `KAFKA_*` | Kafka event bus (optional) |
| `SENTRY_DSN` | Error tracking (optional) |

## Migration Workflow

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Review generated migration
# Edit app/alembic/versions/{hash}_description.py

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

All migrations must be **reversible** — include `downgrade()` that reverses `upgrade()`.

## Architecture References

- [Engineering Constitution](../../engineering-os/ENGINEERING_CONSTITUTION.md)
- [ADR-001: Modular Monolith with DDD](../../engineering-os/adr/ADR-001-modular-monolith-foundation.md)
- [ADR-002: Executive Intelligence Workspace](../../engineering-os/adr/ADR-002-executive-intelligence-workspace.md)
- [Architecture Book](../docs/ARCHITECTURE_BOOK.md)
- [Architecture Compliance](../docs/ARCHITECTURE_COMPLIANCE.md)
- [Decision Platform Blueprint](../docs/DECISION_PLATFORM_BLUEPRINT.md)
