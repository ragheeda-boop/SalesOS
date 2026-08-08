# SalesOS Project Bible

> **The Highest Authority for SalesOS Engineering**
>
> **GO / NO-GO exception:** Production readiness and GA decisions defer to [`docs/audit/ga-engineering-audit/`](audit/ga-engineering-audit/) (2026-07-22 **NO-GO**). Where this bible’s maturity language conflicts with the audit, **the audit wins** (EAB-001-P1-DOC-01 / AGENTS.md).
>
> Version: v5.1.0-rc1
> Last Updated: 2026-07-29
> Status: Ratified
>
> This document supersedes all previous project manifestos. It is the single source of truth for SalesOS architecture, engineering, design, and product decisions. Every agent, engineer, and stakeholder must follow this document.

---

## Table of Contents

1. [Executive Vision](#1-executive-vision)
2. [Product Vision](#2-product-vision)
3. [Product Principles](#3-product-principles)
4. [Engineering Principles](#4-engineering-principles)
5. [Design Principles](#5-design-principles)
6. [AI Principles](#6-ai-principles)
7. [Architecture Principles](#7-architecture-principles)
8. [Development Workflow](#8-development-workflow)
9. [Definition of Ready](#9-definition-of-ready)
10. [Definition of Done](#10-definition-of-done)
11. [Quality Standards](#11-quality-standards)
12. [Feature Development Rules](#12-feature-development-rules)
13. [Screen Standards](#13-screen-standards)
14. [Component Standards](#14-component-standards)
15. [Documentation Standards](#15-documentation-standards)
16. [Release Standards](#16-release-standards)
17. [Decision Log](#17-decision-log)
18. [Future Vision](#18-future-vision)

---

## 1. Executive Vision

### Why SalesOS Exists

SalesOS exists to solve a fundamental problem in B2B sales: **data fragmentation**. Companies in the Middle East — and globally — operate across disconnected CRM systems, ERP platforms, government databases, spreadsheets, and email. No single platform unifies this data into actionable revenue intelligence.

SalesOS is designed for the Saudi Arabian market first, with global expansion capabilities. It addresses KSA PDPL compliance, Arabic-first NLP, Saudi business entity resolution, and local market intelligence out of the box.

### Mission

> **Unify fragmented business data into AI-assisted revenue intelligence that every team member can act on — without engineering support.**

### Vision

SalesOS becomes the **operating system for revenue teams** in the Middle East and emerging markets. Not a CRM — an AI-assisted platform where:

- Every company interaction generates intelligence automatically
- Every decision is informed by data, not intuition
- Every workflow is automated without code
- Every team member has AI assistance built into their workflow
- Every insight respects data sovereignty and privacy

### Long-Term Goals

| Horizon | Timeline | Goal |
|---------|----------|------|
| **vNext** (Current) | 2026 Q3-Q4 | Complete platform stabilization, design system V2, AI runtime, Data Fabric, multi-tenancy, Arabic/RTL |
| **v2.5** | 2027 H1 | Public API, plugin marketplace, self-service tenant provisioning, advanced AI agent orchestration |
| **v3.0** | 2027 H2 | Multi-region deployment, enterprise SSO/SAML, advanced analytics OLAP, partner ecosystem |
| **v4.0** | 2028+ | AI-native OS for revenue: autonomous agents, predictive revenue engine, full marketplace, developer SDK |

### Success Metrics

| Metric | Current | vNext Target | Measurement |
|--------|---------|-------------|-------------|
| Overall Maturity | 7.5/10 | ≥ 9.0/10 | Engineering Dashboard |
| Overall Completion | ~79-85% | ≥ 95% | Feature Matrix |
| Architecture Score | 8/10 | ≥ 9.5/10 | Architecture Compliance Scan |
| Security Posture | 48/100 | ≥ 90/100 | STAR Audit + GA Audit |
| Performance Score | 6.5/10 | ≥ 9.0/10 | k6 Baseline + Endpoint Budgets |
| Unit Test Coverage | 93% | ≥ 90% | pytest-cov |
| Backend AI Tests | 0% | ≥ 85% | pytest-cov (ai domain) |
| Total Tests | 2,110+ | ≥ 3,000 | pytest + Playwright |
| Technical Debt | 1 tracked | ≤ 10 total, 0 critical | Technical Debt Register |
| File Size Compliance | 3 files > 700 lines | 100% ≤ 600 lines | CI Scanner |

---

## 2. Product Vision

### SalesOS Is a Platform, Not a CRM

SalesOS is not a traditional CRM. It is a **Revenue Intelligence Platform** composed of six interconnected platforms:

### 2.1 Revenue Intelligence Platform

The core of SalesOS. Automated pipeline management, deal scoring, forecasting, and revenue execution. Uses AI to identify risks, recommend actions, and predict outcomes.

**Key Capabilities**: Pipeline kanban, deal scoring, forecasting, opportunity management, revenue analytics, quota management, territory planning.

**Current State**: 75% complete. Pipeline and opportunities are strong; quota management, territory planning, and ML-based forecasting are missing.

### 2.2 AI Platform

AI is not a feature — it is the runtime. Every domain exposes intelligence through the Decision Platform. Agents are first-class system components with lifecycle, observability, and testing.

**Key Capabilities**: Multi-agent system, prompt registry, RAG pipeline, decision intelligence, NBA engine, copilot, knowledge graph, Arabic NLP.

**Current State**: 85% complete but with critical gaps. Agent runtime is a placeholder (zero execution capability), backend AI test coverage is 0%, and only OpenAI is supported.

### 2.3 Knowledge Platform

Entity Resolution, Knowledge Graph, Feature Store, and Data Fabric form the unified data layer. All insights derive from a consistent, deduplicated, enriched data foundation.

**Key Capabilities**: Entity resolution (pg_trgm), knowledge graph (Neo4j), feature store, data fabric, scrapers, enrichment pipeline.

**Current State**: 65-85% across sub-capabilities. Data Fabric is the weakest area (65% — no unified ingestion framework). Entity Resolution and Feature Store are strong.

### 2.4 Automation Platform

Visual workflow builder, rules engine, and webhook system that lets business users configure processes without engineering.

**Key Capabilities**: Workflow engine, visual builder, rules engine, webhooks, scheduled jobs, event-driven automation.

**Current State**: 85% complete. Core engine works; visual builder advanced branching is partial. Webhooks router has a critical security gap (no authentication).

### 2.5 Marketplace

Signal marketplace for third-party data providers, widget marketplace for custom dashboard components, and integration marketplace for connectors.

**Key Capabilities**: Signal marketplace, widget registry, third-party integrations, data provider onboarding.

**Current State**: Widget registry and signal marketplace exist. Full marketplace with third-party onboarding and billing is future.

### 2.6 Developer Platform

Public API (REST + GraphQL), plugin SDK, widget SDK, webhook system, and MCP server for AI agent tool access.

**Key Capabilities**: Widget SDK v1.0 (frozen), plugin SDK (scaffold), MCP server, API keys, webhooks.

**Current State**: Widget SDK is mature and frozen. Plugin SDK and public API are early-stage.

---

## 3. Product Principles

### 3.1 AI First

AI is not a feature toggle. Every screen, every workflow, every decision point must ask: "Can AI make this better?" AI must be testable, observable, and swappable.

**Rules**:
- Every API response should include AI-derived insights where possible
- Every dashboard should have at least one AI-powered widget
- Every agent must have contract tests and observability
- Every LLM call must be traceable and cost-tracked

### 3.2 Enterprise Grade

SalesOS serves enterprise revenue teams. Reliability, security, auditability, and compliance are not optional.

**Rules**:
- Zero-trust architecture: every endpoint authenticated, every request authorized
- All mutations must be idempotent where possible
- Every data change must be auditable
- All list endpoints must be paginated (no unbounded result sets)
- Multi-tenancy must be designed in, not bolted on

### 3.3 API First

Every capability must be accessible via API before UI is built. APIs are the product; the UI is a client.

**Rules**:
- OpenAPI schema for every endpoint
- Contract tests (provider + consumer) for every endpoint
- No UI-only features — every feature must have an API surface
- API versioning via URL path (`/api/v1/`, `/api/v2/`)

### 3.4 Design First

Every user-facing feature must have approved designs before implementation begins. Design tokens and components must be used consistently.

**Rules**:
- No raw HTML elements in page components — use `@salesos/ui` only
- No hardcoded colors — use CSS variables from `@salesos/design-language`
- All pages must use semantic CSS variables (`var(--text-primary)`, not `text-neutral-900`)
- All components must pass WCAG AA at minimum

### 3.5 Accessibility (a11y)

Accessibility is not a checklist — it is a design principle. Every user, regardless of ability, must be able to use SalesOS.

**Rules**:
- WCAG AA minimum, WCAG AAA target
- Keyboard navigation must cover all interactive elements
- All images must have alt text
- Color contrast must meet 4.5:1 minimum (AA normal text)
- RTL support is mandatory (Saudi market)
- Reduced motion support for all animations
- Screen reader testing required for all new components

### 3.6 Security

Security is non-negotiable. Every decision must consider security implications.

**Rules**:
- Every endpoint must have authentication (JWT or API key)
- No secrets in code (use environment variables or Vault)
- No hardcoded credentials in any configuration file
- All SQL queries must be parameterized (no string interpolation)
- All AI prompts must pass through guardrails
- Rate limiting on all API endpoints
- CSRF protection on all state-changing endpoints

### 3.7 Performance

Performance is a feature. Every endpoint must meet its latency budget.

**Rules**:
- p99 must be within budget for all endpoints
- No N+1 query patterns — batch all DB operations
- No unbounded list endpoints — all lists must be paginated
- Caching must be intentional, not accidental
- Middleware must be transparent (no request body consumption)
- Frontend bundles must be tree-shakeable
- Images must be optimized (next/image or equivalent)

### 3.8 Scalability

Design for 10x growth today. The platform must handle 1M+ companies, 10M+ contacts, and 100+ tenants without architecture changes.

**Rules**:
- Database partitioning strategy must be in place before hitting scale limits
- All service layers must be stateless (scale horizontally)
- Event-driven architecture for cross-domain communication
- Redis for caching, rate limiting, and session store
- Kafka for durable event streaming

### 3.9 Modularity

Every module must be a bounded context with public contracts, private internals, and CI-enforced boundaries.

**Rules**:
- No cross-domain imports at runtime (enforced by CI)
- No infrastructure imports in domain layer (enforced by CI)
- No file shall exceed 600 lines of production code
- Every domain must have an `__init__.py` that exports only its public API
- Shared packages require ≥ 3 consumers before creation

### 3.10 Developer Experience

DX is product. Engineers must be able to understand, navigate, and contribute to the codebase quickly.

**Rules**:
- Single command to set up local development (`make dev`)
- Pre-commit hooks for linting, type checking, and secrets detection
- Single test command (`pytest tests/unit`) with clear structure
- README must match package.json/pyproject.toml (CI-validated)
- ADRs must be in `docs/adr/` — not scattered across files

---

## 4. Engineering Principles

### 4.1 Coding Standards

**Python**:
- Follow PEP 8 enforced by Ruff
- Type annotations required on all function signatures
- Use `mypy --strict` with no `ignore_missing_imports`
- Use SQLAlchemy async for all database operations
- Use Pydantic v2 for all data validation
- No `print()` in production code (use structured logging)
- No commented-out code
- Maximum file length: 600 lines

**TypeScript/React**:
- Use TypeScript strict mode
- All components must have typed props
- Use React Query for server state, Zustand for client state
- Use `@salesos/ui` for all UI primitives
- No `any` types in public interfaces
- No `console.log`/`console.debug` in production code
- All event handlers must be typed
- Use CSS variables from `@salesos/design-language` — not hardcoded Tailwind color classes

### 4.2 Architecture Rules

- **Domain-Driven Design**: Every domain is a bounded context in `src/domains/`
- **Repository Pattern**: Domain services depend on repository interfaces; implementations are in infrastructure
- **Container/View Pattern**: Widgets must separate data fetching (Container) from rendering (View)
- **Layered Architecture**: Domain → Application → Infrastructure → Interface (strict dependency direction)
- **Event-Driven**: All cross-domain communication via events (in-memory sync + Kafka async)
- **CQRS**: Separate read and write models where query/command complexity diverges
- **Modular Monolith**: Ship as one deployable with clear extraction paths for each domain

### 4.3 Module Boundaries

Modules are organized as:

```
domains/{domain_name}/
  __init__.py         # Public exports only (router, service interface, events)
  domain/             # Domain models, interfaces, repository interfaces
  application/        # Use cases, DTOs, orchestrators
  infrastructure/     # Repository implementations, external clients
  interface/          # REST router, GraphQL schema
```

**Import Rules** (enforced by CI):

| Layer | Can Import | Cannot Import |
|-------|-----------|---------------|
| `domain/` | `dataclasses`, `abc`, `typing`, domain events | Infrastructure, application, interface |
| `application/` | Own domain, other domain SDKs | Infrastructure directly |
| `infrastructure/` | Own domain, shared infrastructure | Other domain infrastructure |
| `interface/` | Own application layer, FastAPI, Pydantic | Other domain layers directly |

### 4.4 Dependency Rules

- No cross-domain imports at runtime (use events or SDK)
- No circular imports (enforced by `pytest-arch`)
- No Frozen Interface modification without ADR
- No infrastructure imports in domain layer
- Frontend packages: Widget packages import only Widget SDK + API client; API packages import only base API client
- All dependencies must be explicitly declared (no transitive reliance)

### 4.5 Folder Rules

```
salesos/
  bootstrap/         # App factory, settings, lifespan, middleware pipeline
  middleware/        # All middleware components
  domains/           # All bounded contexts
  infrastructure/    # Shared infrastructure (DB, event bus, cache, queue, storage)
  runtimes/          # Runtime entry points (9 production + 6 support)
  config/            # Centralized configuration (YAML + vault)
  tests/             # Consolidated test directory
    unit/            # Mirrors src/ structure
    integration/     # Cross-domain + external dependencies
    e2e/             # End-to-end
    contract/        # Consumer-driven contract tests
    performance/     # Load and performance tests
    ai/              # AI-specific evaluation tests
```

### 4.6 Naming Rules

| Element | Convention | Example |
|---------|-----------|---------|
| Python files | `snake_case.py` | `company_service.py` |
| TypeScript files | `kebab-case.ts` | `company-service.ts` |
| React components | `PascalCase.tsx` | `CompanyProfile.tsx` |
| Python classes | `PascalCase` | `CompanyService` |
| Python functions | `snake_case` | `get_company_by_id` |
| TypeScript functions | `camelCase` | `getCompanyById` |
| Database tables | `snake_case` (plural) | `companies` |
| API endpoints | `kebab-case` | `/api/v1/company-profiles` |
| Git branches | `feat/SALES-NNN-description` | `feat/SALES-142-bulk-import` |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_URL` |

### 4.7 Testing Requirements

| Category | Min Coverage | CI Stage | Tools |
|----------|-------------|----------|-------|
| Unit | 90%+ | Stage 3 | pytest, Vitest |
| Integration | 75%+ | Stage 4 | pytest + testcontainers |
| Contract | 100% of endpoints | Stage 2 | pytest (backend), Vitest (frontend) |
| E2E | 300+ tests | Stage 7 | Playwright |
| AI | 85%+ | Stage 3 | pytest + mocked LLM |
| Architecture | 100% compliance | Stage 2 | pytest-arch, import scanner |
| Performance | CI-gated, < 10% regression | Stage 6 | k6, locust, custom benchmark |
| Load | Critical paths covered | Stage 6 | k6 |

### 4.8 CI Requirements

3 consolidated workflows (replacing current 6):

1. **pull_request.yml** — Stages 1-6 (every PR)
2. **merge_to_main.yml** — Stages 1-7 + Docker build + staging deploy
3. **release.yml** — Stages 1-7 + Docker build + production deploy + git tag

7-stage pipeline:
1. Lint & Format (< 2 min)
2. Type Check (< 3 min)
3. Unit + Arch + AI Tests (< 5 min, 85% coverage gate)
4. Integration Tests (< 10 min)
5. Security Scan (< 10 min)
6. Load & Performance (< 15 min, regression < 10%)
7. E2E Tests (< 20 min)

### 4.9 Quality Gates

10 quality gates (8 existing + 2 new for vNext):

| Gate | Automation | Blocking |
|------|-----------|----------|
| 1. Architecture | Import boundaries, file size < 600 lines, no circular deps | ✅ |
| 2. Code Quality | mypy strict, Ruff, no `Any` in public interfaces | ✅ |
| 3. Testing | Coverage ≥ 85%, AI tests ≥ 85% | ✅ |
| 4. Events & Telemetry | Event catalog updated, metrics emitted | ✅ |
| 5. Observability | Logging, tracing, performance baseline check | ✅ |
| 6. AI Quality | Model evaluation results in CI | ✅ |
| 7. Documentation | ADR directory check, README accuracy | ✅ |
| 8. UX & Accessibility | WCAG AA, RTL support, keyboard nav | ✅ |
| 9. Performance (NEW) | Load test regression < 10%, p99 within budget | ✅ |
| 10. Infrastructure (NEW) | Docker healthchecks valid, Terraform state configured | ✅ |

---

## 5. Design Principles

### 5.1 Design Language

SalesOS uses the MUHIDE design language. The design system has three layers:

| Layer | Package | Purpose |
|-------|---------|---------|
| **Tokens** | `@salesos/design-language` (16 files) | Single source of truth for all visual tokens |
| **Components** | `@salesos/ui` | Radix-based UI primitives (17 → 25+ components for vNext) |
| **Theme** | `tailwind.config.ts` + `globals.css` | CSS utility layer bridging tokens to Tailwind |

### 5.2 Brand Colors

| Token | Value | Usage |
|-------|-------|-------|
| `muhide-orange` | `#F57C1E` | Primary brand color, CTAs, active states |
| `muhide-ink` | `#151214` | Darkest neutral, sidebar bg, text on dark |
| `muhide-espresso` | `#403D38` | Secondary dark neutral |
| `muhide-sand` | `#CCC6BA` | Light neutral accent |
| `muhide-paper` | `#FAFAFA` | Lightest neutral, page bg |

### 5.3 Semantic Colors

| Palette | Base | Purpose |
|---------|------|---------|
| `primary` (orange) | `#F57C1E` | Primary actions, links, active states |
| `secondary` (neutral) | `#8B8475` | Neutral backgrounds, borders |
| `success` (green) | `#4CAF50` | Positive states, revenue |
| `warning` (amber) | `#FFC107` | Caution states |
| `danger` (red) | `#F44336` | Error, destructive actions |
| `info` (blue) | `#2196F3` | Focus rings, links, timeline |
| `ai` / `copilot` (purple) | `#8B5CF6` | AI-related features |

### 5.4 Typography

| Token | Family | Fallback |
|-------|--------|----------|
| `display` | Viga | IBM Plex Sans Arabic, sans-serif |
| `sans` / `ui` | IBM Plex Sans | sans-serif |
| `arabic` | IBM Plex Sans Arabic | sans-serif |
| `mono` | IBM Plex Mono | monospace |

**Type Scale**: 8 stops (11px, 12px, 14px, 16px, 20px, 24px, 36px, 48px). Add 56px and 64px for display in vNext.

### 5.5 Spacing

Use a 4px grid scale for all spacing. vNext target: custom `--space` token family (4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px).

### 5.6 Accessibility Minimums

- WCAG AA for all text (4.5:1 contrast for normal text, 3:1 for large text)
- WCAG AA for all interactive elements
- Keyboard navigable: Tab, Enter, Escape, Arrow keys on all interactive components
- ARIA labels on all icons with semantic meaning
- Focus indicators visible on all interactive elements
- `prefers-reduced-motion` respected on all animations
- Dark mode via `class` strategy with full variable overrides

### 5.7 Interaction Patterns

Every interaction pattern must be documented and reusable. No ad-hoc interactions.

- **Selection**: Checkbox for multi-select, Radio for single-select, Switch for binary
- **Navigation**: Sidebar primary, breadcrumb secondary, command palette (Ctrl+K) for power users
- **Feedback**: Toast for transient feedback, Inline for form validation, Modal for confirmations
- **Loading**: Skeleton for initial load, Spinner for actions, Progressive loading for dashboards
- **Empty States**: Illustration + message + CTA for every list/view
- **Error States**: Inline for form errors, Banner for system errors, Fallback UI for crashes

### 5.8 Responsive & RTL

- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px), 2xl (1536px)
- Mobile: Bottom navigation, collapsible sidebar, full-width cards
- RTL: Everything mirrors — sidebar on right, text right-aligned, icons flipped
- RTL must be tested in E2E for every layout change

### 5.9 Chart Design

- Chart colors must match backend tokens (orange first: `#F57C1E`, `#4CAF50`, `#FFC107`, `#F44336`, `#8B5CF6`, `#2196F3`)
- All charts must have dark mode variants
- All charts must have accessible data tables as fallback
- Use Recharts with `@salesos/charts` wrappers (no direct Recharts usage)

---

## 6. AI Principles

### 6.1 Agent Architecture

Agents are first-class system components with:

- **Lifecycle**: Register → Configure → Execute → Complete/Fail → Retry (if applicable)
- **Observability**: Every agent execution must emit traces, logs, and metrics
- **Testability**: Every agent must have contract tests (input → expected output) and unit tests
- **Isolation**: Agents execute in a sandboxed environment with resource limits
- **Registry**: All agents registered in the Agent Registry with metadata, version, dependencies

**Current**: 15 agents exist in code but the runtime is a placeholder. **vNext**: Full agent runtime implementation (Sprint 11-12).

### 6.2 Memory

Agents require memory for contextual conversations and learning:

- **Short-term**: Ephemeral conversation context (in-memory, per session)
- **Long-term**: Persistent knowledge from past interactions (PostgreSQL)
- **Working**: Current task context (scoped to execution)
- **No external memory services**: Start with PostgreSQL, evaluate Redis/Vector DB later

### 6.3 Knowledge

Knowledge is the foundation of AI quality:

- **Knowledge Graph**: Neo4j with entities, relationships, and properties
- **RAG**: Document chunks → embeddings → pgvector retrieval → LLM synthesis
- **Knowledge Packs**: Domain-specific curated knowledge (Healthcare, Construction, Financial Services)
- **Arabic NLP**: Tokenization, lemmatization, NER, sentiment analysis, Saudi stop words

### 6.4 Decision Making

The Decision Platform is the bridge between raw intelligence and user action:

- **Scoring Engine**: Quantitative scoring (ICP fit, engagement, churn risk)
- **Rules Engine**: Business rules configured by users (no-code)
- **NBA Engine**: Next Best Action recommendations
- **Decision Runtime**: Orchestrates scoring + rules + recommendation
- **Feedback Loop**: User decisions (accept/dismiss) train future recommendations

### 6.5 Prompt Engineering

- All prompts must be registered in the Prompt Registry (versioned YAML + DB)
- Prompts must be versioned and A/B testable
- Prompt templates must use Jinja2 for variable substitution
- Prompt versions must be tracked alongside agent versions
- Deprecated prompts must have a migration path

### 6.6 Model Abstraction

- All LLM access through a provider abstraction layer (`LLMProvider` interface)
- Minimum 2 supported providers: OpenAI + Anthropic (production), local fallback (KSA)
- Provider selection per tenant (configurable)
- Failover chain (primary → secondary → fallback)
- All providers covered by contract tests

### 6.7 Evaluation

- Every AI component must have an evaluation harness
- Golden datasets must exist in `tests/evaluation/test_cases/`
- Regression detection: CI must fail if AI quality regresses
- Metrics: faithfulness, relevance, accuracy, latency, cost
- Evaluation results stored and tracked over time

### 6.8 Guardrails & Safety

- **Input Guardrails**: PII detection, prompt injection prevention, topic restriction
- **Output Guardrails**: Factuality checking, tone moderation, content safety
- **Rate Limiting**: Per-tenant, per-model, per-endpoint
- **Cost Tracking**: Every LLM call tracked with token count and cost attribution
- **Human-in-the-Loop**: Critical decisions (enrichment merge, deal closing) require human approval

### 6.9 AI Testing (Closing the Gap)

**Current**: Zero backend AI tests. This is a governance violation (Constitution Article 2.2).

**vNext Target**:
- AIService: Full unit test coverage (all codepaths)
- Agent contracts: Every agent has input/output contract tests
- RAG pipeline: Chunking, embedding, retrieval, synthesis — all tested
- Provider abstraction: Contract tests for each provider
- Prompt Registry: All templates render correctly
- Evaluation: Golden dataset exists, regression detection active

---

## 7. Architecture Principles

### 7.1 Domain-Driven Design

SalesOS uses Domain-Driven Design with bounded contexts. Each domain is independent, with its own models, services, and data.

**14 Domains (vNext)**:
| Domain | Purpose | Dependencies |
|--------|---------|-------------|
| Identity | Authentication, authorization, user management | None |
| Company | Company CRUD, firmographics, hierarchy | Identity |
| Search | Full-text, semantic, hybrid search | Company |
| CRM | Pipeline, opportunities, contacts, activities | Company |
| Enrichment | Data enrichment, async processing | Company |
| Entity Resolution | Duplicate detection, merge, golden record | Company |
| Scoring | Quantitative scoring models | Entity Resolution |
| Pipeline | Pipeline analytics, stage management | Company |
| Employee | Employee profiles, signals, work intelligence | Company |
| Decision Platform | Decision orchestration, recommendations | Scoring, Pipeline, Employee |
| Workflow | Workflow engine, automation rules | Decision Platform |
| Timeline | Universal event timeline | Decision Platform |
| AI | AI service, prompt registry, evaluation | All domains (via SDK) |
| Customer Success | Health scoring, risk detection, churn prevention | Company, CRM |
| Data Fabric | Unified data ingestion, connectors | None (infrastructure) |
| Feature Store | Feature computation, serving | Data Fabric |
| Tenant (NEW) | Multi-tenancy, provisioning, quotas | Identity |
| Billing (NEW) | Usage tracking, invoicing | Company |

### 7.2 Repository Pattern

Every domain service depends on a repository interface. Database implementations are in the infrastructure layer. Domain layer has zero knowledge of the database.

```python
# Domain layer
class CompanyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, company_id: UUID) -> Company: ...

# Infrastructure layer
class PostgresCompanyRepository(CompanyRepository):
    async def get_by_id(self, company_id: UUID) -> Company:
        # SQLAlchemy implementation
```

**Rules**:
- Repository interfaces in `domain/` directory
- PostgreSQL implementations in `infrastructure/` directory
- InMemoryRepository implementations available for tests
- Each repository method must have a single responsibility
- Repository methods must use pagination for list operations

### 7.3 Container/View Pattern

Every widget must separate data fetching from rendering:

```
CompanyProfileContainer.tsx   # Data fetching (React Query), state management
CompanyProfileView.tsx        # Pure rendering, no side effects
```

**Rules**:
- Container uses the Widget SDK's `createWidget()` or `createDashboardWidget()`
- View is a pure React component with typed props
- View never calls API directly
- Container never contains JSX
- Both must have tests: Container (integration), View (unit + visual regression)

### 7.4 Event-Driven Architecture

Cross-domain communication must use events, not direct imports.

```
┌──────────┐   publish(event)   ┌──────────┐
│ Domain A │ ─────────────────▶ │ Event Bus │
└──────────┘                    └─────┬────┘
                                      │
                            ┌─────────▼─────────┐
                            │ Domain B Consumer  │
                            └───────────────────┘
```

**Rules**:
- Domain events published after transaction commits (Outbox pattern)
- Integration events via Kafka with schema registry
- Event handlers must be idempotent
- Dead letter queue for failed events
- Event schema owned by publishing domain

### 7.5 CQRS (Command Query Responsibility Segregation)

Where query complexity diverges from command complexity, use separate read and write models:

```
Command Side: API → Domain Service → Repository → PostgreSQL (OLTP)
                                                    │
                                              Event Bus
                                                    │
Query Side: Event Bus → Denormalizer → Read Database → Query API
```

**Implemented**: Timeline domain, some analytics paths. Future: all high-read-volume domains.

### 7.6 Micro-Modules

Not microservices — micro-modules. Each domain is independently deployable within the monolith but has a clear extraction path.

**Extraction Path**: When a domain reaches these thresholds, evaluate extraction:
- 5+ developers working on the same domain simultaneously
- Deploy frequency conflicts between domains
- Resource requirements diverge (e.g., AI needs GPU)

### 7.7 Widget SDK (Frozen v1.0)

The Widget SDK v1.0 is Feature Frozen per ADR-003. All new widgets must use the existing SDK. Any SDK changes require:
1. ADR documenting the gap
2. Architecture Review Board approval
3. Contract tests for the new API surface
4. Migration path for existing widgets

---

## 8. Development Workflow

### 8.1 Full Workflow

```
Idea → RFC → Architecture → UX Design → UI Design → Implementation → Review → Testing → Documentation → Release
```

### 8.2 Step Details

1. **Idea**: Product requirement or engineering proposal. Captured as a feature request or ADR.
2. **RFC** (Optional): 1-page proposal for significant changes. Describes the problem, solution options, and recommendation.
3. **Architecture**: ADR written if architectural change. Technical approach reviewed with Tech Lead (> 3 story points).
4. **UX Design**: Wireframes approved for user-facing features. Interaction patterns documented.
5. **UI Design**: Mockups using `@salesos/ui` components. Tokens from `@salesos/design-language`. Accessibility review.
6. **Implementation**: Feature branch from `main`. Follows Definition of Ready. All code follows coding standards.
7. **Review**: PR created with checklist. Code Reviewer + Domain Expert required. CI gates must pass.
8. **Testing**: Unit tests ≥ 85% coverage. Integration tests for cross-domain. Contract tests for new endpoints. E2E for new user journeys.
9. **Documentation**: CHANGELOG updated. ADR (if architectural). API docs (auto from OpenAPI). User guide (if new feature).
10. **Release**: Feature flag default OFF. Staged rollout. Post-release monitoring.

### 8.3 Branch Strategy

```
main ─────────────────────────────────────────────────────
  │                                                      │
  ├── feat/SALES-NNN-description  (from main, to main)  │
  ├── fix/SALES-NNN-description   (from main, to main)  │
  ├── hotfix/SALES-NNN-description (from main, to main  │
  │                                + latest release)     │
  └── release/vX.Y.Z              (from main, to main)  │
```

- `main` is protected — no direct pushes
- Feature branches max 3 days
- Squash merge to `main`
- Release branches freeze `main` for stabilization

### 8.4 Code Review

| Role | Required For | Responsibilities |
|------|-------------|-----------------|
| Author | Every PR | Self-review, local checks, formatted code |
| Code Reviewer | Every PR | Code quality, patterns, test coverage |
| Domain Expert | Domain logic changes | Business correctness, event semantics |
| Security Reviewer | Auth/data/infra changes | Vulnerability assessment |
| CTO | Hotfixes, overrides | Final approval on exceptions |

**SLA**: First response within 4 business hours, approval within 24 hours.

---

## 9. Definition of Ready

A story is Ready for implementation only when ALL of the following are true:

```
[ ] User story or requirement clearly stated
[ ] Acceptance criteria defined (3-5 concrete, testable conditions)
[ ] Technical approach reviewed with Tech Lead (for stories > 3 story points)
[ ] Dependencies identified and resolved or explicitly accepted
[ ] API contracts drafted (if adding/modifying endpoints)
[ ] ADR drafted (if architectural change)
[ ] Test strategy defined (unit, integration, contract, e2e)
[ ] Feature flag identified (name, default state, removal sprint)
[ ] UX mockups or wireframes approved (if UI change)
[ ] Security implications reviewed (if auth, data, or external input)
[ ] Performance implications identified (if new endpoint or data pipeline)
[ ] Estimation completed (story points, max 8 per story)
[ ] All "Unknowns" resolved — no black-box work items
```

**Exceptions**:
- Bugfixes: Require only "acceptance criteria," "test strategy," "estimation"
- Hotfixes: Emergency bypass with CTO override (post-hoc documentation within 24 hours)
- Technical Debt: Requires "acceptance criteria," "technical approach," "estimation"

---

## 10. Definition of Done

A story is Done only when ALL of the following are true:

```
[ ] Code merged to main (PR approved + all CI gates passing)
[ ] All acceptance criteria met (verified by tests or manual QA)
[ ] Unit tests written and passing (coverage ≥ 85% for new code)
[ ] Integration tests written and passing (if cross-domain or external dependency)
[ ] Contract tests written and passing (if new/modified endpoint)
[ ] E2E tests written and passing (if new user journey)
[ ] Architecture compliance verified (no cross-domain imports, no violations)
[ ] Feature flag created (if new feature) — default OFF
[ ] Events registered in Event Catalog (if new events)
[ ] Capability registered in Capability Registry (if new capability)
[ ] OpenAPI schema updated (auto from Pydantic, verified by contract tests)
[ ] ADR written (if architectural change)
[ ] CHANGELOG updated
[ ] Documentation updated (README, API docs, user guide as applicable)
[ ] Technical debt registered (if any debt introduced)
[ ] Performance impact measured and within budget (if applicable)
[ ] Security review completed (if applicable)
[ ] Accessibility verified (if UI change)
[ ] Monitoring dashboard reviewed (metrics, logs, traces working)
[ ] Product owner acceptance (demo or sign-off)
```

**Done Checklist by Story Type**:

| Criteria | Feature | Bugfix | Tech Debt | Hotfix |
|----------|---------|--------|-----------|--------|
| Code merged | ✅ | ✅ | ✅ | ✅ |
| Acceptance criteria met | ✅ | ✅ | ✅ | ✅ |
| Unit tests | ✅ | ✅ | ✅ | — |
| Integration tests | ✅ | ✅ (if applicable) | — | — |
| Contract tests | ✅ | — | — | — |
| E2E tests | ✅ | ✅ | — | — |
| Architecture compliance | ✅ | ✅ | ✅ | ✅ |
| Feature flag | ✅ | — | — | — |
| Events catalog updated | ✅ | — | — | — |
| Capability catalog updated | ✅ | — | — | — |
| OpenAPI schema updated | ✅ | ✅ | — | ✅ |
| ADR written | ✅ (if architectural) | — | — | — |
| CHANGELOG updated | ✅ | ✅ | ✅ | ✅ |
| Documentation updated | ✅ | ✅ | ✅ | — |
| Technical debt registered | ✅ (if incurred) | — | — | ✅ |
| Performance measured | ✅ | ✅ | — | — |
| Security reviewed | ✅ | ✅ (if security) | — | ✅ |
| Accessibility verified | ✅ (if UI) | — | — | — |
| Monitoring reviewed | ✅ | ✅ | — | ✅ |
| PO acceptance | ✅ | ✅ | — | — |

---

## 11. Quality Standards

### 11.1 Performance

| Standard | Target | Measurement |
|----------|--------|-------------|
| API p50 | < 50ms | Prometheus + Grafana |
| API p95 | < 200ms | Prometheus + Grafana |
| API p99 | < 500ms | Prometheus + Grafana |
| Dashboard load | < 2s | Lighthouse |
| Search p95 | < 100ms | Prometheus |
| Enrichment (async) | < 3s | Celery monitoring |
| Frontend bundle | < 500KB (gzip) | webpack-bundle-analyzer |
| First Contentful Paint | < 1.5s | Lighthouse |
| Time to Interactive | < 3s | Lighthouse |

### 11.2 Security

| Standard | Enforcement |
|----------|-------------|
| All endpoints authenticated | CI gate + automated scan |
| No secrets in code | detect-secrets pre-commit hook + CI |
| Parameterized SQL queries | Code review + automated scan |
| CSRF protection on mutations | Middleware enforcement |
| Rate limiting on all endpoints | Middleware configuration |
| Security headers on all responses | Middleware enforcement |
| JWT with RS256 (target) | Code + CI validation |
| Audit logging on all data changes | Event-driven audit trail |
| Dependency vulnerability scanning | pip-audit, npm audit in CI |
| SAST scanning | Bandit, Semgrep in CI |

### 11.3 Accessibility

| Standard | Target | Validation |
|----------|--------|------------|
| WCAG compliance | AA minimum, AAA target | axe-core + manual audit |
| Keyboard navigation | 100% of interactive elements | E2E test |
| Screen reader | All content accessible | Manual + automated |
| Color contrast | 4.5:1 (normal text), 3:1 (large) | CI check + axe-core |
| Focus indicators | Visible on all interactive | E2E test |
| Reduced motion | All animations respect `prefers-reduced-motion` | CSS audit |
| RTL support | All layouts mirror correctly | E2E test |

### 11.4 Testing

| Metric | Target | Current |
|--------|--------|---------|
| Unit test coverage | ≥ 90% | 93% |
| Integration coverage | ≥ 75% | 70% |
| E2E tests | ≥ 300 | 269 |
| Total tests | ≥ 3,000 | 2,110+ |
| Backend AI test coverage | ≥ 85% | 0% |
| Architecture compliance | ≥ 98% | 95% |
| Contract test coverage | 100% of endpoints | Partial |
| Load test regression | < 10% | Not tracked |

### 11.5 Code Quality

| Metric | Target | Current |
|--------|--------|---------|
| File size | ≤ 600 lines | 3 files > 700 lines |
| `Any` types in public interfaces | 0 | 284 |
| `# type: ignore` | 0 with justification | Present |
| `print()` / `console.log` in production | 0 | 2 |
| Commented-out code | 0 | Verified |
| Technical debt (tracked) | < 10 items | ~3 |

---

## 12. Feature Development Rules

### 12.1 Design Requirements

Every feature must:

1. Have an API-first design — API contracts defined before UI implementation
2. Use `@salesos/design-language` tokens for all visual properties
3. Use `@salesos/ui` components for all UI primitives
4. Have approved mockups before implementation begins
5. Follow the Container/View pattern for any widget
6. Support dark mode from day one
7. Support RTL from day one
8. Support keyboard navigation
9. Pass WCAG AA
10. Have loading, empty, error, and edge case states

### 12.2 Implementation Requirements

Every feature must:

1. Start with the API layer (OpenAPI schema, router, service, repository)
2. Use the Repository Pattern — domain never calls infrastructure directly
3. Use the Event Pattern — cross-domain effects via events
4. Be behind a feature flag (default OFF)
5. Include telemetry (at minimum: usage count, latency, error rate)
6. Follow the folder convention: `domain/`, `application/`, `infrastructure/`, `interface/`
7. Not exceed 600 lines per file
8. Have no cross-domain imports
9. Have no hardcoded configuration values
10. Include proper error handling with typed error responses

### 12.3 Review Requirements

Every feature must be reviewed for:

1. Architecture compliance (domain isolation, layer rules)
2. Code quality (naming, structure, complexity)
3. Test coverage (≥ 85% for new code, all acceptance criteria tested)
4. Security (auth, input validation, parameterized queries)
5. Performance (query efficiency, pagination, caching)
6. Accessibility (ARIA, keyboard nav, contrast, screen reader)
7. Internationalization (string externalization, RTL support)
8. Documentation (CHANGELOG, OpenAPI, user guide)
9. Events (are events needed? are they documented?)
10. Feature flags (correct default state, removal plan)

---

## 13. Screen Standards

Every screen must include:

### 13.1 Purpose

A clear, concise statement of what the screen does. This is the screen's reason for existing.

### 13.2 KPIs

Key performance indicators relevant to the screen's purpose. Every screen should display at least one KPI. Minimum: entity count or status. Target: 3-5 actionable KPIs with trend indicators.

### 13.3 AI

Every screen must integrate AI in at least one way:
- **Insights**: AI-generated summary or recommendation
- **Actions**: AI-suggested next steps
- **Search**: AI-powered search or autocomplete
- **Classification**: AI-driven categorization or scoring

### 13.4 Actions

Primary actions the user can take:
- Create (new entity)
- Edit (existing entity)
- Delete (with confirmation)
- Export (CSV, PDF)
- Share (link or report)
- Custom actions per screen context

### 13.5 Loading

- **Initial Load**: Skeleton components matching page layout
- **Action Load**: Spinner or progress indicator
- **Progressive Load**: Widget-level loading (not all-at-once)
- **Stale Data**: Show cached data while refreshing

### 13.6 Errors

- **API Error**: Banner with error message and retry action
- **Network Error**: Offline indicator with reconnection status
- **Permission Error**: Explanation and request access action
- **Not Found**: 404 with navigation back
- **Unexpected Error**: Error boundary with fallback UI and report action

### 13.7 Empty State

Every list, table, or data view must have an empty state:
- Illustration or icon
- Descriptive message
- Call to action (e.g., "Add your first company")
- Link to documentation or help

### 13.8 Permissions

Every action must check permissions:
- **View**: Show/hide data based on role
- **Create**: Show/hide create button based on permission
- **Edit**: Disable/enable edit capability
- **Delete**: Confirm dialog with permission check
- **Admin-only features**: Hidden from non-admin users

### 13.9 Responsive

Every screen must work on:
- **Desktop** (1280px+): Full layout with sidebar
- **Tablet** (768-1279px): Collapsed sidebar, adjusted grid
- **Mobile** (< 768px): Bottom navigation, stacked layout, touch targets ≥ 44px

### 13.10 Accessibility

Every screen must pass:
- Tab order matches visual order
- All interactive elements focusable
- ARIA landmarks for navigation
- Skip-to-content link
- Screen reader announcements for dynamic content
- Color not used as the only differentiator

---

## 14. Component Standards

### 14.1 Reusable Component Rules

1. Every component must have a single responsibility
2. Every component must have typed props (TypeScript interface)
3. Every component must use `@salesos/design-language` tokens
4. Every component must support dark mode
5. Every component must support RTL
6. Every component must have accessibility attributes
7. Every component must have a Storybook story
8. Every component must have unit tests (jest)
9. Every component must have visual regression tests
10. Every component must export its prop types

### 14.2 Component Tiers

| Tier | Description | Examples |
|------|-------------|---------|
| **Primitive** | Basic building blocks | Button, Input, Select, Checkbox |
| **Composite** | Composed from primitives | FormField, DataTable, Modal |
| **Pattern** | Reusable interaction patterns | SearchPanel, CommandBar, Wizard |
| **Feature** | Feature-specific components | CompanyProfile, PipelineKanban |

### 14.3 Component API Design

```typescript
// Good
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

// Avoid
interface BadButtonProps {
  color: string;           // Don't accept raw colors
  type: 'submit' | 'button'; // Use semantic names
  isDisabled?: boolean;    // Use consistent naming (disabled, not isDisabled)
}
```

### 14.4 Component Distribution

All reusable components must be in `@salesos/ui` or an appropriate feature package. No reusable component should be duplicated across feature modules.

**Rule of Three**: If a component pattern appears in 3+ places, extract it to a shared package.

---

## 15. Documentation Standards

### 15.1 ADR Standards

Every Architecture Decision Record must:

1. Be in `docs/adr/{NNNN}-title.md` format
2. Include: Status, Date, Author, Context, Decision, Consequences, Compliance
3. Reference the relevant section of the Project Bible or vNext plan
4. Be reviewed by the Architecture Review Board
5. Be immutable once approved (new ADR supersedes old one)

ADR Template:
```markdown
# ADR-NNNN: Title

**Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-NNNN]
**Date**: YYYY-MM-DD
**Author**: Name

## Context
Why is this decision needed?

## Decision
What is the decision?

## Consequences
Trade-offs, risks, and benefits.

## Compliance
How will this be enforced (CI check, manual review)?
```

### 15.2 Roadmap Standards

- Master roadmap in `docs/vnext/ROADMAP.md`
- Feature roadmap in `docs/vnext/FEATURE_ROADMAP.md`
- Sprint plan in `docs/vnext/SPRINT_PLAN.md`
- Updated at the start of each sprint
- All changes reviewed by Product Director + Engineering Director

### 15.3 Architecture Documentation

- Architecture overview in `docs/ARCHITECTURE_BOOK.md`
- Target architecture in `docs/vnext/ARCHITECTURE_VNEXT.md`
- Decision log in `docs/PROJECT_BIBLE.md` Section 17
- Each domain must have a minimal README in its folder

### 15.4 Code Comments

- No comments explaining "what" — code should be self-documenting
- Comments explaining "why" — business rules, edge cases, design decisions
- Docstrings on public APIs (Python: Google style, TypeScript: JSDoc)
- No commented-out code — delete it (it's in git history)
- TODO comments must reference a ticket number: `# TODO(SALES-123): description`

### 15.5 README Requirements

Every package and project must have a README with:
- Description
- Quick Start (30 seconds)
- Prerequisites
- Installation
- Usage examples
- Testing instructions
- API documentation (key surfaces)
- Configuration (environment variables)
- Link to CONTRIBUTING.md
- License

---

## 16. Release Standards

### 16.1 Versioning

- **Semantic Versioning**: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)
- **Pre-release**: `MAJOR.MINOR.PATCH-alpha.N`, `-beta.N`, `-rc.N`

### 16.2 Release Phases

| Phase | Duration | Gates |
|-------|----------|-------|
| **Alpha** | Ongoing | Feature flags ON in dev. Not for production. |
| **Beta** | 1 sprint | Feature flags ON in staging. Bug reports tracked. |
| **Release Candidate** | 1 week | All tests passing. Load tests passing. Security scan clean. |
| **General Availability (GA)** | — | Gradual rollout (10% → 50% → 100%). Error rate < 0.1%. p99 within budget. |

### 16.3 Release Checklist

```markdown
## Release vX.Y.Z Checklist

### Pre-Release
[ ] All PRs merged to main
[ ] Release branch cut from main
[ ] CHANGELOG updated with all changes
[ ] Version bumped in all relevant files
[ ] Load tests: no regression > 10%
[ ] Security scan: clean
[ ] Migration scripts: tested on staging
[ ] Rollback plan: documented
[ ] Monitoring: all metrics OK

### Release
[ ] Docker images built and tagged
[ ] Production deploy (gradual: 10% → 50% → 100%)
[ ] Smoke tests pass on production
[ ] Error rate < 0.1% at 5 min
[ ] p99 within budget at 15 min
[ ] Release branch merged back to main

### Post-Release
[ ] Technical debt from this release registered
[ ] Feature flags set to 100%
[ ] Feature flag removal tickets created (2 sprints from now)
```

### 16.4 Rollback Criteria

Rollback immediately if:
- Error rate > 1% for more than 5 minutes
- p99 exceeds budget by 2x for more than 15 minutes
- Critical security vulnerability discovered
- Data integrity issue confirmed

Rollback procedure:
1. Application: Revert Docker image to previous version tag
2. Database: Alembic `downgrade` to previous revision
3. Feature: Disable feature flag (no deploy needed)
4. Full: Revert git merge, rebuild, redeploy

### 16.5 Hotfix Process

1. Hotfix branch from `main`, merge to `main` + latest `release/*`
2. Bypasses quality gates with CTO override (documented in PR)
3. Technical debt registered within 24 hours
4. Formal PR with full testing created within 48 hours
5. Tests added within 1 sprint

---

## 17. Decision Log

This section summarizes all ratified architectural decisions for SalesOS vNext. Each decision references the relevant ADR or source document.

### D-001: Monorepo with Domain Boundaries

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-001, `docs/vnext/ARCHITECTURE_VNEXT.md`
**Decision**: Keep single monorepo with enforced domain boundaries. Use Nx/Turborepo for build orchestration. Fix monolithic files immediately (`api.ts`, `main.py`, `knowledge_graph_runtime`).
**Consequences**: + Atomic commits + Shared CI + Requires import boundary enforcement (ESLint + ruff) + 3 monolithic files must be split

### D-002: REST-first API

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-002
**Decision**: REST-first for vNext. GraphQL available for specific use cases with proper auth. N+1 solved at DB layer with DataLoader pattern.
**Consequences**: + Proven API pattern + Easy codegen + Auth simplicity + Must solve N+1 at DB layer

### D-003: URL-based API Versioning

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-003
**Decision**: `/api/v1/` → `/api/v2/` URL path versioning. Lockstep major version for the entire platform.
**Consequences**: + Clear migration path + Easy deprecation + All 57 routers need version prefix migration

### D-004: Full Kafka Adoption

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-004
**Decision**: Remove in-memory event bus. Full Kafka adoption with healthcheck fix, Celery worker, and migration per domain.
**Consequences**: + Durable event streaming + Production-grade + Ops complexity + TD-002 resolved

### D-005: Hybrid Agent Runtime

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-005, `docs/vnext/AI_STRATEGY.md`
**Decision**: Start with embedded runtime for simple AI calls. Build sidecar agent runtime in Sprint 11-12.
**Consequences**: + Simple start + Scales later + Requires isolation boundaries + Agent runtime placeholder replaced

### D-006: Multi-Provider LLM Strategy

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-006, `docs/vnext/AI_STRATEGY.md`
**Decision**: Provider abstraction layer. Minimum 2 providers: OpenAI + Anthropic. Local models for KSA data sovereignty.
**Consequences**: + No vendor lock-in + KSA compliance + Provider maintenance + Test matrix grows

### D-007: react-intl for i18n

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-007
**Decision**: `react-intl` (FormatJS) for internationalization. Best Arabic/RTL support.
**Consequences**: + Full i18n + Arabic translation + RTL support + Sprint 19-20 allocation

### D-008: Custom Connector SDK (Data Fabric)

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-008
**Decision**: Build lightweight connector SDK. Top 3 connectors (HubSpot, Salesforce, Zoho) in Sprint 15-16. Re-evaluate Airbyte in Phase 7.
**Consequences**: + Standard model + Testable + Top connectors delivered + Airbyte evaluation deferred

### D-009: Redis Everywhere

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-009
**Decision**: Redis for cache, rate limiting, session store. Single dependency, deploy to production in Sprint 1.
**Consequences**: + Single caching backend + Deploy Redis + Ops dependency + Invalidation strategy needed

### D-010: React Query + Zustand

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-010
**Decision**: React Query for server state, Zustand for client state. Enforce with import boundaries.
**Consequences**: + Clean separation + Performant + Add Zustand dependency + Boundary enforcement

### D-011: Widget SDK v1.0 Frozen (No v1.1)

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-011
**Decision**: Keep Widget SDK v1.0 Feature Frozen. Re-evaluate after Phase 2 with concrete gap evidence.
**Consequences**: + Stability + ADR process enforced + May require workarounds + Gaps proven before changes

### D-012: Extension API (Not Plugin System)

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-012
**Decision**: Extension API with defined extension points. No hot-loadable plugin system for vNext.
**Consequences**: + Simple to implement + Clear boundaries + No runtime loading + Versioning required

### D-013: Test Pyramid Audit & Consolidation

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-013, `docs/vnext/ENGINEERING_STRATEGY.md`
**Decision**: Audit existing tests, consolidate to single `tests/` directory, fill AI and Data Fabric gaps.
**Consequences**: + Consistent patterns + Reduced duplication + AI coverage from 0% + Audit effort (3 days)

### D-014: Centralized Configuration (Pydantic + Vault)

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-014
**Decision**: Pydantic BaseSettings for all domains. Vault for secrets. Single config schema per environment.
**Consequences**: + Validated config + No scattered env reads + Vault dependency + Migration effort

### D-015: Helm Charts for K8s

**Status**: Ratified
**Source**: `docs/vnext/DECISIONS.md` D-015
**Decision**: Helm charts with umbrella chart for all 9 production runtimes. Per-domain sub-charts.
**Consequences**: + Industry standard + Reusable + Learning curve + Multi-node scaling

### Frozen Interfaces (Protected by Constitution)

The following interfaces are **Frozen** and cannot be modified without ADR:

| Interface | ADR | Notes |
|-----------|-----|-------|
| Identity Domain | ADR-001 | 100% compliance, no debt |
| Widget SDK v1.0 | ADR-003 | Container/View pattern, lifecycle hooks, telemetry, permissions, flags |
| `describeWidgetContract()` | ADR-003 | Testing utility for widget contracts |

---

## 18. Future Vision

### SalesOS v2.5 (2027 H1)

**After vNext stabilization, focus on:**

1. **Public API** — Fully documented, versioned, rate-limited public API for third-party integration
2. **Plugin Marketplace** — Third-party widget and signal marketplace with billing
3. **Self-Service Tenants** — Automated tenant provisioning, billing, and onboarding
4. **Advanced AI Agents** — Multi-agent orchestration, autonomous workflow execution, agent-to-agent communication
5. **SSO/SAML** — Enterprise single sign-on with major providers
6. **Advanced Analytics** — OLAP cubes, custom dashboards, drag-and-drop report builder

### SalesOS AI OS (v3.0, 2027 H2)

**The platform becomes AI-native at every level:**

1. **Autonomous Agents** — Agents that proactively identify opportunities and execute workflows without human prompting
2. **Predictive Revenue Engine** — ML models that predict revenue outcomes with explainability
3. **Natural Language Interface** — Full conversational interface for all platform operations
4. **Multi-Region Deployment** — Data residency per region, global load balancing
5. **Enterprise SDK** — Full SDK for embedding SalesOS capabilities into other products

### SalesOS Ecosystem (v4.0, 2028+)

**The platform becomes an ecosystem:**

1. **Agent Ecosystem** — Third-party agents on the SalesOS Agent Marketplace
2. **Developer SDK** — Build custom widgets, signals, connectors, and agents
3. **Partner Platform** — Implementation partners, ISVs, and system integrators
4. **Cross-Platform Intelligence** — SalesOS intelligence embedded in Slack, Teams, email, and web
5. **Industry Clouds** — Pre-configured vertical solutions (Healthcare, Construction, Financial Services, Government)

### What Will Never Change

These are the non-negotiable foundations that every future evolution must preserve:

1. **Domain-Driven Design** with bounded contexts — the architectural foundation
2. **Repository Pattern** — domain/infrastructure separation for testability
3. **Widget SDK Container/View Pattern** — data/rendering separation
4. **Zero-Trust Security** — every endpoint authenticated, every request authorized
5. **Event-Driven Architecture** — cross-domain communication via events
6. **Multi-Tenancy by Design** — tenant isolation at every layer
7. **API-First Development** — UI is a client of the API, not the product
8. **Arabic/RTL Support** — core competence, not an afterthought
9. **KSA PDPL Compliance** — data sovereignty and privacy as architecture
10. **Modular Monolith with Extraction Paths** — pragmatism over microservice dogma

---

*This Project Bible is the highest authority for SalesOS development. It supersedes all prior project documentation. Changes require documented ADR and ratification by the Architecture Review Board.*

*"Build the platform you'd want to use. Protect the foundations that make it great."*
