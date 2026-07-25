# SalesOS — Architecture Inventory

> **Sprint 0.5 Deliverable: Platform Freeze**
> Generated from repository analysis on 2026-07-17.
> This inventory is immutable. Any change requires ADR.

---

## 1. Repository Scale

| Metric | Value |
|--------|-------|
| Total Python files | 1,540 |
| Total TypeScript/TSX files | 646 |
| Test files (all languages) | 703 |
| Total files (all types) | 2,189+ |
| Documentation (.md) files | 45+ |
| Docker Compose configurations | 3 |
| CI/CD workflow files | 6 |
| Years of engineering | ~1 year |

---

## 2. Backend Domain Packages

| Domain | Python Files | Test Files |
|--------|-------------|------------|
| `commercial` | 75 | 15 |
| `search` | 41 | 15 |
| `revenue` | 33 | 8 |
| `employee` | 17 | 7 |
| `workflow` | 17 | 5 |
| `marketplace` | 16 | 6 |
| `decision` | 15 | 4 |
| `timeline` | 14 | 2 |
| `ai` | 11 | 5 |
| `analytics` | 10 | 0 |
| `copilot` | 9 | 2 |
| `feature_store` | 9 | 2 |
| `decision_center` | 7 | 2 |
| `scoring` | 7 | 2 |
| `notifications` | 4 | 0 |
| `rag` | 2 | 0 |
| `ubom` | 1 | 0 |
| **Total** | **288** | **75** |

---

## 3. Backend App Modules

| Module | Python Files | Test Files |
|--------|-------------|------------|
| `company` | 15 | 5 |
| `identity` | 13 | 2 |
| `entity_resolution` | 12 | 5 |
| `admin` | 9 | 0 |
| `excel_import` | 7 | 3 |
| `notion_sync` | 7 | 3 |
| `signal_marketplace` | 7 | 0 |
| `contact` | 7 | 0 |
| `sso` | 6 | 0 |
| `webhooks` | 6 | 0 |
| `api_keys` | 5 | 0 |
| `audit` | 5 | 0 |
| `telemetry` | 5 | 0 |
| `decision` | 4 | 0 |
| `employee_360` | 4 | 0 |
| `executive` | 4 | 0 |
| `work_intelligence` | 4 | 0 |
| `rules_engine` | 4 | 0 |
| `demo_mode` | 3 | 0 |
| `cache` | 2 | 0 |
| `monitoring` | 2 | 0 |
| `revenue_execution` | 5 | 0 |
| `search` | 0 | 0 |
| `tenant` | 0 | 0 |
| **Total** | **126** | **18** |

---

## 4. API Routers

| Router | Path Prefix |
|--------|-------------|
| `auth.py` | `/api/v1/auth` |
| `company.py` | `/api/v1/companies` |
| `search.py` | `/api/v1/search` |
| `dashboard.py` | `/api/v1/dashboard` |
| `opportunities.py` | `/api/v1/opportunities` |
| `timeline.py` | `/api/v1/timeline` |
| `decision.py` | `/api/v1/decisions` |
| `decision_center.py` | `/api/v1/decisions/center` |
| `webhooks/` | `/api/v1/webhooks` |
| `admin.py` | `/api/v1/admin` |
| `notifications.py` | `/api/v1/notifications` |
| `employee.py` | `/api/v1/employee` |
| `customer_success.py` | `/api/v1/customer-success` |
| `rag.py` | `/api/v1/rag` |
| `revenue.py` | `/api/v1/revenue` |
| `scoring.py` | `/api/v1/scoring` |
| `mcp.py` | `/mcp` |
| `graphql/` | `/graphql` |
| **Total endpoint prefix groups** | **18** |

---

## 5. Backend SDK Modules

| SDK Module | Purpose |
|------------|---------|
| `database.py` | Repository<T,TId>, SqlAlchemyRepository, UnitOfWork, Specification |
| `events/` | DomainEvent, EventBus, KafkaEventBus, outbox, DLQ, schema registry |
| `permissions.py` | Permission, Role, PermissionRegistry, PermissionEnforcer |
| `pagination.py` | Keyset/cursor pagination |
| `cache.py` | CacheService (Redis + in-memory fallback) |
| `telemetry.py` | Structured logging |
| `security.py` | Security utilities |
| `agent_sdk/` | Agent integration SDK |
| `backend_sdk/` | Backend-specific SDK |
| `frontend_sdk/` | Frontend-specific SDK |
| `widget_sdk/` | Widget SDK reference |
| `company_sdk/` | Company-specific SDK |
| `integration_sdk/` | Integration SDK |
| `plugin_sdk/` | Plugin SDK |
| `theme_sdk/` | Theme SDK |
| `commercial/` | Commercial SDK |
| `scoring/` | Scoring SDK |
| `repositories/` | Repository implementations |

---

## 6. Alembic Migrations

| Revision | Name |
|----------|------|
| 0001 | Baseline |
| 0002 | Feature Store |
| 0003 | Decision Engine |
| 0004 | Knowledge Graph |
| 0005 | Timeline Runtime |
| 0006 | Search Runtime |
| 0007 | Commercial Domain |
| 0008 | Contact Module |
| 0009 | Activity Runtime |
| 0010 | Vector Store |
| 0011 | Dead Letter Queue |
| 0012 | Refresh Token Tables |
| 0013 | Meetings & Emails |
| 0014 | Analytics |
| 0015 | RAG Tables |
| 0016 | Drop Dual Embedding |
| 0017 | HNSW Index |
| 0018 | Feature Store FKs |
| 0019 | Commercial FKs |
| 0020 | Add Tenant ID |
| 0021 | Fix Vectors Embedding Type |
| 0022 | Consolidate Contacts |
| 0023 | Fulltext Search |
| 0024 | Enable pg_trgm |
| 0025 | Hybrid Search Optimization |
| 0026 | Feature Store |
| 0027 | Performance Indexes |
| 0028 | Enrichment Performance |
| 0029 | Add GIN Trigram Indexes |
| 0030 | Add Confidence Score Index |
| 0031 | Create Workflow Tables |
| 0032 | Create Notifications Table |
| 0033 | Add Users Lockout Columns |
| 0034 | Add Missing Company Columns |
| 0035 | Employee Signals |
| 0036 | Marketplace Tables |
| 0037 | Admin Phase 16 |
| **Total** | **37 migrations** |

---

## 7. SQL Migration Files

| # | File |
|---|------|
| 1 | `001_initial.sql` |
| 2 | `003_revenue_analytics.sql` |
| 3 | `004_workflow.sql` |
| 4 | `005_notifications.sql` |
| 5 | `006_database_indexes.sql` |
| 6 | `007_ai_foundation.sql` |

---

## 8. Intelligence Modules (20)

| Module | Status |
|--------|--------|
| `agents` | ⚠️ Partial |
| `arabic` | ⚠️ Partial |
| `business_objects` | ⚠️ Partial |
| `company` | ⚠️ Partial |
| `data_fabric` | ⚠️ Partial |
| `digital_twin` | 🔴 Skeleton |
| `enrichment` | ⚠️ Partial |
| `evaluation` | 🔴 Skeleton |
| `graph` | ⚠️ Partial |
| `market` | ⚠️ Partial |
| `memory` | ⚠️ Partial |
| `notifications` | ⚠️ Partial |
| `prompts` | ⚠️ Partial |
| `providers` | ⚠️ Partial |
| `rag` | ⚠️ Partial |
| `revenue_brain` | 🔴 Skeleton |
| `signals` | ⚠️ Partial |
| `simulation` | 🔴 Skeleton |
| `streaming` | ⚠️ Partial |

---

## 9. Backend MCP Server

| File | Purpose |
|------|---------|
| `server.py` | MCP FastMCP factory |
| `tools.py` | AI tool registration |
| `resources.py` | MCP resource registration |
| `salesos_client.py` | Internal API client |

---

## 10. Frontend Features

| Feature | Files | Status |
|---------|-------|--------|
| `revenue-execution` | 115 | ✅ Active |
| `dashboard` | 86 | ✅ Active |
| `company-intelligence` | 60 | ✅ Active |
| `search` | 44 | ✅ Active |
| `employee-intelligence` | 34 | ✅ Active |
| `admin` | 22 | ✅ Active |
| `customer-success` | 13 | ✅ Active |
| `rag` | 10 | ✅ Active |
| `analytics` | 9 | ✅ Active |
| `automation` | 6 | ✅ Active |
| `demo` | 4 | ✅ Active |
| `monitoring` | 1 | ✅ Active |
| `rules` | 1 | ✅ Active |
| **Total** | **405** | |

---

## 11. Frontend Packages

| Package | @salesos/ name | Files | Status |
|---------|---------------|-------|--------|
| `ui` | `@salesos/ui` | 31 | ✅ Production |
| `workspace` | `@salesos/workspace` | 29 | ⚠️ Dual SDK |
| `search` | `@salesos/search` | 21 | ✅ Production |
| `design-language` | `@salesos/design-language` | 19 | ✅ Production |
| `hooks` | `@salesos/hooks` | 15 | ✅ Production |
| `runtime` | `@salesos/runtime` | 11 | ✅ Production |
| `renderer` | `@salesos/renderer` | 7 | ✅ Production |
| `charts` | `@salesos/charts` | 2 | ✅ Production |
| `forms` | `@salesos/forms` | 1 | ✅ Production |
| `icons` | `@salesos/icons` | 1 | ✅ Production |
| `config` | `@salesos/config` | 1 | ✅ Production |
| `platform` | (internal) | 19 | ⚠️ Decision Engine stub |
| `workspace-generator` | `@salesos/workspace-generator` | 0 | 🔴 Empty |
| **Total** | | **157** | |

---

## 12. Frontend App Routes

| Route Group | Routes |
|-------------|--------|
| `(auth)` | login, register |
| `(dashboard)` | activities, admin (audit, config, flags, tenants), ai, analytics, automation, companies/[id], contacts, copilot, customer-success, decisions, employees/[id]/me, forecast, graph, knowledge, marketplace/[pluginId], meetings, monitoring, opportunities, pipeline, rag, revenue (analytics, quotas, territories), rules, search, settings, signals |
| **Total unique route segments** | **28+** |

---

## 13. Frontend Application Layer

| Domain | Files | Pattern |
|--------|-------|---------|
| `api/` | 2 | React Query hooks |
| `dashboard/` | 8 | DTO + Mapper + Query + Store + Contract |
| `company-intelligence/` | 7 | DTO + Query + Store + Hooks |
| `search/` | 4 | API + DTO + Hooks |
| `revenue-execution/` | 18 | DTO + Store + Engine |
| **Total** | **39** | |

---

## 14. E2E Test Coverage

| # | Spec | Covers |
|---|------|--------|
| 01 | login | Auth flow |
| 02 | dashboard | Dashboard widgets |
| 03 | search | Universal search |
| 04 | company-detail | Company 360 |
| 05 | create-opportunity | CRM create |
| 06 | pipeline-kanban | Pipeline |
| 07 | revenue-dashboard | Revenue |
| 08 | admin-panel | Admin |
| 09 | rtl-layout | RTL/Arabic |
| 10 | mobile-responsive | Mobile |
| 11 | contacts-crud | Contacts |
| 12 | employee-360 | Employee |
| 13 | workflow-automation | Workflow |
| 14 | error-states | Error handling |
| 15 | graph-knowledge | Knowledge Graph |
| 16 | decision-center | Decision Center |
| 17 | revenue-intelligence | Revenue Intel |
| 18 | pipeline-analytics | Pipeline analytics |
| 19 | forecast | Forecast |
| 20 | meeting-intelligence | Meetings |
| 21 | ai-prompt-registry | AI |
| 22 | analytics | Analytics |
| 23 | rules-engine | Rules |
| 24 | signal-marketplace | Signals |
| 25 | copilot-page | Copilot |
| 26 | analytics-data | Analytics data |
| **Total** | **26 specs** | **14+ critical paths** |

---

## 15. CI/CD Pipeline

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Main CI — tests, lint, build |
| `deploy-production.yml` | Production deployment |
| `deploy-staging.yml` | Staging deployment |
| `deploy.yml` | Deployment orchestration |
| `docker-smoke.yml` | Docker smoke tests |
| `security-scan.yml` | Trivy, Bandit, Semgrep |

---

## 16. Configuration & Build

| File | Type |
|------|------|
| `pyproject.toml` | Python dependencies + coverage |
| `package.json` | NPM workspace root |
| `next.config.js` | Next.js configuration |
| `tailwind.config.ts` | Tailwind + MUHIDE palette |
| `tsconfig.json` | TypeScript configuration |
| `jest.config.js` | Jest configuration |
| `playwright.config.ts` | Playwright (4 projects) |
| `eslint.config.mjs` | ESLint configuration |
| `postcss.config.js` | PostCSS configuration |
| `alembic.ini` | Alembic configuration |

---

## 17. Infrastructure

| Component | Configuration |
|-----------|--------------|
| Docker Compose | `docker-compose.yml` (dev), `.prod.yml`, `.test.yml` |
| Dockerfiles | `Dockerfile` (frontend), `Dockerfile.backend` (backend) |
| Nginx | `frontend/nginx.conf` |
| PostgreSQL | asyncpg, pg_trgm, pgvector |
| Neo4j | Connection pool with context managers |
| Redis | Configured but inactive (in-memory fallback) |
| Kafka | Configured but inactive (in-memory EventBus) |
| Celery | Configured in docker-compose |

---

## 18. Documentation Inventory

| Location | Count | Types |
|----------|-------|-------|
| `salesos/docs/` | 44 files | Architecture, guides, reports, playbooks |
| `salesos/docs/portal/` | 62 files | API portal, architecture, deployment, SDK |
| `salesos/docs/portal/api/` | API docs | Per-domain API documentation |
| `docs/` (root) | 20+ files | Blueprint, Bible, Domain Map, Audit |
| `docs/vnext/` | 10+ files | Strategy, roadmap, sprint plan, risk |
| `docs/vnext/work-orders/` | 25 files | Implementation work orders |
| `docs/adr/` | 2 files | Product ADRs (0030, 0031) |
| `engineering-os/adr/` | 4 files | Platform ADRs (001, 002, 003, 0032) |
| `engineering-os/` | 12 files | Constitution, Dashboard, Spec, References |

---

## 19. Total Architecture Inventory

| Category | Count |
|----------|-------|
| Backend domains | 17 |
| App modules | 24 |
| API routers | 18+ |
| Backend SDK modules | 18 |
| Alembic migrations | 37 |
| SQL migrations | 6 |
| Intelligence modules | 20 |
| Runtime files | 3 (core) |
| Frontend features | 13 |
| Frontend packages | 13 |
| Frontend app route segments | 28+ |
| Frontend application files | 39 |
| Frontend component files | 12+ |
| Frontend foundation components | 22 |
| E2E tests | 26 specs |
| Unit/Integration tests | 539 test files |
| CI/CD workflows | 6 |
| Docker configurations | 3 |
| ADRs | 8 total (4 platform + 4 product) |
| Documentation | 100+ files |
| Work orders | 25 |
