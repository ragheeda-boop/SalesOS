# Backend Audit

> SalesOS FastAPI Backend — Full Architecture, Routing, Domain, and Infrastructure Audit
> Last Updated: 2026-07-15

---

## Table of Contents

1. [Project Configuration](#1-project-configuration)
2. [Application Entry Point](#2-application-entry-point)
3. [Configuration / Settings](#3-configuration--settings)
4. [Database Layer](#4-database-layer)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [Top-Level API Routers](#6-top-level-api-routers)
7. [Module Routers](#7-module-routers)
8. [Application Routers](#8-application-routers)
9. [Domain Layer](#9-domain-layer)
10. [Runtime Layer](#10-runtime-layer)
11. [SDK Layer](#11-sdk-layer)
12. [Background Tasks & Celery](#12-background-tasks--celery)
13. [Middleware Stack](#13-middleware-stack)
14. [Dependency Map](#14-dependency-map)
15. [Key Observations](#15-key-observations)

---

## 1. Project Configuration

**File**: `pyproject.toml`

### Build System
- Python >=3.11
- Poetry for dependency management

### Core Dependencies

| Category | Packages |
|----------|----------|
| **Web Framework** | fastapi, uvicorn[standard], starlette |
| **ORM / Database** | sqlalchemy[asyncio] >=2.0, asyncpg, alembic, psycopg2-binary |
| **Auth** | python-jose[cryptography], passlib[bcrypt], python-multipart, itsdangerous (CSRF) |
| **AI / ML** | openai >=1.0, anthropic, instructor, pydantic-ai, langchain-core, langchain-community, llama-index, sentence-transformers |
| **Vector / Search** | pgvector, meilisearch |
| **Message Queue** | celery[redis] >=5.4, aiokafka, redis[hiredis] |
| **Graph DB** | neo4j |
| **Monitoring** | prometheus-client, opentelemetry-api, opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-exporter-otlp, sentry-sdk[fastapi] |
| **HTTP / Networking** | httpx >=0.27, aiohttp, httpx-sse |
| **Data Processing** | pandas, numpy, lxml, beautifulsoup4 |
| **Utilities** | pydantic[email] >=2.0, pydantic-settings, tiktoken, tenacity, tqdm, jsonschema, jsonpath-ng |
| **Notion** | notion-client |

### Dev Dependencies
- pytest, pytest-asyncio, pytest-cov
- ruff, mypy
- factory_boy (test factories)

### Tool Configuration
- **ruff**: line-length=127, target-version=py311, ignore=D100,D101,D102,D103,D104,D105,D107,D200,D205,D400,D401,D415,ANN,ERA001,INP001
- **mypy**: python-version=3.11, strict=false, various plugin configs for SQLAlchemy, Pydantic, Factory
- **pytest**: asyncio_mode=auto, markers (slow, integration, e2e, security)

---

## 2. Application Entry Point

**File**: `app/main.py`

### FastAPI App
- `title="SalesOS API"`, `version="2.0.0"`
- Docs: `/docs` (Swagger), `/redoc` (ReDoc), `/openapi.json`

### Lifespan
Initializes on startup:
1. Database engine (`init_db()`)
2. Event bus (Kafka if configured, else InMemory)
3. Runtime engines: `DecisionEngine`, `FeatureStore`, `KnowledgeGraphEngine`, `SearchRuntime`, `TimelineRuntime`, `EventRuntime`, `DataFabricPipeline`, `PolicyEngine`, `RecommendationEngine`, `ContextBuilder`, `ActivityRuntime`, `UXRuntime`
4. Telemetry: OpenTelemetry (if OTLP configured), Sentry (if DSN configured)
5. Background task: periodic DB pool status logging (every 300s)

Cleans up on shutdown:
1. Neo4j driver close
2. Kafka producer close
3. OpenAI/Anthropic client close
4. Database engine dispose

### Root Endpoint
- `GET /` → `{"service": "SalesOS API", "version": "2.0.0"}`

---

## 3. Configuration / Settings

**File**: `app/config.py`

Class `Settings(BaseSettings)` with `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`

### Database
| Variable | Default | Description |
|----------|---------|-------------|
| `database_url` | `postgresql+asyncpg://...` | Async PostgreSQL URL |
| `database_url_sync` | `postgresql://...` | Sync URL for Alembic |
| `db_pool_size` | 20 | Connection pool size |
| `db_max_overflow` | 10 | Max overflow connections |

### Redis
| Variable | Default | Description |
|----------|---------|-------------|
| `redis_url` | `redis://localhost:6379/0` | Redis connection URL |

### Neo4j
| Variable | Default | Description |
|----------|---------|-------------|
| `neo4j_uri` | `bolt://localhost:7687` | Graph DB URI |
| `neo4j_user` | `neo4j` | Username |
| `neo4j_password` | — | Password |

### Kafka
| Variable | Default | Description |
|----------|---------|-------------|
| `kafka_bootstrap_servers` | `localhost:9092` | Kafka bootstrap servers |

### JWT / Auth
| Variable | Default | Description |
|----------|---------|-------------|
| `jwt_secret_key` | — | HS256 key |
| `jwt_algorithm` | `HS256` | Algorithm |
| `jwt_expire_minutes` | 30 | Access token TTL |
| `jwt_refresh_expire_days` | 30 | Refresh token TTL |
| `csrf_secret_key` | — | CSRF signing key |

### OpenAI
| Variable | Default | Description |
|----------|---------|-------------|
| `openai_api_key` | — | OpenAI API key |
| `openai_model` | `gpt-4o` | Default model |
| `openai_embedding_model` | `text-embedding-3-small` | Embedding model |

### Meilisearch
| Variable | Default | Description |
|----------|---------|-------------|
| `meili_url` | `http://localhost:7700` | Meilisearch URL |
| `meili_master_key` | — | API key |

### Celery
| Variable | Default | Description |
|----------|---------|-------------|
| `celery_max_retries` | 3 | Max task retries |
| `celery_default_retry_delay` | 60s | Default retry delay |
| `celery_process_entity_delay` | 30s | process_entity retry delay |
| `celery_enrich_delay` | 30s | enrich retry delay |
| `celery_index_delay` | 30s | Meilisearch index retry delay |
| `celery_sync_notion_delay` | 30s | Notion sync retry delay |
| `celery_task_time_limit` | 600 | Hard time limit (seconds) |
| `celery_task_soft_time_limit` | 300 | Soft time limit (seconds) |
| `celery_worker_max_tasks_per_child` | 200 | Max tasks per worker before restart |
| `celery_worker_prefetch_multiplier` | 4 | Prefetch multiplier |
| `celery_result_expires` | 86400 | Result expiry (seconds) |

### Feature Flags (env booleans)
| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_OPENAI` | true | AI service enabled |
| `ENABLE_KAFKA_EVENTS` | false | Use Kafka instead of InMemory |
| `ENABLE_NEO4J` | true | Neo4j graph enabled |
| `ENABLE_RECOMMENDATIONS` | true | Recommendation engine |
| `ENABLE_ADVANCED_ANALYTICS` | false | Advanced analytics features |
| `ENABLE_SENTRY` | false | Sentry error tracking |
| `ENABLE_OTLP` | false | OpenTelemetry exporter |
| `ENABLE_RATE_LIMIT` | true | Rate limiting |
| `ENABLE_CSRF` | true | CSRF protection |
| `ENABLE_DEMO_MODE` | false | Demo mode endpoints |
| `ENABLE_MONITORING` | true | Monitoring/metrics |
| `ENABLE_PROMETHEUS` | true | Prometheus metrics |

---

## 4. Database Layer

**File**: `app/database.py`

### Engine
```python
engine = create_async_engine(settings.database_url, pool_size=20, max_overflow=10, echo=False)
```

### Session Factory
```python
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### Model Registrations (for Alembic `--autogenerate`)
```python
from app.modules.identity.models import User, Role, Permission, UserRole
from app.modules.company.models import Company, Contact, CompanyStatus, CompanyType, Industry
from app.modules.contact.models import Contact as ContactModel
from app.modules.entity_resolution.models import EntityResolutionRecord
from app.modules.decision.models import Decision
from app.modules.admin.models import AuditLog, SystemConfig
from app.modules.api_keys.models import ApiKey
from app.modules.audit.models import AuditTrailEntry
from app.modules.webhooks.models import WebhookSubscription, WebhookDelivery
from app.modules.notion_sync.models import NotionSyncLog
from app.domains.customer_success.models import HealthScore
from app.modules.sso.models import SSOProvider, SSOConfig
from app.modules.cache.models import CacheEntry
from app.modules.signal_marketplace.models import SignalSubscription, SignalProvider
from app.modules.revenue_execution.models import RevenueTarget, RevenueActual
from app.modules.executive.models import ExecutiveKpi, ExecutiveDashboard
from app.modules.work_intelligence.models import WorkPattern, WorkUnit
from app.modules.excel_import.models import ExcelImportJob
from app.modules.rules_engine.models import BusinessRule, RuleExecution
from app.modules.monitoring.models import SystemHealth, AlertConfig
from app.modules.telemetry.models import TelemetryEvent
```

### DatabaseConfig (Pydantic model)
- `dsn`, `pool_size`, `max_overflow`, `echo`, `pool_pre_ping`, `pool_recycle`

### Utility Functions
- `init_db()` — initializes the async engine
- `get_db()` — async generator dependency yielding sessions
- `get_base()` — returns DeclarativeBase

---

## 5. Authentication & Authorization

**File**: `app/dependencies.py`

### Core Dependencies

| Function | Type | What it does |
|----------|------|-------------|
| `verify_token()` | Header | Extracts & validates JWT from `Authorization: Bearer <token>`. Returns `TokenData(tenant_id, user_id, roles, permissions, scopes)` |
| `get_current_tenant_id()` | Header | Extracts `X-Tenant-Id` header, validates against JWT tenant_id |
| `get_current_user_id()` | Header | Extracts user_id from JWT payload |
| `require_role_dep(role: str)` | Factory | Returns dependency that checks user has specific role |
| `require_permission_dep(permission: str)` | Factory | Returns dependency that checks user has specific permission |

### CSRF Protection
- Applied via `csrf_middleware`
- Uses `itsdangerous` to sign/unsign CSRF tokens
- Checks `X-CSRF-Token` header on mutating requests (POST, PUT, DELETE, PATCH)

### RBAC / Permission Model
- `PermissionEnforcer` in `sdk.permissions`
- Permission check via `enforcer.enforce(user_id, action, resource)`
- Admin role check via `is_admin()` function
- `require_admin` dependency for admin-only routes

---

## 6. Top-Level API Routers

All top-level routers are mounted under `/api/v1/` and registered in `app/main.py`.

### 6.1 AI Router — `/api/v1/ai/`

**File**: `app/routers/ai.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/analyze` | JWT | Analyze entity data using AI |
| POST | `/generate-insights` | JWT | Generate business insights |
| POST | `/recommend` | JWT | AI-powered recommendations |

### 6.2 Analytics Router — `/api/v1/analytics/`

**File**: `app/routers/analytics.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/dashboard` | JWT | Analytics dashboard aggregation |

### 6.3 Benchmarks Router — `/api/v1/benchmarks/`

**File**: `app/routers/benchmarks.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | JWT | Benchmark comparisons |
| GET | `/industry/{industry}` | JWT | Industry-specific benchmarks |

### 6.4 Commercial Router — `/api/v1/commercial/`

**File**: `app/routers/commercial.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/pipeline` | JWT | Pipeline overview |
| POST | `/pipeline/stage` | JWT | Move deal in pipeline |
| GET | `/forecast` | JWT | Revenue forecasts |
| GET | `/opportunities` | JWT | List opportunities |

### 6.5 Copilot Router — `/api/v1/copilot/`

**File**: `app/routers/copilot.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/chat` | JWT | AI copilot chat |
| POST | `/suggest` | JWT | Contextual suggestions |

### 6.6 Demo Router — `/api/v1/demo/`

**File**: `app/routers/demo.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/reset` | Demo token | Reset demo data |
| POST | `/seed` | Demo token | Seed demo data |

### 6.7 Enrichment Router — `/api/v1/enrich/`

**File**: `app/routers/enrichment.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | JWT | Trigger enrichment (async, returns 202) |
| GET | `/status/{task_id}` | JWT | Check enrichment task status |

### 6.8 MCP Router — `/api/v1/mcp/`

**File**: `app/routers/mcp.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/execute` | JWT (or API key) | Execute MCP tool |
| GET | `/health` | JWT | MCP health check |

### 6.9 Meetings Router — `/api/v1/meetings/`

**File**: `app/routers/meetings.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/transcribe` | JWT | Transcribe meeting |
| POST | `/brief` | JWT | Generate meeting brief |
| GET | `/history` | JWT | Meeting history |

### 6.10 Metrics Router — `/api/v1/metrics/`

**File**: `app/routers/metrics.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | JWT | Prometheus metrics |
| GET | `/pool` | JWT | DB pool metrics |
| GET | `/app` | JWT | Application metrics |

### 6.11 Notifications Router — `/api/v1/notifications/`

**File**: `app/routers/notifications.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | JWT | List notifications |
| POST | `/` | JWT | Create notification |
| WS | `/ws` | JWT (query) | WebSocket notifications |
| GET | `/ws/metrics` | JWT | WS connection metrics |

### 6.12 Opportunities Router — `/api/v1/opportunities/`

**File**: `app/routers/opportunities.py`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| GET | `/` | JWT | 60/min | List opportunities |
| POST | `/` | JWT | 60/min | Create opportunity |
| GET | `/{id}` | JWT | 60/min | Get opportunity |
| PUT | `/{id}` | JWT | 60/min | Update opportunity |
| DELETE | `/{id}` | JWT | 60/min | Delete opportunity |

### 6.13 RAG Router — `/api/v1/rag/`

**File**: `app/routers/rag.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/query` | JWT | RAG query |
| POST | `/index` | JWT | Index document |

### 6.14 Revenue Router — `/api/v1/revenue/`

**File**: `app/routers/revenue.py`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| GET | `/` | JWT | 15/60s | Revenue data |
| GET | `/forecast` | JWT | 15/60s | Revenue forecast |

### 6.15 Search Router — `/api/v1/search/`

**File**: `app/routers/search.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | JWT | Hybrid search (full-text + semantic + RRF) |
| GET | `/suggest` | JWT | Autocomplete suggestions |

### 6.16 Workflows Router — `/api/v1/workflows/`

**File**: `app/routers/workflows.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | JWT | List workflows |
| POST | `/` | JWT | Create workflow |
| GET | `/{id}` | JWT | Get workflow |
| PUT | `/{id}` | JWT | Update workflow |
| POST | `/{id}/execute` | JWT | Execute workflow |

### 6.17 Admin / Demo Router — `/api/v1/admin/`

**File**: `app/routers/admin_demo.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/sla-report` | Admin | SLA compliance report |

---

## 7. Module Routers

Module routers are standalone feature modules under `app/modules/<name>/router.py`. They are included via `app.include_router()` or nested under the app.

| Module | Router Prefix | Auth | Key Endpoints |
|--------|--------------|------|---------------|
| **Company** | `/api/v1/companies` | JWT | CRUD companies, list by tenant, search, enrichment trigger |
| **Contact** | `/api/v1/contacts` | JWT | CRUD contacts, list by tenant, search |
| **Identity** | `/api/v1/auth` | Mixed | Login, register, refresh, verify email, password reset, SSO callback |
| **Entity Resolution** | `/api/v1/entity-resolution` | JWT | Match entities, merge, resolve conflicts |
| **Employee 360** | `/api/v1/employee-360` | JWT | Full employee profile, signals, scoring |
| **Executive** | `/api/v1/executive` | JWT | Executive KPIs, dashboards |
| **Work Intelligence** | `/api/v1/work-intelligence` | JWT | Work patterns, productivity |
| **Decision** | `/api/v1/decision` | JWT | Decision evaluations, NBA actions |
| **Revenue Execution** | `/api/v1/revenue-execution` | JWT | Revenue targets, actuals, pipeline |
| **Monitoring** | `/api/v1/monitoring` | JWT | System health, alerts, uptime |
| **SSO** | `/api/v1/sso` | JWT | SSO provider config, OIDC login |
| **Audit** | `/api/v1/audit` | JWT | Audit trail queries |
| **API Keys** | `/api/v1/api-keys` | JWT | API key management |
| **Admin** | `/api/v1/admin` | Admin | System config, user management |
| **Signal Marketplace** | `/api/v1/signals` | JWT | Signal subscriptions, providers |
| **Notion Sync** | `/api/v1/notion-sync` | JWT | Import Notion databases |
| **Cache** | `/api/v1/cache` | JWT | Cache management |
| **Telemetry** | `/api/v1/telemetry` | JWT | Telemetry events |
| **Webhooks** | `/api/v1/webhooks` | JWT | Webhook CRUD, delivery logs |
| **Rules Engine** | `/api/v1/rules` | JWT | Business rules CRUD, execution |
| **Excel Import** | `/api/v1/excel-import` | JWT | Excel upload, parse, preview, commit |
| **Customer Success** | `/api/v1/customer-success` | JWT | Health scores, risk flags |

---

## 8. Application Routers

### Dashboard CQRS Router

**File**: `app/application/dashboard/router.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/dashboard` | JWT | Aggregated dashboard data |

This router uses the CQRS pattern — reads are separated from write operations. It queries the `DashboardProjection` for pre-computed dashboard state.

---

## 9. Domain Layer

Located under `domains/`. Each domain is a bounded context with zero cross-domain imports.

| Domain | Path | Export |
|--------|------|--------|
| **commercial** | `domains/commercial/` | RT1 — opportunity, pipeline, account, forecast, activity sub-contexts |
| **ai** | `domains/ai/` | `AIModel`, `PromptTemplate`, `AIEvaluation`, `EvaluationMetric`, `PromptRegistry`, `AIEvaluator`, `BUILTIN_METRICS`, `AIService`, `AIProvider`, `OpenAIProvider`, `DecisionPlatformProvider` |
| **analytics** | `domains/analytics/` | Analytics engine |
| **rag** | `domains/rag/` | `Document`, `DocumentChunk`, `EmbeddingConfig` |
| **search** | `domains/search/` | Search domain models |
| **workflow** | `domains/workflow/` | Workflow domain |
| **timeline** | `domains/timeline/` | Timeline domain |
| **decision** | `domains/decision/` | Decision domain |
| **notifications** | `domains/notifications/` | Notification domain |
| **ubom** | `domains/ubom/` | UBOM (Universal Bill of Materials) domain |
| **scoring** | `domains/scoring/` | Scoring domain |
| **revenue** | `domains/revenue/` | Revenue domain |
| **feature_store** | `domains/feature_store/` | Feature store domain models |
| **customer_success** | `app/domains/customer_success/` | Legacy: HealthScore model |

---

## 10. Runtime Layer

Located under `runtime/`. Core execution engines initialized during app lifespan.

| Engine | Module | Description |
|--------|--------|-------------|
| **EventRuntime** | `runtime/event_runtime/` | Event lifecycle orchestrator: Store → Subscribers → Retry → DLQ → Metrics |
| **DataFabricPipeline** | `runtime/data_fabric_runtime/` | Ingestion pipeline: Collector → Normalizer → Validator → Entity Resolution → Golden Record (includes Balady + Taqeem scrapers) |
| **FeatureStore** | `runtime/feature_store/` | Precomputed business features with caching and event refresh. Computers: IcpComputer, FundingScoreComputer, HiringScoreComputer, GrowthScoreComputer, IntentScoreComputer, ExpansionScoreComputer, RevenueScoreComputer |
| **DecisionEngine** | `runtime/decision_runtime/` | Decision Intelligence Engine: Context → Policies → Engine → NBA → Feedback |
| **DecisionFeedbackLoop** | `runtime/decision_runtime/feedback_loop` | Feedback collection and model improvement |
| **ContextBuilder** | `runtime/context_runtime/` | Multi-dimensional company context builder |
| **PolicyEngine** | `runtime/policy_runtime/` | Business policy evaluation (DNC, VIP, Government, etc.) |
| **RecommendationEngine** | `runtime/recommendation_runtime/` | Recommendation generation from templates |
| **KnowledgeGraphEngine** | `runtime/knowledge_graph_runtime/` | Graph engine (Neo4j + SQL fallback). Node labels, edge types, path finding |
| **TimelineRuntime** | `runtime/timeline_runtime/` | Universal Timeline for every object |
| **SearchRuntime** | `runtime/search_runtime/` | Semantic + Hybrid + Ranking search |
| **ActivityRuntime** | `runtime/activity_runtime/` | Activity records spine table |
| **UXRuntime** | `runtime/ux_runtime/` | Experience layer: Navigation, Layout, Widget, Theme, Command, Notification |
| **WidgetEngine** | `runtime/widget_engine/` | Widget registry and built-in widgets |
| **CapabilityFramework** | `runtime/capability_framework/` | Self-describing capabilities |
| **UiSchemaEngine** | `runtime/ui_schema_engine/` | Dynamic UI schema generation |
| **FormEngine** | `runtime/form_engine/` | Dynamic form generation from JSON Schema |
| **ActionEngine** | `runtime/action_engine/` | Action registry and execution |
| **ExtensionAPI** | `runtime/extension_api/` | Hook point registry |
| **PluginSandbox** | `runtime/plugin_sandbox/` | Isolated plugin execution |
| **AdminRouter** | `runtime/admin_router/` | Admin-only endpoints |
| **ObjectViewer** | `runtime/object_viewer/` | Universal object viewer |

---

## 11. SDK Layer

Located under `sdk/`. Foundational layer consumed by all modules and runtimes.

| Module | Key Exports |
|--------|-------------|
| `sdk.events` | `DomainEvent`, `EventBus`, `EventStore`, `InMemoryEventBus`, `KafkaEventBus`, `PostgresEventStore`, `EVENT_REGISTRY`, 9 event types |
| `sdk.permissions` | `Permission`, `PermissionAction`, `PermissionEnforcer`, `PermissionRegistry`, `Role` |
| `sdk.security` | `create_jwt`, `decode_jwt`, `verify_password`, `hash_password`, `generate_api_key`, `verify_api_key` |
| `sdk.database` | `Entity`, `Repository`, `Specification`, `SqlAlchemyRepository`, `UnitOfWork` |
| `sdk.cache` | `CacheService`, `RedisCache` |
| `sdk.telemetry` | `StructuredLogger`, `get_meter`, `get_tracer`, `record_metric`, `setup_telemetry`, `trace_span` |
| `sdk.search` | `FullTextSearch`, `PgVectorSearch`, `VectorSearch`, `SearchQuery`, `SearchResult` |
| `sdk.vector` | `EmbeddingService`, `OpenAIEmbeddingService` |
| `sdk.audit` | `AuditTrail` |
| `sdk.exceptions` | `SalesOsError`, `ObjectNotFoundError`, `PermissionDeniedError`, `ValidationError`, `ConfigurationError`, `DuplicateObjectError`, `InvalidStateTransitionError` |
| `sdk.feature_registry` | `FeatureModule`, `FeatureRegistry`, `ModuleStatus` |
| `sdk.graph` | `GraphService` |
| `sdk.metadata` | `EntityMetadata`, `FieldMetadata`, `FieldType`, `MetadataRegistry`, `UiWidget` |
| `sdk.queue` | `TaskQueue`, `RedisTaskQueue` |
| `sdk.config` | `SdkSettings`, `sdk_settings` |

---

## 12. Background Tasks & Celery

### Celery App

**File**: `app/celery_app.py`

```python
celery_app = Celery("salesos", broker=settings.redis_url, backend=settings.redis_url, include=["app.tasks"])
```

Configuration:
- Serializer: JSON (task + result + content)
- Timezone: UTC
- `task_track_started=True`
- `task_time_limit`: 600s (from settings)
- `task_soft_time_limit`: 300s (from settings)
- `worker_max_tasks_per_child`: 200
- `task_acks_late=True` (at-least-once delivery)
- `worker_prefetch_multiplier`: 4
- `result_expires`: 86400s (24h)

### Celery Tasks

**File**: `app/tasks.py`

| Task | Retries | Delay | Description |
|------|---------|-------|-------------|
| `ping` | max_retries | default | Heartbeat, returns "pong" |
| `process_entity` | max_retries | 30s | **Orchestrator**: syncs to Neo4j graph + generates vector embedding for companies/contacts |
| `index_for_search` | max_retries | 30s | Indexes entity in Meilisearch via HTTP API |
| `enrich_company` | max_retries | 30s | **Pipeline**: runs Balady + Taqeem scrapers in parallel, recomputes all feature scores (ICP, Funding, Hiring, Growth, Intent, Expansion, Revenue) |
| `enrich_company_task` | 3 | 60s | **Async enrichment**: used by POST /enrich endpoint. Runs full pipeline + caches result in Redis for 24h |
| `sync_notion_database` | max_retries-1 | 30s | Imports Notion database entries as companies via `NotionSyncService` |

### Async Bridge
- Celery tasks are synchronous but delegate to async services via `_run_async(coro)` which calls `asyncio.run(coro)` in a fresh event loop
- This pattern is used by all tasks (process_entity, enrich_company, enrich_company_task, sync_notion_database)

---

## 13. Middleware Stack

Applied in `app/main.py` using `app.add_middleware()`:

| Order | Middleware | Purpose |
|-------|-----------|---------|
| 1 | `CORSMiddleware` | CORS: `http://localhost:3000, http://localhost:5173` |
| 2 | `TrustedHostMiddleware` | Host header validation |
| 3 | `SessionMiddleware` | Signed cookie sessions |
| 4 | CSRF Middleware (custom) | CSRF token validation on mutating requests |
| 5 | Rate Limit Middleware (custom) | Per-IP rate limiting with tiered limits |
| 6 | `PrometheusMiddleware` | Request metrics for Prometheus |
| 7 | OpenTelemetry Middleware | Distributed tracing (if OTLP enabled) |

### Exception Handlers
- `ValidationError` (Pydantic) → 422
- `ObjectNotFoundError` → 404
- `PermissionDeniedError` → 403
- `DuplicateObjectError` → 409
- `InvalidStateTransitionError` → 409
- `SalesOsError` (generic) → 400
- `Exception` (unhandled) → 500

---

## 14. Dependency Map

```
app/main.py
├── app/config.py          ← Settings (env vars + feature flags)
├── app/database.py        ← SQLAlchemy engine, session, model registrations
├── app/dependencies.py    ← JWT verification, tenant/resolver, RBAC
├── app/celery_app.py      ← Celery app (Redis broker + backend)
├── app/tasks.py           ← Background task definitions
│
├── app/routers/           ← 16 API router files
│   ├── ai.py              POST /analyze, /generate-insights, /recommend
│   ├── analytics.py       GET /dashboard
│   ├── benchmarks.py      GET /, /industry/{id}
│   ├── commercial.py      Pipeline, forecast, opportunities
│   ├── copilot.py         Chat, suggestions
│   ├── demo.py            Reset, seed
│   ├── enrichment.py      POST / (async 202), GET /status/{id}
│   ├── mcp.py             POST /execute, GET /health
│   ├── meetings.py        Transcribe, brief, history
│   ├── metrics.py         Prometheus + pool + app metrics
│   ├── notifications.py   CRUD + WebSocket
│   ├── opportunities.py   Full CRUD (rate limited 60/min)
│   ├── rag.py             Query, index
│   ├── revenue.py         Revenue + forecast (rate limited 15/60s)
│   ├── search.py          POST / (hybrid), GET /suggest
│   └── workflows.py       CRUD + execute
│
├── app/modules/           ← 22 feature modules
│   ├── company/           CRUD + enrichment trigger
│   ├── contact/           CRUD + search
│   ├── identity/          Login, register, refresh, SSO
│   ├── entity_resolution/ Match, merge, resolve
│   ├── employee_360/      Full profile + signals + scoring
│   ├── executive/         KPIs + dashboards
│   ├── work_intelligence/ Patterns + productivity
│   ├── decision/          Evaluations + NBA
│   ├── revenue_execution/ Targets + actuals
│   ├── monitoring/        System health + alerts
│   ├── sso/               Provider config + OIDC
│   ├── audit/             Audit trail
│   ├── api_keys/          Key management
│   ├── admin/             Config + user management
│   ├── signal_marketplace/ Subscriptions + providers
│   ├── notion_sync/       Notion DB import
│   ├── cache/             Cache management
│   ├── telemetry/         Events
│   ├── webhooks/          Subscriptions + deliveries
│   ├── rules_engine/      Business rules CRUD + execution
│   ├── excel_import/      Upload + parse + preview + commit
│   └── (customer_success under app/domains/)
│
├── app/application/
│   └── dashboard/router.py  CQRS dashboard aggregation
│
├── runtime/               ← 18+ runtime engines
│   ├── event_runtime/        Event lifecycle
│   ├── data_fabric_runtime/  Ingestion + scrapers
│   ├── feature_store/        Feature computation (7 computers)
│   ├── decision_runtime/     Decision engine + feedback loop
│   ├── context_runtime/      Context builder
│   ├── policy_runtime/       Policy evaluation
│   ├── recommendation_runtime/ Recommendations
│   ├── knowledge_graph_runtime/ Neo4j + SQL fallback
│   ├── timeline_runtime/     Universal timeline
│   ├── search_runtime/       Hybrid search
│   ├── activity_runtime/     Activity records
│   ├── ux_runtime/           Experience layer
│   ├── widget_engine/        Widget registry
│   ├── capability_framework/ Capabilities
│   ├── ui_schema_engine/     Dynamic UI schemas
│   ├── form_engine/          Dynamic forms
│   ├── action_engine/        Action registry
│   ├── extension_api/        Hook points
│   ├── plugin_sandbox/       Plugin isolation
│   ├── admin_router/         Admin endpoints
│   └── object_viewer/        Universal viewer
│
├── domains/               ← 14 bounded contexts
│   ├── commercial/        RT1 (opportunity, pipeline, account, etc.)
│   ├── ai/                AI model, prompt registry, evaluator
│   ├── analytics/         Analytics domain
│   ├── rag/               Document + chunk + embedding config
│   ├── search/            Search models
│   ├── workflow/          Workflow domain
│   ├── timeline/          Timeline domain
│   ├── decision/          Decision domain
│   ├── notifications/     Notification domain
│   ├── ubom/              UBOM domain
│   ├── scoring/           Scoring domain
│   ├── revenue/           Revenue domain
│   ├── feature_store/     Feature store domain
│   └── (customer_success under app/domains/)
│
└── sdk/                   ← 15 SDK modules
    ├── events/            Event bus (InMemory/Kafka/Postgres)
    ├── permissions/       RBAC enforcer
    ├── security/          JWT + password + API key utils
    ├── database/          Repository + Unit of Work pattern
    ├── cache/             Redis cache service
    ├── telemetry/         Tracing + metrics + structured logging
    ├── search/            Full-text + pgvector search
    ├── vector/            OpenAI embedding service
    ├── audit/             Audit trail
    ├── exceptions/        Domain exceptions
    ├── feature_registry/  Feature module registration
    ├── graph/             Graph service
    ├── metadata/          Entity metadata registry
    ├── queue/             Task queue (Redis-backed)
    └── config/            SDK settings
```

---

## 15. Key Observations

### Strengths
1. **Clean layered architecture**: SDK → Runtime → Domain → Module → Router, clear dependency direction
2. **Bounded contexts**: 14 domains with zero cross-domain imports (per `domains/__init__.py` — each is independent)
3. **Repository Pattern**: `SqlAlchemyRepository`, `UnitOfWork`, `Specification` in SDK — domain services depend on interfaces
4. **Multi-tenancy**: Consistent `X-Tenant-Id` header + JWT validation across all endpoints
5. **Defense in depth**: JWT auth + CSRF + rate limiting + RBAC + permission enforcer
6. **Event-driven**: InMemory (default) or Kafka event bus with postgres event store, retry policy, DLQ
7. **Comprehensive monitoring**: Prometheus metrics, OpenTelemetry traces, Sentry errors, structured logging
8. **Rich runtime**: 20+ runtime engines covering search, decision intelligence, feature computation, graph, timeline, activity, UX, widgets, capabilities, policies, recommendations

### Potential Risks / Technical Debt
1. **Celery async bridge**: `asyncio.run()` in each Celery task creates a new event loop per invocation — may cause event loop issues under load. Consider `celery-pool-asyncio` or dedicated async worker
2. **Middleware body consumption**: Known issue — POST body handling in middleware chain causes hangs during HTTP load testing (documented in ENGINEERING_DASHBOARD.md)
3. **Feature Store computers are hardcoded**: 7 `FeatureComputer` classes instantiated directly in both `tasks.py` and `enrichment.py`. Should be pluggable via registry
4. **Scrapers hardcode `use_mock=False`**: Balady and Taqeem scrapers are instantiated without environment-aware configuration
5. **Namespace duplication**: `CustomerSuccess` lives under `app/domains/` while all other domains are under `domains/` — likely a migration artifact
6. **No Redis in production**: Redis is configured but marked "Not Deployed" in dashboard — Celery and caching both depend on it
7. **No Kafka in production**: KafkaEventBus exists but `ENABLE_KAFKA_EVENTS` defaults to false. TD-002 tracks this
8. **Rate limit key is global-per-IP**: All endpoints share the same rate limit counter per IP (per Sprint 6 fix). This means aggressive use of one endpoint can throttle unrelated endpoints for the same user
