# SalesOS vNext — Target Architecture

> **Author**: Chief Software Architect
> **Status**: Draft
> **Last Updated**: 2026-07-16
> **Supersedes**: v1.0 architecture (pre-vNext)

---

## Table of Contents

1. [Target Architecture Overview](#1-target-architecture-overview)
2. [Frontend Architecture](#2-frontend-architecture)
3. [Backend Architecture](#3-backend-architecture)
4. [AI Architecture](#4-ai-architecture)
5. [Runtime Architecture](#5-runtime-architecture)
6. [Module Boundaries](#6-module-boundaries)
7. [Folder Structure](#7-folder-structure)
8. [Dependency Rules](#8-dependency-rules)
9. [Shared Packages](#9-shared-packages)
10. [Data Flow](#10-data-flow)
11. [API Contracts](#11-api-contracts)
12. [Event Flow](#12-event-flow)
13. [Extension Strategy](#13-extension-strategy)
14. [Plugin Strategy](#14-plugin-strategy)

---

## 1. Target Architecture Overview

### 1.1 Big Picture Vision

SalesOS vNext transforms the current monolithic-adjacent system into a **modular monolith with eventual microservice extraction paths**. Every module is a bounded context with explicit public contracts, private internals, and CI-enforced boundaries.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SALESOS VNEXT PLATFORM                        │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  GATEWAY      │  │  AUTH         │  │  RATE LIMIT  │              │
│  │  (Edge Proxy) │  │  (Middleware)  │  │  (Middleware) │              │
│  └──────┬───────┘  └──────────────┘  └──────────────┘              │
│         │                                                          │
│  ┌──────▼────────────────────────────────────────────────────┐     │
│  │                    DOMAIN LAYER (14 Domains)                │     │
│  │                                                             │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │     │
│  │  │ Identity  │ │ Company  │ │ Search   │ │ CRM      │      │     │
│  │  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤      │     │
│  │  │ Timeline  │ │ Scoring  │ │ AI       │ │ Workflow │      │     │
│  │  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤      │     │
│  │  │ Employee  │ │Customer  │ │Enrichment│ │Pipeline  │      │     │
│  │  │           │ │Success   │ │          │ │          │      │     │
│  │  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────┤      │     │
│  │  │ Data     │ │Decision  │ │ (New)    │ │ (New)    │      │     │
│  │  │ Fabric   │ │Platform  │ │ Billing  │ │ Tenant   │      │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │     │
│  └──────────────────────────┬────────────────────────────────┘     │
│                             │                                      │
│  ┌──────────────────────────▼────────────────────────────────┐     │
│  │                    INFRASTRUCTURE LAYER                    │     │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │     │
│  │  │PG Repos│ │Neo4j   │ │Redis   │ │Kafka   │ │S3/Blob │  │     │
│  │  │        │ │Client  │ │Cache   │ │Client  │ │Storage │  │     │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    API SURFACE                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │   │
│  │  │  REST API    │  │  GraphQL    │  │  MCP Resources   │    │   │
│  │  │  /api/v2/*   │  │  /graphql   │  │  /mcp/*          │    │   │
│  │  └─────────────┘  └─────────────┘  └──────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    EVENT BUS                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │
│  │  │  In-Memory    │  │  Kafka       │  │  Dead Letter     │   │   |
│  │  │  (sync)       │  │  (async)     │  │  Queue           │   │   |
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │   |
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Description |
|-----------|-------------|
| **Strict Bounded Contexts** | Every domain is a folder with zero cross-domain imports at runtime. Communication only via events or SDK. |
| **Modular Monolith First** | Ship as one deployable unit; extraction paths defined for each domain. |
| **API-First Contracts** | Every boundary has a contract (OpenAPI, GraphQL schema, or typed interface). |
| **Configuration Centralized** | One configuration system, environment-specific overlays, no scattered `.env` files. |
| **Evolutionary Architecture** | Fitness functions in CI prevent architectural drift. |
| **Sensible Defaults, Explicit Overrides** | Convention over configuration, but every override is visible. |

---

## 2. Frontend Architecture

### 2.1 Current State

| Issue | Detail |
|-------|--------|
| **Monolithic API client** | `api.ts` at 1,240 lines — all domains, all endpoints, one file |
| **No import boundaries** | 13 packages with no enforcement of package-level dependencies |
| **Widget SDK v1.0 frozen** | Container/View pattern works, but SDK has no versioning strategy for consumers |

### 2.2 Problems

1. **api.ts** is a single point of failure — any change risks breaking unrelated domains
2. Without import boundaries, any package can import any other package, creating hidden circular deps and tight coupling
3. The frontend has no domain isolation — Company widgets can import Timeline internals

### 2.3 Target Design

#### Domain-Split API Client

```
src/
  api/
    client.ts                  # Base HTTP client (auth, retry, base URL)
    identity/
      identity.api.ts          # Login, logout, token refresh
      identity.types.ts        # Request/response types
    company/
      company.api.ts
      company.types.ts
    search/
      search.api.ts
      search.types.ts
    timeline/
      timeline.api.ts
      timeline.types.ts
    workflow/
      workflow.api.ts
      workflow.types.ts
    scoring/
      scoring.api.ts
      scoring.types.ts
    crm/
      crm.api.ts
      crm.types.ts
    ai/
      ai.api.ts
      ai.types.ts
    enrichment/
      enrichment.api.ts
      enrichment.types.ts
    pipeline/
      pipeline.api.ts
      pipeline.types.ts
    employee/
      employee.api.ts
      employee.types.ts
    customer-success/
      customer-success.api.ts
      customer-success.types.ts
    decision/
      decision.api.ts
      decision.types.ts
```

Each `*.api.ts` has:
- All endpoints for that domain
- Typed request/response types
- No cross-domain imports — if you need Company data in a Timeline widget, use the Timeline API client, not the Company one

#### Package Import Boundaries

| Package | Can Import | Cannot Import |
|---------|-----------|---------------|
| `@salesos/ui` | `@salesos/design-language` | Any domain package |
| `@salesos/widget-sdk` | `@salesos/design-language`, `@salesos/ui` | Any domain package |
| `@salesos/identity` | `@salesos/api-client` | `@salesos/workflow`, `@salesos/company` |
| `@salesos/company` | `@salesos/api-client`, `@salesos/widget-sdk` | `@salesos/timeline`, `@salesos/workflow` |
| `@salesos/widget-*` | `@salesos/widget-sdk`, `@salesos/api-client` | Other `@salesos/widget-*` packages |

Enforced by `eslint-plugin-import` + custom rule in CI.

#### Widget SDK Evolution (v1.1)

| Change | Detail |
|--------|--------|
| **Versioned SDK** | `@salesos/widget-sdk` follows semver; consumers pin `^1.x` |
| **SDK Extensions** | Plugins can extend the SDK without modifying it (see §14) |
| **Lifecycle Hooks** | `onMount`, `onUpdate`, `onError`, `onUnmount` — standard lifecycle |
| **Testing Kit** | `describeWidgetContract` remains but versioned alongside SDK |
| **Deprecation Policy** | 2-major-version deprecation window with runtime warnings |

#### Monorepo Structure

```
packages/
  design-language/     # @salesos/design-language — tokens, icons, typography
  ui/                  # @salesos/ui — design system components
  widget-sdk/          # @salesos/widget-sdk — Widget SDK v1.1
  api-client/          # @salesos/api-client — base HTTP client
  api-identity/        # @salesos/api-identity
  api-company/         # @salesos/api-company
  api-search/          # @salesos/api-search
  api-timeline/        # @salesos/api-timeline
  api-workflow/        # @salesos/api-workflow
  api-scoring/         # @salesos/api-scoring
  api-crm/             # @salesos/api-crm
  api-ai/              # @salesos/api-ai
  api-enrichment/      # @salesos/api-enrichment
  api-pipeline/        # @salesos/api-pipeline
  api-employee/        # @salesos/api-employee
  api-customer-success/# @salesos/api-customer-success
  api-decision/        # @salesos/api-decision
  widgets/             # @salesos/widgets — all widgets in one package
    mission-center/
    company-profile/
    search/
    timeline/
    scoring/
    workflow/
    employee/
    crm/
    customer-success/
```

---

## 3. Backend Architecture

### 3.1 Current State

| Issue | Detail |
|-------|--------|
| **Monolithic bootstrap** | `main.py` at 773 lines — all routers, middleware, init in one file |
| **Middleware chain bug** | 10-layer middleware chain has POST body consumption issue |
| **3 Redis pools** | Separate pools for cache, session, and rate limiting |
| **Admin in-memory** | Admin router uses in-memory stores — data loss on restart |

### 3.2 Problems

1. **main.py** violates Single Responsibility — every new domain adds to this file
2. Middleware chain is fragile; body consumption bug makes POST endpoints unreliable
3. Redis pools should be unified into a single connection manager
4. Admin state should be persistent

### 3.3 Target Design

#### Modular Bootstrap

```
src/
  bootstrap/
    __init__.py              # create_app() — public entry point
    app.py                   # FastAPI app factory
    settings.py              # Centralized settings (pydantic-settings)
    database.py              # Database init (PG, Neo4j, Redis)
    event_bus.py             # Event bus init
    middleware.py             # Middleware pipeline
    routers.py               # Router registration (reads from registry)
    health.py                # Health check endpoints
    lifespan.py              # Lifespan events (startup/shutdown)
    metrics.py               # Prometheus metrics setup
    logging.py               # Logging config
    cors.py                  # CORS config
  middleware/
    auth.py                  # JWT validation
    rbac.py                  # Role-based access
    tenant.py                # Tenant isolation
    rate_limit.py            # Rate limiting (single Redis pool)
    request_id.py            # Request ID tracking
    audit_log.py             # Audit logging
    csrf.py                  # CSRF protection
    body_cache.py            # Request body caching (fixes POST bug)
    error_handler.py         # Global error handling
    timing.py                # Request timing
```

**Middleware ordering** (top → bottom):

```
Request → RequestID → CORS → Auth → Tenant → RBAC → BodyCache → RateLimit → AuditLog → Timing → Router
```

The `BodyCache` middleware reads and caches the request body **once**, then downstream middlewares and routers access the cached copy. This fixes the POST body consumption bug.

#### Router Registration

Routers are auto-discovered via a registry — no manual imports in `main.py`:

```python
# In bootstrap/app.py
for domain in settings.ENABLED_DOMAINS:
    app.include_router(
        registry.get(domain),
        prefix=f"/api/v2/{domain}",
    )
```

Each domain module exports a `router` in its `__init__.py`.

#### Configuration Centralization

Replace 6+ scattered `.env` files with:

```
config/
  defaults.yaml              # All settings with defaults
  production.yaml            # Production overrides
  staging.yaml               # Staging overrides
  development.yaml           # Development overrides
  secrets/                   # Not in version control
    production.yaml
    staging.yaml
```

Settings loaded via `pydantic-settings` with YAML file source:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(yaml_file="config/development.yaml")
    # ... all settings here
```

---

## 4. AI Architecture

### 4.1 Current State

The AI domain exists as one of 14 domains with a `PromptRegistry`, `AIService`, router, and 92% test coverage.

### 4.2 Problems

1. AI is tightly coupled to the monorepo — cannot scale independently
2. No prompt versioning strategy (PromptRegistry is flat)
3. No evaluation pipeline outside of tests

### 4.3 Target Design (Summary — see `AI_STRATEGY.md` for full detail)

| Concern | Target |
|---------|--------|
| **AI Service** | Extracted as a standalone service with gRPC + REST interfaces |
| **Prompt Registry** | Versioned, stored in DB, with A/B testing support |
| **Evaluation** | CI-gated evaluation pipeline with regression detection |
| **Agent Framework** | Pluggable agent runtimes (see §5) |
| **Model Gateway** | Unified gateway (OpenAI, Anthropic, local models) with failover |
| **Telemetry** | Every LLM call traced: latency, tokens, cost, quality score |

The AI domain remains in the monorepo for development but has a clear extraction path:

```
src/ai/
  __init__.py            # Router, public exports
  domain/                # Domain logic (extraction path: → shared lib)
    models.py
    prompts.py
    evaluation.py
  infrastructure/        # Infrastructure (extraction path: → AI service)
    llm_gateway.py
    prompt_repository.py
    telemetry.py
  interface/             # API surface (extraction path: → gRPC service)
    rest.py
    grpc.py
```

---

## 5. Runtime Architecture

### 5.1 Current State

| Runtime | Status | Notes |
|---------|--------|-------|
| API (main FastAPI) | Active | Monolithic, needs modularization |
| Agent | Planned stub | — |
| Celery Worker | Active | Background tasks |
| Execution | Planned stub | — |
| Health Check | Active | Integrated into main |
| Scheduler | Planned stub | — |
| Simulation | Planned stub | — |
| WebSocket | Active | Integrated into main |
| Workflow | Planned stub | — |

Plus 20 other active runtimes (migration, seed, benchmark, etc.) = 28 total.

### 5.2 Target Design: 9 Focused Runtimes

Merge, rename, and create to reach 9 production runtimes + 6 support runtimes:

```
Production Runtimes (9)
┌─────────────────────────────────────────────────────────────┐
│  1. API Server         │  FastAPI + Uvicorn (domain routers)  │
│  2. Celery Worker      │  Background task processing          │
│  3. WebSocket Server   │  Standalone WebSocket process         │
│  4. Scheduler          │  NEW — cron/schedule coordinator     │
│  5. Workflow Engine    │  NEW — workflow state machine        │
│  6. Agent Runtime      │  NEW — AI agent execution           │
│  7. Event Consumer     │  Kafka consumer group               │
│  8. Simulation Engine  │  NEW — data simulation & testing     │
│  9. Health + Metrics   │  Prometheus + health probes          │
└─────────────────────────────────────────────────────────────┘

Support Runtimes (6)
┌─────────────────────────────────────────────────────────────┐
│  10. Migration          │  Alembic migrations                │
│  11. Seed Data          │  Database seeding                  │
│  12. Benchmark          │  Performance benchmarking          │
│  13. Audit              │  Security & compliance scan         │
│  14. CLI                │  Admin CLI tool                    │
│  15. Eval               │  AI evaluation pipeline            │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Runtime Consolidation Map

| Current Runtime | vNext Target | Action |
|----------------|-------------|--------|
| API (main.py) | API Server | Modularize — split into domain-init registry |
| Agent (stub) | Agent Runtime | Implement |
| Celery Worker | Celery Worker | Keep |
| Execution (stub) | → merged into Workflow Engine | Merge |
| Health Check | → merged into Health + Metrics | Merge |
| Scheduler (stub) | Scheduler | Implement |
| Simulation (stub) | Simulation Engine | Implement |
| WebSocket | WebSocket Server | Extract from main |
| Workflow (stub) | Workflow Engine | Implement |
| Migration | Migration | Keep |
| Seed | Seed Data | Keep |
| Benchmark | Benchmark | Keep |
| Audit | Audit | Keep |
| CLI | CLI | Keep |
| (other 15 active) | → consolidated into shared lib | Merge |

---

## 6. Module Boundaries

### 6.1 Domain Dependency Rules

```
                    ┌──────────────────┐
                    │   Identity       │  (no domain dependencies)
                    └──────────────────┘
                            │
                    ┌───────▼────────┐
                    │   Company       │  → Identity
                    └───────┬────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼───────┐ ┌────▼────┐ ┌────────▼────────┐
    │   Search      │ │  CRM    │ │  Enrichment     │
    │ → Company     │ │→Company │ │→ Company        │
    └───────────────┘ └─────────┘ └─────────────────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
                    ┌───────▼────────┐
                    │   Entity      │
                    │   Resolution  │
                    │ → Company     │
                    └───────┬────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼───────┐ ┌────▼────┐ ┌────────▼────────┐
    │   Scoring     │ │Pipeline │ │  Employee       │
    │ → Entity Res  │ │→Company │ │ → Company       │
    └───────┬───────┘ └─────────┘ └─────────────────┘
            │
    ┌───────▼──────────────────┐
    │   Decision Platform      │
    │ → Scoring, Pipeline,     │
    │   Employee, Entity Res   │
    └───────┬──────────────────┘
            │
    ┌───────▼────────┐ ┌───────────┐ ┌──────────────┐
    │   Workflow     │ │ Timeline  │ │ AI           │
    │ → Decision     │ │→ Decision │ │ → All domains│
    └────────────────┘ └───────────┘ └──────────────┘

    ┌──────────────────┐ ┌──────────────────┐
    │ Data Fabric       │ │ Feature Store    │
    │ → No domain deps  │ │ → Data Fabric    │
    └──────────────────┘ └──────────────────┘

    ┌──────────────────┐ ┌──────────────────┐
    │ Customer Success  │ │ Billing (NEW)    │
    │ → Company, CRM    │ │ → Company        │
    └──────────────────┘ └──────────────────┘

    ┌──────────────────────┐
    │   Tenant (NEW)       │
    │ → Identity           │
    └──────────────────────┘
```

### 6.2 Layer Rules

```
┌──────────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                                  │
│  Contains: domain models, service interfaces, repository ifaces  │
│  Imports: nothing from infrastructure                            │
│  Exports: service interfaces, domain events, domain models       │
├──────────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                               │
│  Contains: use cases, DTOs, orchestrators                         │
│  Imports: domain layer                                            │
│  Exports: use case interfaces                                     │
├──────────────────────────────────────────────────────────────────┤
│                   INFRASTRUCTURE LAYER                             │
│  Contains: repository impls, external clients, DB models          │
│  Imports: domain + application layer                              │
│  Exports: concrete implementations                                │
├──────────────────────────────────────────────────────────────────┤
│                   INTERFACE LAYER                                  │
│  Contains: REST, GraphQL, CLI, MCP resources                      │
│  Imports: application layer                                       │
│  Exports: HTTP routes, schema types                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Folder Structure

### 7.1 Monorepo Root

```
salesos/
  packages/                          # Shared packages (Python + TypeScript)
    salesos-design-language/         # Tokens, icons, typography
    salesos-ui/                      # Design system
    salesos-widget-sdk/              # Widget SDK v1.1
    salesos-api-client/              # Base HTTP client (TypeScript)
    salesos-domain-event/            # Domain event types (Python)
    salesos-testing/                 # Shared test utilities
    salesos-config/                  # Configuration library
    salesos-middleware/              # Shared middleware components

  salesos/                           # Python backend
    bootstrap/                       # App factory, settings, lifespan
    middleware/                      # Middleware pipeline
    domains/
      identity/                      # Domain
        __init__.py                  # Public exports only
        domain/                      # Domain models, interfaces
        application/                 # Use cases
        infrastructure/              # Repos, external clients
        interface/                   # REST router, GraphQL schema
      company/                       # Same structure
      search/
      crm/
      timeline/
      scoring/
      ai/
      workflow/
      employee/
      customer-success/
      enrichment/
      entity-resolution/
      pipeline/
      decision-platform/
      data-fabric/
      feature-store/
      tenant/                        # NEW
      billing/                       # NEW
    infrastructure/                  # Shared infra
      database/
        postgres.py
        neo4j.py
        redis.py
      event_bus/
        in_memory.py
        kafka.py
      storage/
        s3.py
      cache/
        redis_cache.py
      queue/
        celery.py
    runtimes/                        # Runtime entry points
      api.py                         # API Server
      websocket.py                   # WebSocket Server
      celery_worker.py               # Celery Worker
      scheduler.py                   # Scheduler
      workflow_engine.py             # Workflow Engine
      agent_runtime.py               # Agent Runtime
      event_consumer.py              # Kafka Consumer
      simulation.py                  # Simulation Engine
      health.py                      # Health + Metrics
      migration.py                   # Alembic migrations
      seed.py                        # Seed data
      benchmark.py                   # Performance benchmark
      audit.py                       # Security audit
      cli.py                         # Admin CLI
      eval.py                        # AI evaluation

  frontend/                          # TypeScript frontend
    packages/
      design-language/
      ui/
      widget-sdk/
      api-client/
      api-identity/
      api-company/
      api-search/
      api-timeline/
      api-workflow/
      api-scoring/
      api-crm/
      api-ai/
      api-enrichment/
      api-pipeline/
      api-employee/
      api-customer-success/
      api-decision/
      widgets/
        mission-center/
        company-profile/
        search/
        timeline/
        scoring/
        workflow/
        employee/
        crm/
        customer-success/
    apps/
      dashboard/
      employee-360/
      company-workspace/

  config/                            # Centralized configuration
    defaults.yaml
    production.yaml
    staging.yaml
    development.yaml
    secrets/                         # Not in VCS
      production.yaml
      staging.yaml

  tests/                             # Test consolidation
    unit/                            # Mirrors src/ structure
      bootstrap/
      middleware/
      domains/
        identity/
        company/
        ...
    integration/                     # Cross-domain + external deps
    e2e/                             # End-to-end
    contract/                        # Contract tests
    performance/                     # Load tests
    conftest.py                      # Shared fixtures
    pytest.ini                       # Single pytest config

  migration/                         # Alembic migrations
  docs/                              # Documentation
```

---

## 8. Dependency Rules

### 8.1 Rules Enforced by CI

| Rule | Check | Violation Action |
|------|-------|-----------------|
| **No cross-domain imports at runtime** | Import scanner | Block PR |
| **No infrastructure import in domain** | Layer scanner | Block PR |
| **No domain import in shared lib** | Import scanner | Block PR |
| **No circular imports** | `pytest-arch` | Block PR |
| **API client per domain** | Frontend import scanner | Block PR |
| **Single config source** | Config integrity check | Block PR |
| **No print/debug statements** | `ruff` rule | Block PR |
| **No commented-out code** | `ruff` rule | Block PR |
| **No secrets in code** | `detect-secrets` | Block PR |
| **No `Any` types in public interfaces** | `mypy` strict | Warn → Block in v1.0 |

### 8.2 Import Enforcement Strategy

```python
# pyproject.toml
[tool.ruff.lint.per-file-ignores]
"src/domains/*/domain/**" = ["F403"]
"src/domains/*/domain/*" = ["FA100"]  # May only import: dataclasses, abc, typing, domain.events
"src/domains/*/application/*" = ["FA101"]  # May only import: own domain, other domain SDKs
"src/domains/*/infrastructure/*" = ["FA102"]  # May only import: own domain, shared infra
"src/domains/*/interface/*" = ["FA103"]  # May only import: own application layer, fastapi, pydantic
```

### 8.3 Frontend Import Boundaries

```jsonc
// .eslintrc.json
{
  "rules": {
    "@salesos/import-boundaries": [
      "error",
      {
        "boundaries": [
          { "from": ["@salesos/widget-*"], "allow": ["@salesos/widget-sdk", "@salesos/api-client"] },
          { "from": ["@salesos/api-*"], "allow": ["@salesos/api-client"] },
          { "from": ["@salesos/widget-sdk"], "allow": ["@salesos/design-language", "@salesos/ui"] },
          { "from": ["@salesos/ui"], "allow": ["@salesos/design-language"] },
          { "from": ["@salesos/design-language"], "allow": [] }
        ]
      }
    ]
  }
}
```

---

## 9. Shared Packages

### 9.1 Python Shared Packages

| Package | Purpose | Consumers |
|---------|---------|-----------|
| `salesos-domain-event` | Domain event type definitions | All domains |
| `salesos-config` | Pydantic settings + YAML loader | All runtimes |
| `salesos-testing` | Test fixtures, factories, mocks | All test suites |
| `salesos-middleware` | Middleware components (tenant, auth, body cache) | API Server, WebSocket |
| `salesos-domain-sdk` | Cross-domain SDK interfaces | All domains |

### 9.2 TypeScript Shared Packages

| Package | Purpose | Consumers |
|---------|---------|-----------|
| `@salesos/design-language` | Design tokens, icons, typography | All frontend packages |
| `@salesos/ui` | Design system components | All frontend packages |
| `@salesos/widget-sdk` | Widget SDK v1.1 | All widget packages |
| `@salesos/api-client` | Base HTTP client (auth, retry) | All API packages |
| `@salesos/testing` | Test utilities, mocks, contract test helpers | All frontend tests |

### 9.3 Package Creation Rules

- A shared package must have **at least 3 consumers** before creation
- Shared packages must be **versioned independently** (semver)
- Shared packages must have **their own test suite**
- Breaking changes to shared packages require **ADR + migration plan**

---

## 10. Data Flow

### 10.1 Request Flow (REST)

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐
│ Client   │───▶│ Gateway  │───▶│ Middle-  │───▶│ Domain       │
│ (Widget) │    │ (Edge)   │    │ ware     │    │ Router       │
└─────────┘    └──────────┘    └──────────┘    └──────┬───────┘
                                                      │
                                              ┌───────▼───────┐
                                              │ Application   │
                                              │ Use Case      │
                                              └───────┬───────┘
                                                      │
                                              ┌───────▼───────┐
                                              │ Domain        │
                                              │ Service       │
                                              └───────┬───────┘
                                                      │
                                        ┌──────────────┼──────────────┐
                                        │              │              │
                                ┌───────▼──────┐ ┌────▼────┐ ┌──────▼─────┐
                                │ Repository   │ │ Event   │ │ External   │
                                │ (PostgreSQL) │ │ Bus     │ │ Service    │
                                └──────────────┘ └─────────┘ └────────────┘
```

### 10.2 Write Flow (Event-Driven)

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐
│ Client   │───▶│ API      │───▶│ Domain   │───▶│ Repository   │
│          │    │ Router   │    │ Service  │    │ (Write)      │
└─────────┘    └──────────┘    └─────┬────┘    └──────────────┘
                                      │
                                      │ publish(event)
                                      ▼
                              ┌───────────────┐
                              │   Event Bus    │
                              │ (In-Memory /   │
                              │  Kafka)        │
                              └───────┬───────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
            ┌───────▼──────┐ ┌───────▼──────┐ ┌───────▼──────┐
            │ Domain A     │ │ Domain B     │ │ Denormalizer │
            │ Consumer     │ │ Consumer     │ │ (Read Model) │
            └──────────────┘ └──────────────┘ └──────────────┘
                                                    │
                                            ┌───────▼──────┐
                                            │ Read Database │
                                            │ (PostgreSQL)  │
                                            └──────────────┘
```

### 10.3 CQRS Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                          COMMAND SIDE                                │
│                                                                     │
│  Write API ──▶ Domain Service ──▶ Repository ──▶ PostgreSQL (OLTP) │
│                                     │                               │
│                                     └──▶ Event Bus                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ async
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          QUERY SIDE                                  │
│                                                                     │
│  Event Bus ──▶ Denormalizer ──▶ Read DB ──▶ Query API ──▶ Client   │
│                                    │                               │
│                                    ├── PostgreSQL (read-optimized) │
│                                    ├── Redis Cache                 │
│                                    └── ElasticSearch (future)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 11. API Contracts

### 11.1 Versioning Strategy

| Layer | Versioning | Breaking Change Policy |
|-------|-----------|----------------------|
| **REST API** | URL path: `/api/v2/` → `/api/v3/` | Lockstep major version |
| **GraphQL** | No versioning — additive schema evolution only | Deprecation field annotation |
| **Internal SDK** | Semver on package | Minor bump for additive, major for breaking |
| **Domain Events** | Schema registry with compatibility checks | Backward-compatible by default |
| **MCP Resources** | Versioned per resource type | Lockstep with REST |

### 11.2 API Design Rules

- All responses use **envelope format**: `{ data, meta, error }`
- Pagination uses **keyset-based** (cursor) not offset-based
- List endpoints support **field selection**: `?fields=id,name,email`
- List endpoints support **filtering**: `?filter[name][like]=*acme*`
- All mutations are **idempotent** where possible (idempotency key header)
- Rate limit info in response headers: `X-RateLimit-*`
- Deprecated endpoints return `Sunset` header + `Deprecation` header

### 11.3 Contract Testing

```
tests/contract/
  provider/                    # Provider-side contract tests
    identity.provider.test.py
    company.provider.test.py
    ...
  consumer/                    # Consumer-side contract tests
    identity.consumer.test.js
    company.consumer.test.js
    ...
  schemas/                     # OpenAPI + JSON Schema
    identity.openapi.yaml
    company.openapi.yaml
    ...
```

- Every endpoint has a **provider contract test** (verifies the API matches the schema)
- Every frontend API client has a **consumer contract test** (verifies the client matches the schema)
- Contract tests run in CI on both sides
- Schema changes require both provider and consumer tests to pass

---

## 12. Event Flow

### 12.1 Event Types

| Event Type | Description | Delivery |
|-----------|-------------|---------|
| **Domain Event** | Something happened in a domain (e.g., `CompanyCreated`) | At-least-once |
| **Integration Event** | Cross-domain communication (e.g., `CompanyEnriched`) | Exactly-once (Kafka transactions) |
| **Command** | Request for action (e.g., `EnrichCompany`) | At-most-once |
| **Notification** | User-facing alert (e.g., `EnrichmentCompleted`) | Best-effort |

### 12.2 Event Bus Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EVENT BUS                                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  In-Memory Bus (sync)                         │   │
│  │  • Same process, same transaction                            │   │
│  │  • For domain events that MUST be consistent                 │   │
│  │  • Subscribers run in the same transaction                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Kafka Bus (async)                            │   │
│  │  • Cross-process, cross-service                              │   │
│  │  • For integration events and background processing          │   │
│  │  • Topic per domain: salesos.company, salesos.search         │   │
│  │  • Dead letter queue for failed events                       │   │
│  │  • Schema registry for event compatibility                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Event Store                                   │   │
│  │  • All events persisted to PostgreSQL                         │   │
│  │  • Source of truth for event replay                           │   │
│  │  • Enables audit trail and debugging                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.3 Event Flow Rules

1. **Domain events** are published **after** the transaction commits (Outbox pattern)
2. **Integration events** are published via **Kafka** with schema registry
3. **Event handlers** are idempotent — same event delivered twice produces same result
4. **Dead letter queue** captures all failed events with error context
5. **Event schema** evolves via schema registry with backward compatibility checks
6. **Event ownership** belongs to the publishing domain — the publisher defines the schema

### 12.4 Outbox Pattern

```
┌──────────┐    1. Write     ┌──────────────┐    2. Commit    ┌──────────┐
│  Service  │──────────────▶│  Outbox Table │───────────────▶│  DB      │
│           │    event +     │  (same DB)    │                │          │
│           │   entity       │               │                │          │
└──────────┘                └──────────────┘                └──────────┘
                                                                    │
                                                            3. Poll (bg)
                                                                    │
                                                                    ▼
                                                            ┌──────────────┐
                                                            │  Relay       │
                                                            │  Process     │
                                                            └──────┬───────┘
                                                                    │
                                                            4. Publish
                                                                    │
                                                                    ▼
                                                            ┌──────────────┐
                                                            │  Kafka       │
                                                            │  Topic       │
                                                            └──────────────┘
```

---

## 13. Extension Strategy

### 13.1 Extension Points

| Extension Point | Mechanism | Example |
|----------------|-----------|---------|
| **New Domain** | Add folder in `src/domains/`, register router | `billing/` |
| **New Widget** | Use Widget Template, register in widget registry | `widget-billing/` |
| **New Event Handler** | Subscribe to domain event | Send email on `CompanyCreated` |
| **New Middleware** | Add to middleware pipeline | Request logging |
| **New Runtime** | Create entry point in `src/runtimes/` | Data export runtime |
| **New External Integration** | Add infrastructure client | Salesforce connector |

### 13.2 Extension Workflow

```
1. RFC → 2. ADR → 3. Implementation → 4. Contract Test → 5. Integration Test → 6. Docs
```

- **RFC**: 1-page proposal describing the extension, its interfaces, and affected domains
- **ADR**: Required for any new extension point (see Engineering Constitution §3.1)
- **Contract Test**: Required for any new API surface
- **Integration Test**: Required for any cross-domain interaction

### 13.3 Feature Flags

All extensions behind feature flags:

```yaml
# config/defaults.yaml
features:
  billing:
    enabled: false         # Feature flag
    beta: true             # Beta flag
    rollout_percentage: 0  # Gradual rollout
  new_search:
    enabled: true
    rollout_percentage: 100
```

Feature flags are:
- Evaluated at runtime (not compile time)
- Configurable per tenant
- Tracked in monitoring
- Removed after full rollout (feature flag tech debt tracked in TDR)

---

## 14. Plugin Strategy

### 14.1 Plugin Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PLUGIN SYSTEM                                 │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  Plugin A   │  │  Plugin B   │  │  Plugin C   │                │
│  │             │  │             │  │             │                │
│  │  hooks/     │  │  hooks/     │  │  hooks/     │                │
│  │  widgets/   │  │  widgets/   │  │  widgets/   │                │
│  │  config.yaml│  │  config.yaml│  │  config.yaml│                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                │                │                        │
│         └────────────────┼────────────────┘                        │
│                          │                                         │
│  ┌───────────────────────▼──────────────────────────────────────┐  │
│  │                    PLUGIN REGISTRY                             │  │
│  │  • Loads plugins from configured paths                       │  │
│  │  • Validates plugin manifest (name, version, hooks)          │  │
│  │  • Manages plugin lifecycle (install, enable, disable)       │  │
│  │  • Enforces plugin sandboxing (isolated imports)             │  │
│  └───────────────────────▲──────────────────────────────────────┘  │
│                          │                                         │
│  ┌───────────────────────┴──────────────────────────────────────┐  │
│  │                    HUB SYSTEM                                  │  │
│  │  • Plugin marketplace (internal)                             │  │
│  │  • Versioning + compatibility checks                         │  │
│  │  • Dependency resolution between plugins                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 14.2 Plugin Types

| Plugin Type | What It Can Do | Sandbox |
|-------------|---------------|---------|
| **Widget Plugin** | Register new widgets via SDK | Full isolation (iframe) |
| **Backend Plugin** | Register new endpoints, event handlers | Import-restricted |
| **Data Source Plugin** | Add external data source (CRM, ERP, etc.) | Import-restricted |
| **AI Plugin** | Register new AI provider or prompt | Full isolation |
| **Integration Plugin** | Add external connector (Slack, Teams, etc.) | Import-restricted |

### 14.3 Plugin Manifest

```yaml
# plugin.yaml
name: salesforce-connector
version: 1.0.0
type: data-source
requires:
  salesos: ">=2.0.0"
  salesos-sdk: "^1.2.0"
hooks:
  - event: company.created
    handler: handlers.on_company_created
  - event: company.updated
    handler: handlers.on_company_updated
widgets:
  - salesforce-sync-status
permissions:
  - company:read
  - event:subscribe:company.*
```

### 14.4 Plugin Lifecycle

```
Install ▶ Disabled ▶ Enable ▶ Active ▶ Disable ▶ Uninstall
                │                    │
                └──▶ Error  ────────▶│
                                    ▶ Upgrade
```

- **Install**: Plugin code copied/extracted, manifest validated
- **Enable**: Plugin registered in registry, hooks wired
- **Active**: Plugin running, consuming events and providing data
- **Disable**: Plugin unhooked but code remains
- **Uninstall**: Plugin code removed, cleanup hooks called

---

## Migration Plan

| Phase | Changes | Duration |
|-------|---------|----------|
| **Phase 1: Modular Bootstrap** | Extract `main.py` to `bootstrap/`, consolidate middleware, fix body cache bug | 1 sprint |
| **Phase 2: API Client Split** | Split `api.ts` into domain-specific clients, enforce frontend import boundaries | 1 sprint |
| **Phase 3: Runtime Consolidation** | Merge 28 runtimes → 15, implement new runtimes (Scheduler, Workflow, Agent) | 2 sprints |
| **Phase 4: Configuration Centralization** | Replace 6+ `.env` files with single config system | 1 sprint |
| **Phase 5: Plugin System** | Implement plugin registry, manifest validation, lifecycle | 2 sprints |
| **Phase 6: Event Bus Consolidation** | Unify Redis pools, implement Outbox pattern, add Dead Letter Queue | 1 sprint |
| **Phase 7: Monorepo Restructure** | Align folder structure to target layout, update CI rules | 1 sprint |

---

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| API client (frontend) lines | 1,240 lines | ≤ 100 lines per domain |
| `main.py` lines | 773 lines | ≤ 100 lines |
| Cross-domain violations | Unknown | 0 (CI-enforced) |
| `.env` files | 6+ | 1 (secrets overlaid) |
| Runtimes | 28 | 15 |
| Middleware chain | 10 layers | 10 layers (fixed POST bug) |
| Redis pools | 3 | 1 |
| Monorepo packages | 13 | 20+ (domain-split) |
| Import boundary enforcement | None | CI-enforced on all packages |
| POST body reliability | Buggy | Always reliable |

---

*This document is the architectural target for SalesOS vNext. All changes must align with this architecture per the Engineering Constitution §3.1 — any deviation requires an ADR.*
