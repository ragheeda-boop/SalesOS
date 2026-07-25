# Master File Index

> Comprehensive index of every important file in the SalesOS repository.
> **Audit Date**: 2026-07-16
> **Repository**: salesos/
> **Total Indexed Files**: 280+

---

## Table of Contents

1. [Configuration Files](#1-configuration-files)
2. [Backend Entry Points](#2-backend-entry-points)
3. [API Routers](#3-api-routers)
4. [Domain Models & Services](#4-domain-models--services)
5. [Runtime Engines](#5-runtime-engines)
6. [SDK Modules](#6-sdk-modules)
7. [AI & Intelligence Components](#7-ai--intelligence-components)
8. [Frontend Pages](#8-frontend-pages)
9. [Frontend Components](#9-frontend-components)
10. [Frontend Features](#10-frontend-features)
11. [Internal Packages](#11-internal-packages)
12. [Hooks & Utilities](#12-hooks--utilities)
13. [Database Migrations](#13-database-migrations)
14. [Test Files](#14-test-files)
15. [Documentation](#15-documentation)
16. [Infrastructure (Docker, K8s, CI/CD)](#16-infrastructure)
17. [Scripts & Tools](#17-scripts--tools)
18. [SDK Submodules Detail](#18-sdk-submodules-detail)

---

## 1. Configuration Files

| File | Purpose | Dependencies | Used By | Importance |
|---|---|---|---|---|
| `opencode.json` | opencode AI configuration for the repo | engineering-os references | AI agents | High |
| `.env.example` | Environment variable template | — | Developers | High |
| `docker-compose.yml` | Local dev orchestration (Postgres, Neo4j, Redis, Kafka, API) | `Dockerfile.backend`, `Dockerfile.frontend` | Docker Compose | Critical |
| `docker-compose.prod.yml` | Production Docker Compose | — | DevOps | High |
| `docker-compose.test.yml` | Test Docker Compose | — | CI | High |
| `Makefile` | Build targets (test, lint, format) | — | Developers | Medium |
| `pyproject.toml` | Python project config (ruff, mypy, pytest) | — | Backend | Critical |
| `setup.ps1` | Windows dev environment setup | — | Developers | Medium |
| `start.sh` | Unix dev environment startup | — | Developers | Medium |
| `start.bat` | Windows dev environment startup | — | Developers | Medium |
| `SLA_CONFIG.json` | SLA configuration for monitoring | — | Monitoring | High |
| `backend/pyproject.toml` | Backend Python dependencies | — | Backend | Critical |
| `backend/alembic.ini` | Alembic migration config | `migrations/` | Database | Critical |
| `backend/.env` | Backend environment secrets | — | Backend | Critical |
| `backend/.env.production.template` | Production env template | — | DevOps | High |
| `frontend/package.json` | Frontend npm dependencies | — | Frontend | Critical |
| `frontend/next.config.js` | Next.js configuration | — | Frontend | High |
| `frontend/tsconfig.json` | TypeScript configuration | — | Frontend | Critical |
| `frontend/tailwind.config.ts` | Tailwind CSS theme config | `design-language` | Frontend | High |
| `frontend/postcss.config.js` | PostCSS configuration | — | Frontend | Medium |
| `frontend/playwright.config.ts` | E2E test configuration | — | Testing | Medium |
| `infra/k8s/kustomization.yaml` | K8s kustomize overlay | All K8s manifests | K8s | High |
| `.github/dependabot.yml` | Dependabot dependency updates | — | CI | Medium |
| `backend/benchmark.db` | SQLite benchmark database | `benchmark/run.py` | Performance | Low |
| `.pre-commit-config.yaml` | Pre-commit hooks config | — | Developers | Medium |

---

## 2. Backend Entry Points

| File | Purpose | Dependencies | Used By | Importance |
|---|---|---|---|---|
| `backend/app/main.py` | FastAPI application factory, lifespan, router registration | All routers, SDKs, runtimes | Docker, uvicorn | Critical |
| `backend/app/config.py` | Pydantic settings (env-based config) | `pydantic_settings` | All backend modules | Critical |
| `backend/app/database.py` | SQLAlchemy async engine + session factory | `sqlalchemy.ext.asyncio` | All repositories | Critical |
| `backend/app/dependencies.py` | FastAPI dependency injection (auth, DB, permissions) | Identity module, SDK | All routers | Critical |
| `backend/app/cache.py` | Redis cache service | `redis.asyncio` | Runtime engines | High |
| `backend/app/celery_app.py` | Celery async task queue | `celery` | Enrichment, async tasks | High |
| `backend/app/tasks.py` | Celery task definitions | `celery_app.py` | Background jobs | High |
| `backend/mcp_server/server.py` | MCP protocol server (SSE transport) | MCP tools, resources | AI agents | High |

---

## 3. API Routers

### App Routers (backend/app/routers/)

| File | Endpoint Prefix | Purpose | Dependencies | Importance |
|---|---|---|---|---|
| `routers/__init__.py` | — | Router package init | — | Low |
| `routers/search.py` | `/api/v1/search` | Full-text + semantic search API | SearchRuntime, PostgresSearchRepository | Critical |
| `routers/ai.py` | `/api/v1/ai` | AI prompt registry + evaluation | AIService, PromptRegistry | High |
| `routers/analytics.py` | `/api/v1/analytics` | Analytics & reporting API | AnalyticsService | High |
| `routers/revenue.py` | `/api/v1/revenue` | Revenue intelligence API | RevenueService | High |
| `routers/opportunities.py` | `/api/v1/opportunities` | Opportunity management API | OpportunityService | High |
| `routers/meetings.py` | `/api/v1/meetings` | Meeting intelligence API | MeetingService | Medium |
| `routers/workflows.py` | `/api/v1/workflows` | Workflow engine API | WorkflowService | High |
| `routers/rag.py` | `/api/v1/rag` | RAG pipeline API | RAGService | High |
| `routers/commercial.py` | `/api/v1/commercial` | Commercial domain API | CommercialService | Medium |
| `routers/copilot.py` | `/api/v1/copilot` | AI Copilot API | AIService | Medium |
| `routers/demo.py` | `/demo` | Demo environment (public) | — | Low |
| `routers/admin_demo.py` | `/admin/demo` | Admin demo management | IdentityService | Low |
| `routers/notifications.py` | `/api/v1/notifications` | WebSocket + REST notifications | WS Manager | High |
| `routers/metrics.py` | `/metrics` | Prometheus metrics, pool stats | Collector | High |
| `routers/enrichment.py` | `/api/v1/enrich` | Async company enrichment (Celery) | Celery tasks | High |
| `routers/mcp.py` | `/mcp` | MCP protocol SSE endpoint | MCPServer | High |
| `routers/benchmarks.py` | `/benchmarks` | Benchmark endpoints | BenchmarkRunner | Low |

### Module Routers (backend/app/modules/*/)

| File | Endpoint Prefix | Purpose | Dependencies | Importance |
|---|---|---|---|---|
| `modules/identity/router.py` | `/api/v1/identity` | Auth (login, register, JWT) | IdentityService | Critical |
| `modules/identity/signup_router.py` | `/api/v1/identity/signup` | User signup flow | SignupService | High |
| `modules/identity/invite_router.py` | `/api/v1/identity/invite` | User invitation flow | InviteService | High |
| `modules/company/router.py` | `/api/v1/companies` | Company CRUD + intelligence | CompanyService, IntelligenceComputer | Critical |
| `modules/contact/router.py` | `/api/v1/contacts` | Contact CRUD + enrichment | ContactService | High |
| `modules/entity_resolution/router.py` | `/api/v1/entity-resolution` | Entity dedup + merge (pg_trgm) | EntityResolutionService | High |
| `modules/signal_marketplace/router.py` | `/api/v1/signals` | Signal marketplace API | SignalEngine | Medium |
| `modules/notion_sync/router.py` | `/api/v1/notion-sync` | Notion sync API | NotionSyncService | Medium |
| `modules/excel_import/router.py` | `/api/v1/excel-import` | Excel import API | ExcelImportService | Medium |
| `modules/employee_360/router.py` | `/api/v1/employee-360` | Employee 360 view API | Employee360Service | High |
| `modules/executive/router.py` | `/api/v1/executive` | Executive dashboard API | ExecutiveService | High |
| `modules/dashboard/router.py` | `/api/v1/dashboard` | Dashboard widgets API | DashboardService | Critical |
| `modules/work_intelligence/router.py` | `/api/v1/work-intelligence` | Work intelligence API | WorkIntelligenceEngine | Medium |
| `modules/decision/router.py` | `/api/v1/decisions` | Decision platform API | DecisionPlatformEngine | Critical |
| `modules/revenue_execution/router.py` | `/api/v1/revenue-execution` | Revenue execution API | RevenueExecutionService | High |
| `modules/monitoring/router.py` | `/api/v1/monitoring` | System monitoring API | — | High |
| `modules/cache/router.py` | `/api/v1/cache` | Cache management API | CacheService | Low |
| `modules/sso/router.py` | `/api/v1/sso` | SSO (Google, Microsoft, GitHub) | SSOService | High |
| `modules/sso/saml_router.py` | `/api/v1/sso/saml` | SAML SSO | SAMLService | High |
| `modules/webhooks/router.py` | `/api/v1/webhooks` | Webhook management | WebhookService | High |
| `modules/audit/router.py` | `/api/v1/audit` | Audit log API | AuditService | High |
| `modules/api_keys/router.py` | `/api/v1/api-keys` | API key management | ApiKeyService | High |
| `modules/admin/router.py` | `/api/v1/admin` | Admin panel API | AdminService | High |
| `modules/telemetry/router.py` | `/api/v1/telemetry` | Customer telemetry API | TelemetryService | High |
| `modules/rules_engine/router.py` | `/api/v1/rules` | Business rules engine API | RulesEngine | High |

### Runtime Routers (backend/runtime/*/)

| File | Endpoint Prefix | Purpose | Dependencies | Importance |
|---|---|---|---|---|
| `runtime/admin_router.py` | `/admin` | Admin system routes | — | High |
| `runtime/decision_runtime/router.py` | `/api/v1/decisions` | Decision engine runtime API | DecisionEngine | Critical |
| `runtime/search_runtime/router.py` | `/api/v1/search` | Search runtime API | SearchRuntime | Critical |
| `runtime/data_fabric_runtime/router.py` | `/api/v1/data-fabric` | Data fabric pipeline API | DataFabricPipeline | High |
| `runtime/feature_store/router.py` | `/api/v1/feature-store` | Feature store runtime API | FeatureStore | High |
| `runtime/knowledge_graph_runtime/router.py` | `/api/v1/graph` | Knowledge graph API | KnowledgeGraphEngine | High |
| `runtime/event_runtime/router.py` | `/api/v1/events` | Event runtime API | EventRuntime | Medium |
| `runtime/activity_runtime/router.py` | `/api/v1/activities` | Activity runtime API | ActivityRuntime | High |
| `runtime/timeline_runtime/router.py` | `/api/v1/timeline` | Timeline runtime API | TimelineRuntime | High |
| `runtime/nba_engine/api/router.py` | `/api/v1/nba` | Next-best-action engine API | NBAEngine | High |
| `runtime/pipeline_analytics/router.py` | `/api/v1/pipeline-analytics` | Pipeline analytics API | PipelineAnalytics | High |
| `runtime/ui_schema_engine/router.py` | `/api/v1/schemas` | UI schema engine API | UISchemaEngine | Medium |
| `runtime/form_engine/router.py` | `/api/v1/forms` | Dynamic form engine API | FormEngine | Medium |
| `runtime/action_engine/router.py` | `/api/v1/actions` | Action registry API | ActionRegistry | Medium |
| `runtime/extension_api/router.py` | `/api/v1/extensions` | Extension API | ExtensionHooks | Low |
| `runtime/plugin_sandbox/router.py` | `/api/v1/plugins` | Plugin sandbox API | PluginSandbox | Low |
| `runtime/capability_framework/router.py` | `/api/v1/capabilities` | Capability framework API | CapabilityRegistry | Medium |
| `runtime/ux_runtime/router.py` | `/api/v1/ux` | UX experience layer API | UXRuntime | Medium |
| `runtime/scheduler_runtime/` | — | Scheduled task runtime | — | Medium |

### Domain Routers (backend/domains/*/)

| File | Endpoint Prefix | Purpose | Dependencies | Importance |
|---|---|---|---|---|
| `domains/timeline/router.py` | `/api/v1/timeline` | Timeline domain API | TimelineService | High |
| `domains/feature_store/router.py` | `/api/v1/feature-store` | Feature store domain API | FeatureStoreDomainService | High |

### GraphQL

| File | Purpose | Dependencies | Importance |
|---|---|---|---|
| `app/graphql/schema.py` | GraphQL schema (Strawberry) | All domain types | High |

---

## 4. Domain Models & Services

### Identity Domain

| File | Purpose | Importance |
|---|---|---|
| `app/modules/identity/models.py` | Identity DB models (User, Role, Tenant) | Critical |
| `app/modules/identity/service.py` | JWT creation/validation, user CRUD | Critical |
| `app/modules/identity/repositories.py` | Identity repository (PostgreSQL) | Critical |
| `app/modules/identity/schemas.py` | Identity Pydantic schemas | Critical |
| `app/modules/identity/signup_service.py` | User signup with activation | High |
| `app/modules/identity/invite_service.py` | User invitation flow | High |

### Company Domain

| File | Purpose | Importance |
|---|---|---|
| `app/modules/company/models.py` | Company DB models | Critical |
| `app/modules/company/router.py` | Company CRUD routes | Critical |
| `app/modules/company/repositories.py` | Company repository (PostgreSQL) | Critical |
| `app/modules/company/search_repository.py` | Company full-text search repo | High |
| `app/modules/company/pgvector_repository.py` | Company vector search repo | High |
| `app/modules/company/intelligence_computer.py` | Company intelligence scoring | High |
| `app/modules/company/intelligence_dto.py` | Company intelligence DTO | High |

### Search Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/search/contracts/models.py` | Search domain models | Critical |
| `domains/search/contracts/repository.py` | Search repository interface | Critical |
| `domains/search/engine/hybrid_search.py` | Hybrid search (full-text + vector + RRF) | Critical |
| `domains/search/engine/postgres_repo.py` | PostgreSQL search repository | Critical |
| `domains/search/engine/embedding_service.py` | OpenAI embedding integration | High |
| `domains/search/engine/vector_store.py` | pgvector vector store | High |
| `domains/search/engine/planner.py` | Search query planner | High |
| `domains/search/engine/parser.py` | Search query parser | High |
| `domains/search/engine/strategy_matrix.py` | Search strategy selection | Medium |
| `domains/search/engine/specifications.py` | Search specification patterns | Medium |
| `domains/search/normalization/arabic_normalizer.py` | Arabic text normalization | High |
| `domains/search/normalization/arabic_thesaurus.py` | Arabic thesaurus for synonyms | Medium |
| `domains/search/normalization/company_matcher.py` | Company name fuzzy matching | High |
| `domains/search/normalization/stop_words.py` | Arabic stop words list | Medium |
| `domains/search/ranking/pipeline.py` | Search result ranking pipeline | High |

### Scoring Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/scoring/models.py` | Scoring domain models | Critical |
| `domains/scoring/engine.py` | Scoring engine (lead scoring, fit scoring) | Critical |
| `domains/scoring/infrastructure/postgres_repository.py` | PostgreSQL scoring repository | High |

### Decision Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/decision/recommendation/models.py` | Recommendation models | Critical |
| `domains/decision/recommendation/engine.py` | Recommendation engine | Critical |
| `domains/decision/recommendation/repo.py` | Recommendation repository interface | High |
| `domains/decision/recommendation/in_memory_repo.py` | In-memory recommendation repo | Testing |
| `domains/decision/context/models.py` | Decision context models | High |
| `domains/decision/context/service.py` | Decision context service | High |
| `domains/decision/context/repo.py` | Context repository interface | High |

### Timeline Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/timeline/models.py` | Timeline domain models | Critical |
| `domains/timeline/service.py` | Timeline service | Critical |
| `domains/timeline/contracts/models.py` | Timeline contract models | High |
| `domains/timeline/contracts/repository.py` | Timeline repository interface | High |
| `domains/timeline/engine/recorder.py` | Timeline event recorder | Critical |
| `domains/timeline/engine/postgres_repo.py` | PostgreSQL timeline repo | High |
| `domains/timeline/engine/in_memory_repo.py` | In-memory timeline repo | Testing |

### Workflow Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/workflow/models.py` | Workflow domain models | Critical |
| `domains/workflow/service.py` | Workflow service | Critical |
| `domains/workflow/engine.py` | Workflow execution engine | Critical |
| `domains/workflow/repository.py` | Workflow repository interface | High |
| `domains/workflow/postgres_repo.py` | PostgreSQL workflow repo | High |
| `domains/workflow/schemas.py` | Workflow Pydantic schemas | Critical |
| `domains/workflow/templates.py` | Workflow template definitions | Medium |
| `domains/workflow/event_subscriber.py` | Workflow event subscriber | Medium |
| `domains/workflow/db_models.py` | Workflow SQLAlchemy models | Critical |

### Revenue Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/revenue/forecast/models.py` | Forecast domain models | High |
| `domains/revenue/forecast/service.py` | Forecast service | High |
| `domains/revenue/forecast/engine.py` | Forecast computation engine | High |
| `domains/revenue/forecast/repo.py` | Forecast repository interface | Medium |
| `domains/revenue/analytics/models.py` | Revenue analytics models | High |
| `domains/revenue/analytics/service.py` | Revenue analytics service | High |
| `domains/revenue/analytics/postgres_repo.py` | PostgreSQL analytics repo | High |
| `domains/revenue/analytics/registry.py` | Analytics metric registry | Medium |

### Feature Store Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/feature_store/models.py` | Feature store models | Critical |
| `domains/feature_store/service.py` | Feature store domain service | Critical |
| `domains/feature_store/repository.py` | Feature store repository interface | High |
| `domains/feature_store/postgres_repo.py` | PostgreSQL feature store repo | High |
| `domains/feature_store/infrastructure.py` | Feature store infrastructure | Medium |

### AI Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/ai/models.py` | AI domain models (Prompt, Evaluation) | Critical |
| `domains/ai/service.py` | AI service (prompt execution, LLM calls) | Critical |
| `domains/ai/registry.py` | Prompt registry | High |
| `domains/ai/evaluator.py` | AI output evaluator | High |

### Commercial Domain

| File | Purpose | Importance |
|---|---|---|
| `domains/commercial/opportunity/engine/service.py` | Opportunity service | Critical |
| `domains/commercial/infrastructure/postgres_repositories.py` | PostgreSQL opportunity repo | High |

### Support Modules (backend/app/modules/*/)

| File | Purpose | Importance |
|---|---|---|
| `modules/contact/models.py` | Contact DB models | Critical |
| `modules/contact/service.py` | Contact service | Critical |
| `modules/entity_resolution/models.py` | Entity resolution models | High |
| `modules/entity_resolution/repositories.py` | Entity resolution repository | High |
| `modules/signal_marketplace/engine.py` | Signal detection engine | High |
| `modules/signal_marketplace/models.py` | Signal marketplace models | Medium |
| `modules/telemetry/models.py` | Telemetry data models | Medium |
| `modules/webhooks/models.py` | Webhook models | High |
| `modules/webhooks/service.py` | Webhook delivery service | High |
| `modules/audit/models.py` | Audit log models | High |
| `modules/audit/service.py` | Audit log service | High |
| `modules/audit/middleware.py` | Audit middleware | High |
| `modules/api_keys/models.py` | API key models | High |
| `modules/api_keys/service.py` | API key service | High |
| `modules/api_keys/middleware.py` | API key middleware | High |
| `modules/admin/models.py` | Admin panel models | High |
| `modules/admin/repositories.py` | Admin panel repositories | High |
| `modules/admin/health_score_service.py` | Admin health score computation | Medium |
| `modules/notion_sync/service.py` | Notion sync service | Medium |
| `modules/excel_import/service.py` | Excel import service | Medium |
| `modules/employee_360/service.py` | Employee 360 service | High |
| `modules/executive/service.py` | Executive dashboard service | High |
| `modules/revenue_execution/models.py` | Revenue execution models | High |
| `modules/revenue_execution/service.py` | Revenue execution service | High |

---

## 5. Runtime Engines

| File | Purpose | Dependencies | Importance |
|---|---|---|---|
| `runtime/__init__.py` | Runtime exports (DecisionEngine, SearchRuntime, etc.) | All runtimes | Critical |
| `runtime/activity_runtime/` | Unified activity spine (CRUD, queries, aggregation) | SQLAlchemy | Critical |
| `runtime/agent_runtime/` | AI agent execution runtime | AIService, LLM providers | High |
| `runtime/context_runtime/` | Context builder for decision engine | FeatureStore | Critical |
| `runtime/decision_runtime/models.py` | Decision engine models | — | Critical |
| `runtime/decision_runtime/registry.py` | Decision widget registry | — | High |
| `runtime/decision_runtime/feedback_loop.py` | Decision feedback loop (learn from outcomes) | — | High |
| `runtime/decision_runtime/events.py` | Decision events | — | Medium |
| `runtime/event_runtime/` | In-memory event bus with subscriber pattern | asyncio | High |
| `runtime/execution_runtime/` | Execution runtime for actions | ActionRegistry | Medium |
| `runtime/feature_store/computers/` | Feature computers (ICP, Funding, Hiring, Growth, Intent, Expansion, Revenue) | — | Critical |
| `runtime/knowledge_graph_runtime/` | Neo4j knowledge graph engine | neo4j driver | High |
| `runtime/data_fabric_runtime/` | Data fabric pipeline (entity resolution, enrichment, vectorization) | All computers | Critical |
| `runtime/data_fabric_runtime/scrapers/` | Web scraper integrations | httpx | Medium |
| `runtime/memory_runtime/` | In-memory state runtime | — | Medium |
| `runtime/nba_engine/engine/ai/reasoner.py` | NBA AI reasoner | LLM | High |
| `runtime/nba_engine/engine/risk/deal_health.py` | Deal health scoring | ScoringEngine | High |
| `runtime/pipeline_analytics/` | Pipeline analytics engine | SQLAlchemy | High |
| `runtime/policy_runtime/` | Policy engine (business rules) | RulesEngine | High |
| `runtime/recommendation_runtime/` | Recommendation engine | ScoringEngine | High |
| `runtime/search_runtime/` | Search runtime (hybrid search orchestrator) | SearchDomain | Critical |
| `runtime/simulation_runtime/` | What-if simulation engine | DecisionEngine | Medium |
| `runtime/timeline_runtime/` | Universal timeline runtime | TimelineDomain | Critical |
| `runtime/ux_runtime/` | UX experience layer (personalization) | — | Medium |
| `runtime/widget_engine/` | Widget registry & rendering engine | SDK | High |
| `runtime/workflow_runtime/` | Workflow execution runtime | WorkflowDomain | High |
| `runtime/capability_framework/` | Capability registry & discovery | — | Medium |
| `runtime/form_engine/` | Dynamic form generation engine | UISchemaEngine | Medium |
| `runtime/ui_schema_engine/` | Schema-driven UI engine | — | Medium |
| `runtime/action_engine/` | Action registry & execution | — | Medium |
| `runtime/extension_api/` | Extension/plugin hook system | — | Low |
| `runtime/plugin_sandbox/` | Plugin sandbox (secure execution) | — | Low |
| `runtime/object_viewer.py` | Universal object viewer | — | Low |

---

## 6. SDK Modules

| File | Purpose | Dependencies | Importance |
|---|---|---|---|
| `sdk/__init__.py` | SDK exports | — | Critical |
| `sdk/backend_sdk/` | Backend client SDK for internal use | All runtime | High |
| `sdk/frontend_sdk/` | Frontend client SDK | — | High |
| `sdk/agent_sdk/` | Agent SDK (tool definitions, agent context) | — | High |
| `sdk/plugin_sdk/` | Plugin development SDK | — | Medium |
| `sdk/integration_sdk/` | Third-party integration SDK | — | Medium |
| `sdk/theme_sdk/` | Theme/design token SDK | — | Low |
| `sdk/widget_sdk/` | Widget development SDK | Workspace package | High |
| `sdk/audit.py` | Audit trail SDK | — | High |
| `sdk/capability_registry.py` | Capability registry SDK | — | Medium |
| `sdk/cache/` | Cache abstraction (Redis, in-memory) | — | High |
| `sdk/commercial/` | Commercial domain SDK | — | Medium |
| `sdk/company_sdk/` | Company domain SDK | — | Medium |
| `sdk/config.py` | SDK configuration | — | High |
| `sdk/database.py` | Database access SDK | SQLAlchemy | High |
| `sdk/events/` | Event system SDK (in-memory + Kafka) | kafka-python | Critical |
| `sdk/events/base.py` | Domain event base class | — | Critical |
| `sdk/events/kafka_bus.py` | Kafka event bus implementation | kafka-python | High |
| `sdk/exceptions.py` | SDK exception hierarchy | — | High |
| `sdk/feature_registry.py` | Feature flag registry | — | Medium |
| `sdk/graph.py` | Graph database SDK (Neo4j) | neo4j | High |
| `sdk/metadata.py` | Metadata SDK | — | Low |
| `sdk/pagination.py` | Pagination utilities | — | High |
| `sdk/permissions.py` | RBAC permission enforcer | — | Critical |
| `sdk/queue.py` | Queue abstraction (Celery, RQ) | — | Medium |
| `sdk/repositories/` | Base repository patterns | — | High |
| `sdk/scoring/` | Scoring engine SDK | — | High |
| `sdk/search.py` | Search SDK | — | Medium |
| `sdk/security.py` | Security utilities (hashing, encryption) | — | Critical |
| `sdk/telemetry.py` | Structured logging & telemetry | structlog | Critical |
| `sdk/vector.py` | Vector embedding service SDK | openai | High |

---

## 7. AI & Intelligence Components

### AI Agents (backend/intelligence/agents/)

| File | Purpose | Importance |
|---|---|---|
| `intelligence/agents/base.py` | Base agent class with common tool execution | Critical |
| `intelligence/agents/coordinator.py` | Agent coordinator (orchestrates sub-agents) | Critical |
| `intelligence/agents/llm.py` | LLM interaction agent | Critical |
| `intelligence/agents/research.py` | Company research agent | High |
| `intelligence/agents/competitor.py` | Competitive analysis agent | High |
| `intelligence/agents/meeting.py` | Meeting intelligence agent | High |
| `intelligence/agents/contract.py` | Contract analysis agent | High |
| `intelligence/agents/pricing.py` | Pricing optimization agent | Medium |
| `intelligence/agents/proposal.py` | Proposal generation agent | Medium |
| `intelligence/agents/renewal.py` | Renewal prediction agent | Medium |
| `intelligence/agents/forecast.py` | Revenue forecast agent | High |
| `intelligence/agents/relationship.py` | Relationship intelligence agent | Medium |
| `intelligence/agents/news.py` | News monitoring agent | Medium |
| `intelligence/agents/tender.py` | Tender detection agent | Medium |

### AI Infrastructure

| File | Purpose | Importance |
|---|---|---|
| `intelligence/agent_base.py` | Agent base class (lower-level) | High |
| `intelligence/providers/base.py` | LLM provider interface | Critical |
| `intelligence/providers/factory.py` | LLM provider factory (OpenAI, etc.) | Critical |
| `intelligence/providers/openai_provider.py` | OpenAI LLM provider | Critical |
| `intelligence/prompts/agents.yaml` | Agent prompt definitions (YAML) | Critical |
| `intelligence/prompts/registry.py` | Prompt registry (loads agents.yaml) | Critical |
| `intelligence/reasoning.py` | Reasoning engine (chain-of-thought) | High |
| `intelligence/grounding.py` | Grounding / fact-checking module | High |
| `intelligence/guardrails.py` | Output guardrails (content filters) | High |
| `intelligence/schemas.py` | AI pipeline schemas | High |
| `intelligence/cost_tracker.py` | AI token cost tracking | Medium |
| `intelligence/evaluation/` | AI evaluation framework | High |

### RAG Pipeline

| File | Purpose | Importance |
|---|---|---|
| `intelligence/rag/` | RAG pipeline (retrieval, context building) | High |
| `domains/rag/models.py` | RAG domain models | High |

### Intelligence Pipelines (backend/intelligence/)

| File | Purpose | Importance |
|---|---|---|
| `intelligence/arabic/` | Arabic NLP processing | High |
| `intelligence/business_objects/` | Business object extraction | Medium |
| `intelligence/company/` | Company intelligence pipeline | High |
| `intelligence/data_fabric/` | Data fabric intelligence | High |
| `intelligence/digital_twin/` | Digital twin modeling | Medium |
| `intelligence/enrichment/` | Data enrichment pipeline | High |
| `intelligence/graph/` | Graph intelligence (Neo4j queries) | High |
| `intelligence/market/` | Market intelligence | Medium |
| `intelligence/revenue_brain/` | Revenue brain (unified revenue AI) | High |
| `intelligence/signals/` | Signal detection pipeline | High |

---

## 8. Frontend Pages

| File | Route | Purpose | Importance |
|---|---|---|---|
| `src/app/layout.tsx` | `/` | Root layout with providers | Critical |
| `src/app/page.tsx` | `/` | Home/landing page | Critical |
| `src/app/providers.tsx` | — | React context providers (auth, workspace, etc.) | Critical |
| `src/app/globals.css` | — | Global CSS with design tokens | Critical |
| `src/app/(auth)/login/page.tsx` | `/login` | Login page | Critical |
| `src/app/(auth)/register/page.tsx` | `/register` | Registration page | High |
| `src/app/(dashboard)/layout.tsx` | `/` (dashboard) | Dashboard shell layout | Critical |
| `src/app/(dashboard)/page.tsx` | `/dashboard` | Main dashboard page | Critical |
| `src/app/(dashboard)/admin/page.tsx` | `/admin` | Admin panel | High |
| `src/app/(dashboard)/search/page.tsx` | `/search` | Global search | Critical |
| `src/app/(dashboard)/companies/page.tsx` | `/companies` | Company list & detail | Critical |
| `src/app/(dashboard)/contacts/page.tsx` | `/contacts` | Contact management | High |
| `src/app/(dashboard)/opportunities/page.tsx` | `/opportunities` | Opportunity pipeline | Critical |
| `src/app/(dashboard)/activities/page.tsx` | `/activities` | Activity feed | High |
| `src/app/(dashboard)/decisions/page.tsx` | `/decisions` | Decision center | High |
| `src/app/(dashboard)/analytics/page.tsx` | `/analytics` | Analytics & reports | High |
| `src/app/(dashboard)/revenue/page.tsx` | `/revenue` | Revenue intelligence | High |
| `src/app/(dashboard)/forecast/page.tsx` | `/forecast` | Revenue forecasting | High |
| `src/app/(dashboard)/pipeline/page.tsx` | `/pipeline` | Pipeline analytics | High |
| `src/app/(dashboard)/ai/page.tsx` | `/ai` | AI assistant/copilot | Medium |
| `src/app/(dashboard)/copilot/page.tsx` | `/copilot` | AI copilot interface | Medium |
| `src/app/(dashboard)/signals/page.tsx` | `/signals` | Signal marketplace | Medium |
| `src/app/(dashboard)/graph/page.tsx` | `/graph` | Knowledge graph visualization | Medium |
| `src/app/(dashboard)/meetings/page.tsx` | `/meetings` | Meeting intelligence | Medium |
| `src/app/(dashboard)/automation/page.tsx` | `/automation` | Workflow automation | Medium |
| `src/app/(dashboard)/rules/page.tsx` | `/rules` | Business rules engine | High |
| `src/app/(dashboard)/rag/page.tsx` | `/rag` | RAG query interface | Medium |
| `src/app/(dashboard)/monitoring/page.tsx` | `/monitoring` | System monitoring | High |
| `src/app/(dashboard)/settings/page.tsx` | `/settings` | User/tenant settings | High |
| `src/app/(dashboard)/employees/page.tsx` | `/employees` | Employee 360 | High |
| `src/app/(dashboard)/customer-success/page.tsx` | `/customer-success` | Customer success hub | Medium |

---

## 9. Frontend Components

| File | Purpose | Importance |
|---|---|---|
| `src/components/executive-dashboard.tsx` | Executive dashboard view | High |
| `src/components/company-workspace.tsx` | Company workspace (tabs: overview, signals, etc.) | Critical |
| `src/components/employee-360-view.tsx` | Employee 360 view | High |
| `src/components/pipeline-kanban.tsx` | Pipeline kanban board | High |
| `src/components/search-panel.tsx` | Search panel | Critical |
| `src/components/timeline-widget.tsx` | Timeline widget | High |
| `src/components/copilot-panel.tsx` | AI copilot chat panel | Medium |
| `src/components/error-boundary.tsx` | React error boundary | Critical |
| `src/components/skeleton.tsx` | Loading skeleton component | Medium |
| `src/components/command-bar.tsx` | Command palette (⌘K) | Medium |
| `src/components/foundation/` | Foundation UI components | High |
| `src/components/layout/` | Layout components (headers, sidebars) | High |
| `src/components/guidance/` | Guidance/onboarding components | Low |

---

## 10. Frontend Features

| Directory | Purpose | Importance |
|---|---|---|
| `features/search/` | Search UI (SearchSection, SearchPill, SearchLoading) | Critical |
| `features/dashboard/` | Dashboard widgets, telemetry | Critical |
| `features/revenue-execution/` | Revenue execution UI (tasks, opportunities, NBA) | Critical |
| `features/company-intelligence/` | Company intelligence feature | High |
| `features/analytics/` | Analytics dashboards | High |
| `features/automation/` | Automation/workflow UI | Medium |
| `features/admin/` | Admin panel UI | High |
| `features/rag/` | RAG query UI | Medium |
| `features/demo/` | Demo mode UI | Low |
| `features/customer-success/` | Customer success UI | Medium |
| `features/employee-intelligence/` | Employee intelligence UI | High |
| `features/monitoring/` | System monitoring UI | High |
| `features/rules/` | Business rules UI | Medium |

---

## 11. Internal Packages

| Package | Purpose | Importance |
|---|---|---|
| `frontend/packages/ui/` | UI component library (Button, Card, Table, Modal, Sidebar, etc.) | Critical |
| `frontend/packages/workspace/` | Workspace SDK (Widget, Grid, Activity Feed, etc.) | Critical |
| `frontend/packages/design-language/` | Design tokens, theme, colors, typography | Critical |
| `frontend/packages/charts/` | Chart components (recharts wrapper) | High |
| `frontend/packages/forms/` | Form components & validation | High |
| `frontend/packages/search/` | Search provider & UI | High |
| `frontend/packages/hooks/` | Shared React hooks | High |
| `frontend/packages/icons/` | SVG icon library | Medium |
| `frontend/packages/config/` | Shared configuration | Medium |
| `frontend/packages/renderer/` | Dynamic component renderer | Medium |
| `frontend/packages/runtime/` | Frontend runtime utilities | Medium |
| `frontend/packages/platform/` | Platform integration utilities | Medium |
| `frontend/packages/workspace-generator/` | Workspace code generator | Low |
| `packages/platform/` | Shared platform package | Low |
| `packages/plugin-sdk/` | Plugin SDK (shared) | Low |

---

## 12. Hooks & Utilities

| File | Purpose | Importance |
|---|---|---|
| `frontend/src/lib/api.ts` | API client (fetch wrapper) | Critical |
| `frontend/src/lib/api/` | API query hooks (TanStack Query) | Critical |
| `frontend/src/lib/hooks/` | Shared React hooks | High |
| `frontend/src/lib/utils.ts` | Utility functions | High |
| `frontend/src/lib/commands.ts` | Command palette commands | Medium |
| `frontend/src/lib/queryKeys.ts` | TanStack Query key definitions | High |
| `frontend/src/lib/decisionQueries.ts` | Decision engine query hooks | High |
| `frontend/src/lib/ragQueries.ts` | RAG query hooks | Medium |
| `frontend/src/lib/workflowQueries.ts` | Workflow query hooks | Medium |
| `frontend/src/lib/telemetryQueries.ts` | Telemetry query hooks | Medium |
| `frontend/src/lib/analytics.ts` | Analytics utility | Medium |
| `frontend/src/lib/monitoring.ts` | Monitoring client utility | High |
| `frontend/src/lib/monitoring-init.ts` | Monitoring initialization | High |
| `frontend/src/lib/dynamic-imports.tsx` | Dynamic import utilities | Medium |
| `frontend/src/lib/i18n/` | Internationalization (Arabic + English) | High |
| `frontend/src/application/api/` | API application hooks (TanStack Query mutations) | Critical |
| `frontend/src/application/dashboard/` | Dashboard state & mappers | Critical |
| `frontend/src/application/search/` | Search state & keys | High |
| `frontend/src/application/company-intelligence/` | Company intelligence state | High |
| `frontend/src/application/revenue-execution/` | Revenue execution state (tasks, opportunities, NBA) | Critical |

---

## 13. Database Migrations

| File | Purpose | Importance |
|---|---|---|
| `backend/migrations/001_initial.sql` | Initial schema (users, tenants, companies, contacts) | Critical |
| `backend/migrations/003_revenue_analytics.sql` | Revenue analytics tables | High |
| `backend/migrations/004_workflow.sql` | Workflow engine tables | High |
| `backend/migrations/005_notifications.sql` | Notifications schema | High |
| `backend/migrations/006_database_indexes.sql` | Performance indexes (trigram, GIN, GiST) | Critical |
| `backend/migrations/versions/002_create_opportunities_tasks.sql` | Opportunities & tasks schema | High |

### Alembic Auto-Generated Migrations

| File | Purpose | Importance |
|---|---|---|
| `backend/app/alembic/` | Alembic environment + auto-migrations | High |
| `backend/app/alembic/versions/` | Individual migration versions (28+ versions) | High |

---

## 14. Test Files

### Unit Tests (backend/tests/unit/)

| File | What It Tests | Importance |
|---|---|---|
| `tests/unit/test_authorization.py` | RBAC permission enforcement | Critical |
| `tests/unit/test_ai_reasoner.py` | NBA AI reasoner | High |
| `tests/unit/test_search_runtime.py` | Search runtime | Critical |
| `tests/unit/test_hybrid_search.py` (domains/search/tests/) | Hybrid search engine | Critical |
| `tests/unit/test_arabic_normalizer.py` | Arabic text normalization | High |
| `tests/unit/test_scoring.py` | Scoring engine | High |
| `tests/unit/test_workflow_engine.py` | Workflow execution | Critical |
| `tests/unit/test_rules_engine.py` | Business rules engine | High |
| `tests/unit/test_rag_pipeline.py` | RAG pipeline | High |
| `tests/unit/test_entity_resolution_confidence.py` | Entity resolution confidence scoring | High |
| `tests/unit/test_revenue_service.py` | Revenue services | High |
| `tests/unit/test_revenue_dashboard.py` | Revenue dashboard | High |
| `tests/unit/test_forecast.py` | Revenue forecasting | High |
| `tests/unit/test_feature_store.py` | Feature store | High |
| `tests/unit/test_feature_store_cache.py` | Feature store caching | Medium |
| `tests/unit/test_meeting_intelligence.py` | Meeting intelligence | Medium |
| `tests/unit/test_email_intelligence.py` | Email intelligence | Medium |
| `tests/unit/test_contact_service.py` | Contact service | High |
| `tests/unit/test_company_matcher.py` | Company name matching | High |
| `tests/unit/test_employee_360_service.py` | Employee 360 service | High |
| `tests/unit/test_executive_service.py` | Executive dashboard service | High |
| `tests/unit/test_playbook.py` | Playbook execution | Medium |
| `tests/unit/test_deal_health.py` | Deal health scoring | High |
| `tests/unit/test_nba_pipeline.py` | NBA pipeline | High |
| `tests/unit/test_notifications.py` | Notifications (WebSocket) | High |
| `tests/unit/test_middleware.py` | HTTP middleware stack | Critical |
| `tests/unit/test_rate_limiter.py` | Rate limiter | High |
| `tests/unit/test_metrics.py` | Prometheus metrics | High |
| `tests/unit/test_audit.py` | Audit logging | High |
| `tests/unit/test_api_keys.py` | API key authentication | High |
| `tests/unit/test_sso.py` | SSO integration | High |
| `tests/unit/test_webhooks.py` | Webhook delivery | High |
| `tests/unit/test_kafka_bus.py` | Kafka event bus | Medium |
| `tests/unit/test_kafka_producer.py` | Kafka producer | Medium |
| `tests/unit/test_kafka_consumer.py` | Kafka consumer | Medium |
| `tests/unit/test_graphql.py` | GraphQL endpoint | Medium |
| `tests/unit/test_pagination.py` | Keyset pagination | High |
| `tests/unit/test_telemetry.py` | Customer telemetry | High |
| `tests/unit/test_analytics.py` | Analytics engine | High |
| `tests/unit/test_topic_mapping.py` | Topic mapping | Low |
| `tests/unit/test_schema_registry.py` | Schema registry | Medium |
| `tests/unit/test_signal_marketplace.py` | Signal marketplace | Medium |
| `tests/unit/test_outbox.py` | Transactional outbox | Medium |
| `tests/unit/test_dlq.py` | Dead letter queue | Medium |
| `tests/unit/test_work_intelligence.py` | Work intelligence | Medium |
| `tests/unit/test_pipeline_analytics.py` | Pipeline analytics | High |
| `tests/unit/test_normalizers.py` | Data normalizers | Medium |
| `tests/unit/test_benchmarks.py` | Benchmark runner | Low |
| `tests/unit/test_dashboard_mappers.py` | Dashboard DTO mappers | High |
| `tests/unit/test_demo.py` | Demo mode | Low |
| `tests/unit/test_redis_cache.py` | Redis cache service | High |
| `tests/unit/test_mcp_server.py` | MCP server | High |
| `tests/unit/test_meeting_email_repos.py` | Meeting/email repos | Medium |

### Integration Tests (backend/tests/integration/)

| File | What It Tests | Importance |
|---|---|---|
| `tests/integration/test_trigram_search.py` | Trigram search with PostgreSQL | High |
| `tests/integration/test_arabic_search.py` | Arabic full-text search | High |
| `tests/integration/test_keyset_pagination.py` | Keyset pagination with real DB | High |
| `tests/integration/test_migration_0029.py` | Migration 0029 verification | High |
| `tests/integration/test_migration_0030.py` | Migration 0030 verification | High |
| `tests/integration/test_migrations_applied.py` | All migrations applied check | Critical |
| `tests/integration/test_kafka_live.py` | Live Kafka integration | Medium |
| `tests/integration/test_post_middleware.py` | Post-middleware integration | High |

### E2E Tests (backend/tests/e2e/)

| File | What It Tests | Importance |
|---|---|---|
| `tests/e2e/test_critical_paths.py` | All critical user journeys | Critical |
| `tests/e2e/test_executive_dashboard.py` | Executive dashboard flow | High |
| `tests/e2e/test_decision_center.py` | Decision center flow | High |
| `tests/e2e/test_employee_360.py` | Employee 360 flow | High |
| `tests/e2e/test_meeting_intelligence.py` | Meeting intelligence flow | High |
| `tests/e2e/test_knowledge_graph.py` | Knowledge graph flow | High |
| `tests/e2e/test_feature_store.py` | Feature store flow | High |
| `tests/e2e/test_revenue_intelligence.py` | Revenue intelligence flow | High |
| `tests/e2e/test_forecast.py` | Forecasting flow | High |
| `tests/e2e/test_pipeline_analytics.py` | Pipeline analytics flow | High |
| `tests/e2e/test_contacts.py` | Contact management flow | High |
| `tests/e2e/test_analytics.py` | Analytics flow | High |
| `tests/e2e/test_workflows.py` | Workflow execution flow | High |
| `tests/e2e/test_rate_limit.py` | Rate limiting end-to-end | High |

### Evaluation Tests (backend/tests/evaluation/)

| File | What It Tests | Importance |
|---|---|---|
| `tests/evaluation/test_rag_faithfulness.py` | RAG output faithfulness | High |
| `tests/evaluation/test_agent_grounding.py` | Agent grounding accuracy | High |
| `tests/evaluation/evaluation_config.py` | Eval configuration | High |

### Domain-Specific Tests

| File | What It Tests | Importance |
|---|---|---|
| `domains/ai/tests/test_evaluator.py` | AI evaluator | High |
| `domains/ai/tests/test_ai_extended.py` | Extended AI tests | High |
| `domains/search/tests/test_hybrid_search.py` | Hybrid search engine | High |
| `domains/search/tests/test_arabic_normalizer.py` | Arabic normalizer | High |
| `domains/search/tests/test_ranking.py` | Search ranking | High |
| `domains/search/tests/test_planner.py` | Query planner | High |
| `domains/search/tests/test_parser.py` | Query parser | High |
| `domains/search/tests/test_models.py` | Search models | Medium |
| `domains/scoring/tests/test_engine.py` | Scoring engine | High |
| `domains/decision/recommendation/tests/` | Recommendation engine | High |
| `domains/decision/context/tests/` | Decision context | High |
| `domains/timeline/tests/test_timeline.py` | Timeline service | High |
| `domains/workflow/tests/test_service.py` | Workflow service | High |
| `domains/workflow/tests/test_workflow_extended.py` | Extended workflow tests | High |
| `domains/revenue/forecast/tests/test_forecast.py` | Forecast engine | High |
| `domains/revenue/analytics/tests/test_analytics.py` | Analytics engine | High |
| `domains/feature_store/tests/test_feature_store.py` | Feature store | High |
| `tests/unit/test_search_postgres_repo.py` (domains/search/tests/) | PostgreSQL search repo | High |

### Architecture & Health Tests

| File | Purpose | Importance |
|---|---|---|
| `tests/test_architecture.py` | Architecture compliance (cross-domain imports) | Critical |
| `tests/test_health.py` | Health endpoint tests | High |
| `tests/test_integration.py` | General integration tests | High |
| `tests/fakes.py` | Fake repositories for testing | High |

---

## 15. Documentation

| File | Purpose | Importance |
|---|---|---|
| `README.md` | Project overview & quick start | Critical |
| `CHANGELOG.md` | Release changelog | High |
| `docs/admin_guide.md` | Administrator guide | High |
| `docs/user_guide.md` | End-user guide | High |
| `docs/deployment_guide.md` | Deployment instructions | High |
| `docs/production_runbook.md` | Production runbook / SRE | High |
| `docs/troubleshooting.md` | Troubleshooting guide | Medium |
| `docs/sla.md` | SLA definitions | High |
| `docs/quick_start.md` | Quick start guide | Medium |
| `docs/ARCHITECTURE_BOOK.md` | Architecture documentation | High |
| `docs/ARCHITECTURE_COMPLIANCE.md` | Architecture compliance report | High |
| `docs/DECISION_ENGINE_GUIDE.md` | Decision engine guide | High |
| `docs/RULE_ENGINE_GUIDE.md` | Rules engine guide | High |
| `docs/DECISION_PLATFORM_BLUEPRINT.md` | Decision platform architecture | High |
| `docs/DECISION_PLATFORM_ARCHITECTURE.md` | Decision platform architecture detail | High |
| `docs/DECISION_PLATFORM_API_MAPPING.md` | API mapping for decision platform | High |
| `docs/DECISION_PLATFORM_COMPONENT_CATALOG.md` | Component catalog | High |
| `docs/DECISION_PLATFORM_IMPLEMENTATION_PLAN.md` | Implementation plan | Medium |
| `docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md` | Domain-driven design docs | High |
| `docs/GA_DASHBOARD.md` | GA launch dashboard | Medium |
| `docs/GA_LAUNCH_PLAN.md` | GA launch plan | High |
| `docs/DOCKER_VALIDATION_REPORT.md` | Docker validation | Medium |
| `docs/PRODUCTION_AUDIT_REPORT.md` | Production audit report | High |
| `docs/FINAL_SECURITY_REPORT.md` | Final security sweep report | High |
| `docs/FINAL_PERFORMANCE_REPORT.md` | Final performance report | High |
| `docs/SECURITY_SWEEP_REPORT.md` | Security sweep report | High |
| `docs/PILOT_LAUNCH_REPORT.md` | Pilot launch report | High |
| `docs/RELEASE_READINESS_REPORT.md` | Release readiness | High |
| `docs/DEPLOYMENT_REPORT_v0.7.md` | Deployment report v0.7 | Medium |
| `docs/DEPLOYMENT_REPORT_v0.8.md` | Deployment report v0.8 | Medium |
| `docs/PERFORMANCE_OPTIMIZATION_REPORT.md` | Performance optimization | Medium |
| `docs/COMPLIANCE_AUDIT_REPORT.md` | Compliance audit | High |
| `docs/INCIDENT_RESPONSE_PLAN.md` | Incident response plan | High |
| `docs/ONCALL_RUNBOOK.md` | On-call runbook | High |
| `docs/WIDGET_MIGRATION_GUIDE.md` | Widget migration guide | Medium |
| `docs/hiring/` | Hiring documentation | Low |
| `docs/pentest/` | Penetration test reports | High |
| `docs/portal/` | API portal documentation | High |
| `docs/releases/` | Release-specific docs | Medium |
| `docs/wave-2/` | Wave 2 feature docs | Medium |
| `docs/wave-3/` | Wave 3 feature docs | Medium |
| `REVENUE_EXECUTION_BIBLE.md` | Revenue execution reference | High |
| `PERFORMANCE_BASELINE.md` | Performance baseline metrics | High |
| `RELEASE_GATES.md` | Release gate definitions | High |
| `infra/k8s/DEPLOYMENT_RUNBOOK.md` | K8s deployment runbook | High |
| `infra/k8s/README.md` | K8s infrastructure overview | Medium |
| `backend/mcp_server/README.md` | MCP server documentation | Medium |
| `backend/README.md` | Backend-specific documentation | Medium |
| `frontend/README.md` | Frontend-specific documentation | Medium |

---

## 16. Infrastructure

### Docker

| File | Purpose | Importance |
|---|---|---|
| `backend/Dockerfile` | Backend Docker image | Critical |
| `backend/Dockerfile.backend` | Backend Docker build | Critical |
| `backend/Dockerfile.test` | Test Docker image | High |
| `backend/docker-entrypoint.sh` | Backend Docker entrypoint | Critical |
| `frontend/Dockerfile` | Frontend Docker image | Critical |
| `frontend/Dockerfile.frontend` | Frontend Docker build | Critical |
| `frontend/nginx.conf` | Nginx reverse proxy config | High |
| `infra/docker/monitoring/` | Docker monitoring (Prometheus, Grafana) | High |
| `infra/docker/postgres/` | PostgreSQL Docker config | High |

### Kubernetes

| File | Purpose | Importance |
|---|---|---|
| `infra/k8s/namespace.yaml` | K8s namespace definition | Critical |
| `infra/k8s/configmap.yaml` | ConfigMap for env vars | Critical |
| `infra/k8s/secrets.yaml` | Secret definitions (encrypted) | Critical |
| `infra/k8s/backend/` | Backend K8s deployment, service, HPA | Critical |
| `infra/k8s/frontend/` | Frontend K8s deployment, service, HPA | Critical |
| `infra/k8s/postgres/` | PostgreSQL K8s statefulset | Critical |
| `infra/k8s/neo4j/` | Neo4j K8s statefulset | Critical |
| `infra/k8s/redis/` | Redis K8s deployment | High |
| `infra/k8s/kafka/` | Kafka K8s deployment (Strimzi) | Medium |
| `infra/k8s/prometheus/` | Prometheus K8s config | High |
| `infra/k8s/grafana/` | Grafana K8s config | High |
| `infra/k8s/alertmanager/` | Alertmanager config | High |
| `infra/k8s/monitoring-ingress.yaml` | Monitoring ingress | Medium |
| `infra/k8s/network-policy.yaml` | Network policies | High |
| `infra/k8s/pdb.yaml` | Pod disruption budgets | High |
| `infra/k8s/resource-quota.yaml` | Resource quotas | Medium |
| `infra/k8s/limit-range.yaml` | Limit ranges | Medium |
| `infra/k8s/backup-cronjob.yaml` | Backup cronjob | High |
| `infra/k8s/restore-test-cronjob.yaml` | Restore test cronjob | Medium |

### CI/CD (GitHub Actions)

| File | Purpose | Importance |
|---|---|---|
| `.github/workflows/ci.yml` | CI pipeline (lint, test, build) | Critical |
| `.github/workflows/deploy.yml` | General deployment workflow | Critical |
| `.github/workflows/deploy-production.yml` | Production deployment | Critical |
| `.github/workflows/deploy-staging.yml` | Staging deployment | High |
| `.github/workflows/docker-smoke.yml` | Docker smoke tests | High |
| `.github/workflows/security-scan.yml` | Security scanning (Trivy, Bandit, Semgrep) | Critical |

### Terraform

| File | Purpose | Importance |
|---|---|---|
| `infra/terraform/` | Terraform infrastructure-as-code | High |

### Staging

| File | Purpose | Importance |
|---|---|---|
| `infra/staging/` | Staging environment config | High |

### Caddy

| File | Purpose | Importance |
|---|---|---|
| `infra/caddy/` | Caddy reverse proxy config | Medium |

### Monitoring

| File | Purpose | Importance |
|---|---|---|
| `infra/monitoring/` | Monitoring stack config (Prometheus, Grafana, Alertmanager) | High |

---

## 17. Scripts & Tools

| File | Purpose | Importance |
|---|---|---|
| `scripts/security-audit.ps1` | Automated security audit | Critical |
| `scripts/arch-compliance.ps1` | Architecture compliance checker | Critical |
| `scripts/check-coverage.ps1` | Test coverage reporter | High |
| `scripts/audit-migrations.ps1` | Migration audit script | High |
| `scripts/smoke-test.ps1` | Smoke test runner | High |
| `scripts/docker-smoke.ps1` | Docker smoke test runner | High |
| `scripts/load-test.py` | Load test (locust-style) | High |
| `scripts/load-test-comprehensive.py` | Comprehensive load test | High |
| `scripts/stress-test.py` | Stress test | High |
| `scripts/soak-test.py` | Soak/longevity test | Medium |
| `scripts/backup.ps1` | Database backup | Critical |
| `scripts/neo4j-backup.ps1` | Neo4j backup | High |
| `scripts/neo4j-recover.ps1` | Neo4j recovery | High |
| `scripts/verify-backup.ps1` | Backup verification | High |
| `scripts/restore-test.ps1` | Restore test | Medium |
| `scripts/restore-test.sh` | Restore test (Unix) | Medium |
| `scripts/check-performance.ps1` | Performance baseline check | High |
| `scripts/sbom.ps1` | SBOM generation | High |
| `scripts/scan-deps.ps1` | Dependency vulnerability scan | High |
| `scripts/update-deps.sh` | Dependency update (Unix) | Medium |
| `scripts/pilot-onboard.ps1` | Pilot tenant onboarding | High |
| `scripts/pilot-verify.ps1` | Pilot verification | High |
| `scripts/pilot-metrics.ps1` | Pilot metrics collection | Medium |
| `scripts/provision-pilot-tenants.ps1` | Provision pilot tenants | High |
| `scripts/seed-pilot-data.ps1` | Seed pilot data | High |
| `scripts/verify-pilot-deployment.ps1` | Verify pilot deployment | High |
| `backend/benchmark/run.py` | Performance benchmark runner | High |
| `backend/benchmark/data_generator.py` | Benchmark data generator | High |
| `backend/benchmark/runner.py` | Benchmark execution runner | High |
| `backend/benchmark/queries.py` | Benchmark query definitions | High |
| `backend/benchmark/reporter.py` | Benchmark report generator | Medium |
| `backend/benchmark/reports/` | Benchmark output reports | Medium |

---

## 18. SDK Submodules Detail

### Widget SDK (sdk/widget_sdk/)

| File | Purpose | Importance |
|---|---|---|
| `frontend/packages/workspace/src/create-widget.tsx` | `createWidget()` — primary Widget creation function | Critical |
| `frontend/packages/workspace/src/create-workspace-widget.tsx` | `createDashboardWidget()` — dashboard widget factory | Critical |
| `frontend/packages/workspace/src/types.ts` | Widget type definitions (WidgetConfig, WidgetStatus) | Critical |
| `frontend/packages/workspace/src/widget-lifecycle.ts` | Widget lifecycle hooks (mount, unmount, refresh) | Critical |
| `frontend/packages/workspace/src/widget-telemetry.ts` | Widget telemetry (render time, errors) | High |
| `frontend/packages/workspace/src/widget-permissions.ts` | Widget permission checks | High |
| `frontend/packages/workspace/src/widget-feature-flags.ts` | Widget feature flag evaluation | High |
| `frontend/packages/workspace/src/derive-status.ts` | Widget status derivation | Medium |
| `frontend/packages/workspace/src/presets.ts` | Widget layout presets | Medium |
| `frontend/packages/workspace/src/generator.ts` | Widget code generator | Medium |
| `frontend/packages/workspace/src/workspace-registry.ts` | Widget registry | High |
| `frontend/packages/workspace/src/workspace-provider.tsx` | Workspace context provider | Critical |
| `frontend/packages/workspace/src/workspace-grid.tsx` | Responsive widget grid | Critical |
| `frontend/packages/workspace/src/workspace-loading.tsx` | Workspace loading state | Medium |
| `frontend/packages/workspace/src/workspace-error-boundary.tsx` | Workspace error boundary | High |
| `frontend/packages/workspace/src/renderer.tsx` | Widget renderer | High |
| `frontend/packages/workspace/src/universal-inbox.tsx` | Universal inbox widget | Medium |
| `frontend/packages/workspace/src/global-activity-feed.tsx` | Global activity feed widget | Medium |
| `frontend/packages/workspace/src/ai-operating-assistant.tsx` | AI operating assistant widget | Medium |
| `frontend/packages/workspace/src/revenue-command-center.tsx` | Revenue command center widget | High |
| `frontend/packages/workspace/src/testing/renderWidget.tsx` | Test utility: render widget in isolation | High |
| `frontend/packages/workspace/src/testing/WidgetContract.tsx` | `describeWidgetContract()` — contract test suite | Critical |

### Design Language (frontend/packages/design-language/)

| File | Purpose | Importance |
|---|---|---|
| `design-language/src/` | Design tokens (colors, spacing, typography, shadows) | Critical |

### UI Package (frontend/packages/ui/src/)

| File | Purpose | Importance |
|---|---|---|
| `ui/src/button.tsx` | Button component | Critical |
| `ui/src/card.tsx` | Card component | Critical |
| `ui/src/table.tsx` | Table component | Critical |
| `ui/src/modal.tsx` | Modal component | High |
| `ui/src/sidebar.tsx` | Sidebar component | Critical |
| `ui/src/input.tsx` | Input component | High |
| `ui/src/select.tsx` | Select component | High |
| `ui/src/tabs.tsx` | Tabs component | High |
| `ui/src/toast.tsx` | Toast notification | High |
| `ui/src/tooltip.tsx` | Tooltip component | Medium |
| `ui/src/badge.tsx` | Badge component | Medium |
| `ui/src/spinner.tsx` | Spinner/loader component | Medium |
| `ui/src/avatar.tsx` | Avatar component | Medium |
| `ui/src/dropdown.tsx` | Dropdown component | Medium |
| `ui/src/kbd.tsx` | Keyboard shortcut indicator | Low |
| `ui/src/layout.tsx` | Layout component | High |

### Application Layer (frontend/src/application/)

| File | Purpose | Importance |
|---|---|---|
| `application/dashboard/` | Dashboard state, mappers, widget store | Critical |
| `application/search/` | Search state, API hooks | Critical |
| `application/company-intelligence/` | Company intelligence state | High |
| `application/revenue-execution/` | Revenue execution state (tasks, opportunities, NBA) | Critical |
| `application/api/` | API mutation hooks | Critical |

### Application Dashboard (salesos/application/dashboard/)

| File | Purpose | Importance |
|---|---|---|
| `application/dashboard/` | Application-level dashboard implementation | High |

---

## File Count Summary

| Category | Count |
|---|---|
| Configuration files | ~25 |
| Backend entry points | ~8 |
| API Routers (app module + runtime + domain) | ~55+ |
| Domain models & services | ~60+ |
| Runtime engines | ~28 |
| SDK modules | ~30 |
| AI & Intelligence components | ~35+ |
| Frontend pages | ~30 |
| Frontend components (key) | ~15 |
| Frontend features | ~13 |
| Internal packages | ~15 |
| Hooks & utilities | ~20+ |
| Database migrations | ~34+ |
| Test files (key) | ~70+ |
| Documentation (key) | ~50+ |
| Infrastructure (Docker, K8s, CI/CD) | ~40+ |
| Scripts & tools | ~30+ |
| **Total Indexed** | **~280+** |
