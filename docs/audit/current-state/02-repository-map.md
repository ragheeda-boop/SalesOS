# Repository Map — SalesOS Engineering Audit

> Generated: 2026-07-15
> Scope: Full monorepo at `C:\Users\raghe\OneDrive - RATL Technology Ltd\Muhide`

---

## 1. Top-Level Repository Layout

```
Muhide/                                    ← Monorepo root
├── salesos/                               ★ PRIMARY PRODUCT — Enterprise Company Intelligence Platform
├── engineering-os/                        Engineering OS governance kernel (submodule)
├── engineering-recovery/                  Incident post-mortem documents (3 files)
├── sales-os/                              Legacy/standalone Python scripts (CRM pipeline, Notion sync)
├── docs/                                  Audit reports, architecture docs, domain maps
│   └── audit/                             16-part audit series + current-state/ + execution/
├── WidgetTemplate/                        Reference widget template (Container/View pattern)
├── open-design/                           Placeholder (empty — only node_modules)
├── balady_scraper/                        Legacy scraper: Balady municipality data
├── najiz_scraper/                         Legacy scraper: Najiz judicial data
├── rega_scraper/                          Legacy scraper: Rega data
├── taqeem_scraper/                        Legacy scraper: Taqeem facilities data
├── output/                                Generated reports and output files
├── docker-compose.yml                     Root-level compose (likely superseded by salesos/)
├── opencode.json                          AI agent config (references engineering-os/)
├── SALESOS_*.md                           High-level audit & roadmap documents (7 files)
├── *.py                                   Standalone Python scripts (batch processing, enrichment)
└── *.pptx                                 Pitch decks (MUHIDE v1/v2/v3)
```

---

## 2. `salesos/` — Primary Product (The Platform)

**Purpose:** Enterprise AI-native platform for company intelligence, CRM, data enrichment, and marketplace capabilities. Built for Saudi Arabian market, designed for global expansion.

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 (backend) | Next.js 15 + React 19 + Tailwind CSS 4 (frontend) | PostgreSQL 16 + pgvector + pg_trgm | Neo4j 5.x | Kafka | Redis 7 | Docker + K8s + Terraform (AWS)

**Version:** v2.0.0 (GA target: 2026-08-15)

**Total Tests:** 2110+ (100% pass rate)

### 2.1 `salesos/backend/` — Python Backend

**Owner:** Backend Engineering Team
**Framework:** FastAPI + Uvicorn
**Package Manager:** Poetry (pyproject.toml)

#### 2.1.1 `backend/app/` — FastAPI Application Core

| Directory/File | Purpose | Owner | Status |
|---|---|---|---|
| `main.py` | FastAPI app factory, lifespan, middleware stack, router mounting | Backend | Active |
| `config.py` | Pydantic Settings — all env vars (DB, Neo4j, Kafka, Redis, JWT, OpenAI) | Backend | Active |
| `database.py` | Async SQLAlchemy engine + session factory | Backend | Active |
| `dependencies.py` | FastAPI dependency injection (auth, DB session) | Backend | Active |
| `celery_app.py` | Celery worker config for async tasks | Backend | Active |
| `tasks.py` | Celery task definitions | Backend | Active |
| `cache.py` | Redis cache service layer | Backend | Active |
| `app/routers/` | **18 HTTP routers** — AI, analytics, benchmarks, commercial, copilot, demo, enrichment, mcp, meetings, metrics, notifications, opportunities, rag, revenue, search, workflows, admin_demo | Backend | Active |
| `app/common/` | **13 shared modules** — middleware (CSRF, rate limit, security headers, request logging), models, schemas, validation, logging, metrics, cache, redis, exceptions, API key manager | Backend | Active |
| `app/modules/` | **26 feature modules** — See §2.1.3 below | Backend | Active |
| `app/graphql/` | GraphQL API — schema, query, mutation, types (Strawberry) | Backend | Active |
| `app/metrics/` | Prometheus metrics collector + SLA monitor | Backend | Active |
| `app/application/` | Application-layer services (admin, dashboard) | Backend | Active |
| `app/alembic/` | Alembic migration runner | Backend | Active |

#### 2.1.2 `backend/app/modules/` — Feature Modules (26 modules)

| Module | Purpose | Dependencies |
|---|---|---|
| `identity/` | Authentication, users, tenants, RBAC | SDK (permissions, audit), PostgreSQL |
| `company/` | Company CRUD, branches, licenses, contacts | PostgreSQL, Entity Resolution |
| `contact/` | Contact management | PostgreSQL |
| `search/` | Hybrid Search (full-text + semantic + RRF) | PostgreSQL (GIN + pgvector) |
| `entity_resolution/` | Fuzzy matching + merge (pg_trgm) | PostgreSQL |
| `feature_store/` | Feature computation + caching | PostgreSQL, Redis |
| `revenue_execution/` | Opportunities, Pipeline, NBA, Goals | Decision Engine |
| `decision/` | Decision engine integration | Scoring Engine |
| `rules_engine/` | Business rules CRUD and evaluation | PostgreSQL |
| `signal_marketplace/` | Third-party data signals marketplace | Event Bus |
| `monitoring/` | System monitoring dashboards | Prometheus metrics |
| `admin/` | Admin panel functionality | Identity module |
| `audit/` | Audit trail logging | SDK (audit) |
| `api_keys/` | API key management | Identity module |
| `cache/` | Module-level caching | Redis |
| `demo_mode/` | Demo mode toggle | None (isolated) |
| `employee_360/` | Employee intelligence 360 view | Scoring, Analytics |
| `executive/` | Executive dashboard services | Analytics, Revenue |
| `excel_import/` | Excel file import/parsing | Company module |
| `notion_sync/` | Notion integration sync | Notion API |
| `sso/` | Single Sign-On (SAML/OIDC) | Identity module |
| `telemetry/` | OpenTelemetry integration | OTel SDK |
| `tenant/` | Multi-tenant isolation | PostgreSQL |
| `webhooks/` | Outbound webhook management | Event Bus |
| `work_intelligence/` | Work intelligence features | Analytics |
| `customer_success/` | Customer success metrics | Analytics |

#### 2.1.3 `backend/domains/` — Domain-Driven Design Layer (15 domains)

| Domain | Purpose | Key Files | Status |
|---|---|---|---|
| `ai/` | Prompt registry, AI service, evaluator, models | `registry.py`, `service.py`, `evaluator.py`, `models.py` | Active |
| `analytics/` | OLAP cubes, analytics engine, templates | `engine.py`, `cubes.py`, `repository.py`, `templates.py` | Active |
| `commercial/` | Full commercial lifecycle: activity, contract, email, meeting, opportunity, pipeline, playbook, proposal, quote | 12 subdirectories | Active |
| `decision/` | Decision context + recommendation engine | `context/`, `recommendation/` | Active |
| `feature_store/` | Feature computation, caching, versioning | `service.py`, `postgres_repo.py`, `models.py`, `infrastructure.py` | Active |
| `notifications/` | Notification domain models + DB | `db_models.py`, `postgres_repo.py` | Active |
| `rag/` | RAG domain models | `models.py` | Active |
| `revenue/` | Revenue analytics + forecasting | `analytics/`, `forecast/` | Active |
| `scoring/` | Scoring engine + infrastructure | `engine.py`, `infrastructure/`, `models.py` | Active |
| `search/` | Search contracts, engine, normalization, ranking, repositories | Full DDD structure | Active |
| `timeline/` | Timeline engine, contracts, router, service | `engine/`, `contracts/`, `router.py`, `service.py` | Active |
| `ubom/` | Use-Case Bill of Materials | `__init__.py` only | **Placeholder** |
| `workflow/` | Workflow engine, templates, event subscriber | `engine.py`, `service.py`, `templates.py`, `postgres_repo.py` | Active |

#### 2.1.4 `backend/runtime/` — Runtime Engine Layer (31 runtimes)

| Runtime | Purpose | Has Router | Status |
|---|---|---|---|
| `search_runtime/` | Search execution runtime | Yes | Active |
| `decision_runtime/` | Decision engine + feedback loop + registry | Yes | Active |
| `timeline_runtime/` | Timeline event execution | Yes | Active |
| `workflow_runtime/` | Workflow execution | No (stub) | **Placeholder** |
| `feature_store/` | Feature computation at runtime | Yes | Active |
| `nba_engine/` | Next-Best-Action engine (API + engine + subscribers) | Yes (via api/) | Active |
| `knowledge_graph_runtime/` | Neo4j graph traversal | Yes | Active |
| `data_fabric_runtime/` | Data pipeline orchestration + master data + scrapers | Yes | Active |
| `event_runtime/` | Event bus runtime (in-memory + Kafka) | Yes | Active |
| `agent_runtime/` | AI agent execution | No (stub) | **Placeholder** |
| `policy_runtime/` | Policy enforcement | No (stub) | **Placeholder** |
| `context_runtime/` | Request context builder | No (stub) | **Placeholder** |
| `activity_runtime/` | Activity tracking runtime | Yes | Active |
| `action_engine/` | Action execution engine | Yes | Active |
| `capability_framework/` | Capability registry + execution | Yes | Active |
| `pipeline_analytics/` | Pipeline analytics runtime | Yes | Active |
| `recommendation_runtime/` | Recommendation engine | No (stub) | **Placeholder** |
| `memory_runtime/` | Memory/context persistence | No (stub) | **Placeholder** |
| `execution_runtime/` | Generic execution runtime | No (stub) | **Placeholder** |
| `form_engine/` | Dynamic form rendering | Yes | Active |
| `ui_schema_engine/` | UI schema generation | Yes | Active |
| `ux_runtime/` | UX runtime | Yes | Active |
| `widget_engine/` | Widget lifecycle management | No (stub) | **Placeholder** |
| `plugin_sandbox/` | Plugin isolation sandbox | Yes | Active |
| `extension_api/` | Extension API endpoints | Yes | Active |
| `scheduler_runtime/` | Job scheduling | No (stub) | **Placeholder** |
| `simulation_runtime/` | Simulation engine | No (stub) | **Placeholder** |
| `admin_router.py` | Admin API endpoints | Yes | Active |
| `object_viewer.py` | Generic object viewer | Yes | Active |

#### 2.1.5 `backend/sdk/` — Platform SDK (30 modules)

| Module | Purpose | Status |
|---|---|---|
| `permissions.py` | RBAC permission registry + role enforcement | Active |
| `audit.py` | Audit trail SDK | Active |
| `telemetry.py` | OpenTelemetry structured logger | Active |
| `events/` | Event system: base, bus, DLQ, Kafka bus/consumer/producer, outbox, schema registry, topic mapping | Active |
| `repositories/` | Repository pattern base (`in_memory_base.py`) | Active |
| `cache/` | Cache abstraction | Active |
| `vector.py` | Vector embedding service (OpenAI) | Active |
| `search.py` | Search SDK | Active |
| `graph.py` | Graph DB SDK (Neo4j) | Active |
| `database.py` | Database SDK | Active |
| `config.py` | SDK configuration | Active |
| `metadata.py` | Metadata management | Active |
| `pagination.py` | Keyset pagination | Active |
| `security.py` | Security utilities | Active |
| `queue.py` | Queue abstraction | Active |
| `exceptions.py` | Exception hierarchy | Active |
| `capability_registry.py` | Capability registration | Active |
| `feature_registry.py` | Feature flag registration | Active |
| `widget_sdk/` | Widget SDK (Container/View pattern) | **Frozen v1.0** |
| `plugin_sdk/` | Plugin SDK | Frozen |
| `frontend_sdk/` | Frontend SDK bridge | Frozen |
| `backend_sdk/` | Backend SDK utilities | Frozen |
| `theme_sdk/` | Theme/styling SDK | Frozen |
| `agent_sdk/` | AI agent SDK | Frozen |
| `company_sdk/` | Company domain SDK | Frozen |
| `commercial/` | Commercial SDK | Frozen |
| `integration_sdk/` | External integration SDK | Frozen |
| `scoring/` | Scoring SDK | Frozen |

#### 2.1.6 `backend/intelligence/` — AI/Intelligence Layer (25 modules)

| Module | Purpose | Status |
|---|---|---|
| `agent_base.py` | Base class for all AI agents | Active |
| `agents/` | **16 specialized agents** — base, competitor, contract, coordinator, forecast, LLM, meeting, news, pricing, proposal, relationship, renewal, research, tender | Active |
| `arabic/` | Arabic NLP pipeline (tokenization, NER, sentiment) | Active |
| `business_objects/` | Business object definitions | Active |
| `company/` | Company intelligence | Placeholder |
| `cost_tracker.py` | AI token cost tracking | Active |
| `data_fabric/` | Data fabric: connectors, entity matching, identity resolution, quality | Active |
| `digital_twin/` | Digital twin simulation (company twin) | Active |
| `enrichment/` | Data enrichment (placeholder) | **Placeholder** |
| `evaluation/` | AI evaluation runner + test cases | Active |
| `graph/` | Graph intelligence | Placeholder |
| `grounding.py` | AI grounding/context | Active |
| `guardrails.py` | AI safety guardrails | Active |
| `market/` | Market intelligence | Placeholder |
| `notifications/` | Intelligence notifications | Placeholder |
| `prompts/` | Prompt registry (YAML-based) | Active |
| `providers/` | LLM provider abstraction (OpenAI, factory) | Active |
| `rag/` | RAG pipeline: chunking, embeddings, retrieval, service | Active |
| `reasoning.py` | Chain-of-thought reasoning | Active |
| `revenue_brain/` | Revenue intelligence brain | Placeholder |
| `schemas.py` | Intelligence schemas | Active |
| `signals/` | Signal processing (placeholder) | **Placeholder** |
| `simulation/` | Scenario simulation | Active |

#### 2.1.7 `backend/tests/` — Test Suite

| Directory | Count | Purpose |
|---|---|---|
| `tests/unit/` | 49 test files | Unit tests for all modules |
| `tests/integration/` | 11 test files | DB integration, migration, search tests |
| `tests/e2e/` | 18 test files | End-to-end critical path tests |
| `tests/evaluation/` | — | AI evaluation tests |
| `tests/conftest.py` | — | Shared fixtures (DB engine, session, permissions) |
| `tests/fakes.py` | — | Fake/stub implementations |
| `tests/test_architecture.py` | — | Architecture compliance tests |
| `tests/test_health.py` | — | Health check tests |

#### 2.1.8 Other Backend Directories

| Directory | Purpose | Status |
|---|---|---|
| `backend/migrations/` | SQL migration files + Alembic versions | Active |
| `backend/modules/` | Module registry (registration at startup) | Active |
| `backend/pipeline/` | Data pipeline: Excel utils, Notion sync, validation engine | Active |
| `backend/mcp_server/` | MCP server: tools, resources, SalesOS client | Active |
| `backend/benchmark/` | Performance benchmarking | Active |
| `backend/benchmarks/` | Benchmark results | Active |
| `backend/demo/` | Demo mode data | Active |
| `backend/design_tokens/` | Design token definitions | Active |
| `backend/docs/` | Backend-specific documentation | Active |

---

### 2.2 `salesos/frontend/` — Next.js Frontend

**Owner:** Frontend Engineering Team
**Framework:** Next.js 15 + React 19
**Package Manager:** npm (workspaces)
**Version:** 5.0.0

#### 2.2.1 `frontend/src/` — Application Source

| Directory | Purpose | Key Files |
|---|---|---|
| `src/app/` | Next.js App Router pages | `layout.tsx`, `page.tsx`, `providers.tsx`, `globals.css` |
| `src/app/(auth)/` | Auth pages: `login/`, `register/` | Auth flow |
| `src/app/(dashboard)/` | **27 dashboard routes** — activities, admin, ai, analytics, automation, companies, contacts, copilot, customer-success, decisions, employees, forecast, graph, meetings, monitoring, opportunities, pipeline, rag, revenue, rules, search, settings, signals | All dashboard pages |
| `src/components/` | Shared UI components | See §2.2.2 |
| `src/features/` | Feature modules (Container/View pattern) | See §2.2.3 |
| `src/lib/` | Utilities, API client, hooks, i18n | See §2.2.4 |
| `src/application/` | Application-layer services | `api/`, `company-intelligence/`, `dashboard/`, `revenue-execution/`, `search/` |
| `src/mocks/` | MSW mock handlers | Test infrastructure |

#### 2.2.2 `frontend/src/components/` — Shared Components

| Component | Purpose |
|---|---|
| `foundation/` | App shell, card, error boundary, language switcher, mobile nav |
| `guidance/` | Coach marks, empty states, onboarding, tours |
| `layout/` | Layout components (empty) |
| `command-bar.tsx` | Command palette (Cmd+K) |
| `company-workspace.tsx` | Company 360 workspace |
| `copilot-panel.tsx` | AI copilot side panel |
| `employee-360-view.tsx` | Employee intelligence view |
| `executive-dashboard.tsx` | Executive dashboard |
| `pipeline-kanban.tsx` | Pipeline kanban board |
| `search-panel.tsx` | Search panel |
| `timeline-widget.tsx` | Timeline widget |
| `skeleton.tsx` | Loading skeleton |

#### 2.2.3 `frontend/src/features/` — Feature Modules (13 features)

| Feature | Components | Pattern | Status |
|---|---|---|---|
| `dashboard/` | Widget registry, SDK, workspace adapter, hooks, providers, telemetry | Container/View + SDK | Active |
| `search/` | AI search, command bar, quick overlay, search page | Container/View | Active |
| `company-intelligence/` | Widgets, registry, providers | Container/View | Active |
| `revenue-execution/` | Widgets, workspace, registry, providers | Container/View | Active |
| `analytics/` | AnalyticsContainer, AnalyticsView, AnalyticsWorkspace, FeedbackWidget | Container/View | Active |
| `employee-intelligence/` | Widgets, workspace, providers | Container/View | Active |
| `admin/` | AdminWorkspace, widgets | Container/View | Active |
| `automation/` | Widgets, workspace | Container/View | Active |
| `customer-success/` | Widgets, workspace | Container/View | Active |
| `rag/` | Widgets, workspace | Container/View | Active |
| `rules/` | RulesWorkspace | Single file | Active |
| `monitoring/` | MonitoringWidget | Single file | Active |
| `demo/` | DemoBadge, DemoResetButton, ScenarioLauncher | Utility | Active |

#### 2.2.4 `frontend/src/lib/` — Utilities & API Layer

| File/Dir | Purpose |
|---|---|
| `api/client.ts` | HTTP client (Axios) |
| `api/types.ts` | API type definitions |
| `hooks/` | **15 query/mutation hooks** — company, contact, employee, executive, opportunity, search, task, activity, admin, rule, tenant, unified search, focus trap |
| `i18n/` | Internationalization (Arabic + English) |
| `analytics.ts` | Analytics tracking |
| `commands.ts` | Command definitions |
| `dynamic-imports.tsx` | Lazy loading |
| `monitoring.ts` | Frontend monitoring |
| `queryKeys.ts` | React Query cache keys |
| `utils.ts` | General utilities |

#### 2.2.5 `frontend/packages/` — Monorepo Packages (13 packages)

| Package | Purpose | Status |
|---|---|---|
| `@salesos/ui` | Base UI component library | Active |
| `@salesos/design-language` | Design tokens + MUHIDE palette | **Frozen** |
| `@salesos/platform` | Platform kernel: agents, contracts, decision, shared, testing | Active |
| `@salesos/runtime` | Frontend runtime layer | Active |
| `@salesos/workspace` | Workspace components | Active |
| `@salesos/hooks` | Shared React hooks | Active |
| `@salesos/forms` | Form components + validation | Active |
| `@salesos/charts` | Chart components | Active |
| `@salesos/icons` | Icon library | Active |
| `@salesos/search` | Search components | Active |
| `@salesos/renderer` | Widget renderer | Active |
| `@salesos/config` | Shared configuration | Active |
| `@salesos/workspace-generator` | Workspace scaffolding tool | Active |

#### 2.2.6 `frontend/apps/` — Application Shells (4 apps)

| App | Status | Notes |
|---|---|---|
| `command-center/` | **Empty** | Placeholder |
| `company-workspace/` | **Empty** | Placeholder |
| `copilot/` | **Empty** | Placeholder |
| `search/` | **Empty** | Placeholder |

#### 2.2.7 Other Frontend Directories

| Directory | Purpose | Status |
|---|---|---|
| `e2e/` | **26 Playwright spec files** + global setup/teardown | Active |
| `server/` | Custom Next.js server (`server.js`) | Active |
| `public/` | Static assets | Active |
| `coverage/` | Test coverage reports | Generated |
| `playwright-report/` | E2E test reports | Generated |
| `test-results/` | E2E test results | Generated |

---

### 2.3 `salesos/packages/` — Backend Shared Packages

| Package | Purpose | Status |
|---|---|---|
| `platform/agents/` | Agent contracts and orchestration | Active |
| `platform/decision/` | Decision platform contracts | Active |
| `plugin-sdk/` | Plugin SDK (npm package) | Active |

---

### 2.4 `salesos/infra/` — Infrastructure

**Owner:** DevOps / Platform Engineering

| Directory | Purpose | Key Files |
|---|---|---|
| `docker/` | Docker configs: backup/, monitoring/, postgres/ (init scripts) | DB init, monitoring |
| `k8s/` | **43 Kubernetes manifests** — namespace, backend/frontend deployments, Postgres, Neo4j, Redis, Kafka, Prometheus, Grafana, Alertmanager, network policies, PDB, resource quotas, HPA, secrets, backup/restore cronjobs | Full K8s stack |
| `terraform/` | IaC: `main.tf`, `variables.tf`, `outputs.tf` (AWS) | Cloud provisioning |
| `monitoring/` | Prometheus config, Alertmanager config, Grafana dashboards, alerting rules (staging + production) | Observability |
| `staging/` | `docker-compose.staging.yml` | Staging environment |
| `scripts/` | 5 ops scripts: backup-db.sh, backup-neo4j.sh, cron-backup.sh, deploy.sh, restore-db.sh | Automation |
| `caddy/` | `Caddyfile` — reverse proxy config | Edge |
| `README.md` | Infrastructure documentation | Docs |

---

### 2.5 `salesos/docs/` — Documentation (47 files)

| Category | Key Files |
|---|---|
| **Architecture** | `ARCHITECTURE_BOOK.md`, `SALESOS_DOMAIN_DRIVEN_DESIGN.md`, `DECISION_PLATFORM_*.md` (6 files) |
| **Operations** | `production_runbook.md`, `ONCALL_RUNBOOK.md`, `INCIDENT_RESPONSE_PLAN.md`, `sla.md` |
| **Deployment** | `deployment_guide.md`, `GA_LAUNCH_PLAN.md`, `GA_DASHBOARD.md`, `DOCKER_VALIDATION_REPORT.md` |
| **Security** | `FINAL_SECURITY_REPORT.md`, `security_sweep_report.md`, `BRANCH_PROTECTION.md` |
| **Performance** | `FINAL_PERFORMANCE_REPORT.md`, `PERFORMANCE_OPTIMIZATION_REPORT.md`, `LOAD_TEST_REPORT_TEMPLATE.md` |
| **Pilot** | `PILOT_LAUNCH_CHECKLIST.md`, `PILOT_LAUNCH_REPORT.md`, `PILOT_*_GUIDE.md` (3 files) |
| **Widget** | `WIDGET_MIGRATION_GUIDE.md` |
| **API** | `portal/` — API portal docs |
| **Compliance** | `ARCHITECTURE_COMPLIANCE.md` |
| **Wave docs** | `wave-2/`, `wave-3/` — feature wave specs |
| **Releases** | `releases/` — release-specific docs |
| **Hiring** | `hiring/` — hiring playbooks |
| **Pentest** | `pentest/` — penetration test reports |

---

### 2.6 `salesos/scripts/` — Operations Scripts (26 files)

| Script | Purpose | Category |
|---|---|---|
| `arch-compliance.ps1` | Architecture compliance scanner | Governance |
| `audit-migrations.ps1` | Migration audit | Database |
| `backup.ps1` | Database backup | Operations |
| `check-coverage.ps1` | Test coverage check | Quality |
| `check-performance.ps1` | Performance benchmarking | Quality |
| `docker-smoke.ps1` | Docker smoke test | DevOps |
| `load-test.py` | HTTP load testing | Performance |
| `load-test-comprehensive.py` | Comprehensive load test | Performance |
| `soak-test.py` | Soak testing | Performance |
| `stress-test.py` | Stress testing | Performance |
| `neo4j-backup.ps1` | Neo4j backup | Operations |
| `neo4j-recover.ps1` | Neo4j recovery | Operations |
| `pilot-metrics.ps1` | Pilot metrics collection | Pilot |
| `pilot-onboard.ps1` | Pilot onboarding | Pilot |
| `pilot-verify.ps1` | Pilot verification | Pilot |
| `provision-pilot-tenants.ps1` | Tenant provisioning | Pilot |
| `restore-test.ps1` / `.sh` | Restore testing | Operations |
| `sbom.ps1` | Software Bill of Materials | Security |
| `scan-deps.ps1` | Dependency scanning | Security |
| `security-audit.ps1` | Security audit | Security |
| `seed-pilot-data.ps1` | Pilot data seeding | Pilot |
| `smoke-test.ps1` | Smoke testing | Quality |
| `update-deps.sh` | Dependency updates | Maintenance |
| `verify-backup.ps1` | Backup verification | Operations |
| `verify-pilot-deployment.ps1` | Pilot deployment verification | Pilot |

---

### 2.7 `salesos/platform/` — Platform Governance Documents

| File | Purpose | Status |
|---|---|---|
| `CONSTITUTION.md` | 10 Article Platform Constitution (Replaceability, SDK Sovereignty, Domain Events, Testability, Measurement, Evidence, Frozen Interface, Business Over Technology, Microservice Isolation, Data Sovereignty) | Active |
| `OPERATING_SYSTEM.md` | Company operating system: mission, thesis, EPC framework, release policy | Active |
| `ROADMAP.md` | Product roadmap | Active |
| `PHASES.md` | Development phases | Active |
| `CUSTOMER_OUTCOMES.md` | Customer outcome definitions | Active |
| `ARB-001.md` | Architecture Review Board decision | Active |
| `EPC-001.md` | Evidence, Product, Customer decision | Active |
| `HN-001.md` | Decision record | Active |
| `LR-001.md` | Decision record | Active |

---

### 2.8 `salesos/application/` — Application Layer

| Directory | Purpose | Status |
|---|---|---|
| `dashboard/` | Dashboard application shell | Active |

---

### 2.9 `salesos/knowledge-packs/` — Domain Knowledge (10 packs)

| Pack | Contents | Status |
|---|---|---|
| `construction/` | features/, prompts/, scoring/, signals/, manifest.json | Active |
| `healthcare/` | features/, prompts/, scoring/, signals/, manifest.json | Active |
| `financial-services/` | features/, prompts/, scoring/, signals/, manifest.json | Active |
| `arabic-business-terms/` | README only | **Placeholder** |
| `saudi-market/` | README only | **Placeholder** |
| `nba-best-practices/` | README only | **Placeholder** |
| `prompt-engineering/` | README only | **Placeholder** |
| `rag-optimization/` | README only | **Placeholder** |
| `enrichment-sources/` | README only | **Placeholder** |
| `tests/` | `test_knowledge_packs.py` | Active |

---

### 2.10 `salesos/reports/` — Generated Reports (9 files)

| File | Purpose |
|---|---|
| `arch-compliance-report.json` | Architecture compliance scan results |
| `benchmark_100.json` / `.md` | Benchmark at 100 companies |
| `benchmark_full.json` / `.md` | Full benchmark |
| `benchmark_optimized.json` / `.md` | Optimized benchmark |
| `smoke_test.json` / `.md` | Smoke test results |

---

### 2.11 `salesos/memory/` — Engineering Memory

| File | Purpose | Status |
|---|---|---|
| `technical-debt.md` | Technical debt register | Active |

---

### 2.12 `salesos/cli/` — CLI Tool

| File | Purpose | Status |
|---|---|---|
| `__main__.py` | CLI entry point | Active |
| `generator.py` | Code generation utility | Active |

---

### 2.13 `salesos/.github/workflows/` — CI/CD (6 workflows)

| Workflow | Purpose | Trigger |
|---|---|---|
| `ci.yml` | Main CI pipeline | Push/PR |
| `deploy.yml` | General deploy | Manual |
| `deploy-staging.yml` | Staging deployment | Manual |
| `deploy-production.yml` | Production deployment | Manual |
| `docker-smoke.yml` | Docker smoke test | On build |
| `security-scan.yml` | Trivy + Bandit + Semgrep | On build |

---

### 2.14 `salesos/` — Root Configuration Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Dev environment: Postgres, PgBouncer, Neo4j, Redis, Backend, Frontend |
| `docker-compose.prod.yml` | Production compose |
| `docker-compose.test.yml` | Test compose |
| `Makefile` | 30+ make targets (dev, test, lint, migrate, deploy, backup, etc.) |
| `CHANGELOG.md` | Version history (v1.6.0 → v2.0.0 GA) |
| `README.md` | Project overview, architecture diagram, tech stack, API reference |
| `RELEASE_GATES.md` | Release gate checklist |
| `PERFORMANCE_BASELINE.md` | Performance baseline metrics |
| `REVENUE_EXECUTION_BIBLE.md` | Revenue execution domain bible |
| `SLA_CONFIG.json` | SLA configuration |
| `.env` / `.env.example` / `.env.staging` / `.env.production` | Environment configs |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.gitignore` | Git ignore rules |
| `setup.ps1` | Windows setup script |
| `start.bat` / `start.sh` | Quick start scripts |

---

## 3. Supporting Repositories (Outside `salesos/`)

### 3.1 `engineering-os/` — Engineering Governance Kernel

**Purpose:** Shared governance: constitution, sprint gates, kernel specs, agent registry, memory, rules, skills.
**Owner:** Architecture / CTO
**Status:** Active (submodule reference)

| Directory/File | Purpose |
|---|---|
| `ENGINEERING_CONSTITUTION.md` | 8-article engineering constitution (quality, testing, architecture, security, documentation, release, data, widgets) |
| `ENGINEERING_DASHBOARD.md` | Production readiness dashboard (all metrics) |
| `kernel/` | Capability registry, sprint planner, decision engine |
| `governance/` | Governance rules and processes |
| `adr/` | Architecture Decision Records |
| `.opencode/` | AI agent configuration |
| `opencode.json` | Agent config (references salesos/) |
| `REFERENCES.md` | Cross-repo reference map |
| `RUNBOOK.md` | Operations runbook |
| `SPRINT_GATES.md` | Sprint gate definitions |

### 3.2 `engineering-recovery/` — Incident Recovery

**Purpose:** Post-mortem and recovery documents.
**Status:** Historical (3 files: inventory, verification, root-cause)

### 3.3 `sales-os/` — Legacy Scripts

**Purpose:** Standalone Python scripts for CRM pipeline, Notion sync, dedup scanning.
**Status:** **Deprecated** — superseded by `salesos/` platform

| File | Purpose |
|---|---|
| `main.py` | Entry point |
| `config.py` | Configuration |
| `notion_api.py` | Notion API client |
| `completeness_scorer.py` | Data completeness scoring |
| `dedup_scanner.py` | Deduplication scanner |
| `priority_assigner.py` | Priority assignment |
| `sfda_sync_checker.py` | SFDA sync checking |
| `stale_detector.py` | Stale data detection |
| `run_on_suppliers.py` | Supplier data processing |

### 3.4 `docs/audit/` — Engineering Audit (16-part series)

**Purpose:** Comprehensive architecture and engineering audit of the SalesOS platform.

| Part | Topic |
|---|---|
| `00-salesos-knowledge-base.md` | Knowledge base |
| `01-cto-assessment.md` | CTO assessment |
| `02-repository-map.md` | **← This document** |
| `03-product-architecture.md` | Product architecture |
| `04-ux-architecture.md` | UX architecture |
| `05-design-system.md` | Design system |
| `06-frontend-architecture.md` | Frontend architecture |
| `07-backend-architecture.md` | Backend architecture |
| `08-database-architecture.md` | Database architecture |
| `09-ai-architecture.md` | AI architecture |
| `10-devops-architecture.md` | DevOps architecture |
| `11-security-architecture.md` | Security architecture |
| `12-qa-architecture.md` | QA architecture |
| `13-performance-architecture.md` | Performance architecture |
| `14-business-logic.md` | Business logic |
| `15-cross-validation.md` | Cross-validation |

### 3.5 Root-Level Supporting Files

| Directory/File | Purpose | Status |
|---|---|---|
| `WidgetTemplate/` | Reference widget template (Container/View) | Active |
| `open-design/` | Empty placeholder (only node_modules) | **Dead** |
| `balady_scraper/` | Balady municipality scraper | Legacy |
| `najiz_scraper/` | Najiz judicial scraper | Legacy |
| `rega_scraper/` | Rega scraper | Legacy |
| `taqeem_scraper/` | Taqeem facilities scraper | Legacy |
| `output/` | Generated report artifacts | Generated |

---

## 4. Dependency Tree

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY TREE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  engineering-os/ (governance)                                        │
│  ├── ENGINEERING_CONSTITUTION.md  ← Rules for ALL code               │
│  ├── kernel/  ← Sprint planner, capability registry                  │
│  └── opencode.json  ← Agent config → references salesos/            │
│                                                                      │
│  salesos/  (PRIMARY PRODUCT)                                         │
│  ├── platform/  (governance docs)                                    │
│  │   └── CONSTITUTION.md  ← 10 articles, governs all domains        │
│  │                                                                    │
│  ├── backend/app/  (FastAPI entrypoint)                              │
│  │   ├── ← imports from: app/common/                                │
│  │   ├── ← imports from: app/modules/                               │
│  │   ├── ← imports from: app/routers/                               │
│  │   ├── ← imports from: runtime/ (all runtime engines)              │
│  │   ├── ← imports from: sdk/ (permissions, audit, events, etc.)    │
│  │   ├── ← imports from: domains/ (domain services)                 │
│  │   └── ← imports from: intelligence/ (AI agents, RAG)             │
│  │                                                                    │
│  ├── backend/sdk/  (Platform SDK)                                    │
│  │   ├── ← standalone (no app/ dependency)                          │
│  │   ├── events/ ← aiokafka, schema registry                        │
│  │   ├── repositories/ ← in-memory base                             │
│  │   ├── widget_sdk/ ← frozen v1.0                                  │
│  │   └── permissions.py ← core auth model                           │
│  │                                                                    │
│  ├── backend/domains/  (DDD layer)                                   │
│  │   ├── ← imports from: sdk/ (repositories, events)                │
│  │   ├── search/ ← PostgreSQL (pg_trgm, pgvector, GIN)             │
│  │   ├── scoring/ ← Feature Store                                   │
│  │   ├── decision/ ← Scoring + Context                              │
│  │   ├── commercial/ ← 12 subdomains                                │
│  │   └── workflow/ ← Event Bus                                      │
│  │                                                                    │
│  ├── backend/runtime/  (Execution layer)                             │
│  │   ├── ← imports from: domains/                                   │
│  │   ├── ← imports from: sdk/                                       │
│  │   ├── ← imports from: intelligence/                              │
│  │   ├── nba_engine/ ← Decision Engine + Feedback Loop              │
│  │   ├── search_runtime/ ← Hybrid Search                            │
│  │   ├── data_fabric_runtime/ ← Entity Resolution + Graph           │
│  │   └── event_runtime/ ← Kafka / In-Memory                         │
│  │                                                                    │
│  ├── backend/intelligence/  (AI layer)                               │
│  │   ├── ← imports from: sdk/ (telemetry, vector)                   │
│  │   ├── agents/ ← 16 specialized AI agents                         │
│  │   ├── rag/ ← chunking + embeddings + retrieval                   │
│  │   ├── arabic/ ← Arabic NLP                                       │
│  │   └── data_fabric/ ← connectors + entity matching                │
│  │                                                                    │
│  ├── backend/tests/  (2110+ tests)                                   │
│  │   ├── unit/ (49 files) ← tests every module                      │
│  │   ├── integration/ (11 files) ← DB + migration tests             │
│  │   └── e2e/ (18 files) ← critical path tests                     │
│  │                                                                    │
│  ├── frontend/src/  (Next.js app)                                    │
│  │   ├── ← imports from: packages/* (all @salesos/* packages)       │
│  │   ├── app/(dashboard)/ ← 27 route groups                         │
│  │   ├── features/ ← 13 feature modules (Container/View)            │
│  │   ├── lib/api/ ← HTTP client → backend API                       │
│  │   └── lib/hooks/ ← 15 query hooks → TanStack Query               │
│  │                                                                    │
│  ├── frontend/packages/  (13 internal packages)                      │
│  │   ├── @salesos/platform ← kernel, agents, decision, contracts    │
│  │   ├── @salesos/ui ← base component library                       │
│  │   ├── @salesos/design-language ← tokens (frozen)                 │
│  │   ├── @salesos/runtime ← frontend runtime                        │
│  │   └── (10 more packages)                                          │
│  │                                                                    │
│  ├── infra/  (Infrastructure)                                        │
│  │   ├── k8s/ → 43 manifests ← Postgres, Neo4j, Redis, Kafka       │
│  │   ├── terraform/ → AWS provisioning                               │
│  │   ├── monitoring/ → Prometheus + Grafana + Alertmanager           │
│  │   └── docker/ → Postgres init, backup, monitoring                │
│  │                                                                    │
│  └── knowledge-packs/  (Domain knowledge)                            │
│      ├── construction/ ← features + prompts + scoring + signals     │
│      ├── healthcare/ ← features + prompts + scoring + signals       │
│      └── financial-services/ ← features + prompts + scoring + signals│
│                                                                      │
│  Root-level files (outside salesos/)                                 │
│  ├── SALESOS_*.md ← High-level audit docs (7 files)                 │
│  ├── docs/audit/ ← 16-part engineering audit                        │
│  ├── WidgetTemplate/ ← Reference widget (Container/View)            │
│  └── sales-os/ ← DEPRECATED legacy scripts                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Cross-Cutting Dependency Summary

```
                    ┌─────────────────────┐
                    │  engineering-os/     │
                    │  (Governance Rules)  │
                    └─────────┬───────────┘
                              │ governs
                              ▼
┌──────────────────────────────────────────────────────────┐
│                    salesos/ (Platform)                    │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐      │
│  │ Frontend  │───►│ Backend  │───►│ Databases    │      │
│  │ Next.js   │    │ FastAPI  │    │ PostgreSQL   │      │
│  │ React 19  │    │ Python   │    │ Neo4j        │      │
│  │ 13 pkgs   │    │ 26 mods  │    │ Redis        │      │
│  └──────────┘    └────┬─────┘    └──────────────┘      │
│                       │                                  │
│            ┌──────────┼──────────┐                      │
│            ▼          ▼          ▼                      │
│     ┌──────────┐ ┌────────┐ ┌───────────┐             │
│     │ Domains  │ │Runtime │ │Intel-     │             │
│     │ 15 DDD   │ │ 31     │ │ligence    │             │
│     │ domains  │ │runtimes│ │25 modules │             │
│     └──────────┘ └────────┘ └───────────┘             │
│                       │                                  │
│                       ▼                                  │
│              ┌────────────────┐                         │
│              │   SDK Layer    │                         │
│              │ 30 modules     │                         │
│              │ (Frozen v1.0)  │                         │
│              └────────────────┘                         │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐            │
│  │ infra/   │  │scripts/  │  │knowledge- │            │
│  │ K8s+Terra│  │ 26 ops   │  │packs      │            │
│  └──────────┘  └──────────┘  └───────────┘            │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Status Summary

### 5.1 Active Components

| Component | Files | Tests | Health |
|---|---|---|---|
| Backend (app/) | ~80 | 2110+ | Healthy |
| Domains (DDD) | ~80 | Per-domain | Healthy |
| Runtime engines | ~60 | Per-runtime | Mostly active |
| SDK | ~50 | 129 widget SDK | Frozen v1.0 |
| Intelligence/AI | ~60 | Per-module | Active |
| Frontend (src/) | ~100 | Jest + Playwright | Healthy |
| Frontend packages | ~80 | Per-package | Healthy |
| Infrastructure | ~60 | Smoke tests | Operational |
| CI/CD | 6 workflows | Automated | Passing |

### 5.2 Placeholder / Stub Components

| Component | Location | Evidence |
|---|---|---|
| `ubom/` domain | `backend/domains/ubom/` | Only `__init__.py` |
| 8 runtime stubs | `agent_runtime`, `policy_runtime`, `context_runtime`, `workflow_runtime`, `memory_runtime`, `execution_runtime`, `scheduler_runtime`, `simulation_runtime` | Only `__init__.py` |
| 4 frontend app shells | `frontend/apps/{command-center,company-workspace,copilot,search}/` | Empty directories |
| 6 knowledge packs | arabic-business-terms, saudi-market, nba-best-practices, prompt-engineering, rag-optimization, enrichment-sources | README only |
| `frontend/components/layout/` | Empty directory |
| `frontend/packages/platform/testing/` | Empty directory |
| Several intelligence modules | company, market, revenue_brain, graph, enrichment, signals | Only `__init__.py` |

### 5.3 Deprecated / Legacy Components

| Component | Location | Replacement |
|---|---|---|
| `sales-os/` | Root-level | `salesos/` platform |
| `balady_scraper/` | Root-level | `backend/intelligence/data_fabric/scrapers/` |
| `najiz_scraper/` | Root-level | `backend/intelligence/data_fabric/scrapers/` |
| `rega_scraper/` | Root-level | `backend/intelligence/data_fabric/scrapers/` |
| `taqeem_scraper/` | Root-level | `backend/intelligence/data_fabric/scrapers/` |
| `open-design/` | Root-level | Dead (empty) |

---

*End of Repository Map*
