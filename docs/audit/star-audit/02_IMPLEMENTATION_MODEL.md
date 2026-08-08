# 02 — IMPLEMENTATION MODEL: What Actually Exists in Code

> Source: Source code analysis (Phase 2)
> Classification: IMPLEMENTATION ONLY

---

## Executive Summary

The SalesOS backend is a **5-layer modular monolith** built with FastAPI, SQLAlchemy 2.x (async), PostgreSQL, and Alembic. The frontend is a **Next.js 15 App Router** application with a 21-package internal monorepo. The codebase is substantial — ~70+ API routers, 33 modules, 19 domains, 31 runtime engines, 28 intelligence packages, and 30 SDK packages.

However, many of these are **scaffolded but not fully implemented**. The core working surface is narrower than the directory tree suggests.

---

## 1. Backend Architecture (What Actually Exists)

### 1.1 Application Layer (`app/`)
- **`main.py`** — FastAPI app factory with 6 health endpoints. Fully implemented.
- **`config.py`** — 100+ Pydantic Settings fields, production-hardened. Fully implemented.
- **`database.py`** — Dual-engine pattern (app role + owner role), ContextVar tenant pinning, bounded timeouts, pool abort. Fully implemented.
- **`dependencies.py`** — JWT verification, tenant resolution, role hierarchy, permission enforcement. Fully implemented.
- **`owner_auth.py`** — Separate audience JWT for Owner Platform. Fully implemented.
- **`boot/startup.py`** — 5-phase parallel startup orchestrator. Fully implemented.
- **`boot/routers.py`** — ~70+ router registrations. Fully implemented.
- **`boot/middleware.py`** — 7 middleware classes registered. Fully implemented.

### 1.2 Security Middleware (`app/common/middleware.py`)
| Middleware | Status |
|-----------|--------|
| `CsrfEnforcementMiddleware` | ✅ Production-grade |
| `SecurityHeadersMiddleware` | ✅ Production-grade (CSP, HSTS, X-Frame-Options) |
| `RateLimitMiddleware` | ✅ Production-grade (Redis-backed + in-memory fallback) |
| `TenantContextMiddleware` | ✅ Production-grade (fail-closed) |
| `BodyCacheMiddleware` | ✅ Production-grade (10MB limit) |
| `RequestIDMiddleware` | ✅ Production-grade |
| `RequestLoggingMiddleware` | ✅ Production-grade |

### 1.3 Identity & Auth (`app/modules/identity/`)
- **RS256 JWT** via JWKS (RSA-4096). ✅ Production-grade.
- **Refresh token rotation** with reuse detection. ✅ Production-grade.
- **Device session management**. ✅ Production-grade.
- **Brute force protection** (5 attempts → 15min lockout). ✅ Production-grade.
- **PDPL right to erasure** (user anonymization). ✅ Production-grade.
- **Token blacklist** (JTI-based revocation). ✅ Production-grade.

### 1.4 RBAC (`sdk/permissions.py`)
- 4 default roles: admin, manager, user/api, auditor
- 7 permission actions: CREATE, READ, UPDATE, DELETE, EXPORT, IMPORT, ADMIN
- 27 registered resources
- `PermissionEnforcer.check()` with proper error handling. ✅ Production-grade.

### 1.5 Entitlements (`app/modules/admin/`)
- `PlanEntitlements` — 4 tiers (free, starter, growth, enterprise)
- Domain gating, quota enforcement, AI model tier ceiling
- `EntitlementMiddleware` — plan-based feature access control. ✅ Production-grade.

### 1.6 Billing
- `SubscriptionService` — CRUD + state machine. ⚠️ Functional but **no Stripe integration**.
- State machine: 5 states, 7 events, 13 valid transitions. ✅ Pure logic, no I/O.
- Stripe webhooks endpoint exists but **no actual Stripe API calls** in service layer.

---

## 2. Domain Layer (What Actually Exists)

| Domain | Status | Notes |
|--------|--------|-------|
| `ai/` | ⚠️ Partial | Evaluator, registry, models exist; service incomplete |
| `analytics/` | ✅ Real | Cubes, engine, repository, templates |
| `commercial/` | ✅ Real | Opportunity, contract, proposal, quote subdomains |
| `copilot/` | ⚠️ Partial | SearchCompaniesTool real; other tools not implemented |
| `decision/` | ⚠️ Partial | Context + recommendation exist; engine incomplete |
| `decision_center/` | ✅ Real | PostgreSQL-backed, CRUD + service |
| `employee/` | ✅ Real | 360, intelligence, webhooks, scoring, signals, tasks |
| `feature_store/` | ✅ Real | PostgreSQL-backed, 7 score computers |
| `marketplace/` | ⚠️ Partial | Models + lifecycle; sandbox + plugins minimal |
| `notifications/` | ⚠️ Partial | DB models + repo; delivery pipeline incomplete |
| `rag/` | ⚠️ Partial | Models exist; pipeline incomplete |
| `revenue/` | ✅ Real | Analytics, forecast, quota, territory subdomains |
| `scoring/` | ✅ Real | Engine + infrastructure |
| `search/` | ✅ Real | Trigram + pgvector, ranking, normalization, caching |
| `timeline/` | ✅ Real | Engine, contracts, models, router |
| `ubom/` | ❌ Empty | Empty `__init__.py` only |
| `workflow/` | ✅ Real | Engine, event subscriber, scheduler, templates |

---

## 3. Runtime Engines (What Actually Exists)

| Engine | Status | Notes |
|--------|--------|-------|
| `event_runtime/` | ✅ Real | In-memory bus; Kafka configured but not primary |
| `feature_store/` | ✅ Real | 7 score computers (ICP, funding, hiring, growth, intent, expansion, revenue) |
| `search_runtime/` | ✅ Real | Multi-executor (trigram, pgvector, Meilisearch) |
| `knowledge_graph_runtime/` | ⚠️ Partial | Neo4j + SQL fallback; Neo4j offline in production |
| `decision_runtime/` | ⚠️ Partial | Engine + feedback loop; widgets incomplete |
| `policy_runtime/` | ⚠️ Partial | Basic engine |
| `recommendation_runtime/` | ⚠️ Partial | Basic engine |
| `context_runtime/` | ⚠️ Partial | Context builder |
| `activity_runtime/` | ✅ Real | Event logging |
| `timeline_runtime/` | ✅ Real | Aggregation |
| `data_fabric_runtime/` | ⚠️ Partial | Scrapers exist (Balady, Taqeem, Najiz, Rega); ETL mock |
| `nba_engine/` | ⚠️ Partial | Basic rule-based; no AI reasoning |
| `pipeline_analytics/` | ✅ Real | Analytics engine |
| `capability_framework/` | ⚠️ Partial | Discovery + planning |
| `workflow_runtime/` | ✅ Real | Execution engine |
| `agent_runtime/` | ❌ Placeholder | String "PLANNED FOR RT3" only |
| `memory_runtime/` | ⚠️ Partial | Basic persistence |
| `simulation_runtime/` | ❌ Placeholder | Minimal |
| `action_engine/` | ⚠️ Partial | Registry + router |
| `form_engine/` | ⚠️ Partial | Dynamic form rendering |
| `ui_schema_engine/` | ⚠️ Partial | UI schema rendering |
| `widget_engine/` | ⚠️ Partial | Widget registry |
| `plugin_sandbox/` | ⚠️ Partial | Sandboxing |
| `extension_api/` | ⚠️ Partial | Extension hooks |
| `ux_runtime/` | ⚠️ Partial | UX runtime + widgets |
| `scheduler_runtime/` | ⚠️ Partial | Task scheduling |

---

## 4. Intelligence Layer (What Actually Exists)

| Package | Status | Notes |
|---------|--------|-------|
| `grounding.py` | ✅ Real | Postgres + Neo4j retrieval, Arabic prompts |
| `guardrails.py` | ✅ Real | Injection protection, PII scrubbing, output validation |
| `reasoning.py` | ⚠️ Partial | Chain-of-thought basic |
| `cost_tracker.py` | ✅ Real | LLM cost tracking |
| `arabic/` | ⚠️ Partial | Normalization exists; full NLP incomplete |
| `providers/` | ⚠️ Partial | OpenAI only; Anthropic planned |
| `rag/` | ⚠️ Partial | Pipeline exists |
| `prompts/` | ⚠️ Partial | Templates exist |
| `agents/` | ❌ Placeholder | Base class only |
| `evaluation/` | ⚠️ Partial | Grounding + faithfulness tests |
| `memory/` | ⚠️ Partial | Basic |
| `streaming/` | ⚠️ Partial | SSE streaming |
| All others | ⚠️ Partial | Models/services exist but incomplete |

---

## 5. Frontend Architecture (What Actually Exists)

### 5.1 Pages
- **93+ pages** across auth (3), dashboard (75), and v3 (18) route groups
- **Companies page:** Fully functional (942 lines, full CRUD, search, filter, pagination)
- **Copilot page:** Partially functional (gated, chat works if enabled)
- **Dashboard:** Thin wrapper delegating to feature module
- **Many routes:** Likely have pages but not all audited

### 5.2 Components
- **31 UI primitives** (`@salesos/ui`): Button, Card, Modal, DataTable, Toast, etc.
- **Copilot Panel:** Full chat UI with branching, feedback, contextual insights
- **AI Insights:** ContextualInsightsProvider, ConfidenceBadge, InlineSuggestion
- **V3 Shell:** Sidebar, topbar, command palette, AI popup (preview only)
- **Foundation:** AppShell, AuthSessionSync, EntitlementDenialListener, LanguageSwitcher

### 5.3 API Client
- **37 API modules** covering all backend domains
- **Axios interceptors:** Auto-attach auth, tenant, CSRF; auto-refresh on 401; auto-retry on CSRF 403

### 5.4 State Management
- **TanStack React Query v5** (primary)
- **40+ query hooks** + 6 mutation hooks
- **FrontendRuntime** with 9 subsystems (state, session, realtime, cache, localization, accessibility, rendering, collaboration, offline)

### 5.5 Security
- Route-based auth gating (middleware)
- CSRF double-submit pattern
- httpOnly cookie support (OFF by default)
- JWT audience split (tenant vs owner)

---

## 6. SDK Layer (What Actually Exists)

| Package | Status | Notes |
|---------|--------|-------|
| `security.py` | ✅ Real | bcrypt, JWT, API keys, Fernet, CSRF, PII masking |
| `permissions.py` | ✅ Real | RBAC registry + enforcer |
| `database.py` | ✅ Real | Base ORM models |
| `audit.py` | ✅ Real | Audit trail helpers |
| `cache/` | ✅ Real | Cache service |
| `events/` | ✅ Real | Event bus, domain events, outbox pattern |
| `telemetry.py` | ✅ Real | Structured logging |
| `vector.py` | ✅ Real | OpenAI embedding service |
| `pagination.py` | ✅ Real | Pagination utilities |
| `graph.py` | ✅ Real | Graph helpers |
| `search.py` | ✅ Real | Search utilities |
| `queue.py` | ✅ Real | Queue helpers |
| `capability_registry.py` | ✅ Real | Capability registration |
| `feature_registry.py` | ✅ Real | Feature registration |
| `metadata.py` | ✅ Real | Metadata helpers |
| `config.py` | ✅ Real | SDK config |
| `exceptions.py` | ✅ Real | SDK exceptions |

---

## 7. MCP Server

- **`mcp_server/`** — FastMCP server with tools, resources, and SalesOS API client
- Provides AI agent interface to SalesOS capabilities
- ⚠️ Basic but functional

---

## 8. Test Suite

| Category | Count | Status |
|----------|-------|--------|
| Unit tests | 133 files | ⚠️ 99 passing (some quarantined) |
| E2E tests | 17 files | ⚠️ Not all executed |
| Contract tests | 12 files | ⚠️ Not all executed |
| Integration tests | 25 files | ⚠️ Not all executed |
| AI evaluation tests | 3 files | ⚠️ Minimal |
| **Total** | **190+ test files** | **Partial coverage** |

---

## 9. Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| Docker Compose (local) | ✅ 14 services | Backend, frontend, Postgres, Redis, Neo4j, Kafka, Meilisearch, etc. |
| Docker Compose (prod) | ✅ Exists | Railway deployment |
| Docker Compose (test) | ✅ Exists | CI test environment |
| Alembic | ✅ 83 migrations | Through migration 0051 |
| Celery | ✅ Real | Worker + beat on Railway |
| Railway | ✅ Live | Backend serving HTTP 200 |
| Vercel | ✅ Live | Frontend serving HTTP 200 |

---

## 10. What's Real vs What's Scaffolded

### ✅ REAL (Production-grade or near-production)
- Auth/Identity (RS256, refresh rotation, brute force, PDPL erasure)
- Tenant isolation architecture (dual-engine, RLS, ContextVar)
- RBAC (4 roles, 27 resources, enforcer)
- Security middleware (7 classes)
- Database architecture (dual-engine, connection pooling, bounded timeouts)
- Entitlements (4 tiers, domain gating, quota enforcement)
- Companies CRUD + search
- Employee 360
- Timeline
- Feature Store (7 score computers)
- Search (trigram + pgvector)
- Guardrails (injection, PII, output validation)
- Grounding (Postgres + Neo4j retrieval)

### ⚠️ PARTIAL (Exists but incomplete)
- Copilot (search tool only, other tools missing)
- Decision Center (PostgreSQL-backed but IDOR vulnerability)
- Knowledge Graph (Neo4j offline in production)
- Data Fabric (scrapers exist, ETL mock)
- NBA Engine (rule-based, no AI)
- Workflow Engine (functional but limited)
- Billing (state machine works, no Stripe)
- Arabic NLP (normalization only)
- i18n (English/Arabic, no framework)

### ❌ PLACEHOLDER (Scaffolded but not functional)
- Agent Runtime (string "PLANNED FOR RT3")
- Digital Twin (zero components)
- Revenue Brain (missing)
- Simulation Engine (minimal)
- platform (not in code)
- AuditOS, DecisionOS, LocalContentOS (not in code)
- Frontend Decision Engine (all methods throw STUB)
- AI Memory (basic only)
- Prompt Studio (templates only)
- AI Governance (not implemented)

---

*This model represents the IMPLEMENTATION reality as found in code. Theory is captured in 01_THEORY_MODEL.md.*
