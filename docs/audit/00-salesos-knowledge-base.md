# SalesOS — Comprehensive Knowledge Base

> **Document Type:** FINAL Synthesis — Complete Platform Understanding
> **Date:** 2026-07-13
> **Classification:** For CTO, Board, and incoming engineering leadership
> **Purpose:** Single authoritative document sufficient for a new CTO to fully understand the product without reading source code
> **Sources:** 14 specialist agent audits + all platform documentation + codebase analysis

---

## Executive Summary

**SalesOS is a Business Intelligence Operating System (Enterprise BIOS) built for the Saudi Arabian market.** It is not a CRM — it is a 4-layer platform that ingests government data, resolves entities across 6+ sources, enriches companies with AI-powered intelligence, executes revenue workflows, and delivers explainable recommendations through a frozen Widget SDK.

**Current State:** The platform has completed an extraordinary 8-sprint build (July 5-12, 2026), producing 51 widgets, 2054 tests at 93% unit coverage, 13 domain packages, 31 runtime modules, and comprehensive documentation. It has 3 pilot tenants and is being positioned for GA in August 2026.

**Honest Assessment:** The platform has world-class architecture, strong code quality, and an ambitious vision. However, it is not production-hardened. Critical infrastructure (Redis, Kafka) is not deployed. No frontend E2E tests exist. The enrichment endpoint operates at 3x its budget. The engineering dashboard's self-reported metrics systematically overstate readiness by 10-30%. A single architect carries the entire technical burden. The platform needs 90 days of infrastructure hardening before it can support 50+ tenants at 99.9% SLA.

**Overall Grade: B+ (Technical Excellence) / C (Production Readiness) / D (Commercial Validation)**

---

## Part I — What SalesOS Is

### 1.1 Product Vision

> "SalesOS is the intelligent layer that transforms company data into sales and investment decisions."
> — PRODUCT_BIBLE.md:15

SalesOS solves four problems in the Saudi corporate market:
1. **Data fragmentation** — Companies are registered with 6+ government agencies (Ministry of Commerce, Ministry of Investment, Chambers of Commerce, CMA, Balady, Taqeem) with no unified source
2. **Intelligence gap** — Even when data is available, there is no automated analysis revealing opportunities, risks, and growth patterns
3. **Weak tooling** — Sales and investment teams manage thousands of companies using Excel and personal notes
4. **Tacit knowledge** — Knowledge lives in individuals' heads, not in the platform

### 1.2 What SalesOS IS NOT

- **Not a CRM** — It augments CRM. CRM records what happened; SalesOS decides what happens next
- **Not a data provider** — It ingests, resolves, enriches, and acts on data. It's a platform, not a feed
- **Not generic AI** — The AI is context-specific (Saudi market, Arabic language, government signals)

### 1.3 Core Platform Thesis

> "Enterprise sales organizations lack a platform that preserves ownership of business facts, transforms facts into explainable knowledge, measures business performance systematically, and delivers traceable, contextual, optional recommendations."
> — OPERATING_SYSTEM.md:15-23

### 1.4 Target Personas

| Persona | Arabic Title | Core Need | Key Features |
|---------|-------------|-----------|--------------|
| Business Development Director | مدير تطوير الأعمال | Discover expansion targets | Company Intelligence, Universal Search, AI Summary, Entity Resolution |
| Sales Manager | مدير مبيعات B2B | Prioritize and forecast | NBA Engine, Pipeline Intelligence, Deal Health, Revenue Dashboard |
| Sales Representative | مندوب مبيعات | Know what to do next | NBA Engine, Playbook Engine, Meeting Intelligence, Opportunity Workspace |
| Investment Analyst | محلل استثماري | Due diligence at scale | Company DNA, Relationship Graph, Golden Record, Financial Health |
| Customer Success Manager | مدير نجاح العملاء | Prevent churn | Churn Intelligence, Expansion Intelligence, Revenue Health |
| VP of Sales / CRO | — | Revenue visibility | Revenue Workspace, Forecast Intelligence, Team Performance |
| Executive (CEO/VP/GM) | — | Decision speed | Executive Dashboard, AI Brief, Market Pulse |
| Administrator | — | Platform management | Admin Dashboard with 8 tabs |

### 1.5 Competitive Positioning

SalesOS is positioned as **"the Bloomberg Terminal for Saudi companies — with AI intelligence at a CRM price point."**

| Dimension | SalesOS Advantage | Risk |
|-----------|-----------------|------|
| Saudi Government Data | 6+ government sources integrated (Balady, Taqeem, NCNP, Najiz, Rega, Ministry of Commerce) | Scraper API keys are placeholders — data pipeline not live |
| Arabic-Native | Full RTL, Arabic-first design, proper normalization, bilingual UI | BUG-002 (Arabic text normalization) unfixed |
| Explainable AI | NBA Engine provides evidence trails, confidence breakdowns, alternatives | Adopted by only 5.6% of widgets |
| Entity Resolution | pg_trgm fuzzy matching, golden records, merge pipeline | Only 3 sources connected; city/region normalization missing |
| Widget SDK v1.0 | Standardized, testable, accessible widgets, frozen interface | Feature freeze limits innovation speed |
| Market Window | Saudi Vision 2030 digital transformation push creates 12-24 month window | Global competitors (Salesforce, HubSpot) will localize offerings |

---

## Part II — Architecture at a Glance

### 2.1 Four-Layer Platform Architecture

```
LAYER 4 — APPLICATIONS (User-facing)
  ─ Company 360 │ Deal Room │ AI Copilot │ Revenue Dashboard │ ICP Builder │
    GTM Builder │ Rules Studio │ Prompt Studio

LAYER 3 — BUSINESS CAPABILITIES (Domain logic)
  ─ Company Intel │ Pipeline │ Forecast │ Analytics │ Scoring │
    GTM │ Marketing │ Success │ Partner │ Talent │ Activity │
    Opportunity Mgmt │ Recommendation │ Playbook Engine

LAYER 2 — PLATFORM SERVICES (Shared infrastructure)
  ─ Data Fabric │ Intelligence Fabric │ Workflow │ Events │
    Feature Store │ Semantic Cache │ Knowledge Graph │
    Entity Resolution │ Hybrid Search │ RAG Pipeline │
    OS API: REST API (active) │ GraphQL (not built) │ MCP Server (not built) │ Agent SDK (not built)

LAYER 1 — KERNEL (Frozen — cannot be changed without ADR)
  ─ Identity │ Company │ Search │ Timeline │ SDK │ Events │
    Metadata │ Capability Registry │ Universal Timeline
```

### 2.2 Code Architecture (What Actually Exists)

```
salesos/backend/
├── sdk/           (29 sub-packages) — Cross-cutting contracts
├── domains/       (15 packages) — DDD domain layer
├── runtime/       (31 packages) — Orchestration/engines
├── app/modules/   (14+ modules) — REST API layer
└── intelligence/   — AI agents, RAG, graph, data fabric

salesos/frontend/
├── packages/      (12 internal packages) — @salesos/ui, design-language, runtime, etc.
├── features/      (12 feature modules) — dashboard, search, company-intelligence, revenue, etc.
├── components/    — Foundation + top-level components
├── application/   — Clean Architecture layer (DTOs, queries, mappers, stores)
└── lib/            — API client, hooks, i18n, monitoring, analytics
```

### 2.3 Key Architectural Decisions

| ADR | Decision | Rationale | Assessment |
|-----|----------|-----------|------------|
| ADR-001 | Modular monolith (not microservices) | Right for team size; eventual extraction path defined | ✅ Correct |
| ADR-002 | PostgreSQL as primary OLTP | pgvector + pg_trgm + JSONB = single DB for relational + vector + fuzzy matching | ✅ Correct |
| ADR-003 | Widget SDK v1.0 Feature Freeze | Prevents fragmentation; mandatory Container/View pattern | ✅ Correct |
| ADR-005 | pgvector over dedicated vector DB | Zero new infrastructure; JOIN company + embedding | ✅ Correct |
| ADR-009 | InMemory repositories first, PostgreSQL later | Rapid iteration; transition completed Sprint 5 | ✅ Correct |
| ADR-DDD-03 | Kafka as event bus | In-memory bus is current reality; Kafka planned | ⚠️ Premature — Kafka not deployed |
| DEC-005 | Rejected LangChain | Custom SDK provides more control | ✅ Correct decision |
| REJ-001 | Rejected Elasticsearch | pgvector sufficient for current scale | ✅ Correct |

### 2.4 Tech Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Backend Framework** | FastAPI + Uvicorn | 0.111 | Async-native, 4 workers in production |
| **Python** | Python | 3.12 | |
| **ORM** | SQLAlchemy 2.0 + asyncpg | 2.0 | Async throughout |
| **Database** | PostgreSQL + pgvector + pg_trgm | 16 | Single node |
| **Graph DB** | Neo4j Community | 5.x | Single node; connection pool fixed |
| **Cache** | Redis | 7-alpine | Configured but NOT deployed in production |
| **Event Bus** | Kafka | 7.0.0 | Configured but NOT used (in-memory EventBus active) |
| **Frontend Framework** | Next.js (App Router) | 15 | SPA mode (all client components) |
| **UI Library** | React | 19 | |
| **Styling** | Tailwind CSS | 3.4 | MUHIDE custom palette |
| **State Management** | TanStack React Query | 5.60 | Server state |
| **Forms** | react-hook-form + zod | — | |
| **Icons** | Lucide React | 0.460 | |
| **Charts** | Recharts | 2.15 | |
| **Testing (Backend)** | pytest + pytest-asyncio + pytest-cov | 8.2 | |
| **Testing (Frontend)** | Jest + Testing Library + MSW | 29.7 | |
| **CI/CD** | GitHub Actions | — | 4 workflows, 22 jobs |
| **IaC** | Terraform (AWS) | — | VPC, EKS, RDS, Secrets Manager |
| **Container** | Docker + Docker Compose | — | Multi-stage builds, non-root users |
| **Monitoring** | Prometheus + Grafana | — | In dev/staging, NOT in production |
| **Reverse Proxy** | Caddy (prod) / NGINX (dev) | 2-alpine | Auto-TLS via Let's Encrypt |
| **LLM** | OpenAI (GPT-4o-mini, GPT-4o) | — | Embeddings: text-embedding-3-large |

### 2.5 Infrastructure Reality

| Component | Status | Criticality |
|-----------|--------|-------------|
| PostgreSQL 16 + pgvector + pg_trgm | 🟢 Operational | Foundation — working |
| Neo4j 5-community | 🟢 Operational (single node) | Connection leak fixed |
| Redis 7 | 🔴 In docker-compose, **not deployed** in production | Blocks rate limiting, caching, sessions |
| Kafka | 🔴 In docker-compose, **not used** (in-memory EventBus active) | Events lost on restart |
| Prometheus + Grafana | 🟡 In dev/staging only | No production monitoring |
| CI/CD (GitHub Actions) | 🟢 Operational | Security + arch gates, rollback, smoke tests |
| Caddy (TLS) | 🟢 Configured in production | Auto Let's Encrypt |
| Backup (pg_dump) | 🟢 Daily cron | Restore never tested |
| CDN / DDoS (Cloudflare) | 🔴 Not configured | Production exposed |
| Load Testing | 🟡 Script exists, manual only | 5 scenarios, low concurrency |
| Staging Environment | 🟢 Docker Compose with 3 pilot tenants | No K8s staging |

---

## Part III — Business Capability Heatmap

### 3.1 Capability Status Matrix

| Capability | Status | Completeness | Production-Ready | Critical Gaps |
|-----------|--------|-------------|-----------------|---------------|
| **Identity & Auth** | 🟢 Complete | 100% | ✅ | HS256 JWT (symmetric), no MFA, no account lockout |
| **Company CRUD + 360** | 🟢 Complete | 95% | ✅ | City/region normalization missing |
| **Entity Resolution** | 🟢 Complete | 90% | ✅ | Only 3 sources connected; scraper keys placeholder |
| **Universal Search** | 🟢 Complete | 93% | ✅ | Benchmarks simulated; Arabic normalization bug |
| **Hybrid Search (RRF)** | 🟢 Complete | 90% | ✅ | HNSW index not verified for semantic path |
| **Feature Store** | 🟢 Complete | 90% | ✅ | 7 computers active; TTL-based only |
| **Knowledge Graph** | 🟡 Partial | 70% | ⚠️ | Neo4j single node; no automated backup |
| **NBA Engine** | 🟢 Complete | 80% | ✅ | AI reasoning stubbed; rule-only active |
| **Decision Platform** | 🟡 Partial | 60% | ⚠️ | 5.6% widget adoption; DecisionProvider gap |
| **Pipeline/Kanban** | 🟢 Complete | 90% | ✅ | Drag-drop, SLA tracking, velocity |
| **Opportunity Management** | 🟢 Complete | 90% | ✅ | Full lifecycle with stage rules |
| **Forecast Intelligence** | 🟡 Partial | 75% | ⚠️ | 4-scenario engine; hardcoded demo data in endpoint |
| **Meeting Intelligence** | 🟢 Complete | 85% | ✅ | Pre-brief + post-summary; rate-limited AI calls |
| **Email Intelligence** | 🟢 Complete | 80% | ✅ | Sentiment, topic, urgency detection |
| **Playbook Engine** | 🟢 Complete | 80% | ✅ | Stage-gated with task templates |
| **Quote/Proposal/Contract** | 🟡 Partial | 75% | ⚠️ | In-memory workflow repo; proposal auto-approves |
| **Workflow Engine** | 🟡 Partial | 50% | 🔴 | In-memory repo; 50% arch compliance |
| **AI Platform** | 🟡 Partial | 60% | ⚠️ | 11 agents, all in-memory; mock connectors |
| **RAG Pipeline** | 🟡 Partial | 70% | ⚠️ | Working pipeline; text query bug in hybrid retrieval |
| **Customer Success** | 🟡 Partial | 70% | ⚠️ | Widget + workspace; no dedicated unit tests |
| **Analytics/Reporting** | 🟡 Partial | 65% | ⚠️ | 18 KPI registry; hardcoded demo data |
| **Admin Dashboard** | 🟢 Complete | 85% | ✅ | 8 tabs (Tenants, Plans, Users, Flags, Jobs, AI Costs, Health) |
| **Marketplace** | 🔴 Shell only | 20% | ❌ | Frontend shell; zero backend infrastructure |
| **MCP Server** | 🔴 Planned | 0% | ❌ | Zero implementation |
| **Agent Runtime** | 🔴 Planned | 0% | ❌ | Zero autonomous agent implementation |
| **GraphQL API** | 🔴 Planned | 0% | ❌ | No schema, no resolvers |
| **Billing Engine** | 🔴 Planned | 0% | ❌ | Plan/license models exist; no payment integration |

### 3.2 Business Process Completeness

| Process | Frontend Widgets | Backend Logic | Integration Depth | Status |
|---------|-----------------|---------------|-------------------|--------|
| **Discover Company** | Search + Command Bar + Quick Overlay | Hybrid search (tsvector + pgvector + RRF) | Full | ✅ |
| **Understand Company** | Company DNA + AI Summary + Signals + Graph | 360 view + enrichment + signal detection | Medium (scraper keys placeholder) | 🟡 |
| **Create Opportunity** | Pipeline Kanban drag-drop | Stage rules, probability, SLA tracking | Full | ✅ |
| **Execute Revenue Workflow** | NBA + Playbook + Meeting + Email | Full activity → outcome → rule pipeline | Full | ✅ |
| **Quote → Contract** | Modal forms | Full lifecycle (Draft → Submitted → Approved → Sent → Accepted) | Full | ✅ |
| **Forecast Revenue** | Forecast Intelligence widget | 4-scenario engine (Most Likely, Commit, Best, Worst) | Partial (hardcoded demo data) | 🟡 |
| **Prevent Churn** | Churn Intelligence + Expansion | Health scoring + signal detection | Medium | 🟡 |
| **Analyze Performance** | Revenue Dashboard + Analytics | 18-KPI registry + pipeline velocity | Partial | 🟡 |
| **Administer Platform** | Admin Dashboard (8 tabs) | Tenant/user/plan/flag management, AI cost tracking | Full | ✅ |

---

## Part IV — Technical Health Dashboard

### 4.1 Combined Scores From All 14 Agents

| Dimension | Engineering Dashboard (Self-Reported) | CTO Auditor | Specialist Agent | Delta | Verdict |
|-----------|--------------------------------------|------------|-----------------|-------|--------|
| **Production Readiness** | 9.5/10 | 7.2/10 | 4.7/10 (Performance) | -4.8 | 🔴 Overstated |
| **Architecture Compliance** | 95% | 85% | 64% (EA Auditor) | -31% | 🔴 Overstated |
| **Security Posture** | 9.5/10 | 7.5/10 | 7/10 (Security) | -2.5 | 🟡 Overstated |
| **Test Coverage (Unit)** | 93% | 88% (weighted) | 93% (QA) | 0 | ✅ Accurate |
| **Test Coverage (E2E)** | 40% | 40% | 40% backend / 0% frontend | 0 | ✅ Accurate |
| **Documentation** | 9.5/10 | 8.5/10 | 8.5/10 (Product) | -1.0 | 🟡 Slightly overstated |
| **Data Integrity** | 9/10 | 7/10 | 7/10 (DB) | -2.0 | 🟡 Overstated |
| **Monitoring** | 7/10 | 5/10 | 3/10 (DevOps) | -4.0 | 🔴 Overstated |
| **Infrastructure Maturity** | — | — | 3.5/5 (DevOps) | — | — |
| **Frontend Quality** | — | — | 7/10 (FE Architect) | — | — |
| **Backend Quality** | — | — | 8/10 (BE Architect) | — | — |
| **Design System** | — | — | 72/100 (DS Architect) | — | — |
| **UX Quality** | — | — | 7.5/10 (UX Architect) | — | — |
| **Overall Performance** | — | — | 4.7/10 (Perf Architect) | — | — |
| **QA Maturity** | — | — | 6.3/10 (QA Architect) | — | — |

### 4.2 Architecture Compliance by Domain (Actual Measured)

| Domain | ARCHITECTURE_COMPLIANCE.md | ENGINEERING_DASHBOARD.md | Discrepancy |
|--------|---------------------------|------------------------|-------------|
| Identity | 100% | 100% | ✅ Match |
| Widget SDK | 100% | 100% | ✅ Match |
| Company | 95% | 95% | ✅ Match |
| Search | 90% | 95% | ⚠️ +5% |
| CRM | 90% | 95% | ⚠️ +5% |
| Scoring | 95% | 95% | ✅ Match |
| AI | 85% | 95% | 🔴 +10% |
| Timeline | 80% | 95% | 🔴 +15% |
| Workflow | 50% | 95% | 🔴 +45% |
| Feature Store | 95% | 95% | ✅ Match |
| Entity Resolution | 95% | 95% | ✅ Match |
| **OVERALL** | **87%** | **95%** | 🔴 **+8%** |

### 4.3 Security Posture Summary

| Category | Status | Critical Issues | High Issues |
|----------|--------|----------------|-------------|
| Authentication | 🟡 Needs hardening | 0 | 1 (HS256 JWT) |
| Authorization/RBAC | 🟢 Solid | 0 | 0 |
| Middleware Security | 🟢 Strong | 0 | 0 |
| Input Validation | 🟢 Good | 0 | 0 |
| Secrets Management | 🟢 Clean | 0 | 0 |
| SSO/OAuth | 🟡 Needs hardening | 0 | 1 (SSO tokens plaintext) |
| Data Encryption | 🟡 Partial | 0 | 1 (no app-level encryption) |
| API Security | 🟢 Mostly secured | 0 | 0 |
| Dependency Security | 🟢 CI/CD enforced | 0 | 0 |
| OWASP Top 10 | 🟢 7/10 green | 0 | 1 |
| Incident Response | 🟡 Immature | 1 (no IR plan) | 0 |

### 4.4 Performance by Endpoint

| Endpoint | p50 | p95 | p99 | Budget | Status |
|----------|-----|-----|-----|--------|--------|
| `GET /companies/{id}` | 45ms | 120ms | 250ms | 200ms | 🟢 (p99 exceeds) |
| `POST /search` | 180ms | 450ms | 900ms | 500ms | 🟡 (p99 1.8x budget) |
| `GET /timeline` | 90ms | 300ms | 600ms | 300ms | 🟡 (p99 2x budget) |
| `POST /enrich` | 2.5s | 8s | 15s | 5s | 🔴 (all percentiles exceed) |

---

## Part V — Combined Risk Register

### 5.1 Critical Risks (Must Address Before GA)

| ID | Risk | Probability | Impact | Source Agent | Timeline |
|----|------|-------------|--------|-------------|----------|
| R-001 | Solo architect incapacitation — bus factor of 1 | Medium | Critical | CTO, Backend | 30 days |
| R-002 | Data loss from in-memory event bus (no Kafka/Redis) | High | Critical | CTO, DevOps, Performance | 60 days |
| R-003 | Arabic NLP quality blocks market adoption (BUG-002) | Medium | Critical | CTO | 14 days |
| R-004 | PostgreSQL single-node failure — no replication | Low | Critical | CTO, Database | 30 days |
| R-005 | Neo4j single-node failure — no backup automation | Low | High | CTO, DevOps | 60 days |
| R-006 | Enrichment endpoint SLA breach (8s p95 vs 5s budget) | Certain | High | CTO, Performance | 30 days |
| R-007 | No backup restore ever tested | Certain | Critical | CTO, DevOps | 1 day |
| R-008 | Scraper API keys are placeholders — no real data pipeline | Certain | Critical | Product, Business Logic | 14 days |
| R-009 | In-memory stores grow unboundedly — eventual memory exhaustion | High | High | Performance | 3 days |

### 5.2 High Risks (Address Within 60 Days)

| ID | Risk | Probability | Impact | Source Agent |
|----|------|-------------|--------|-------------|
| R-010 | Frontend localStorage misuse for opportunity/task data | High | Medium | CTO, Frontend |
| R-011 | Rate limiting bypass without Redis (in-memory only, per-server) | Medium | High | CTO, Security |
| R-012 | SSO provider tokens stored plaintext in database | Medium | High | Security |
| R-013 | No incident response plan or security alerting | Medium | High | Security |
| R-014 | JWT uses symmetric HS256 — no key rotation | Low | High | Security |
| R-015 | Decision Platform adopted by only 5.6% of widgets | High | Medium | CTO, Product |
| R-016 | No frontend E2E tests — critical user paths untested in browser | Certain | Medium | QA |
| R-017 | Coverage gate not enforced (fail_under=30 vs constitutional 85%) | High | Medium | QA |
| R-018 | Search benchmarks are mathematical simulations, not real queries | High | Medium | Performance |
| R-019 | Unbounded in-memory stores in 4 engines — O(n) degradation | High | Medium | Performance |

### 5.3 Medium Risks (Address Within 90 Days)

| ID | Risk | Probability | Impact | Source Agent |
|----|------|-------------|--------|-------------|
| R-020 | AI cost overrun — no semantic cache, no per-tenant budgets | Medium | Medium | CTO, AI |
| R-021 | PostgreSQL repos migrated in days, not proven over months | Low | Medium | CTO |
| R-022 | No staged rollback ever executed | Medium | Medium | CTO, DevOps |
| R-023 | No Cloudflare/CDN/DDoS protection configured | Medium | Medium | CTO, DevOps |
| R-024 | Backend design tokens use old blue palette (not MUHIDE orange) | Medium | Medium | Design System |
| R-025 | Three duplicate cache implementations — inconsistency risk | Medium | Medium | Performance |
| R-026 | Company Workspace tabs missing from design spec | Medium | Medium | UX |
| R-027 | Dashboard and Company Workspace use different widget architectures | Medium | Medium | UX, Product |
| R-028 | Widget Contract tests missing for 7+ deployed widgets | Medium | Medium | QA |
| R-029 | Forecast/Analytics/Workspace endpoints return hardcoded demo data | Medium | Medium | Business Logic |
| R-030 | No NGINX gzip compression or caching — every request uncompressed | Medium | Medium | Performance |

---

## Part VI — Combined Technical Debt Register

### Critical (P0)

| ID | Item | Source | Age | Effort | Owner |
|----|------|--------|-----|--------|-------|
| TD-001 | 7 InMemory repos → PostgreSQL | Multiple | Sprint 0.5 | Resolved ✅ | Backend |
| TD-CRIT-001 | No automated Neo4j backup | DevOps | Now | 1 sprint | DevOps |
| TD-CRIT-002 | In-memory EventBus (Kafka not deployed) | TD-002 | 3 months | 2 sprints | Architecture |
| TD-CRIT-003 | Redis not deployed in production | Multiple | Now | 1 day | DevOps |
| TD-CRIT-004 | BUG-002 — Arabic text normalization unfixed | CTO | 1 month | 3 days | Backend |
| TD-CRIT-005 | POST /enrich p95=8s vs 5s budget | Performance | Now | 1 week | Backend |
| TD-CRIT-006 | 4 unbounded in-memory stores (no TTL/LRU eviction) | Performance | Now | 3 days | Backend |
| TD-CRIT-007 | Workflow domain at 50% architecture compliance | EA | Now | 2 sprints | Backend |
| TD-CRIT-008 | 31 runtime modules vs 15 documented domains | EA | Now | Audit effort | Architecture |

### High (P1)

| ID | Item | Source | Age | Effort |
|----|------|--------|-----|--------|
| TD-H-001 | No frontend E2E tests | QA | Now | 3 sprints |
| TD-H-002 | SSO provider tokens stored plaintext in DB (SEC-H-02) | Security | Now | 2 days |
| TD-H-003 | JWT uses symmetric HS256 (SEC-H-01) | Security | Now | 3 days |
| TD-H-004 | No incident response plan or alerting (SEC-H-04) | Security | Now | 1 sprint |
| TD-H-005 | Decision Platform adoption at 5.6% (VIO-105) | CTO, Product | Sprint 5 | 1 week |
| TD-H-006 | NGINX: no gzip, no caching | Performance | Now | 1 hour |
| TD-H-007 | Search benchmarks are simulated — need real PostgreSQL queries | Performance | Now | 2 days |
| TD-H-008 | Backend design tokens not migrated to MUHIDE palette | Design System | Now | 2 days |
| TD-H-009 | Coverage gate: fail_under=30 should be 85% (QA-002) | QA | Now | 1 hour |
| TD-H-010 | Scraper API keys are placeholders (D-005) | Product | Now | 1 week |
| TD-H-011 | Prometheus + Grafana not in production compose | DevOps | Now | 1 sprint |
| TD-H-012 | No centralized log aggregation in production | DevOps | Now | 1 sprint |
| TD-H-013 | Hardcoded demo data in forecast/analytics/workspace endpoints | Business Logic | Now | 3 days |
| TD-H-014 | localStorage misuse for opportunity/task stores | CTO, Frontend | Sprint 5 | 3 days |
| TD-H-015 | No AI evaluation pipeline automation | QA, AI | Now | 2 sprints |

### Medium (P2)

| ID | Item | Source | Effort |
|----|------|--------|--------|
| TD-M-001 | Backup restore never tested | CTO, DevOps | 1 day |
| TD-M-002 | No automated backup verification | DevOps | 1 sprint |
| TD-M-003 | No WAL archiving — no point-in-time recovery | DevOps | 1 sprint |
| TD-M-004 | No container image signing (Cosign) | DevOps | 1 sprint |
| TD-M-005 | Hardcoded configs (TD-005) | Multiple | 3 days |
| TD-M-006 | Three duplicate cache implementations | Performance | 2 days |
| TD-M-007 | Widget Contract tests missing for 7+ widgets (QA-005) | QA | 1 sprint |
| TD-M-008 | CSS variables referenced in components but undefined | Design System | 1 day |
| TD-M-009 | Renderer uses hardcoded Tailwind colors, not design tokens | Design System | 2 days |
| TD-M-010 | Duplicate Card/Badge/Sidebar implementations | Design System | 3 days |
| TD-M-011 | Company Workspace tabs (5 tabs) from design spec missing | UX | 8 days |
| TD-M-012 | Two competing search interfaces (Command Bar vs Search Panel) | UX | 5 days |
| TD-M-013 | Dashboard and Company Workspace use different widget architectures | UX | 5 days |
| TD-M-014 | No a11y automated tests despite WCAG AA target | QA, UX | 1 sprint |
| TD-M-015 | No RTL-specific automated tests | QA, UX | 1 sprint |
| TD-M-016 | Two separate prompt registries not synchronized | AI | 3 days |
| TD-M-017 | AI prompt injection detection exists but never called | AI, Security | 1 hour |
| TD-M-018 | K8s manifests incomplete (ingress/HPA/PVC not deployed) | DevOps | 2 sprints |
| TD-M-019 | Terraform missing DynamoDB state locking | DevOps | 3 days |
| TD-M-020 | No password complexity requirements | Security | 1 hour |
| TD-M-021 | No account lockout mechanism | Security | 1 day |
| TD-M-022 | CSRF token generation exists but no enforcement middleware | Security | 4 hours |
| TD-M-023 | `facets_raw()` executes N sequential SQL queries | Performance | 1 day |
| TD-M-024 | Two Competing search interfaces (Command Bar vs Search Panel) | UX | 5 days |
| TD-M-025 | Mobile nav redundancy (FAB drawer + CSS bottom bar) | UX | 1 day |
| TD-M-026 | PostgreSQL repos recently migrated — edge cases untested | CTO | Monitoring |
| TD-M-027 | Timeline domain at 82% coverage (below 85% minimum) | QA | 1 sprint |
| TD-M-028 | CRM domain at 80% coverage (below 85% minimum) | QA | 1 sprint |
| TD-M-029 | Scoring domain at 78% coverage (below 85% minimum) | QA | 1 sprint |

---

## Part VII — Current State Assessment

### 7.1 What's Working Well (Strengths and Superpowers)

1. **World-class Architecture Governance** — 9-article Engineering Constitution with enforcement mechanisms; 10+ ADRs; 26 project principles; frozen interfaces; automated architecture compliance checks

2. **Domain-Driven Design** — 13 bounded contexts with strict module boundaries; zero cross-domain imports confirmed by automated checks; Repository Pattern consistently applied

3. **NBA Decision Pipeline** — 12-stage decision engine with deterministic rules, AI reasoning fallback, confidence scoring, explainable outputs, and feedback loop. This is the platform's core IP and competitive moat.

4. **Widget SDK v1.0** — Frozen, tested (103 tests for Mission Center), mandatory Container/View pattern, contract testing utilities, accessibility requirements. 51 widgets built on this foundation.

5. **Data Fabric Layer** — Entity Resolution (pg_trgm fuzzy matching) + Hybrid Search (tsvector + pgvector, RRF fusion) + Feature Store (7 computers) is genuinely innovative at this stage.

6. **Test Coverage** — 2,054 tests at 93% unit coverage, 100% pass rate, 0 any types. 60+ backend test files, 105+ frontend test files, 41 backend E2E tests.

7. **Arabic-First Design** — Full RTL CSS layer with 30+ directional overrides; IBM Plex Sans Arabic font; native Arabic in all prompts, schemas, and outputs; Arabic-aware tokenization; KSA PDPL compliance built-in.

8. **CI/CD Pipeline** — 4 GitHub Actions workflows (CI, Deploy, Docker Smoke, Security Scan); automatic rollback on deploy failure; SBOM generation; 7 security scanning tools; version-pinned container images.

9. **API Design** — 205+ REST endpoints across 40+ routers; Pydantic validation; OpenAPI auto-docs; RFC 7807 errors; RBAC on every route; tiered rate limiting; comprehensive audit trail.

10. **Documentation** — 1,623-line deployment guide; 1,410-line production runbook; 26-file API portal; ADRs; CHANGELOG; user guide; admin guide; SLA; product bible; revenue execution bible.

### 7.2 Critical Gaps and Weaknesses

1. **Infrastructure Not Deployed** — Redis and Kafka are in docker-compose files but NOT in production. Events are lost on restart. Rate limiting is in-memory (per-server, no clustering). This is the single most important gap.

2. **Solo Architect Bottleneck** — One person designed and built everything. No knowledge transfer mechanism. No team. Velocity is capped at what one person can do with AI assistance. Onboarding any new engineer requires that same person to stop building and start teaching.

3. **Data Pipeline Not Live** — 5 scraper API keys are placeholder values. Connector data is mock/simulated. Three production API endpoints return hardcoded demo data. Arabic text normalization is broken (BUG-002). The "Data First, AI Second" principle is aspirational.

4. **No Production Monitoring** — Prometheus + Grafana are configured but not deployed in the production docker-compose. No APM. No log aggregation. No alerting rules deployed. No PagerDuty/OpsGenie. If production goes down at 3 AM, nobody knows.

5. **No Frontend E2E Tests** — Zero browser-based tests. No Playwright. No Cypress. No Selenium. The 41 E2E tests are ALL backend (HTTP client integration). This is the QA team's single largest gap.

6. **Enrichment Endpoint Broken** — `POST /enrich` operates at 8s p95 against a 5s budget. p99 reaches 15s (3x budget). There is no remediation plan beyond recording it as a known issue.

7. **Unbounded Memory Growth** — Four decision engines (DecisionEngine, EvidenceEngine, FeedbackEngine, LearningEngine) store data in unbounded arrays and maps with no TTL or LRU eviction. Over time, O(n) degradation will consume all available memory.

8. **Backend Design Token Divergence** — Backend Python design tokens still use the old blue-based palette (`#2563EB`), zinc neutrals, and Inter fonts. Frontend uses MUHIDE orange (`#F57C1E`), warm neutrals, and IBM Plex fonts. Any server-rendered content will be visually inconsistent.

9. **Dashboard Metrics Overstate Reality** — The Engineering Dashboard reports 95% architecture compliance; the actual compliance document reports 87%. The dashboard reports 9.5/10 production readiness; the CTO auditor found 7.2/10. The dashboard cannot be used as a source of truth for board reporting.

10. **No Commercial Validation** — 3 pilot tenants were just provisioned. Zero outcome metrics populated. Zero paying customers. All customer success metrics are pending. The platform is technically capable but commercially unproven.

---

## Part VIII — 90-Day Action Plan

### Phase 1: Stabilize (Days 1-30) — "Don't Lose What You Have"

| Week | Focus | Key Actions |
|------|-------|------------|
| **Week 1** | Infrastructure Hardening | Deploy Redis in production; deploy Prometheus + Grafana in production; verify all 9 runtime routers are authenticated; configure Cloudflare/DDoS protection; test backup restore to staging |
| **Week 2** | Arabic & Search Quality | Fix BUG-002 (Arabic text normalization); load Arabic thesaurus/stop words; benchmark search relevance with native Arabic speakers; convert search benchmarks to real PostgreSQL queries |
| **Week 3** | Data Integrity & DR | Migrate localStorage stores to API-backed persistence; execute rollback drill; document recovery procedures; verify all Alembic migrations are reversible; activate scraper API keys for live data pipeline |
| **Week 4** | Team Scaling | Post backend engineer role; post frontend engineer role; begin onboarding documentation; create architecture decision framework (so decisions don't require solo architect) |

### Phase 2: Harden (Days 31-60) — "Close the Gaps"

| Week | Focus | Key Actions |
|------|-------|------------|
| **Week 5-6** | Decision Platform & NBA | Extend DecisionProvider to Dashboard + Company Intelligence; increase widget adoption from 5.6% to 50%+; complete NBA AI reasoning pipeline (NBAReasoner built but unused); persist agent results and signal stores to PostgreSQL |
| **Week 7-8** | E2E Testing & Performance | Set up Playwright/Cypress for frontend E2E tests (10 critical paths); close E2E coverage gap from 40% to 60%; fix `facets_raw()` N sequential queries; consolidate 3 cache implementations to one; add TTL/LRU eviction to 4 unbounded in-memory stores |

### Phase 3: Scale Prep (Days 61-90) — "Prepare for Growth"

| Week | Focus | Key Actions |
|------|-------|------------|
| **Week 9-10** | Event Bus & Resilience | Deploy Kafka; migrate event bus from in-process to Kafka (dual-run strategy); implement dead letter queue; set up PostgreSQL streaming replication; add Neo4j read replica or evaluate Neo4j AuraDB managed service |
| **Week 11-12** | Production Hardening | Implement city/region normalization; deploy semantic cache; enable gzip + caching headers in NGINX; unify backend design tokens to MUHIDE palette; consolidate duplicate components (Card, Badge, Sidebar); add Contract tests for all 7+ deployed widgets |
| **Week 13** | Production Audit | Conduct external pentest; run full production audit against all 25 GA gates with independent verification; verify all SLA metrics; document all outstanding technical debt; create incident response plan with alerting |

### What NOT to Build During These 90 Days

- ❌ Revenue Brain, Agent Runtime, Prompt Studio, AI Governance Portal
- ❌ GraphQL, MCP Server, Agent SDK
- ❌ Knowledge Packs, Signal Marketplace
- ❌ Workflow Engine, Business Rules Studio
- ❌ Any V5 blueprint capability not already in progress
- ❌ New widgets beyond contract test completion
- ❌ New domains beyond documentation completion

**Rationale:** The platform has enough capability to serve 10-50 enterprise customers with the existing feature set. Adding features on a shaky foundation multiplies risk without creating commercial value. The 90-day priority is to make what exists production-grade.

---

## Part IX — Key Decisions Needed from Leadership

| # | Decision | Context | Options | Recommended |
|---|----------|---------|---------|-------------|
| 1 | **GA Timing** | Dashboard declares "GA Complete" but 8 critical gaps remain | (A) August 15 with conditional gates; (B) September 15 after hardening; (C) Pilot-only Q3 2026 | (B) September 15 — close critical gaps first |
| 2 | **Team Hiring** | Solo architect is unsustainable | (A) Hire 6-7 people immediately; (B) Hire 2-3 contractors; (C) Run solo with AI assistance | (A) Minimum 6-person team within 90 days of GA |
| 3 | **Redis/Kafka Deployment** | Both configured but not deployed | (A) Deploy both before GA; (B) Start with Redis + Redis Streams, defer Kafka; (C) Run without either | (B) Redis urgently; Redis Streams as stepping stone to Kafka |
| 4 | **Neo4j vs PostgreSQL Graph** | Neo4j adds operational complexity, revenue graph unfilled | (A) Keep Neo4j, add backup; (B) Migrate graph to PostgreSQL; (C) Run both in parallel | (A) Keep Neo4j for now, add automated backup, benchmark vs PostgreSQL for graph queries post-GA |
| 5 | **Self-Hosted Embeddings vs OpenAI** | E5 model costs $120/mo, quality for Arabic unproven | (A) Deploy self-hosted E5; (B) Stay with OpenAI embeddings; (C) Benchmark both with Arabic data | (C) Benchmark both before deciding |
| 6 | **Dashboard Metrics Integrity** | Self-reported metrics overstate reality by 10-30% | (A) Fix dashboard to use automated CI metrics; (B) Add confidence column; (C) Remove aspirational metrics | (A + B) Fix dashboard AND add confidence indicators |
| 7 | **Architecture Compliance Definition** | Two conflicting documents (87% vs 95%) | (A) Accept 87% as truth; (B) Investigate discrepancy; (C) Create single source of truth | (B + C) Investigate discrepancy AND create single automated source |
| 8 | **Monorepo Structure** | 31 runtime modules vs 15 documented domains | (A) Document all modules; (B) Deprecate unused runtime packages; (C) Keep as-is | (B) Aggressively deprecate unused runtime packages, document the rest |
| 9 | **Frontend E2E Testing** | Zero browser-based tests exist | (A) Adopt Playwright immediately; (B) Use Cypress; (C) Defer to post-GA | (A) Playwright — faster, better parallelization, maintained by Microsoft |
| 10 | **Coverage Gate Enforcement** | fail_under=30 in pyproject.toml vs constitutional 85% | (A) Set to 85% immediately; (B) Incremental increase; (C) Keep at 30% | (A) Set to 85% immediately — fix or skip failing tests |

---

## Part X — Platform Quick Reference

### Key Numbers

| Metric | Value |
|--------|-------|
| Total code modules (runtime + domains + sdk) | 75 |
| Total REST endpoints | ~205 |
| Total registered routers | ~40 |
| Total frontend features | 12 |
| Total widgets | 51 |
| Total tests | 2,054 |
| Unit test coverage | 93% |
| E2E tests (backend) | 41 |
| E2E tests (frontend) | 0 |
| Database tables | ~60 |
| Alembic migrations | 27 |
| GitHub Actions workflows | 4 |
| Docker services (all envs) | 20 |
| AI agents | 11 |
| Built-in decision rules | 7 |
| Feature store computers | 7 |
| NB4 decision pipeline stages | 12 |
| Scoring dimensions | 6 |
| RAG chunking strategies | 3 |
| Registered KPIs | 18 |
| Data scraper sources | 5 (placeholders) |
| Government data sources | 6 |
| Target personas | 8 |
| Estimated lines of code | ~200,000+ |
| Days to build (8 sprints) | ~7 days |
| Pilot tenants | 3 |

### Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| Governance | `engineering-os/ENGINEERING_CONSTITUTION.md` | Engineering Constitution (9 articles) |
| Dashboard | `engineering-os/ENGINEERING_DASHBOARD.md` | Self-reported metrics (NOTE: overstated) |
| Product Vision | `docs/PRODUCT_BIBLE.md` | Product vision, personas, differentiation |
| Revenue Vision | `docs/REVENUE_EXECUTION_BIBLE.md` | Revenue execution bible |
| Architecture | `salesos/docs/ARCHITECTURE_BOOK.md` | 2,006-line architecture reference |
| DDD | `salesos/docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md` | 1,283-line DDD specification |
| Compliance | `salesos/docs/ARCHITECTURE_COMPLIANCE.md` | Actual architecture compliance scores |
| Roadmap | `docs/ROADMAP_5_YEARS.md` | 5-year roadmap to $50M ARR |
| Blueprint | `docs/MASTER_BLUEPRINT.md` | V5 master blueprint (26 principles, 36 capabilities) |
| Capabilities | `docs/CAPABILITY_CATALOG.md` | 40 capabilities (CAP-001 through CAP-040) |
| Decision Log | `docs/DECISION_LOG.md` | 10 accepted + 5 rejected decisions |
| Release Plan | `salesos/frontend/PRODUCT_COMPLETION_REPORT.md` | Completed widget inventory |
| Launch Plan | `salesos/docs/GA_LAUNCH_PLAN.md` | 25 GA gates |
| SLAs | `salesos/docs/SLA.md` | SLA commitments |
| API Docs | `salesos/docs/portal/api/` | 26 API portal files |
| User Guide | `salesos/docs/user_guide.md` | End-user documentation |
| Admin Guide | `salesos/docs/admin_guide.md` | Administrator documentation |
| Deployment | `salesos/docs/deployment_guide.md` | 1,623-line deployment guide |
| Runbook | `salesos/docs/production_runbook.md` | 1,410-line production runbook |
| Backend Main | `salesos/backend/app/main.py` | FastAPI application entry (310+ lines) |
| Frontend Layout | `salesos/frontend/src/app/(dashboard)/layout.tsx` | Dashboard shell |
| Feature Registry | `salesos/backend/runtime/` | 31 runtime modules |
| Domain Code | `salesos/backend/domains/` | 15 domain packages |
| SDK | `salesos/backend/sdk/` | 29 cross-cutting SDK packages |
| Migrations | `salesos/backend/app/alembic/versions/` | 27 Alembic migrations |
| Terraform | `salesos/infra/terraform/main.tf` | AWS infrastructure |
| Docker Prod | `salesos/docker-compose.prod.yml` | Production Docker deployment |
| CI | `salesos/.github/workflows/ci.yml` | CI pipeline |
| Deploy | `salesos/.github/workflows/deploy.yml` | Deploy pipeline with rollback |

---

## Part XI — Appendices

### A. GA Launch Decision Framework

**Go for GA on August 15 ONLY IF:**
- [ ] Redis deployed and rate limiting is Redis-backed (not in-memory)
- [ ] Backup restore tested successfully to staging
- [ ] Rollback drill completed successfully
- [ ] Arabic text normalization fix deployed (BUG-002)
- [ ] All 25 GA gates pass — independently verified, not self-reported
- [ ] At least 1 additional backend engineer onboarded
- [ ] Monitoring alerting deployed and tested
- [ ] Cloudflare/DDoS protection configured
- [ ] PostgreSQL streaming replication configured
- [ ] At least 10 frontend E2E tests in Playwright covering critical paths

**Defer GA if:**
- Any of the above items are incomplete
- Pilot feedback shows NPS < 30 or NBA acceptance rate < 40%
- Any critical security issue discovered in pentest

**Post-GA Commitment:**
The organization must commit to hiring a minimum 6-person engineering team within 90 days of GA.

### B. Minimum Team for Production Operations

| Role | Count | Justification |
|------|-------|---------------|
| Backend Engineer | 2 | Maintain 15+ domains, fix bugs, build new capabilities |
| Frontend Engineer | 2 | Maintain 51 widgets, build new applications |
| DevOps/SRE Engineer | 1 | Production deployment, monitoring, CI/CD, DR |
| QA Engineer | 1 | E2E tests, performance testing, regression suites |
| Security Engineer | 0.5 (shared) | Pentest management, dependency audit, secret rotation |
| Product Manager | 1 | Feature prioritization, customer feedback, roadmap |

**Annual cost estimate:** ~$250-400K (Saudi/GCC market rates)

### C. Version History

| Version | Date | Key Deliverables |
|---------|------|-----------------|
| 0.0.1 | 2026-07-05 | Initial: project scaffolding, domain model, core infra |
| 0.0.2 | 2026-07-06 | Sprint 1: Design System, 22 Foundation Components, MUHIDE theme, dark mode, RTL |
| 0.1.0 | 2026-07-07 | Sprint 2: Decision Platform, AI Agents, Timeline, Workflow, Employee Intelligence |
| 0.2.0 | 2026-07-08 | Sprint 3: Hardening, monitoring, customer success, pilot prep |
| 0.3.0 | 2026-07-08 | Sprint 5: Entity Resolution, Hybrid Search, Feature Store, KG, Pilot launch |
| 0.4.0 | 2026-07-10 | Sprint 6: GA Security Hardening, all routers authed, tiered rate limiting |
| 0.5.0 | 2026-07-12 | Sprint 0.5: Production stabilization, 57 RBAC fixes, CSRF, Neo4j fix |
| 1.0.0 | 2026-07-08 | Initial GA tag (premature — continued 0.x) |
| 1.1.0 | 2026-07-12 | Entity Resolution, Hybrid Search, Feature Store, 119 new tests |
| 1.2.0 | 2026-07-12 | Sprint 6: Auth on all routers, tiered rate limiting, admin/deployment/runbook guides |

---

> **This Knowledge Base synthesizes findings from 14 independent specialist agent audits, all platform documentation, and full codebase analysis. It is the single authoritative reference for understanding SalesOS without reading source code.**
>
> *Compiled by Reverse Engineering Lead — 2026-07-13*
> *Classification: CONFIDENTIAL — FOR CTO, BOARD, AND INCOMING ENGINEERING LEADERSHIP*
