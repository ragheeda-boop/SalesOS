# SalesOS — PROJECT MANIFEST

> **دستور SalesOS — المبادئ غير القابلة للتغيير، قرارات التصميم، معايير الجودة**
> Version 2.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## PREAMBLE

This Manifest is the supreme governing document of the SalesOS project. Every line of code, every architecture decision, every pull request, and every conversation with OpenCode must comply with this Manifest.

**Hierarchy of Authority:**
1. PROJECT_MANIFEST.md (How we build — supreme)
2. MASTER_BLUEPRINT.md (What we build — authoritative reference)
3. RUNTIME_ARCHITECTURE.md (How it runs at runtime — execution model)
4. PROJECT_STATUS.md (Where we are — completion tracker)
5. CAPABILITY_CATALOG.md (Complete capability registry)
6. Platform Constitution (`platform/CONSTITUTION.md` — immutable articles)
7. All ADRs (Architecture Decision Records)
8. All other `/docs/` documents

---

## PART I: IMMUTABLE PRINCIPLES

These principles CANNOT be violated. Doing so requires a formal Amendment via ADR with CTO approval.

### Principle 1: Domain-Driven Design First
Every module is a bounded context with zero cross-domain Python imports. Domains communicate only through events and contracts. No domain directly imports another domain's models, services, or repositories.

### Principle 2: SDK Sovereignty
All cross-cutting concerns (Permissions, Audit, Events, Telemetry, Metadata) go through the SalesOS SDK. No module implements its own auth, logging, or event publishing. Violations must be refactored immediately.

### Principle 3: Event-Driven State Changes
Every domain mutation emits a CloudEvents 1.0 DomainEvent. There is no silent state change. No event → no change. The EventBus is the nervous system of the platform.

### Principle 4: Repository Abstraction
Every domain service depends on a Repository interface, never on a concrete database implementation. Services must be testable with InMemoryRepository. This guarantees:
- Testability without a database
- Replaceability of storage technology
- Domain isolation from infrastructure concerns

### Principle 5: Frozen Interface Protection
Interfaces marked as Frozen (SearchQuery, SearchResult, SearchPlanner, TimelineEvent, DomainEvent, Actor→Activity→Target→Outcome) cannot be modified without an ADR, a Benchmark, and Architecture Review. These are the platform's API to the future.

### Principle 6: Measurement Before Optimization
No technology is added (Index, Cache, Vector Store, Queue, AI Model, NoSQL) without a Benchmark proving the need. PostgreSQL + Trigram is the default. Everything else must earn its place with data.

### Principle 7: Business Over Technology
If a business requirement conflicts with a technology preference, the technology is re-evaluated — not the business requirement. The stack serves the domain.

### Principle 8: Data Sovereignty
Data is the System of Record. AI is a consumer, never the sole source of truth. No AI Agent or Embedding model can be the only record of a business fact. Every AI-generated insight must be traceable to source data.

### Principle 9: Append-Only Timeline
The Timeline is immutable. Events are appended, never updated or deleted. If a correction is needed, a new event is emitted that supersedes the old one. History is never rewritten.

### Principle 10: Forecast Never Owns Facts
The Forecast domain computes predictions from immutable snapshots of other domains (Opportunities, Activities, Quotes, Contracts). It never owns business facts. It is a consumer, not an authority.

### Principle 11: Platform-First Design (V4)
Every feature is built as a platform capability before becoming an application. No application UI is built until its underlying platform capability (API + DB + Workflow + Permissions) is complete and tested. This guarantees the Intelligence Fabric is available to all consumers, not just the first app.

### Principle 12: Capability Surface Completeness (V4)
Every capability must expose the full surface: API + UI + Database + Workflow + Permissions + AI + Reports + Events + Metrics. A capability with missing surface is a capability in progress, not complete. Partial surface blocks promotion to market-ready status.

### Principle 13: API Plurality (V4)
All capabilities are accessible through all four API surfaces: REST + GraphQL + MCP Server + Agent SDK. No capability is REST-only. The MCP Server makes SalesOS a knowledge source and tool provider for any AI agent ecosystem, not just our own UI.

### Principle 14: Knowledge Portability (V4)
All domain knowledge is packaged in portable, installable Knowledge Packs. Each pack contains: Ontology + Signals + Scoring + Prompts + Workflows + Dashboards + Reports + AI Memory + Competitors. Industry knowledge is never hardcoded — it is always a Pack.

### Principle 15: Revenue Graph Primacy (V4)
The Revenue Graph (Company → Contact → Deal → Activity → Campaign → Revenue → Forecast) is the authoritative relationship store for all commercial entities. It takes precedence over ad-hoc relationship modeling. Every new commercial entity adds to this graph.

### Principle 16: Feature Store Singularity (V4)
Every computed feature is computed once and consumed everywhere. Duplicate computation is forbidden. Features (Growth Rate, Funding Score, Hiring Velocity, ICP Score, Intent Score, Revenue Score) are computed by the Feature Store and served to Scoring, Forecasting, AI, Analytics, and Dashboards.

### Principle 17: Semantic Cache First (V4)
Every LLM query passes through the Semantic Cache before model invocation. If a semantically similar query exists, the cached response is returned — saving 40-70% on LLM costs. The cache is invalidated when source data changes, not on a timer.

### Principle 18: Timeline Universality (V4)
Every entity has an append-only timeline — not just Companies. Deals, Contacts, Meetings, Campaigns, Tasks, Workflows, and AI decisions all have timelines. The Kernel Timeline service is universal.

### Principle 19: Simulation Before Execution (V4)
Every workflow, email campaign, or sequence is simulated before production execution. Simulation predicts replies, meetings, and revenue outcomes. No bulk action executes without simulation results available for review.

### Principle 20: Next Best Action (V4)
The Revenue Brain computes a Next Best Action for every user interaction. Every page, dashboard, and notification is guided by what action maximizes revenue impact for the current context. This is the primary output of the Intelligence Fabric.

### Principle 21: Capability over Module (V5)
The term "Module" is deprecated. Every platform component is a **Capability** with full surface area: Domain + API + UI + AI + Workflow + Events + Analytics + Permissions + Documentation + Tests + Monitoring. No new "modules" shall be created — only Capabilities.

### Principle 22: Deterministic Request Path (V5)
Every user request follows the documented Runtime Flow (docs/RUNTIME_ARCHITECTURE.md). No capability bypasses the runtime layer. No silent execution. Every request produces a trace, a log, and a metric.

### Principle 23: Digital Twin Every Workspace (V5)
Every workspace has a Digital Twin that continuously computes current state, predictions, risks, scenarios, recommendations, and outcomes. No workspace operates blind to its future state.

### Principle 24: Decision Intelligence over Reporting (V5)
Every dashboard displays not just what happened, but what to do about it. Every page is guided by the Revenue Brain's Next Best Action. Reporting is the baseline; Decision Intelligence is the standard.

### Principle 25: Feedback Loop Completeness (V5)
Every prediction has an actual outcome recorded. Every AI model has a feedback loop. Every recommendation is measured for accuracy. No model or recommendation operates without outcome tracking.

### Principle 26: Resilience by Default (V5)
Every capability implements Circuit Breaker, Retry with Backoff, Timeout, and Fallback patterns. No external dependency is assumed available. The platform degrades gracefully when dependencies fail.

---

## PART II: ARCHITECTURE DECISIONS (ADRs)

### ADR-001: Modular Monolith First, Microservices Later
- **Status:** Accepted
- **Context:** Team size 5-7, uncertain domain boundaries, deployment simplicity
- **Decision:** Modular monolith with strict module boundaries. Extract to microservices when a module needs independent scaling or has a dedicated team.
- **Consequences:** In-process EventBus (replaceable with Kafka), cross-module JOINs allowed (trade-off for simplicity), database schemas namespaced per domain.

### ADR-002: PostgreSQL as Primary OLTP
- **Status:** Accepted
- **Rationale:** pgvector, JSONB, full-text search (Arabic + English), RLS, extensions ecosystem, 30+ year maturity.
- **Consequence:** Single-node write bottleneck acceptable to millions of records. Read replicas for scale.

### ADR-003: Neo4j for Knowledge Graph
- **Status:** Accepted
- **Rationale:** Cypher, Graph Data Science algorithms, temporal properties on edges.
- **Consequence:** Second database to manage. Eventual consistency between PostgreSQL and Neo4j.

### ADR-004: Kafka for Event Streaming
- **Status:** Accepted
- **Rationale:** Durability, replay, tenant-level partitioning, ecosystem (Kafka Connect, Schema Registry).
- **Consequence:** Start with in-process EventBus. Add Kafka when event volume exceeds in-memory capacity.

### ADR-005: pgvector over Dedicated Vector DB
- **Status:** Accepted
- **Rationale:** Single database, JOIN company + embedding, HNSW indexes, no additional service cost.
- **Consequence:** May need migration at 100M+ vectors (Year 3+).

### ADR-006: FastAPI for REST API
- **Status:** Accepted
- **Rationale:** Python ecosystem, async-native, Pydantic validation, OpenAPI auto-docs.

### ADR-007: Apache Iceberg for Data Lake
- **Status:** Accepted (future)
- **Rationale:** Open format, ACID on data lake, engine flexibility.

### ADR-008: Phased Build Order
- **Status:** Accepted
- **Order:** Identity → Company → Search → Timeline → CRM → Scoring → AI → Workflow → Marketplace → Data Lake

### ADR-009: In-Memory Repositories First
- **Status:** Accepted (temporary)
- **Rationale:** Validate domain logic before committing to persistence. All services must work with InMemoryRepository before PostgreSQL implementation.
- **Consequence:** Transition to PostgreSQL repositories is P0 critical path.

### ADR-010: CloudEvents 1.0 Standard
- **Status:** Accepted
- **Consequence:** All events follow CloudEvents spec. Interoperable with any CloudEvents-compatible system.

---

## PART III: NAMING CONVENTIONS

### Code
| Element | Convention | Example |
|---------|-----------|---------|
| Python files | `snake_case` | `company_service.py` |
| Classes | `PascalCase` | `CompanyService` |
| Functions/Methods | `snake_case` | `compute_lead_score()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_SEARCH_RESULTS` |
| Type variables | `CamelCase` | `T`, `TEntity` |
| Private members | `_prefix` | `_validate_cr()` |

### Database
| Element | Convention | Example |
|---------|-----------|---------|
| Schemas | `snake_case` | `company`, `identity` |
| Tables | `snake_case` (singular) | `organization`, not `organizations` |
| Columns | `snake_case` | `legal_name_ar` |
| Foreign Keys | `{table}_id` | `organization_id` |
| Junction Tables | `{table1}_{table2}` | `person_organization` |
| Primary Keys | `id` (UUID) | — |
| Timestamps | `created_at`, `updated_at`, `deleted_at` | — |
| Soft Delete | `deleted_at TIMESTAMPTZ` | — |
| Optimistic Lock | `version INTEGER` | — |

### API
| Element | Convention | Example |
|---------|-----------|---------|
| URL paths | `/v1/{resource}` | `/v1/companies` |
| Resource names | Plural | `/companies`, `/contacts` |
| Query params | `snake_case` | `?page_size=20` |
| JSON fields | `snake_case` | `legal_name_ar` |

### Git
| Element | Convention | Example |
|---------|-----------|---------|
| Branches | `feat/`, `fix/`, `chore/`, `hotfix/` | `feat/SALES-42-company-ingestion` |
| Commits | Conventional Commits | `feat(company): add ingestion pipeline` |
| PRs | Squash merge to main | — |

---

## PART IV: QUALITY STANDARDS

### Code Quality
1. **Ruff** for linting (all rules enabled). Pass before commit.
2. **Black** for formatting (line length 100). Pass before commit.
3. **mypy** strict mode. No `Any` without explicit justification comment.
4. **Google-style docstrings** on every public function/method.
5. **No commented-out code.** Delete it. Git has it.
6. **No print statements.** Use `structlog` for structured logging.
7. **No TODO/FIXME without ticket number.** `TODO(SALES-42): implement dedup`

### Test Quality
1. **Every service function must have unit tests.**
2. **Tests use InMemoryRepository** — never require a real database.
3. **Test must be deterministic** — no flaky tests.
4. **Test <1 second each** — entire unit suite <30 seconds.
5. **Coverage >85% on business logic.** Not measured on DTOs, config, migrations.

### API Quality
1. **Every endpoint returns RFC 7807 problem details on errors.**
2. **Every endpoint has OpenAPI schema** (auto from Pydantic).
3. **Every mutation endpoint is idempotent** where possible.
4. **Every list endpoint supports pagination** (page + page_size).
5. **Every endpoint has a Sunset header for deprecated versions.**
6. **Rate limiting by tenant** — 1000 req/min default.

### Security
1. **Never log PII** (emails, phones, names in plaintext).
2. **Never store secrets in code** — environment variables or Vault.
3. **Always parameterize SQL** — no string interpolation.
4. **Always validate at API boundary** — Pydantic models.
5. **Always TLS 1.3** in production.
6. **Always security scan** in CI (bandit, safety).
7. **Rotate API keys every 90 days.**

### Architecture Quality
1. **No circular dependencies** between modules — enforced by arch tests.
2. **No cross-domain imports** — domain isolation verified by tests.
3. **No infrastructure imports in domain layer** — domain is pure Python.
4. **Every feature behind a feature flag** — default OFF.
5. **Flags removed within 2 sprints of GA.**

---

## PART V: WHAT IS PERMITTED AND FORBIDDEN

### ✅ Permitted
- Adding new domains under `salesos/modules/` following the module template
- Adding new engines under `salesos/domains/` following domain isolation rules
- Implementing PostgreSQL repositories for existing in-memory domains
- Creating frontend pages using shadcn/ui components
- Adding new event types following CloudEvents 1.0 spec
- Adding new AI models through the EmbeddingService abstraction
- Creating integration tests with test databases
- Adding benchmark scenarios to `backend/benchmark/`
- Creating CLI commands in `backend/cli/`
- Adding new Knowledge Packs under `knowledge_packs/`
- Creating a new Business Capability following the capability template
- Adding new Signals to the Signal Registry
- Implementing MCP Server tools
- Creating experiments in the Experiment Engine
- Adding new Feature Store computations

### 🟡 Permitted with ADR
- Modifying a Frozen Interface
- Adding a new database technology (beyond PostgreSQL + Neo4j)
- Changing the modular monolith architecture
- Adding a new AI provider (beyond OpenAI)
- Changing the event serialization format
- Removing or modifying a constitutional article
- Changing the build order of phases
- Adding a new API surface (beyond REST, GraphQL, MCP, Agent SDK)
- Changing the Revenue Graph schema (entities, edges, properties)
- Modifying the Semantic Cache strategy

### ❌ Forbidden
- Cross-domain Python imports (domain → domain directly)
- Bypassing SDK for Permissions, Audit, Events, Telemetry, or Metadata
- Hardcoding secrets in source code
- Writing tests that require a real database connection
- Modifying alembic migration history after commit
- Using `Any` in type annotations without justification
- Calling external APIs in unit tests
- Merging code that fails lint, type check, or tests
- Adding a technology without a benchmark proving the need
- Storing PII in logs (use structured logging with redaction)
- Hardcoding computed features (must use Feature Store)
- Building application UI before its platform capability is complete
- Adding LLM calls without passing through Semantic Cache
- Creating domain entities outside the Revenue Graph structure
- Duplicating feature computation across domains
- Executing bulk actions without simulation results

---

## PART VI: OPENCODE USAGE RULES

### Before Every Task
OpenCode MUST read (in order):
1. `docs/PROJECT_MANIFEST.md` — How to build
2. `docs/MASTER_BLUEPRINT.md` — What to build
3. `docs/RUNTIME_ARCHITECTURE.md` — How it runs
4. `docs/PROJECT_STATUS.md` — Where we are
5. `platform/CONSTITUTION.md` — Immutable principles
6. `docs/CAPABILITY_CATALOG.md` — Capability definitions
7. `docs/EVENT_CATALOG.md` — Event definitions (if working on events)
8. `docs/AI_CATALOG.md` — AI assets (if working on AI)

### During Every Task
1. Check if the capability/domain already exists before creating new code
2. Follow the existing patterns (capability template, domain structure, service/repository)
3. Never add cross-domain imports
4. Always use SDK for cross-cutting concerns
5. Write tests alongside implementation
6. Add events for every domain mutation
7. Follow the Runtime Architecture execution model
8. Run lint + type check before completing

### After Every Task
1. Update `docs/PROJECT_STATUS.md` with completion percentages
2. Add any new ADRs to this Manifest
3. Update MASTER_BLUEPRINT.md if architecture changed
4. Record technical debt found during implementation
5. Update EVENT_CATALOG.md if new events were added
6. Update AI_CATALOG.md if new AI assets were created

---

## PART VII: CODE ACCEPTANCE CRITERIA

For any code to be accepted (merged):

### Gate 1: Architecture Compliance
- [ ] Complies with all 26 Constitutional + Platform + Runtime Principles
- [ ] No cross-domain imports
- [ ] Uses SDK for cross-cutting concerns
- [ ] Follows capability template (not "module")
- [ ] No Frozen Interfaces modified (without ADR)
- [ ] Follows Runtime Architecture execution model

### Gate 2: Quality
- [ ] Ruff passes (all rules)
- [ ] mypy strict mode passes
- [ ] Black formatting applied
- [ ] Google-style docstrings on public API
- [ ] No debug/print statements
- [ ] No hardcoded secrets
- [ ] Lint + type check pass in CI

### Gate 3: Testing
- [ ] Unit tests for all new business logic
- [ ] Tests use InMemoryRepository
- [ ] All existing tests pass
- [ ] Architecture constraint tests pass
- [ ] No test depends on external services
- [ ] Integration tests pass against PostgreSQL (if applicable)

### Gate 4: Events & Telemetry
- [ ] Domain events emitted for all mutations
- [ ] Structured logging added
- [ ] Audit trail for all user-initiated mutations
- [ ] Feature flag added (if new feature)
- [ ] Observability: trace, log, metric for new capability

### Gate 5: Documentation
- [ ] ADR added (if architectural decision)
- [ ] API changes reflected in OpenAPI schema
- [ ] README updated if project structure changed
- [ ] PROJECT_STATUS.md updated
- [ ] EVENT_CATALOG.md updated (if new events)
- [ ] AI_CATALOG.md updated (if new AI assets)
- [ ] CAPABILITY_CATALOG.md updated (if new or modified capability)

---

## PART VIII: AMENDMENT PROCESS

This Manifest is a living document. Amendments require:

1. **Rationale** — Why the change is needed
2. **Impact Analysis** — What existing rules are affected
3. **CTO Approval** — Final sign-off
4. **Documentation** — Update this Manifest with change log entry

### Change Log
| Date | Section | Change | Approver |
|------|---------|--------|----------|
| 2026-06-30 | All | Initial version | CTO |
| 2026-06-30 | Part I (Principles 11-20) | V4 Platform Principles added (Platform-First, Capability Surface, API Plurality, Knowledge Portability, Revenue Graph, Feature Store, Semantic Cache, Timeline Universality, Simulation, Next Best Action) | CTO |
| 2026-06-30 | Part V | Updated Permitted/Forbidden for V4 architecture (Knowledge Packs, Feature Store, Semantic Cache, Simulation, MCP) | CTO |
| 2026-06-30 | Part I (Principles 21-26) | V5 Runtime Principles added (Capability over Module, Deterministic Request Path, Digital Twin, Decision Intelligence, Feedback Loop, Resilience by Default) | CTO |
| 2026-06-30 | Part II | Updated ADR hierarchy with new docs | CTO |
| 2026-06-30 | Part VI | Updated OpenCode rules to read new V5 docs (RUNTIME_ARCHITECTURE, CAPABILITY_CATALOG, EVENT_CATALOG, AI_CATALOG) | CTO |
| 2026-06-30 | Part VII | Updated Code Acceptance Gates with V5 checks (26 principles, observability, 7 new catalog docs) | CTO |

---

*This Manifest is binding on all SalesOS development activity.*
*Violations must be corrected before code is accepted.*
