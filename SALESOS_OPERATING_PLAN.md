# SalesOS — Operating Plan v1

> **دليل التشغيل المتكامل — من Prototype إلى شركة SaaS عالمية**
> Version 1.0 | Last Updated: 2026-07-08
> Owner: CTO / Chief Architect

---

## Philosophy

نحن لم نعد مطورين نضيف Features.

نحن **شركة تبني منتج SaaS**، تديرها AI Workforce، وتعمل بنظام Pipeline صارم.

كل سطر كود يمر عبر: Architect → Developer × N → Reviewer → Security → Performance → Test → Refactor → Release.

لا يوجد Commit مباشر إلى Main. لا يوجد Feature قبل Foundation.

---

## محتويات الخطة

1. [Product Roadmap — 11 مرحلة](#1-product-roadmap)
2. [AI Workforce — 6 طبقات و 30+ Agent](#2-ai-workforce)
3. [Skills Library — 20+ Skill قابلة لإعادة الاستخدام](#3-skills-library)
4. [Dependency Graph & Sequencing](#4-dependency-graph)
5. [Execution Model — كيف تعمل الـ Pipeline](#5-execution-model)
6. [Quality Gates](#6-quality-gates)
7. [KPIs & Success Criteria لكل مرحلة](#7-kpis)
8. [OpenCode Configuration](#8-opencode-configuration)

---

# 1. Product Roadmap

## Phase 0 — Foundation (Weeks 1-8)

**لا Feature. فقط بنية تحتية.**

| Priority | Area | Deliverable | Dependencies | AI Agent |
|----------|------|-------------|--------------|----------|
| P0 | Persistence | PostgreSQL Repositories (Identity + Company) | None | Backend Engineer |
| P0 | Database | Alembic Baseline Migration | None | Database Engineer |
| P0 | Entity Resolution | Matching Engine + Golden Record Store | Scrapers exist | AI Engineer |
| P0.5 | CI/CD | GitHub Actions: lint → type → test → build → deploy | Repos ready | Platform Architect |
| P0.5 | Design System | shadcn/ui: Button, Input, Card, Table, Dialog, Form | None | Frontend Architect |
| P0.5 | Observability | OpenTelemetry + structured logging + metrics | SDK exists | Platform Architect |
| P0.5 | Error Handling | Circuit Breaker + Retry + Timeout + Fallback | SDK exists | Backend Engineer |
| P0.5 | Data Ingestion | Scrapers → Normalizers → Platform Pipeline | Scrapers exist | Integration Engineer |

**Exit Criteria:**
- [x] 100% of domain services work with PostgreSQL (not in-memory)
- [x] CI/CD passes on every PR — lint, type, test, build
- [x] Design System deployed as npm package
- [x] All 5 scrapers feed into unified data pipeline
- [x] p95 API latency < 200ms

---

## Phase 1 — Core Platform (Weeks 9-16)

| Priority | Area | Deliverable | Dependencies |
|----------|------|-------------|--------------|
| P0 | Identity | Multi-tenant: Users, Orgs, Teams, Roles, Permissions | Phase 0 |
| P0 | API Gateway | Rate limiting, AuthZ, Routing | Phase 0 |
| P1 | Core Services | Files, Notifications, Audit Logs, Settings | Phase 0 |
| P1 | Data Platform | Redis caching, Object Storage (MinIO), pgvector tuned | Phase 0 |
| P1 | Search Backend | Full-text + Semantic + Graph — all persisted | Phase 0 |
| P1 | Company 360 Layout | Frontend pages structure, routing, shell | Phase 0 |

**Exit Criteria:**
- [x] Multi-tenant with schema-per-tenant or RLS
- [x] API Gateway enforces rate limits + auth on every request
- [x] Search returns results from persisted data in < 500ms
- [x] Company 360 page renders with real data

---

## Phase 2 — CRM Engine (Weeks 17-24)

| Entity | Backend | Frontend | AI |
|--------|---------|----------|----|
| Companies | CRUD + Search + Merge | List + Detail + Edit | Dedup suggestions |
| Contacts | CRUD + Search + Import | List + Detail + Edit | Enrichment |
| Deals | Pipeline stages + value | Kanban + Detail | Win probability |
| Leads | Capture + Score + Route | List + Score | Lead scoring |
| Activities | Timeline + Calendar | Timeline widget | Next action |
| Meetings | Schedule + Notes | Calendar + Detail | Summary AI |
| Tasks | Assign + Track + Status | Board + List | Priority AI |
| Notes | Rich text + Files + Tags | Editor + Gallery | Auto-tagging |

**Exit Criteria:**
- [x] Full CRM cycle: Lead → Contact → Deal → Close
- [x] Pipeline Kanban with drag-and-drop
- [x] Activity Timeline for every entity
- [x] Import/Export via Excel

---

## Phase 3 — Company Intelligence (Weeks 25-32)

**أهم صفحة في المنتج.**

| Module | Description |
|--------|-------------|
| Overview | Summary card + key metrics + AI snapshot |
| Timeline | Every event ever (append-only) |
| Relationships | Parent, subsidiary, partners, competitors |
| Documents | CRs, licenses, contracts, reports |
| Financials | Revenue, funding, growth trajectory |
| Government Data | Balady, Najiz, Taqeem, NCNP, REGA |
| Website | Domain validation, tech stack, traffic |
| LinkedIn | Company page, employees, posts |
| Signals | Growth, hiring, funding, risk |
| AI Summary | GPT-4o generates executive brief |

**Exit Criteria:**
- [x] Company 360 loads in < 2s with all sections
- [x] Government data from all 5 scrapers displayed
- [x] AI Summary generates in < 5s
- [x] Signals computed from 10+ data sources

---

## Phase 4 — Employee Intelligence (Weeks 33-38)

| Feature | Description |
|---------|-------------|
| Profile | Skills, experience, education, certifications |
| Performance | KPIs, OKRs, feedback, ratings |
| Activities | Meetings, emails, tasks, calls |
| AI Coach | Personalized development recommendations |
| Org Chart | Interactive hierarchy view |
| Career Path | Projected growth, suggested moves |

---

## Phase 5 — Universal Search (Weeks 39-42)

ليس Search عادي. **Search Engine شامل:**

```
Search Bar
    ↓
[Query Parser] → Arabic/English detection → Intent classification
    ↓
[Search Planner] → Routes to:
    ├── Full-text (PostgreSQL trigram)
    ├── Semantic (pgvector HNSW)
    ├── Graph (Neo4j traversal)
    └── Signals (Feature Store)
    ↓
[RRF Fusion] → Reciprocal Rank Fusion
    ↓
[Rerank] → Cross-encoder model
    ↓
[Results] → Companies, Contacts, Deals, Meetings, Files, Signals
```

**Exit Criteria:**
- [x] Search across 6 entity types
- [x] Arabic + English query support
- [x] p50 latency < 200ms, p95 < 1s
- [x] Precision@10 > 0.85

---

## Phase 6 — Intelligence Fabric (Weeks 43-52)

**أهم مرحلة في المشروع — تبدأ مع Entity Resolution من Phase 0 وتنضج هنا.**

| Component | Description | AI Agent |
|-----------|-------------|----------|
| Entity Resolution | Golden record merge for all 5 scraper sources | AI Engineer |
| Feature Store | 20+ computed features: Growth, Hiring, Funding, ICP, Intent, Risk | Data Engineer |
| Knowledge Graph | Neo4j: Company ⟷ Contact ⟷ Deal ⟷ Activity | Database Engineer |
| Signal Engine | 50+ signals from all data sources | AI Engineer |
| Scoring Engine | ICP fit, Engagement, Intent, Risk, Health | AI Engineer |
| Growth Intel | Hiring velocity, funding rounds, expansion signals | Company Researcher |
| Intent Intel | Website visits, job posts, news mentions | Market Intelligence |
| Revenue Health | Pipeline health, deal velocity, win rate | Sales Director AI |

**Exit Criteria:**
- [x] Entity Resolution with > 95% precision on golden records
- [x] Feature Store serves features in < 50ms
- [x] Knowledge Graph answers relationship queries in < 200ms
- [x] Signal Engine detects signals in near-real-time

---

## Phase 7 — Revenue Brain (Weeks 53-60)

يتحول النظام من CRM إلى **Revenue OS**.

| Capability | Description |
|------------|-------------|
| Next Best Action | لكل مستخدم — ما هو الإجراء التالي الذي يعظم الإيراد؟ |
| Opportunity Detection | اكتشاف الفرص المخفية من الإشارات |
| Risk Detection | صفقات معرضة للخطر، عملاء قد يغادرون |
| Forecast | توقعات دقيقة مع فترات ثقة |
| Win Probability | احتمال إغلاق كل صفقة مع الأسباب |
| Expansion | فرص التوسع في الحسابات القائمة |
| Renewal | توقعات التجديد مع توصيات |
| Executive Summary | ملخص تنفيذي ذكي لكل مستوى إداري |

**Architecture:**

```
[All Data Sources] → [Feature Store] → [Revenue Brain]
                                            ↓
                              ┌─────────────────────────┐
                              │  Next Best Action        │
                              │  Opportunity Detection   │
                              │  Risk Detection          │
                              │  Forecast                │
                              │  Win Probability         │
                              │  Expansion               │
                              │  Renewal                 │
                              └─────────────────────────┘
                                            ↓
                              [Recommendation Engine]
                                            ↓
                              [User: Dashboard / Notification / API]
```

---

## Phase 8 — Workflow Automation (Weeks 61-66)

| Feature | Description |
|---------|-------------|
| Workflow Designer | Visual drag-and-drop workflow builder |
| Business Rules | No-code rule engine (if-then-else) |
| Triggers | Event-based, schedule-based, webhook |
| Conditions | Complex condition builder |
| Actions | Email, Webhook, Update, Create, Notify, AI Agent |
| Approvals | Multi-step approval chains |
| Simulation | "What if we run this workflow?" — predict outcomes |

---

## Phase 9 — AI Platform (Weeks 67-72)

**بدلاً من Chat — Platform.**

| Component | Description |
|-----------|-------------|
| LLM Gateway | Unified interface to OpenAI, Anthropic, open-source |
| Prompt Management | Versioning, testing, evaluation, rollback, A/B |
| Memory | Entity memory with importance decay |
| RAG | Query → Retrieve → Fuse → Rerank → Generate |
| Semantic Cache | Embedding-based cache — saves 40-70% |
| MCP Server | Model Context Protocol — connect any AI agent |
| Tools | Function calling framework with auth |
| AI Governance | Cost tracking, latency, accuracy, hallucination |
| AI Playground | Experiment: Prompt × Model × Temperature |

---

## Phase 10 — Marketplace (Weeks 73-80)

| Feature | Description |
|---------|-------------|
| Plugin SDK | Third-party plugin development kit |
| Extensions | UI extensions, data sources, signals |
| Templates | Workflow templates, dashboard templates |
| Knowledge Packs | Industry-specific: Healthcare, Construction, Finance |
| Industry Packs | ICP scoring calibrated per industry |
| Developer Portal | Docs, SDK, API keys, analytics |
| Revenue Share | 70/30 split with developers |

---

## Phase 11 — Enterprise (Weeks 81-90)

| Feature | Description |
|---------|-------------|
| Multi-Tenant SSO | SAML 2.0, OIDC, SCIM |
| Audit | Immutable audit trail for compliance |
| Compliance | SOC 2 Type II, ISO 27001 readiness |
| Data Residency | KSA, UAE, EU, US regions |
| SLA | 99.9% → 99.99% |
| Support | Enterprise support tiers |
| Billing | Usage-based + subscription + marketplace |

---

# 2. AI Workforce

## 2.1 Architecture Team

### Agent: Chief Architect

```yaml
name: chief-architect
role: Architecture governance — writes zero features
responsibilities:
  - Review all ADRs before implementation
  - Enforce DDD, Clean Architecture, domain isolation
  - Approve/reject architecture decisions
  - Maintain docs/PROJECT_MANIFEST.md
  - Maintain docs/MASTER_BLUEPRINT.md
gates:
  - No PR merges without Chief Architect review
  - No new dependency without ADR
  - No cross-domain imports
skills: [ddd-review, clean-architecture, api-design, adr-authoring]
```

### Agent: Platform Architect

```yaml
name: platform-architect
role: Infrastructure + Backend + SDK
responsibilities:
  - Maintain Docker, K8s, Terraform
  - SDK integrity — no module bypasses SDK
  - Database architecture, caching, queues
  - Performance budgets
  - CI/CD pipeline
skills: [infrastructure-review, sdk-governance, postgres-optimization]
```

### Agent: Frontend Architect

```yaml
name: frontend-architect
role: React + Next + UX + Performance
responsibilities:
  - Design system governance
  - Component library architecture
  - Bundle size budgets
  - Accessibility standards
  - RTL/Arabic layout
skills: [react-review, design-system, accessibility, rtl-arabic]
```

---

## 2.2 Development Team

### Agent: Backend Engineer

```yaml
name: backend-engineer
role: Build API, Repositories, Services, Workers
responsibilities:
  - Implement domain services following DDD
  - Repository pattern (interface → implementation)
  - REST endpoints with Pydantic validation
  - Event emission for every mutation
  - Unit tests with InMemoryRepository
context: |
  You must:
    1. Read PROJECT_MANIFEST.md for rules
    2. Read MASTER_BLUEPRINT.md for architecture
    3. Check CAPABILITY_CATALOG.md before creating new code
    4. Never add cross-domain imports
    5. Always use SDK for cross-cutting concerns
    6. Always write tests alongside implementation
    7. Run lint + type check before completing
skills: [fastapi, sqlalchemy, ddd, repository-pattern, event-driven]
```

### Agent: Frontend Engineer

```yaml
name: frontend-engineer
role: Build Pages, Components, Hooks, UI
responsibilities:
  - Implement pages following the capability template
  - Use shadcn/ui + Radix + Tailwind
  - Arabic-first, RTL layout
  - React Query hooks for every API
  - Zustand for client state
skills: [nextjs, react, shadcn-ui, tailwind, rtl-arabic]
```

### Agent: Database Engineer

```yaml
name: database-engineer
role: Schema, Indexes, Queries, Optimization
responsibilities:
  - Write Alembic migrations
  - Optimize queries (EXPLAIN ANALYZE)
  - Index strategy (B-tree, GIN, GiST, HNSW)
  - Connection pooling
  - Backup/restore strategies
skills: [postgresql, alembic, query-optimization, indexing]
```

### Agent: AI Engineer

```yaml
name: ai-engineer
role: RAG, Agents, Prompting, Memory, Embeddings
responsibilities:
  - Implement RAG pipeline (SearchPlanner → Retrieve → Fuse → Rerank → Generate)
  - Build AI agents with memory
  - Prompt versioning and evaluation
  - Embedding pipeline
  - Semantic Cache integration
skills: [rag, prompt-engineering, embeddings, agent-framework, mcp]
```

### Agent: Search Engineer

```yaml
name: search-engine
role: Full-text + Semantic + Graph + Hybrid Search
responsibilities:
  - Maintain SearchPlanner, SearchQuery, SearchResult
  - RRF fusion algorithm
  - Cross-encoder reranking
  - Arabic NLP tokenization
  - Search quality benchmarks
skills: [search-engineering, rrf, cross-encoder, arabic-nlp]
```

---

## 2.3 Quality Team

### Agent: Code Reviewer

```yaml
name: code-reviewer
role: Review every PR
rules:
  - No cross-domain imports
  - Repository interface before implementation
  - Tests exist for every service
  - No print/debug statements
  - No commented-out code
  - Ruff passes (all rules)
  - mypy strict mode passes
  - Follows capability template
```

### Agent: Security Reviewer

```yaml
name: security-reviewer
role: OWASP, Secrets, Auth, Permissions
checks:
  - No hardcoded secrets
  - SQL injection prevention (parameterized queries)
  - JWT validation (RS256, expiry)
  - RBAC enforcement
  - Rate limiting presence
  - PII not logged
  - TLS configured
```

### Agent: Performance Engineer

```yaml
name: performance-engineer
role: Memory, CPU, Latency, Bundle Size
checks:
  - p95 API latency < 200ms
  - N+1 query detection
  - Missing indexes
  - Bundle size budget (JS < 200KB per page)
  - Image optimization
  - No unnecessary re-renders
```

### Agent: Test Engineer

```yaml
name: test-engineer
role: Unit + Integration + E2E
rules:
  - Every service function has unit tests
  - Tests use InMemoryRepository
  - Tests are deterministic (no flaky tests)
  - Each test < 1 second
  - Coverage > 85% on business logic
  - Integration tests for PostgreSQL repos
```

### Agent: Refactoring Engineer

```yaml
name: refactoring-engineer
role: Technical debt reduction
responsibilities:
  - Identify debt patterns (duplication, dead code, violations)
  - Create refactoring tickets with effort estimates
  - Execute refactoring in isolated PRs
  - Measure before/after metrics
```

---

## 2.4 Product Team

### Agent: Product Manager

```yaml
name: product-manager
role: Backlog + Priority + Roadmap
responsibilities:
  - Maintain PRODUCT_BACKLOG.md
  - Break epics into capabilities, features, stories
  - Assign priority (P0-P3)
  - Define acceptance criteria for each story
  - Track progress against roadmap
```

### Agent: UX Reviewer

```yaml
name: ux-reviewer
role: Flows, Screens, Experience
checks:
  - User flow is logical and minimal steps
  - Error states are handled
  - Loading states exist
  - Empty states are informative
  - Mobile responsive
  - RTL layout correct
```

### Agent: Design System Engineer

```yaml
name: design-system-engineer
role: Tokens, Components, Spacing, Typography
responsibilities:
  - Maintain design tokens (colors, spacing, typography)
  - Component variants (size, color, state)
  - Accessibility (aria, keyboard, focus)
  - Documentation (Storybook)
  - Versioned releases
```

---

## 2.5 AI Business Team

### Agent: Sales Director AI

```yaml
name: sales-director-ai
role: Review Sales Flow, CRM, Pipeline, Revenue
responsibilities:
  - Review sales flow design
  - Validate pipeline stages
  - Review revenue metrics
  - Suggest improvements to sales process
  - Review CRM data quality
context: |
  You are a SaaS Sales Director with 15+ years experience.
  Review every sales-related feature for:
  - Does this match real sales workflows?
  - Are the metrics meaningful?
  - Is the pipeline stage naming correct?
  - Would a sales rep actually use this?
```

### Agent: Customer Success AI

```yaml
name: customer-success-ai
role: Retention, Renewal, Health
responsibilities:
  - Review health score models
  - Validate churn signals
  - Review renewal workflows
  - Suggest expansion opportunities
```

### Agent: CEO Advisor

```yaml
name: ceo-advisor
role: KPIs, Business Impact, ROI
responsibilities:
  - Review business KPIs
  - Validate ROI projections
  - Check pricing strategy
  - Review competitive positioning
  - Monthly business health report
```

### Agent: Company Researcher

```yaml
name: company-researcher
role: Research companies from all sources
responsibilities:
  - Analyze scraped company data for quality
  - Identify enrichment opportunities
  - Validate LinkedIn data matches
  - Research company hierarchies
  - Flag data anomalies
```

### Agent: Market Intelligence

```yaml
name: market-intelligence
role: Track News, Funding, Hiring, Competitors
responsibilities:
  - Monitor Saudi business news
  - Track funding rounds and IPOs
  - Monitor hiring trends per sector
  - Competitor analysis
  - Weekly market brief
```

---

## 2.6 Automation Team

### Agent: Workflow Engineer

```yaml
name: workflow-engineer
role: Workflow engine + Business Rules + Automation
```

### Agent: Integration Engineer

```yaml
name: integration-engineer
role: Connect external systems (Google, Notion, LinkedIn, etc.)
```

### Agent: MCP Engineer

```yaml
name: mcp-engineer
role: MCP Server tools + resources + prompts
```

### Agent: Prompt Engineer

```yaml
name: prompt-engineer
role: System prompts, agent prompts, evaluation
```

---

## 2.7 Release Team

### Agent: Release Manager

```yaml
name: release-manager
role: Orchestrate the release pipeline
steps:
  1. Verify all checks passed
  2. Update version in pyproject.toml / package.json
  3. Generate changelog
  4. Create GitHub Release
  5. Deploy to staging
  6. Run smoke tests
  7. Deploy to production
  8. Tag release in git
  9. Update PROJECT_STATUS.md
```

### Agent: Migration Engineer

```yaml
name: migration-engineer
role: Database migrations + data backfill
rules:
  - Never modify historical migrations
  - Always test migration both up and down
  - Migration must be reversible
  - Large data migrations use batch processing
```

---

# 3. Skills Library

## 3.1 Engineering Skills

### Skill: DDD Review

```yaml
name: ddd-review
description: Review code for Domain-Driven Design compliance
rules:
  - No cross-domain imports
  - Domain uses ubiquitous language
  - Aggregate roots guard invariants
  - Domain events for every mutation
  - Repository interface in domain layer
  - Services are stateless
  - Value objects are immutable
```

### Skill: Clean Architecture

```yaml
name: clean-architecture
description: Verify clean architecture layer separation
rules:
  - Domain layer has zero infrastructure imports
  - Application layer depends on domain interfaces only
  - Infrastructure layer implements domain interfaces
  - Dependency inversion throughout
  - No circular dependencies
```

### Skill: API Design

```yaml
name: api-design
description: Review REST API design
rules:
  - Resource names are plural (/companies, /contacts)
  - HTTP verbs match semantics (GET=read, POST=create, PUT=replace, PATCH=update, DELETE=delete)
  - Query params use snake_case
  - Pagination: page + page_size
  - Error responses follow RFC 7807
  - Idempotency for mutations where possible
  - Versioning via URL prefix (/v1/)
```

### Skill: PostgreSQL Optimization

```yaml
name: postgresql-optimization
description: Review database queries and schema
checks:
  - Missing indexes (EXPLAIN ANALYZE)
  - N+1 queries
  - Connection pool size appropriate
  - JSONB vs normalized columns
  - GIN indexes for full-text search
  - HNSW indexes for pgvector
  - Partitioning strategy for large tables
```

### Skill: React Review

```yaml
name: react-review
description: Review React/Next.js code
checks:
  - Server vs client component correct
  - No unnecessary re-renders
  - Proper key props in lists
  - Accessible (aria, keyboard, focus)
  - RTL layout support
  - Bundle size impact
  - Error boundaries present
```

### Skill: Performance Profiling

```yaml
name: performance-profiling
description: Profile and optimize performance
checks:
  - p95 latency measured before/after
  - Memory leak detection
  - CPU profiling for hot paths
  - Bundle analysis before/after
  - Database query profiling
  - Cache hit ratio
```

---

## 3.2 AI Skills

### Skill: Prompt Engineering

```yaml
name: prompt-engineering
description: Design and evaluate prompts
rules:
  - System prompt defines role and constraints
  - Few-shot examples for complex tasks
  - Output format specified (JSON schema)
  - Temperature set appropriate to task
  - Token limits defined
  - Hallucination guardrails in prompt
```

### Skill: RAG Evaluation

```yaml
name: rag-evaluation
description: Evaluate RAG pipeline quality
metrics:
  - Retrieval Precision@k
  - Retrieval Recall@k
  - Answer relevance (LLM-as-judge)
  - Answer faithfulness (factual consistency)
  - End-to-end latency
  - Ablation: without RAG vs with RAG
```

### Skill: Tool Design

```yaml
name: tool-design
description: Design function-calling tools for AI agents
rules:
  - Tool name is clear and consistent
  - Description explains when to use
  - Parameters have clear descriptions and types
  - Required vs optional clearly marked
  - Error responses are informative
  - Rate limiting considerations
```

### Skill: MCP Integration

```yaml
name: mcp-integration
description: Build MCP servers for AI agent integration
components:
  - Resources (data sources)
  - Tools (functions)
  - Prompts (templates)
  - Transport (stdio/HTTP)
  - Authentication
```

### Skill: Context Compression

```yaml
name: context-compression
description: Reduce token usage without losing information
techniques:
  - Summarization of long documents
  - Entity extraction (keep entities, remove noise)
  - Recursive summarization
  - Hybrid search (dense + sparse)
  - Sliding window for long context
```

---

## 3.3 Business Skills

### Skill: Company Intelligence

```yaml
name: company-intelligence
description: Research and analyze companies
dimensions:
  - Corporate (CR, licenses, legal structure)
  - Financial (revenue, funding, growth)
  - Digital (website, LinkedIn, social media)
  - Talent (hiring, team size, skills)
  - Operations (branches, government data)
  - Signals (growth, risk, intent)
```

### Skill: Revenue Intelligence

```yaml
name: revenue-intelligence
description: Analyze revenue operations
metrics:
  - Pipeline velocity and coverage
  - Win rate by segment
  - Average deal size
  - Sales cycle length
  - Customer acquisition cost
  - Lifetime value
  - Churn rate
  - Net revenue retention
```

### Skill: Sales Playbooks

```yaml
name: sales-playbooks
description: Design sales playbooks for different scenarios
components:
  - Target persona
  - ICP criteria
  - Sequence steps (email, call, meeting)
  - Timing between steps
  - Success metrics
  - Exit criteria (move to next stage)
```

### Skill: ICP Scoring

```yaml
name: icp-scoring
description: Design ICP scoring models
dimensions:
  - Firmographic (size, industry, revenue)
  - Technographic (tech stack, digital maturity)
  - Intent (hiring, funding, expansion)
  - Engagement (website visits, content consumption)
  - Fit (similarity to existing customers)
  - Accessibility (decision maker reachable)
```

### Skill: Executive Reporting

```yaml
name: executive-reporting
description: Generate executive summaries and reports
sections:
  - Executive summary (3-5 bullet points)
  - Key metrics (top 5 KPIs with trends)
  - Risks and opportunities
  - Recommendations (prioritized)
  - Appendix (data sources, methodology)
```

---

## 3.4 Operations Skills

### Skill: Release Checklist

```yaml
name: release-checklist
description: Pre-release verification
checks:
  - All tests pass (unit, integration, E2E)
  - Lint + type check pass
  - Security scan passes
  - Database migrations tested (up + down)
  - Changelog updated
  - Version bumped
  - Smoke tests pass on staging
  - Monitoring configured
  - Backup verified
  - Rollback plan documented
```

### Skill: Security Audit

```yaml
name: security-audit
description: Security review checklist
checks:
  - Secrets scanned (git-secrets, trufflehog)
  - Dependencies scanned (safety, pip-audit)
  - OWASP Top 10 checked
  - Authentication (JWT, session management)
  - Authorization (RBAC, least privilege)
  - Input validation (Pydantic, SQL injection)
  - Output encoding (XSS prevention)
  - Rate limiting present
```

### Skill: Dependency Review

```yaml
name: dependency-review
description: Review new dependencies
checks:
  - License compatibility (MIT, Apache, not GPL)
  - Maintenance status (recent commits, releases)
  - Security advisories
  - Bundle size impact (for frontend)
  - Alternative solutions (can we avoid?)
  - Benchmark requirement (Constitution Article 5)
```

### Skill: Migration Validation

```yaml
name: migration-validation
description: Validate database migrations
checks:
  - Test migration up works
  - Test migration down works (reversible)
  - No data loss on migration
  - Performance impact measured
  - Lock contention considered
  - Rollback plan exists
```

### Skill: Documentation Generation

```yaml
name: documentation-generation
description: Generate and update documentation
rules:
  - Update PROJECT_STATUS.md with completion %s
  - Add ADR for architecture decisions
  - Update EVENT_CATALOG.md for new events
  - Update AI_CATALOG.md for new AI assets
  - Update CAPABILITY_CATALOG.md for capability changes
  - Add docstrings to public API
  - README updated if project structure changed
```

---

# 4. Dependency Graph

```
Phase 0: Foundation
  ├── No dependencies (everything builds from here)
  │
Phase 1: Core Platform
  └── Depends on: Phase 0 (Persistence, CI/CD, Observability)
  │
Phase 2: CRM Engine
  └── Depends on: Phase 1 (Identity, API Gateway, Search)
  │
Phase 3: Company Intelligence
  └── Depends on: Phase 2 (Companies, Contacts, Activities)
  │
Phase 4: Employee Intelligence
  └── Depends on: Phase 2 (Contacts, Activities)
  │
Phase 5: Universal Search
  └── Depends on: Phase 2 + Phase 3 (all entities indexed)
  │
Phase 6: Intelligence Fabric
  ├── Entity Resolution depends on: Phase 0 (early start)
  ├── Feature Store depends on: Phase 1 (Data Platform)
  ├── Knowledge Graph depends on: Phase 2 (all entities)
  └── Signal Engine depends on: Phase 3 (Company Intelligence)
  │
Phase 7: Revenue Brain
  └── Depends on: Phase 6 (Feature Store, Signals, Scoring)
  │
Phase 8: Workflow Automation
  └── Depends on: Phase 7 (Revenue Brain triggers)
  │
Phase 9: AI Platform
  ├── LLM Gateway depends on: Phase 0
  ├── Semantic Cache depends on: Phase 6
  └── MCP Server depends on: Phase 1 (API Gateway)
  │
Phase 10: Marketplace
  └── Depends on: Phase 9 (AI Platform, MCP)
  │
Phase 11: Enterprise
  └── Depends on: Phase 10 (stable platform)
```

---

# 5. Execution Model

## 5.1 Feature Pipeline

كل Feature تمر عبر هذه الـ Pipeline. لا توجد استثناءات.

```
[1] Product Manager:    Define story + acceptance criteria
        ↓
[2] Chief Architect:    Review architecture impact (24h max)
        ↓
[3] Backend Engineer:   Implement domain service + repository + API
    Frontend Engineer:   Implement UI (parallel with backend)
    Database Engineer:   Implement migration (parallel)
    AI Engineer:         Implement AI (if applicable)
        ↓
[4] Code Reviewer:      Review code
        ↓
[5] Security Reviewer:  Review security
        ↓
[6] Performance Eng:    Review performance
        ↓
[7] Test Engineer:      Verify tests pass
        ↓
[8] Refactoring Eng:    Check for technical debt
        ↓
[9] Release Manager:    Merge + Deploy
```

## 5.2 Concurrency Rules

- **Phase 0: Sequential** — كل خطوة تعتمد على التي قبلها
- **Phase 1-3: Parallel within phase** — Backend + Frontend + Database + AI بالتوازي
- **Phase 4+: Full parallel** — كل Feature في Pipeline مستقل

## 5.3 Communication Model

```
[Agent] → [Task Result] → [Next Agent]
    ↓
[Event Bus: OpenCode Memory]
    ↓
[All Agents] → [Context-Aware]
```

كل Agent يكتب نتيجته في ملف مؤقت، والـ Agent التالي يقرأه.
لا يوجد اتصال مباشر بين Agents — فقط عبر Pipeline.

---

# 6. Quality Gates

## Gate 1: Architecture (Chief Architect)

```
☐ No cross-domain imports
☐ Repository pattern used
☐ Domain events emitted for mutations
☐ SDK used for cross-cutting concerns
☐ Frozen interfaces not modified (without ADR)
☐ Follows capability template
☐ No circular dependencies
```

## Gate 2: Code Quality (Code Reviewer)

```
☐ Ruff passes (all rules)
☐ mypy strict mode passes
☐ Black formatting applied
☐ No print/debug statements
☐ No hardcoded secrets
☐ Google-style docstrings on public API
☐ No TODO without ticket number
```

## Gate 3: Security (Security Reviewer)

```
☐ No secrets in code
☐ SQL parameterized
☐ Input validated at API boundary
☐ Auth + permissions checked
☐ Rate limiting present
☐ PII not logged
```

## Gate 4: Performance (Performance Engineer)

```
☐ No N+1 queries
☐ Missing indexes identified
☐ p95 latency < 200ms (API)
☐ Bundle size budget met (< 200KB per page)
☐ Cache strategy defined
```

## Gate 5: Testing (Test Engineer)

```
☐ Unit tests for all business logic
☐ Tests use InMemoryRepository
☐ All existing tests pass
☐ Integration tests for PostgreSQL repos
☐ Coverage > 85% on business logic
☐ No flaky tests
```

## Gate 6: Documentation (Release Manager)

```
☐ PROJECT_STATUS.md updated
☐ ADR added if architecture decision
☐ EVENT_CATALOG.md updated if new events
☐ AI_CATALOG.md updated if new AI assets
☐ CAPABILITY_CATALOG.md updated
☐ CHANGELOG updated
```

---

# 7. KPIs & Success Criteria

## Phase 0 — Foundation

| KPI | Target |
|-----|--------|
| Persistence | 100% of domain services persist to PostgreSQL |
| CI/CD | PR → deploy in < 10 minutes |
| Test Coverage | > 85% on business logic |
| API Latency p95 | < 200ms |
| Scrapers Integrated | 5/5 sources in unified pipeline |
| Design System | 20+ components published |

## Phase 1 — Core Platform

| KPI | Target |
|-----|--------|
| Multi-tenant | 100% of entities tenant-scoped |
| Search Latency p95 | < 500ms |
| API Gateway | 100% of requests routed, rate-limited, auth'd |
| Search Precision@10 | > 0.85 |

## Phase 2 — CRM Engine

| KPI | Target |
|-----|--------|
| CRM Completeness | Lead → Contact → Deal → Close |
| Pipeline Kanban | Drag-and-drop, real-time |
| Import Speed | 10K records in < 60s |
| Timeline | Every entity has timeline |

## Phase 3 — Company Intelligence

| KPI | Target |
|-----|--------|
| Page Load | Company 360 < 2s |
| Government Data | 5/5 sources displayed |
| AI Summary | Generated in < 5s |
| Signals | 10+ signal types computed |

## Phase 6 — Intelligence Fabric

| KPI | Target |
|-----|--------|
| Entity Resolution Precision | > 95% |
| Feature Store Latency | < 50ms |
| Knowledge Graph Latency | < 200ms |
| Signal Detection | Near-real-time (< 5min) |
| Scoring Accuracy | > 85% vs human evaluation |

## Phase 7 — Revenue Brain

| KPI | Target |
|-----|--------|
| Win Probability Accuracy | > 80% |
| Forecast Error (MAPE) | < 15% |
| Risk Detection Precision | > 85% |
| Next Best Action Adoption | > 30% of user actions |

## Overall Business KPIs (Year 1)

| KPI | Target |
|-----|--------|
| Paying Customers | 10 by end of Year 1 |
| Companies in Platform | 100K+ deduplicated |
| Platform Uptime | 99.9% |
| AI Cost per Query | < $0.01 |
| User Activation | > 60% of signups active weekly |

---

# 8. OpenCode Configuration

## 8.1 Agent Registration

```jsonc
// opencode.json — Agents section
{
  "agents": {
    "chief-architect": {
      "role": "Chief Architect",
      "type": "expert",
      "model": "gpt-4o",
      "context": ["docs/PROJECT_MANIFEST.md", "docs/MASTER_BLUEPRINT.md"]
    },
    "backend-engineer": {
      "role": "Backend Engineer",
      "type": "developer",
      "model": "gpt-4o",
      "skills": ["fastapi", "sqlalchemy", "ddd", "repository-pattern"]
    },
    "frontend-engineer": {
      "role": "Frontend Engineer",
      "type": "developer",
      "model": "gpt-4o",
      "skills": ["nextjs", "react", "shadcn-ui", "tailwind"]
    },
    "code-reviewer": {
      "role": "Code Reviewer",
      "type": "reviewer",
      "model": "gpt-4o",
      "rules": ["No cross-domain imports", "Tests before code", "Ruff + mypy pass"]
    },
    "test-engineer": {
      "role": "Test Engineer",
      "type": "quality",
      "model": "gpt-4o-mini",
      "focus": "Unit + Integration + E2E tests"
    }
  }
}
```

## 8.2 Pipeline Configuration

```yaml
# feature-pipeline.yaml
pipeline:
  - stage: "Product Definition"
    agent: product-manager
    output: "feature-spec.md"
    
  - stage: "Architecture Review"
    agent: chief-architect
    input: "feature-spec.md"
    output: "architecture-approval.md"
    
  - stage: "Implementation"
    parallel:
      - agent: backend-engineer
        output: "backend-code.md"
      - agent: frontend-engineer
        output: "frontend-code.md"
      - agent: database-engineer
        output: "migration.sql"
      - agent: ai-engineer
        output: "ai-code.md"
        
  - stage: "Review"
    parallel:
      - agent: code-reviewer
        input: ["backend-code.md", "frontend-code.md"]
      - agent: security-reviewer
        input: ["backend-code.md"]
      - agent: performance-engineer
        input: ["backend-code.md", "frontend-code.md"]
        
  - stage: "Testing"
    agent: test-engineer
    input: "all-code"
    
  - stage: "Refactoring"
    agent: refactoring-engineer
    input: "all-code"
    
  - stage: "Release"
    agent: release-manager
    input: "all-approvals"
```

## 8.3 Skills Registration

```jsonc
// ~/.config/opencode/skills/
{
  "skills": [
    "skills/engineering/ddd-review.md",
    "skills/engineering/clean-architecture.md",
    "skills/engineering/api-design.md",
    "skills/engineering/postgres-optimization.md",
    "skills/engineering/react-review.md",
    "skills/engineering/performance-profiling.md",
    "skills/ai/prompt-engineering.md",
    "skills/ai/rag-evaluation.md",
    "skills/ai/tool-design.md",
    "skills/ai/mcp-integration.md",
    "skills/ai/context-compression.md",
    "skills/business/company-intelligence.md",
    "skills/business/revenue-intelligence.md",
    "skills/business/sales-playbooks.md",
    "skills/business/icp-scoring.md",
    "skills/business/executive-reporting.md",
    "skills/operations/release-checklist.md",
    "skills/operations/security-audit.md",
    "skills/operations/dependency-review.md",
    "skills/operations/migration-validation.md",
    "skills/operations/documentation-generation.md"
  ]
}
```

---

# 9. Implementation Order (Next 90 Days)

## Sprint 1 (Weeks 1-2): Foundation — Backend

| Day | Task | Agent |
|-----|------|-------|
| 1-2 | PostgreSQL Identity Repository | Backend Engineer |
| 3-4 | PostgreSQL Company Repository | Backend Engineer |
| 5-6 | Alembic Baseline Migration | Database Engineer |
| 7-8 | Integration Tests (50+ tests) | Test Engineer |
| 9-10 | CI/CD Pipeline | Platform Architect |

## Sprint 2 (Weeks 3-4): Foundation — Frontend

| Day | Task | Agent |
|-----|------|-------|
| 11-12 | Design System: Button, Input, Card | Frontend Architect |
| 13-14 | Design System: Table, Dialog, Form | Frontend Arch / Eng |
| 15-16 | Login / Register Pages | Frontend Engineer |
| 17-18 | Company List + Search Bar | Frontend Engineer |
| 19-20 | Company Detail Page (MVP) | Frontend Engineer |

## Sprint 3 (Weeks 5-6): Data Pipeline

| Day | Task | Agent |
|-----|------|-------|
| 21-22 | Entity Resolution: Matching Engine | AI Engineer |
| 23-24 | Entity Resolution: Golden Record Store | AI Engineer |
| 25-26 | Balady + NCNP merge (first 2 sources) | AI Engineer |
| 27-28 | Normalizer: City/Region standardization | Database Engineer |
| 29-30 | Observability: Tracing + Metrics + Alerts | Platform Architect |

## Sprint 4 (Weeks 7-8): Core Platform

| Day | Task | Agent |
|-----|------|-------|
| 31-33 | Multi-tenant Identity (Orgs, Teams, Roles) | Backend Engineer |
| 34-35 | API Gateway (Rate limit, AuthZ, Routing) | Backend Engineer |
| 36-37 | Core Services (Files, Notifications, Audit) | Backend Engineer |
| 38-40 | Search: Full-text + Semantic + Graph | Search Engineer |

## Sprint 5 (Weeks 9-10): CRM Engine — Backend

| Day | Task | Agent |
|-----|------|-------|
| 41-43 | Companies CRUD + Search + Merge | Backend Engineer |
| 44-46 | Contacts CRUD + Search + Import | Backend Engineer |
| 47-48 | Deals — Pipeline stages + value | Backend Engineer |
| 49-50 | Leads — Capture + Score + Route | Backend Engineer |

## Sprint 6 (Weeks 11-12): CRM Engine — Frontend

| Day | Task | Agent |
|-----|------|-------|
| 51-52 | Companies List + Detail Page | Frontend Engineer |
| 53-54 | Pipeline Kanban (drag-and-drop) | Frontend Engineer |
| 55-56 | Contacts List + Detail Page | Frontend Engineer |
| 57-58 | Activity Timeline Widget | Frontend Engineer |
| 59-60 | Tasks + Notes + Meetings | Frontend Engineer |

---

# 10. Governance

## 10.1 Decision Hierarchy

```
1. PROJECT_MANIFEST.md — How we build (supreme)
2. MASTER_BLUEPRINT.md — What we build
3. RUNTIME_ARCHITECTURE.md — How it runs
4. SALESOS_OPERATING_PLAN.md — How we operate (this doc)
5. Platform Constitution — Immutable principles
6. ADRs — Architecture decision records
7. Skills Library — Reusable review criteria
```

## 10.2 Amendment Process

أي تغيير في هذه الخطة يتطلب:
1. **Rationale** — لماذا التغيير مطلوب
2. **Impact Analysis** — كيف يؤثر على المراحل الأخرى
3. **AI Workforce Vote** — تصويت من Chief Architect + Product Manager + CEO Advisor
4. **Documentation** — تحديث هذا المستند

## 10.3 Review Cadence

| Review | Frequency | Participants |
|--------|-----------|--------------|
| Daily Standup | Daily | All active agents |
| Sprint Review | Every 2 weeks | All agents |
| Architecture Review | Monthly | Chief + Platform Architects |
| Business Review | Monthly | CEO Advisor + Product Manager |
| Operating Plan Review | Quarterly | All team leads |

---

*This Operating Plan transforms SalesOS from a prototype into an enterprise SaaS company.*
*It replaces ad-hoc development with a pipeline-driven AI Workforce.*
*Every Agent has a role. Every role has a gate. Every gate has a standard.*

*Version 1.0 | 2026-07-08 | Next review: 2026-10-08*
