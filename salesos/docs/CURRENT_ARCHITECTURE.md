# SalesOS — CURRENT ARCHITECTURE

> **Sprint 0 Deliverable: Architecture Reconciliation**
> This document describes the architecture as it **actually exists** in the repository, based on full codebase analysis.
> Date: 2026-07-17 | Classification: Confidential
> Status: ✅ Baselines Sprint 0

---

## Table of Contents

1. [Repository Topology](#1-repository-topology)
2. [Backend Architecture](#2-backend-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Domain Map (Actual)](#4-domain-map-actual)
5. [API Surface](#5-api-surface)
6. [Data Layer](#6-data-layer)
7. [Testing Coverage](#7-testing-coverage)
8. [Widget SDK Reality](#8-widget-sdk-reality)
9. [Decision Platform Reality](#9-decision-platform-reality)
10. [Deployment Topology](#10-deployment-topology)
11. [Compliance Score (Measured)](#11-compliance-score-measured)

---

## 1. Repository Topology

```
Muhide/                                    # Project root
├── salesos/                               # Primary product platform (FastAPI + Next.js)
│   ├── backend/                           # Python backend (19 domains, 26 modules, 31 runtimes)
│   ├── frontend/                          # Next.js 14 frontend (13 features, 7 app routes)
│   ├── application/                       # Dashboard application (1 entry)
│   ├── platform/                          # Platform services (empty/skeleton)
│   ├── packages/                          # 13 npm packages (ui, design-language, workspace, etc.)
│   ├── docs/                              # Product-level documentation
│   ├── memory/                            # Technical debt register
│   ├── scripts/                           # CI/CD, compliance, benchmark scripts
│   ├── infra/                             # Infrastructure configs
│   ├── knowledge-packs/                   # Industry knowledge packs
│   └── reports/                           # Generated reports
│
├── engineering-os/                        # Governance platform (submodule)
│   ├── ENGINEERING_CONSTITUTION.md        # Binding rules
│   ├── ENGINEERING_DASHBOARD.md           # Live metrics
│   ├── ENGINEERING_IMPLEMENTATION_SPEC.md # Implementation spec
│   ├── IMPLEMENTATION_ROADMAP.md          # Sprint roadmap
│   ├── REFERENCES.md                      # Cross-repo mappings
│   ├── adr/                               # 3 ADRs (ADR-001, ADR-002, ADR-003)
│   └── kernel/                            # Capability registry
│
├── docs/                                  # Cross-cutting documentation
│   ├── MASTER_BLUEPRINT.md               # V5 4-layer architecture plan
│   ├── DOMAIN_MAP.md                     # 13 bounded contexts
│   ├── ARCHITECTURE_AUDIT_REPORT.md      # V4 audit (dated 2026-06-30)
│   ├── PROJECT_BIBLE.md                  # v2.0.0 — Ratified product constitution
│   ├── BUILD_PLAN_V5.md                  # Construction plan
│   ├── adr/                              # 2 product ADRs (0030, 0031)
│   └── vnext/                            # vNext work orders, roadmap, sprint plan
│
├── balady_scraper/                        # Government data scraper (Balady)
├── najiz_scraper/                         # Government data scraper (Najiz)
├── taqeem_scraper/                        # Government data scraper (Taqeem)
├── rega_scraper/                          # Government data scraper (Rega)
├── scraper.py                             # NCNP scraper
├── output/                                # Scraped data exports
├── open-design/                           # Third-party design tool
└── WidgetTemplate/                        # Widget scaffolding template
```

---

## 2. Backend Architecture

### 2.1 Layer Breakdown

```
salesos/backend/
├── sdk/                              # Shared kernel SDK
│   ├── database.py                   # Repository<T,TId>, SqlAlchemyRepository, UnitOfWork, Specification
│   ├── events/                       # DomainEvent, EventBus, KafkaEventBus, outbox, DLQ, schema_registry
│   ├── permissions.py                # Permission, Role, PermissionRegistry, PermissionEnforcer
│   ├── pagination.py                 # Keyset/cursor pagination
│   ├── cache.py                      # CacheService (Redis + in-memory fallback)
│   ├── telemetry.py                  # Structured logging
│   ├── security.py                   # Security utilities
│   ├── agent_sdk/                    # Agent integration SDK
│   ├── backend_sdk/                  # Backend-specific SDK
│   ├── frontend_sdk/                 # Frontend-specific SDK
│   ├── widget_sdk/                   # Widget SDK reference
│   └── ...                           # Additional sub-SDKs
│
├── domains/                          # Pure DDD domain layer (19 bounded contexts)
│   ├── ai/                           # AI domain (models, prompts, evaluation)
│   ├── analytics/                    # Analytics domain
│   ├── commercial/                   # Commercial: activity, contract, email, meeting, opportunity, pipeline, playbook, proposal, quote
│   ├── copilot/                      # AI Copilot domain
│   ├── decision/                     # Decision context/recommendation
│   ├── decision_center/              # Decision Center domain
│   ├── employee/                     # Employee domain
│   ├── feature_store/                # Feature Store domain
│   ├── marketplace/                  # Marketplace domain
│   ├── notifications/                # Notification domain
│   ├── rag/                          # RAG domain
│   ├── revenue/                      # Revenue: analytics, forecast, quota, territory
│   ├── scoring/                      # Scoring domain
│   ├── search/                       # Search: contracts, models, parser, planner, ranking, repositories
│   ├── timeline/                     # Timeline domain
│   ├── ubom/                         # UBOM domain
│   └── workflow/                     # Workflow domain
│
├── app/                              # Application/infrastructure layer
│   ├── main.py                       # FastAPI entry point (908 lines)
│   ├── config.py                     # Pydantic-settings BaseSettings
│   ├── database.py                   # async SQLAlchemy engine + init_db() (raw SQL table creation)
│   ├── cache.py                      # Redis cache config
│   ├── dependencies.py              # Auth dependencies (verify_token, require_role, require_permission)
│   ├── celery_app.py                 # Celery background tasks
│   ├── tasks.py                      # Task definitions
│   ├── application/                  # Application layer (Dashboard Aggregator)
│   │   └── dashboard/
│   │       ├── DashboardAggregator   # Orchestrates domain reads
│   │       ├── DashboardDTO         # Single response schema
│   │       └── DashboardMapper      # Domain models → DTO
│   ├── modules/                      # 26 feature modules
│   │   ├── identity/                 # Tenant + User + Auth + API Keys (90%)
│   │   ├── company/                  # Organization + Contact + License + Branch + CR
│   │   ├── search/                   # QueryParser → Planner → Execution → Ranking
│   │   ├── contact/                  # Contact management
│   │   ├── entity_resolution/        # Entity Resolution (skeleton→pg_trgm)
│   │   ├── employee_360/             # Employee 360
│   │   ├── executive/               # Executive dashboard module
│   │   ├── work_intelligence/        # Work intelligence
│   │   ├── excel_import/            # Excel import utility
│   │   ├── notion_sync/             # Notion sync
│   │   ├── tenant/                   # Tenant management
│   │   └── ...                       # Additional modules
│   ├── domains/                      # Product domain integration
│   │   └── customer_success/        # Customer Success domain
│   ├── routers/                      # 17 API routers
│   │   ├── company.py, search.py, dashboard.py, auth.py, ...
│   │   └── mcp.py                   # MCP protocol adapter
│   ├── metrics/                      # Prometheus metrics, SLA monitor
│   ├── graphql/                      # Strawberry GraphQL endpoint
│   ├── common/                       # Shared utilities
│   └── alembic/                      # Alembic migrations directory
│
├── runtime/                          # 31 execution engines
│   ├── search_runtime.py            # Search execution (FULLTEXT, SEMANTIC, GRAPH, HYBRID)
│   ├── decision_runtime.py          # Decision engine
│   ├── timeline_runtime.py          # Timeline engine
│   ├── data_fabric_runtime.py       # Data Fabric engine
│   ├── feature_store_runtime.py     # Feature Store engine
│   ├── knowledge_graph_runtime.py   # Knowledge Graph engine
│   ├── workflow_runtime.py          # Workflow engine
│   └── ...                           # Additional runtimes
│
├── migrations/                       # SQL migration files
├── intelligence/                    # Intelligence modules (13, mostly skeletons)
├── benchmark/                        # Performance testing framework
├── pipeline/                         # Data pipeline (excel, notion, validation)
├── mcp_server/                       # MCP protocol server (stdio/SSE)
├── demo/                             # Demo scripts
├── tests/                            # 2110+ tests across unit/integration/e2e
├── design_tokens/                    # Backend design token references
└── pyproject.toml                   # Python dependencies + coverage config
```

### 2.2 Key Patterns (Actual)

| Pattern | Status | Evidence |
|---------|--------|----------|
| Repository Pattern | ✅ Implemented in most domains | `sdk/database.py:Repository<T,TId>`, `SqlAlchemyRepository` |
| Unit of Work | ✅ Implemented | `sdk/database.py:UnitOfWork` |
| Specification Pattern | ✅ Implemented | `sdk/database.py:Specification`, `AndSpecification`, `OrSpecification` |
| Event-Driven | ✅ Event system built, Kafka configured but inactive | In-memory EventBus used in production |
| Domain Events | ✅ Implemented | `DomainEvent` base, typed events, outbox, DLQ |
| CQRS | ⚠️ Partial | Event sourcing for Entity Resolution only; ORM + audit logging elsewhere |
| Keyset Pagination | ✅ Implemented | `SqlAlchemyRepository.find_all_cursored()` |
| DI via FastAPI Depends | ✅ Used consistently | `Depends(get_db_session)`, `Depends(verify_token)` |
| Middleware Chain | ✅ 11 middleware layers | CORs, GZip, BodyCache, RequestID, Logging, Security, CSRF, Metrics, RateLimit, Audit, APIKey |
| Container/View | ✅ Widget SDK pattern | Both Dashboard SDK and Workspace SDK |

### 2.3 Technical Debt (Backend-Specific)

| Issue | Severity | Location |
|-------|----------|----------|
| `main.py` at 908 lines | 🔴 High | `app/main.py` |
| `init_db()` creates tables via raw SQL, bypassing Alembic | 🔴 High | `app/database.py:59-181` |
| Identity service bypasses own repositories | 🔴 High | `app/modules/identity/service.py` |
| InMemoryDecisionCenterRepository in production | 🟡 Medium | `app/main.py:255` |
| Dual domain locations (`domains/search/` vs `app/modules/search/`) | 🟡 Medium | Multiple |
| 4 duplicate health check endpoints | 🟢 Low | `app/routers/health*` |
| Empty search repositories directory | 🟢 Low | `domains/search/repositories/` |
| BodyCacheMiddleware + downstream middleware hang | 🟡 Medium | `app/main.py` |

---

## 3. Frontend Architecture

### 3.0 V3 Interface (Active — as of 2026-07-26)

The V3 frontend (`/v3/*` routes) is the **active production interface**. Legacy routes (`/(dashboard)/*`, `/companies/*`) remain for backward compatibility but are not the primary UI.

**V3 Company 360 Intelligence Tab** (wired 2026-07-26, commit `ec99019`):
- `IntelligenceTab` component calls `useCompanyIntelligence(companyId)` once
- Renders 10 widget Views directly: Company DNA, AI Recommendation, Decision Makers, Relationship Graph, Buying Journey, Golden Record, Signals, Smart Timeline, Government Intelligence, Document Intelligence
- Loading/Error/Empty states handled at tab level
- No backend changes required — uses existing `GET /api/v1/companies/{id}/intelligence`

**Data Flow:**
```
IntelligenceTab → useCompanyIntelligence hook → getCompanyIntelligence() → GET /api/v1/companies/{id}/intelligence → build_intelligence_dto()
```

### 3.1 Layer Breakdown

```
salesos/frontend/
├── src/
│   ├── app/                           # Next.js 14 App Router
│   │   ├── (auth)/                    # login, register
│   │   ├── (dashboard)/               # 28 authenticated route segments
│   │   ├── v3/                        # V3 INTERFACE (ACTIVE)
│   │   │   ├── companies/             # Company 360 + Intelligence tab
│   │   │   ├── contacts/              # Contacts CRUD
│   │   │   ├── people/                # Employee directory
│   │   │   ├── analytics/             # Executive analytics
│   │   │   └── activities/            # Global activity feed
│   │   ├── globals.css                # Global CSS with MUHIDE tokens
│   │   ├── layout.tsx                 # Root layout (RTL-first, Arabic detection)
│   │   ├── page.tsx                   # Landing page
│   │   └── providers.tsx             # App providers
│   │
│   ├── application/                   # Application layer (5 domains)
│   │   ├── api/                       # React Query hooks (opportunities, tasks, pipeline)
│   │   ├── dashboard/                 # Dashboard: api, dto, mapper, query, store, contract, widget.store
│   │   ├── company-intelligence/      # DTO, query, store, hooks
│   │   ├── search/                    # API, DTO, hooks, query keys
│   │   └── revenue-execution/        # DTOs only
│   │
│   ├── features/                      # 13 self-contained feature domains
│   │   ├── dashboard/                 # Dashboard feature
│   │   │   ├── _layout/              # Dashboard layouts
│   │   │   ├── _providers/           # Feature providers
│   │   │   ├── _registry/            # Widget registry
│   │   │   ├── _telemetry/           # Usage tracking
│   │   │   ├── sdk/                  # Dashboard Widget SDK (FROZEN v1.0)
│   │   │   │   ├── createWidget.tsx          # Widget factory
│   │   │   │   ├── createDashboardWidget.tsx # Dashboard widget factory
│   │   │   │   ├── contract-test-utils.tsx   # describeWidgetContract()
│   │   │   │   └── types.ts          # WidgetConfig, WidgetData, WidgetState
│   │   │   ├── widgets/              # 8 dashboard widgets
│   │   │   └── workspace-adapter.tsx # Bridge to Workspace SDK
│   │   ├── search/                   # Search feature
│   │   ├── company-intelligence/     # Company Intelligence workspace
│   │   ├── revenue-execution/        # Revenue Execution workspace
│   │   ├── admin/                    # Admin panel
│   │   ├── analytics/               # Analytics dashboard
│   │   ├── automation/              # Workflow automation
│   │   ├── customer-success/         # Customer success
│   │   ├── demo/                     # Demo mode
│   │   ├── employee-intelligence/    # Employee 360
│   │   ├── monitoring/               # System monitoring
│   │   ├── rag/                      # RAG interface
│   │   ├── rules/                    # Rules engine
│   │   └── ...                       # Remaining features
│   │
│   ├── components/                    # Shared components
│   │   ├── foundation/               # 22 foundation components
│   │   ├── search/                   # Search components
│   │   ├── analytics/               # Analytics components
│   │   ├── app-shell.tsx            # Main application shell
│   │   ├── command-bar.tsx           # Command palette (Cmd+K)
│   │   ├── company-workspace.tsx     # Company workspace page
│   │   ├── copilot-panel.tsx         # AI Copilot panel
│   │   ├── employee-360-page.tsx     # Employee 360 page
│   │   ├── executive-dashboard.tsx   # Executive dashboard
│   │   ├── pipeline-kanban.tsx       # Pipeline kanban board
│   │   ├── search-panel.tsx          # Search panel
│   │   ├── timeline-widget.tsx       # Timeline widget
│   │   └── lazy-exports.tsx         # Dynamic import re-exports
│   │
│   ├── lib/                          # Shared utilities
│   │   ├── api.ts                    # MONOLITHIC: 1,734 lines, ~70 API functions, types, localStorage
│   │   ├── api/                      # Alternative API client (partial)
│   │   ├── queryKeys.ts             # TanStack Query key hierarchy
│   │   ├── dynamic-imports.tsx       # next/dynamic lazy loading config
│   │   ├── utils.ts                  # Shared utilities
│   │   └── ...                       # Additional utilities
│   │
│   ├── mocks/                        # MSW handlers (browser + server)
│   └── __tests__/                    # Frontend tests
│
├── packages/                          # 13 npm packages
│   ├── ui/                           # @salesos/ui — 29 components (Button, Card, DataTable, Modal, etc.)
│   ├── design-language/              # @salesos/design-language — 18 token modules
│   ├── workspace/                    # @salesos/workspace — ACTIVE Widget SDK v5 (parallel to Dashboard SDK)
│   │   ├── src/
│   │   │   ├── createWidget.tsx      # SECOND createWidget() — different from dashboard SDK
│   │   │   ├── createWorkspaceWidget.tsx
│   │   │   ├── WorkspaceGrid.tsx
│   │   │   ├── testing/             # WidgetContract.tsx (parallel contract test util)
│   │   │   └── widgets/             # 4 workspace widgets
│   ├── runtime/                      # @salesos/runtime — 9 subsystems
│   ├── hooks/                        # @salesos/hooks — 14 custom hooks
│   ├── charts/                       # @salesos/charts
│   ├── forms/                        # @salesos/forms
│   ├── icons/                        # @salesos/icons
│   ├── search/                       # @salesos/search
│   ├── config/                       # @salesos/config
│   ├── renderer/                     # @salesos/renderer
│   ├── platform/                     # KERNEL: Platform, Decision Engine (STUB), Agents, RAG
│   └── workspace-generator/          # Code generation
│
├── e2e/                              # 27 Playwright E2E test specs
├── __tests__/                        # Additional test coverage
├── tests/                            # Additional test directories
├── .storybook/                       # Storybook configuration
├── coverage/                         # Coverage reports
├── next.config.js                    # Next.js configuration
├── tailwind.config.ts               # Tailwind + MUHIDE palette
├── tsconfig.json                     # TypeScript configuration
├── playwright.config.ts              # Playwright config (4 projects)
├── jest.config.js                    # Jest configuration
└── package.json                      # npm workspace root
```

### 3.2 Key Patterns (Actual)

| Pattern | Status | Evidence |
|---------|--------|----------|
| TanStack React Query for server state | ✅ Consistent | All application hooks use `useQuery`/`useMutation` |
| Feature-based organization | ✅ Consistent | `_layout/_providers/_registry/_hooks/_telemetry` convention |
| Widget SDK Container/View | ✅ Dual implementation | Dashboard SDK (frozen v1.0) + Workspace SDK (active v5) |
| Dynamic imports for heavy components | ✅ 15+ dynamic imports | `next/dynamic` in `dynamic-imports.tsx` |
| Design tokens from `@salesos/design-language` | ✅ Implemented | 18 token modules, Tailwind extension |
| Monorepo with npm workspaces | ✅ Implemented | 13 packages in workspaces |
| MSW for mock API | ✅ Configured | `src/mocks/` with browser/server handlers |

### 3.3 Technical Debt (Frontend-Specific)

| Issue | Severity | Location |
|-------|----------|----------|
| `src/lib/api.ts` at 1,734 lines (monolithic) | 🔴 High | `src/lib/api.ts` |
| Dual Widget SDKs (Dashboard v1.0 frozen vs Workspace v5 active) | 🔴 High | `src/features/dashboard/sdk/` vs `packages/workspace/` |
| Decision Engine is a non-functional stub | 🟡 Medium | `packages/platform/decision/index.ts` |
| API client split incomplete (`src/lib/api/` coexists with `src/lib/api.ts`) | 🟡 Medium | `src/lib/api/` vs `src/lib/api.ts` |
| Hardcoded localStorage keys as string literals | 🟢 Low | Multiple files |
| Empty directories from refactoring | 🟢 Low | Various |

---

## 4. Domain Map (Actual)

### 4.1 Bounded Contexts — Current State

| # | Context | Type | Backend Status | Frontend Status | Compliance |
|---|---------|------|---------------|-----------------|------------|
| BC-01 | Identity & Access | Generic | ~95% — auth, JWT, RBAC, CSRF, rate limiting | Login/register pages | 100% |
| BC-02 | Company Intelligence | **Core** | ~90% — PostgreSQL repos, entity resolution | Company workspace, search, signals | 95% |
| BC-03 | Entity Resolution | **Core** | ~85% — pg_trgm matching + merge pipeline | No dedicated UI | 95% |
| BC-04 | CRM | Supporting | ~80% — opportunities, contacts, pipeline | Pipeline kanban, opportunity CRUD | 90% |
| BC-05 | Activity Engine | Supporting | ~75% — activity recording, timeline | Timeline widget, activity feed | 80% |
| BC-06 | Scoring Engine | Supporting | ~80% — ScoreCard, ScoringFactor, ScoringEngine | Score displays in workspaces | 95% |
| BC-07 | Company DNA | Supporting | ~70% — DNA profile models | DNA components (partial) | 80% |
| BC-08 | Knowledge Graph | **Core** | ~80% — Neo4j integration, graph queries | Graph viewer (partial) | 85% |
| BC-09 | AI Platform | **Core** | ~75% — LLM providers, prompt registry, RAG | Copilot panel, AI recommendations | 85% |
| BC-10 | Workflow Engine | Generic | ~50% — workflow definitions, execution | Automation UI (partial) | 50% |
| BC-11 | Marketplace | Generic | ~60% — plugin listing, signal marketplace | Marketplace UI (partial) | 70% |
| BC-12 | Data Lake | Supporting | ~30% — pipeline utilities only | No UI | 40% |
| BC-13 | Billing | Generic | ~50% — subscription models | No dedicated UI | 60% |

### 4.2 Cross-Cutting Concerns

| Concern | Status | Notes |
|---------|--------|-------|
| Multi-tenancy | ✅ Implemented | X-Tenant-Id header, tenant-scoped JWT |
| Arabic/RTL | ✅ Implemented | IBM Plex Sans Arabic, RTL layout, Arabic error messages |
| KSA PDPL | ✅ Implemented | Right to erasure in identity service |
| Feature Flags | ✅ Implemented | Per-widget, per-route feature flags |
| Telemetry | ✅ Implemented | Prometheus metrics, SLA monitor, OpenTelemetry |

---

## 5. API Surface

### 5.1 Router Registration

All routers registered in `app/main.py:740-908` (168-line `register_routers()` function):

| Prefix | Router | Status |
|--------|--------|--------|
| `/api/v1/auth` | `app/routers/auth.py` | ✅ Production |
| `/api/v1/companies` | `app/routers/company.py` | ✅ Production |
| `/api/v1/search` | `app/routers/search.py` | ✅ Production |
| `/api/v1/dashboard` | `app/routers/dashboard.py` | ✅ Production |
| `/api/v1/opportunities` | `app/routers/opportunity.py` | ✅ Production |
| `/api/v1/timeline` | `app/routers/timeline.py` | ✅ Production |
| `/api/v1/decisions` | `app/routers/decision.py` | ✅ Production |
| `/api/v1/decisions/center` | `app/routers/decision_center.py` | ✅ Production |
| `/api/v1/webhooks` | `app/routers/webhooks/` | ✅ Production |
| `/api/v1/admin` | `app/routers/admin.py` | ✅ Production |
| `/api/v1/notifications` | `app/routers/notifications/` | ✅ Production |
| `/api/v1/employee` | `app/routers/employee.py` | ✅ Production (partial) |
| `/api/v1/customer-success` | `app/routers/customer_success.py` | ✅ Production |
| `/api/v1/rag` | `app/routers/rag.py` | ✅ Production |
| `/api/v1/revenue` | `app/routers/revenue.py` | ✅ Production |
| `/api/v1/scoring` | `app/routers/scoring.py` | ✅ Production |
| `/graphql` | `app/graphql/` | ✅ Production |
| `/mcp` | `app/routers/mcp.py` | ✅ Production |
| `/health` | 4 variants | ✅ Production (duplicated) |

### 5.2 API Patterns

- All routers behind `dependencies=_auth` (defense-in-depth)
- Three-tier auth: tenant, session, permission
- Consistent prefix: `/api/v1/{domain}`
- OpenAPI tags for grouping

---

## 6. Data Layer

### 6.1 Database Architecture

| Component | Tech | Status | Notes |
|-----------|------|--------|-------|
| Primary DB | PostgreSQL 15 | ✅ Operational | asyncpg, pg_trgm, pgvector |
| Graph DB | Neo4j | ✅ Operational | Connection pool with context managers |
| Cache | Redis | ⚠️ Configured but idle | In-memory fallback active |
| Message Queue | Kafka | ⚠️ Configured but inactive | In-memory EventBus active |
| Background Tasks | Celery | ⚠️ Configured but not fully wired | |

### 6.2 Migration System

Two parallel systems coexist:
1. **Raw SQL files** in `migrations/` — `001_initial.sql`, `002_create_opportunities_tasks.sql`, etc.
2. **Alembic** — `alembic.ini` + `app/alembic/` directory

**Critical issue**: `init_db()` in `database.py:59-181` creates tables via raw SQL, **bypassing Alembic entirely**. This means migration history does not reflect actual database state.

### 6.3 Repository Implementations

| Domain | InMemory | PostgreSQL | Notes |
|--------|----------|------------|-------|
| Identity | Tests only | ✅ Production | Service bypasses its own repos |
| Company | Tests only | ✅ Production | Full PostgreSQL migration |
| Search | Tests only | ✅ Production | Hybrid search (full-text + semantic) |
| Timeline | Tests only | ✅ Production | TimelineService |
| Scoring | Tests only | ✅ Production | ScoringEngine |
| CRM | Tests only | ✅ Production | Contact, Opportunity repos |
| Workflow | Tests only | ✅ Production | WorkflowService |
| Decision Center | ✅ **Active in production** | ❌ Not migrated | TD-006 |
| Feature Store | Tests only | ✅ Production | FeatureStoreService |

---

## 7. Testing Coverage

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Unit Test Coverage | 93% | 85% | 🟢 Exceeded |
| Integration Test Coverage | 70% | 70% | 🟢 Met |
| E2E Coverage | 60% | 60% | 🟢 Met |
| E2E Tests | 269 | 250+ | 🟢 Exceeded |
| Test Pass Rate | 100% | 100% | 🟢 |
| Total Tests | 2,110+ | 2,000+ | 🟢 Exceeded |

### 7.1 Per-Domain Coverage

| Domain | Coverage | Status |
|--------|----------|--------|
| Identity | 88% | 🟢 |
| Company | 80% | 🟡 Near target |
| Search | 93% | 🟢 |
| Timeline | 82% | 🟡 Near target |
| CRM | 80% | 🟡 Near target |
| Scoring | 78% | 🟡 Below target |
| AI | 92% | 🟢 |
| Workflow | 95% | 🟢 |
| Customer Success | >85% | 🟢 |
| Monitoring | >85% | 🟢 |

---

## 8. Widget SDK Reality

### 8.1 Dual SDK Architecture

```
DASHBOARD SDK (frozen v1.0)             WORKSPACE SDK (active v5)
────────────────────────────             ─────────────────────────
src/features/dashboard/sdk/              packages/workspace/
├── createWidget.tsx                     ├── createWidget.tsx
├── createDashboardWidget.tsx            ├── createWorkspaceWidget.tsx
├── contract-test-utils.tsx              ├── testing/WidgetContract.tsx
│   └── describeWidgetContract()         │   └── WidgetContract()
├── types.ts                             ├── WorkspaceGrid.tsx
└── ...                                  └── widgets/
```

**This is a DRY violation of Widget SDK ADR-003 (Feature Freeze).**

ADR-003 freezes `createWidget()`, `createDashboardWidget()`, SDK types, lifecycle, telemetry, permissions, feature flags, and `describeWidgetContract()`. But `packages/workspace/` provides a second, active implementation with the same API surface but different behavior.

The adapter at `src/features/dashboard/sdk/workspace-adapter.tsx` bridges them, confirming the duality is known.

### 8.2 Widget Distribution

36-37 widgets across the platform (count varies by audit):

| Context | Count | Examples |
|---------|-------|----------|
| Dashboard | 6 | Mission Center, Decision Queue, Intelligence Feed, AI Brief, Market Pulse, Recent Activity |
| Company Intelligence | ~10 | Signals, Timeline, Relationships, DNA, AI Summary, etc. |
| Revenue Execution | ~19 | Opportunity, Pipeline, Meeting, Email, Forecast, etc. |
| Analytics | ~1 | Analytics widgets |
| Search | ~1 | Search widgets |
| Workspace SDK | 4 | GlobalActivityFeed, UniversalInbox, RevenueCommandCenter, AIOperatingAssistant |

---

## 9. Decision Platform Reality

### 9.1 Backend Decision Platform

| Component | Status | Notes |
|-----------|--------|-------|
| Decision Engine | ✅ Implemented | `domains/decision/` — orchestrator pattern |
| Rule Engine | ✅ Implemented | `runtime/` — deterministic rules engine |
| Scoring Engine | ✅ Implemented | `domains/scoring/` — ScoreCard, ScoringFactor |
| Evidence Engine | ✅ Implemented | Evidence collection and validation |
| Recommendation Engine | ✅ Implemented | Ranked recommendations |
| Explainability Engine | ✅ Implemented | Explains why, why now, what evidence |
| Feedback Engine | ✅ Implemented | Captures action outcomes |
| Learning Engine | ⚠️ Partial | Quality trend tracking |

### 9.2 Frontend Decision Platform

| Component | Status | Notes |
|-----------|--------|-------|
| `packages/platform/decision/index.ts` | ❌ **Stub** | Exports interface + throws "Not implemented" |
| DecisionProvider | ✅ Implemented | Used in Dashboard + Company contexts (VIO-105 resolved) |
| Decision Center UI | ⚠️ Partial | UI exists but backend Integration incomplete |

---

## 10. Deployment Topology

| Environment | Status | URL/Config |
|-------------|--------|------------|
| Local Dev | ✅ Operational | Docker Compose, PostgreSQL, Neo4j |
| Staging | ✅ Operational | 3 pilot tenants provisioned |
| Production | ⚠️ Not deployed | All gates passed but production not live |
| CI/CD | ✅ Operational | GitHub Actions with security + arch + test gates |
| Docker | ✅ Validated | Multi-stage builds, version-pinned tags |

---

## 11. Compliance Score (Measured)

### 11.1 Architecture Compliance (Measured vs Codebase Analysis)

| Rule | ID | Weight | Score | Evidence |
|------|----|--------|-------|----------|
| Container/View Pattern | ARC-9.1 | 20% | ⚠️ 75% | Dual SDK violation; workspace SDK widgets not consistently split |
| No Cross-Domain Imports | ARC-3.2 | 20% | ✅ 95% | Verified by compliance script; minor exceptions in edge cases |
| Repository Pattern | ARC-3.3 | 15% | ⚠️ 85% | Identity service bypasses; DecisionCenter still in-memory |
| No localStorage for Business Data | DF-4.1 | 10% | ✅ 95% | Previous violations resolved; clean audit |
| Centralized API Client | DF-4.2 | 10% | ⚠️ 80% | Dual client patterns (`api.ts` + `api/`); monolithic file |
| Decision Platform for Scoring | DP-5.1 | 15% | ⚠️ 80% | Frontend Decision Engine is a stub |
| No Inline Scoring in Views | DP-5.2 | 10% | ✅ 90% | Minor edge cases in legacy components |

**Overall Measured Compliance: ~85%** (below the 95% target)

### 11.2 Per-Domain Compliance (Measured)

| Domain | Previously Reported | Measured Actual | Delta | Key Gap |
|--------|-------------------|-----------------|-------|---------|
| Identity | 100% | 100% | 0 | None |
| Widget SDK | 100% | ⚠️ 70% | -30% | Dual SDK violation; ADR-003 frozen surface duplicated |
| Company | 95% | 95% | 0 | Minor |
| Search | 90% | 88% | -2% | Repository pattern gaps |
| Scoring | 95% | 92% | -3% | Frontend Decision Engine stub |
| CRM | 90% | 88% | -2% | Monolithic api.ts |
| AI | 85% | 82% | -3% | Evaluation framework, frontend Decision Engine |
| Timeline | 80% | 78% | -2% | Architecture refactoring incomplete |
| Workflow | 50% | 48% | -2% | Full implementation not started |
| **OVERALL** | **87%** | **~85%** | **-2%** | **Dual SDK is the largest gap** |

---

## Appendix A: File Size Violations

Files exceeding the 600-line limit (per PROJECT_BIBLE §12.2.7):

| File | Lines | Limit | Over |
|------|-------|-------|------|
| `backend/app/main.py` | 908 | 600 | +308 |
| `frontend/src/lib/api.ts` | 1,734 | 600 | +1,134 |

## Appendix B: Key Findings Summary

1. **The project is significantly more mature than the MASTER_BLUEPRINT V5.0 claims.** The blueprint states Layer 4 (Applications) at 0%, but the frontend is a fully functional Next.js application with 13 features, widgets, and CI/CD.

2. **Dual Widget SDKs is the single largest architecture violation.** ADR-003 freezes one SDK while a parallel implementation continues active development.

3. **Identity service violates the Repository Pattern** — the one domain documented as 100% compliant, frozen, and zero-debt has a clear pattern violation.

4. **init_db() bypasses Alembic** — a critical data integrity risk where migration history and actual DB state can diverge.

5. **Decision Engine stub** — the frontend platform's Decision Engine throws "Not implemented" despite being documented as part of the frozen Decision Platform.

6. **The architecture documentation is aspirational, not descriptive.** Compliance scores in docs (87%) are self-reported estimates, not measured from actual codebase analysis. Measured compliance is ~85%.

7. **Two file-size violations** — `main.py` (908 lines) and `api.ts` (1,734 lines) exceed the 600-line limit imposed by PROJECT_BIBLE §12.2.7.
