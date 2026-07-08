# SalesOS — Complete Architecture Audit & Implementation Roadmap

**Date:** July 2, 2026
**Context:** Production-Ready for Muhide — Real Data, Real Users, Real Integrations
**Goal:** Enterprise Revenue Operating System (NOT a CRM)

---

## PART 1 — COMPLETE ARCHITECTURE AUDIT

---

### 1.1 EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Total Source Files** | ~350+ (backend Python: ~180, frontend TypeScript: ~85, pipeline scripts: ~50, scrapers: ~30) |
| **Backend** | FastAPI + DDD — excellent architecture, 27 runtimes (21 implemented, 6 planned stubs) |
| **Frontend** | Next.js 15 monorepo — innovative runtime composition, **zero app code**, zero tests |
| **Data Pipeline** | 5 government scrapers + 4 CRM enrichment scripts — **the only part producing business value** |
| **Database** | PostgreSQL 16 (pgvector/pg_trgm), Neo4j 5 Community, Redis 7 |
| **Event System** | CloudEvents 1.0, Kafka, PostgresEventStore — production quality |
| **AI** | 11 agent classes, ALL return **hardcoded mock data** |
| **Integrations** | None live — Notion has hardcoded tokens, no email/calendar/workflow |
| **Overall Production Readiness** | **12%** |

---

### 1.2 MODULE-BY-MODULE AUDIT

#### BACKEND — App Layer

| Module | Status | Complete | Missing | Production Ready |
|--------|--------|----------|---------|-----------------|
| `app/main.py` | ✅ Complete | 95% | Sentry init fixed, exception handler finalized | ✅ Yes |
| `app/config.py` | ✅ Complete | 90% | JWT default removed, env validation hardened | ✅ Yes |
| `app/database.py` | ✅ Complete | 95% | Connection pooling (PgBouncer) | ✅ Yes |
| `app/dependencies.py` | ✅ Complete | 85% | Tenant cross-validation against JWT | ✅ Yes |
| `app/common/middleware.py` | ✅ Complete | 100% | Rate limit + Security headers + RequestID + Timing | ✅ Yes |
| `app/common/exceptions.py` | ✅ Complete | 100% | — | ✅ Yes |
| `app/routers/commercial.py` | ⚠️ Partial | 60% | Uses InMemory repos — data lost on restart | ❌ No |
| `app/routers/copilot.py` | ⚠️ Partial | 40% | Uses mock agents, no real LLM wired | ❌ No |

#### BACKEND — App Modules (DDD)

| Module | Status | Complete | Missing | Production Ready |
|--------|--------|----------|---------|-----------------|
| **Identity** (tenant/user/auth) | ✅ Complete | 90% | Password reset flow, refresh endpoint, MFA | ⚠️ Near |
| **Company** (CRUD/search/pgvector) | ✅ Complete | 90% | PostgreSQL repos work, benchmarking done | ⚠️ Near |
| **Entity Resolution** (golden records) | ✅ Complete | 85% | Conflicts tracked, provenance maintained | ⚠️ Near |
| **Contact** | ❌ Empty | 0% | `/app/modules/contact/` is empty `__init__.py` | ❌ No |
| **Search** | ❌ Empty | 0% | `/app/modules/search/` is empty `__init__.py` | ❌ No |
| **Tenant** | ❌ Empty | 0% | `/app/modules/tenant/` is empty `__init__.py` | ❌ No |

#### BACKEND — Runtime Layer (27 packages)

| Runtime | Status | Complete | Missing | Production Ready |
|---------|--------|----------|---------|-----------------|
| **Capability Framework** | ✅ Complete | 100% | Registry, loader, discovery | ✅ Yes |
| **Event Runtime** | ✅ Complete | 100% | CloudEvents, Kafka, PostgresEventStore | ✅ Yes |
| **Feature Store** | ✅ Complete | 95% | 7 feature computers, real-time scoring | ⚠️ Near |
| **Decision Runtime** | ⚠️ Partial | 80% | ContextBuilder, PolicyEngine, RecEngine, DecisionEngine, FeedbackLoop | ⚠️ Near |
| **Search Runtime** | ⚠️ Partial | 85% | Strategy matrix, intent detection, ranking — SQL injection **fixed** | ⚠️ Near |
| **Timeline Runtime** | ✅ Complete | 95% | Universal timeline, domain event subscription | ✅ Yes |
| **Knowledge Graph Runtime** | ⚠️ Partial | 70% | Neo4j schema, CRUD ops — missing complex queries | ❌ No |
| **Data Fabric Runtime** | ⚠️ Partial | 75% | 8-stage pipeline, 20+ source connectors — wired but not fed | ❌ No |
| **UX Runtime** | ⚠️ Partial | 60% | Experience routing, workspaces — not connected to frontend | ❌ No |
| **UI Schema Engine** | ✅ Complete | 90% | Schema generation from capabilities | ✅ Yes |
| **Form Engine** | ✅ Complete | 90% | Dynamic form rendering | ✅ Yes |
| **Action Engine** | ✅ Complete | 90% | Action registration and execution | ✅ Yes |
| **Extension API** | ⚠️ Partial | 50% | Hook points defined, no extensions built | ❌ No |
| **Plugin Sandbox** | ⚠️ Partial | 40% | Resource quotas, hook points — no plugins | ❌ No |
| **Widget Engine** | ✅ Complete | 80% | Widget registry, built-in widgets registered | ⚠️ Near |
| **Policy Runtime** | ⚠️ Partial | 60% | ALLOW/BLOCK/WARN/ESCALATE — not integrated with auth | ❌ No |
| **Recommendation Runtime** | ⚠️ Partial | 50% | Recommendation engine defined — no real data | ❌ No |
| **Context Runtime** | ⚠️ Partial | 60% | Context building — no production callers | ❌ No |
| **Agent Runtime** | 🔴 Planned RT3 | 0% | Empty `__init__.py` | ❌ No |
| **Workflow Runtime** | 🔴 Planned RT3 | 0% | Empty `__init__.py` | ❌ No |
| **Memory Runtime** | 🔴 Planned RT3 | 0% | Empty `__init__.py` | ❌ No |
| **Scheduler Runtime** | 🔴 Planned RT3 | 0% | Empty `__init__.py` | ❌ No |
| **Execution Runtime** | 🔴 Planned RT4 | 0% | Empty `__init__.py` | ❌ No |
| **Simulation Runtime** | 🔴 Planned RT4 | 0% | Empty `__init__.py` | ❌ No |
| **Data Fabric Runtime** | ⚠️ Partial | 75% | Connector engine, pipelines — no connected sources | ❌ No |

#### BACKEND — Intelligence Layer

| Module | Status | Complete | Missing | Production Ready |
|--------|--------|----------|---------|-----------------|
| **Agents** (11 agents) | ⚠️ Partial | 40% | All return hardcoded mock data, no LLM wiring | ❌ No |
| **Business Objects** | ✅ Complete | 90% | Base abstractions, entity types, signal types | ✅ Yes |
| **Company Intelligence** | ⚠️ Partial | 50% | Scoring engine — no live data sources | ❌ No |
| **Data Fabric** | ⚠️ Partial | 75% | 8-stage pipeline, source mappings (balady, taqeem, etc.) | ❌ No |
| **Digital Twin** | ⚠️ Partial | 40% | CompanyTwin only, no events produced | ❌ No |
| **Enrichment** | ⚠️ Partial | 40% | Priority logic exists — no providers wired | ❌ No |
| **Market Intelligence** | ⚠️ Partial | 30% | Source polling architecture — no sources connected | ❌ No |
| **Relationship Graph** | ⚠️ Partial | 50% | BFS algorithm, Neo4j — lightweight mock bypasses graph DB | ❌ No |
| **Revenue Brain** | ⚠️ Partial | 40% | Orchestrator, scoring — all returns hardcoded | ❌ No |
| **Signals** | ⚠️ Partial | 40% | Weighted scoring, recipes — no signal sources connected | ❌ No |
| **Simulation** | ⚠️ Partial | 30% | What-if engine — deterministic outcomes, no real data | ❌ No |

#### BACKEND — SDK Layer

| Module | Status | Complete | Missing | Production Ready |
|--------|--------|----------|---------|-----------------|
| **sdk/auth.py** | ✅ Complete | 95% | JWT, bcrypt, token management | ✅ Yes |
| **sdk/audit.py** | ✅ Complete | 95% | Immutable audit logs | ✅ Yes |
| **sdk/cache.py** | ✅ Complete | 90% | Redis-based CacheService | ✅ Yes |
| **sdk/config.py** | ✅ Complete | 90% | Environment-aware configuration | ✅ Yes |
| **sdk/database.py** | ✅ Complete | 95% | Unit of Work, session management | ✅ Yes |
| **sdk/events/** | ✅ Complete | 100% | CloudEvents 1.0, bus (InMemory/Kafka), store (Postgres) | ✅ Yes |
| **sdk/graph.py** | ✅ Complete | 85% | Neo4j client wrapper | ✅ Yes |
| **sdk/permissions.py** | ⚠️ Partial | 70% | RBAC defined — never called from endpoints | ❌ No |
| **sdk/search.py** | ✅ Complete | 90% | Parameterized search — SQL injection **fixed** | ✅ Yes |
| **sdk/security.py** | ⚠️ Partial | 60% | CSRF token generator — never called | ❌ No |
| **sdk/telemetry.py** | ✅ Complete | 90% | Structured logging | ✅ Yes |
| **sdk/vector.py** | ✅ Complete | 85% | OpenAI embedding service | ✅ Yes |

#### BACKEND — Tests

| Module | Tests | Status |
|--------|-------|--------|
| Architecture fitness | 5 tests | ✅ Passing |
| Health | 2 tests | ✅ Passing |
| Identity | 8 tests | ✅ Passing |
| Company | 7 tests | ✅ Passing |
| Entity Resolution | 26 tests | ✅ Passing |
| Search domain | ~20 tests | ✅ Passing |
| Commercial domains (quote, proposal, pipeline, opp, contract, activity) | ~50 tests | ✅ Passing |
| Forecast | ~10 tests | ✅ Passing |
| Timeline | ~10 tests | ✅ Passing |
| Analytics | ~5 tests | ✅ Passing |
| Recommendation | ~5 tests | ✅ Passing |
| Context | ~5 tests | ✅ Passing |
| **Total Backend Tests** | **~160** | **✅ All Passing** |

---

#### FRONTEND

| Module | Status | Complete | Missing | Production Ready |
|--------|--------|----------|---------|-----------------|
| **App Router** (pages) | ❌ Minimal | 10% | Only login, register, dashboard, companies list, company detail pages exist | ❌ No |
| **packages/runtime** (9 runtimes) | ✅ Complete | 100% | State, Session, Realtime, Cache, Localization, Accessibility, Rendering, Collaboration, Offline — all coded | ✅ Yes |
| **packages/ui** (17 components) | ✅ Complete | 100% | Button, Card, Modal, Table, Input, Select, Tabs, Sidebar, etc. | ✅ Yes |
| **packages/hooks** (14 hooks) | ✅ Complete | 100% | useRuntime, useSession, useDebounce, useTheme, useRealtime, etc. | ✅ Yes |
| **packages/renderer** | ✅ Complete | 100% | SchemaRenderer → ViewerRenderer → TabRenderer → SectionRenderer → WidgetRenderer | ✅ Yes |
| **packages/workspace** | ✅ Complete | 100% | generateWorkspace, 6 role presets, workspace generator → renderer bridge | ✅ Yes |
| **packages/design-language** | ✅ Complete | 100% | 15 token files, 18 semantic colors, 4 densities, Arabic-first typography | ✅ Yes |
| **packages/forms** | ✅ Complete | 100% | 14 form input types, FormSection, FormStep | ✅ Yes |
| **packages/charts** | ⚠️ Basic | 60% | 11 SVG-based charts — not production grade | ❌ No |
| **packages/icons** | ✅ Complete | 100% | Lucide icons organized by category | ✅ Yes |
| **packages/config** | ❌ Empty | 0% | Referenced in package.json, no source files | ❌ No |
| **Components** (CopilotPanel) | ⚠️ Mock | 30% | Uses setTimeout to simulate AI responses | ❌ No |
| **Components** (SearchPanel) | ⚠️ Mock | 40% | Hardcoded search results | ❌ No |
| **lib/api.ts** | ⚠️ Partial | 50% | API client defined — only Company endpoints wired | ❌ No |
| **Dashboard page** | ⚠️ Mock | 20% | Hardcoded "---" values for all stats | ❌ No |
| **Companies pages** | ⚠️ Partial | 50% | List works with debounce bug, detail page basic | ❌ No |
| **Auth pages** (login/register) | ⚠️ Partial | 60% | Login/register UI exists, API integration needed | ❌ No |
| **Tests** | ❌ None | 0% | Jest installed, zero test files | ❌ No |
| **Storybook** | ❌ None | 0% | Zero `.stories` files | ❌ No |

---

#### DATA PIPELINE & SCRAPERS

| Module | Status | Complete | Missing | Production Ready |
|--------|--------|----------|---------|-----------------|
| **crm_enrichment.py** (Phase 1-9) | ✅ Complete | 90% | Dedup, normalization, output — O(n^2) SequenceMatcher | ⚠️ Near |
| **crm_pipeline.py** | ✅ Complete | 85% | Quality scoring, domain validation — duplicated code | ⚠️ Near |
| **sales_intel_pipeline.py** | ✅ Complete | 85% | ICP scoring, TAM, routing — Saudi market classification | ⚠️ Near |
| **website_li_pipeline.py** | ✅ Complete | 80% | DNS/HTTP validation, LinkedIn discovery — duplicated domain check | ⚠️ Near |
| **Balady Scraper** (engineering offices) | ✅ Complete | 95% | 4,904 offices, full detail | ✅ Yes |
| **Najiz Scraper** (lawyers) | ✅ Complete | 95% | 15 fields per lawyer | ✅ Yes |
| **REGA Scraper** (real estate) | ✅ Complete | 85% | Playwright-based, pagination | ✅ Yes |
| **Taqeem Scraper** (valuation facilities) | ✅ Complete | 90% | 349 unique facilities, forensic report | ✅ Yes |
| **NCNP Scraper** (nonprofits) | ✅ Complete | 90% | 9,040 entities, resume capability | ✅ Yes |
| **Notion Integration** (4 DBs) | ✅ Complete | 80% | Rate-limited, progress-tracked — hardcoded tokens | ⚠️ Near |
| **sales-os/** (Notion automation) | ✅ Complete | 85% | Dedup, scoring, priority, stale detection | ⚠️ Near |

---

#### INFRASTRUCTURE

| Component | Status | Complete | Missing | Production Ready |
|-----------|--------|----------|---------|-----------------|
| **Docker Compose** | ✅ Complete | 100% | PostgreSQL, Neo4j, Redis, ZooKeeper, Kafka, PgBouncer, Backend, Frontend | ✅ Yes |
| **K8s Manifests** | ✅ Complete | 90% | Backend + Frontend deployments, secrets, configmaps | ⚠️ Near |
| **Terraform** (AWS me-south-1) | ✅ Complete | 90% | VPC, EKS 1.30, RDS PostgreSQL, ElastiCache Redis, S3, CloudFront | ⚠️ Near |
| **CI (GitHub Actions)** | ⚠️ Partial | 60% | Jobs defined — not all running | ❌ No |
| **Monitoring** | ❌ Missing | 5% | Sentry DSN exists but never initialized pre-fix, no Prometheus/Grafana | ❌ No |
| **Backup/DR** | ❌ Missing | 0% | No backup strategy, no disaster recovery plan | ❌ No |

---

### 1.3 ENGINE-BY-ENGINE ANALYSIS (Original SalesOS Architecture)

#### Strategy Engine
- **What exists:** DecisionEngine, ContextBuilder, PolicyEngine, RecommendationEngine, FeedbackLoop
- **What is partial:** Decision scores use deterministic rules, not ML/AI. Policy engine defines ALLOW/BLOCK/WARN/ESCALATE but not integrated with auth or endpoints.
- **What is missing:** ML-based strategy optimization, A/B testing framework, strategy versioning, competitive strategy analysis
- **Status:** 40% complete

#### ICP Engine (Ideal Customer Profile)
- **What exists:** IcpComputer in feature_store/features.py, ICP scoring in sales_intel_pipeline.py
- **What is partial:** ICP scoring is rule-based (industry fit, company size, digital presence, etc.), hardcoded weights
- **What is missing:** ML-based ICP prediction, dynamic ICP adjustment, lookalike company discovery, ICP decay tracking
- **Status:** 35% complete

#### GTM Engine (Go-to-Market)
- **What exists:** Sales routing (territory map, queues, outreach channels) in sales_intel_pipeline.py
- **What is partial:** Territory assignment, sales queue routing — all Excel-based pipeline, not live
- **What is missing:** Live GTM execution engine, multi-channel orchestration (email, call, LinkedIn), sequence builder, A/B testing campaigns, meeting scheduling
- **Status:** 15% complete

#### Lead Generation Engine
- **What exists:** Data Fabric ConnectorEngine (20+ source connectors), government scrapers (Balady, Najiz, REGA, Taqeem, NCNP)
- **What is partial:** Scrapers work but are not integrated into the live platform. Data Fabric is wired but no sources connected.
- **What is missing:** Web scraping API endpoint, lead scoring on ingestion, lead enrichment pipeline automated, lead dedup in real time, third-party lead APIs (Apollo, ZoomInfo, Lusha)
- **Status:** 30% complete

#### Company Intelligence Engine
- **What exists:** CompanyIntelligence, CompanyIntelligenceEngine, Data Fabric (8-stage pipeline)
- **What is partial:** Scoring engine works, completeness/confidence calculation exists, but no live sources
- **What is missing:** Real-time company data fetching, news monitoring, competitor tracking, regulatory filing monitoring, financial health scoring, employee growth tracking
- **Status:** 25% complete

#### Data Enrichment Engine
- **What exists:** EnrichmentService, priority-based field filling, Entity Resolution (golden records), Data Quality Engine
- **What is partial:** Enrichment providers defined but not wired — no OpenAI Clearbit, no Apollo, no Hunter.io
- **What is missing:** Real enrichment providers (OpenAI extraction, Clearbit, Apollo, Hunter.io, SOCPA data), automated enrichment pipeline, enrichment confidence scoring, enrichment scheduling
- **Status:** 25% complete

#### Market Intelligence Engine
- **What exists:** MarketIntelligenceEngine, source polling architecture
- **What is partial:** Single file, no market data sources connected
- **What is missing:** Saudi market news feeds, government tender monitoring (Etimad), regulatory changes (CMA, SAMA, SFDA), competitor market activity, market trend analysis
- **Status:** 10% complete

#### Buying Signals Engine
- **What exists:** SignalEngine, weighted scoring, signal recipes, recommendation generation, hot-company detection
- **What is partial:** Signal architecture works — no signal sources connected
- **What is missing:** Website visit tracking, content consumption signals, email engagement signals, meeting activity signals, job posting signals, funding announcement signals, RFP/tender signals
- **Status:** 15% complete

#### AI Qualification Engine
- **What exists:** 11 agent classes (Research, News, Proposal, Contract, Meeting, Pricing, Forecast, Renewal, Competitor, Tender, Relationship), AgentCoordinator, LLMService
- **What is partial:** All return hardcoded data. No LLM API calls. No real qualifications.
- **What is missing:** LLM integration (OpenAI/Anthropic/Google), BANT/CHAMP/MEDDIC qualification, scoring pipeline, qualification explanation with provenance, lead-to-qualification automation
- **Status:** 10% complete

#### CRM Execution Engine
- **What exists:** Commercial router (opportunity, pipeline, activity, quote, proposal, contract, forecast, analytics), Company module (CRUD, search, branches, licenses)
- **What is partial:** All repos are InMemory — data lost on restart. No PostgreSQL persistence for commercial domains.
- **What is missing:** PostgreSQL repositories for all commercial domains, real CRUD operations, bulk operations, import/export, data migration tools, Salesforce/HubSpot migration
- **Status:** 25% complete

#### Sales Engagement Engine
- **What exists:** Nothing
- **What is missing:** Email composer (Gmail/Outlook), email sequences, call logging (Twilio/Aircall), meeting scheduler, LinkedIn engagement, SMS, templates, engagement analytics
- **Status:** 0% complete

#### Opportunity Engine
- **What exists:** Opportunity domain (contracts, engine, state machine, tests), Commercial router endpoints
- **What is partial:** InMemory repository — opportunities lost on restart. State machine is well-defined.
- **What is missing:** PostgreSQL OpportunityRepository, opportunity scoring, deal desk, opportunity splitting, team selling support
- **Status:** 30% complete

#### Proposal Engine
- **What exists:** Proposal domain (contracts, engine, state machine, tests), Commercial router
- **What is partial:** InMemory repository. State machine (Draft→Sent→Viewed→Accepted/Rejected).
- **What is missing:** PostgreSQL ProposalRepository, proposal templates, proposal builder (drag-and-drop), e-signature integration, proposal analytics
- **Status:** 25% complete

#### Contract Engine
- **What exists:** Contract domain (contracts, engine, state machine, tests), Commercial router
- **What is partial:** InMemory repository. State machine (Draft→Negotiation→Approved→Signed→Active→Expired).
- **What is missing:** PostgreSQL ContractRepository, contract templates, contract lifecycle management, contract expiry alerts, auto-renewal, e-signature (DocuSign/HelloSign)
- **Status:** 25% complete

#### Customer Success Engine
- **What exists:** Nothing dedicated
- **What is missing:** Health score calculation, NPS tracking, usage monitoring, onboarding workflow, customer health dashboard, renewal risk scoring, CS automation, customer 360
- **Status:** 0% complete

#### Revenue Intelligence Engine
- **What exists:** Revenue Brain (forecast, anomaly detection, decisions, recommendations), Forecast domain (contracts, engine, tests), Analytics domain, 19 KPIs defined
- **What is partial:** Revenue Brain returns hardcoded data. Forecast and Analytics use InMemory repos.
- **What is missing:** PostgreSQL ForecastRepository, real KPI calculation, revenue anomaly detection with ML, revenue prediction with confidence intervals, pipeline coverage analysis, deal velocity tracking
- **Status:** 20% complete

#### AI Layer
- **What exists:** 11 mock agents, AgentCoordinator, LLMService (unwired), CapabilityRegistry, ActionRegistry, vector.py (embeddings)
- **What is partial:** All agents return mock data. No LLM API integration. No tool-calling loop. No prompt management. No memory. No evaluation.
- **What is missing:** LLM API integration (OpenAI/Anthropic), tool-calling framework, agent memory (conversation history), prompt management system (templates, versioning), evaluation framework, hallucination detection, multi-agent orchestration, confidence calibration, safety filters
- **Status:** 5% complete

#### Core Services
- **What exists:** Identity (auth, tenant, user), Company (CRUD, search, branches, licenses), Entity Resolution (golden records, conflicts), Event Runtime (CloudEvents, Kafka, PostgresEventStore), Timeline Runtime, Search Runtime, Feature Store, Knowledge Graph Runtime, Capability Framework, Data Fabric, Decision Engine
- **What is partial:** PostgreSQL persistence only for Identity and Company. All commercial domains in-memory.
- **Missing:** Email Service (Gmail API, Outlook API, SMTP), Calendar Service (Google Calendar API, Outlook Calendar API, CalDAV), Notification Service (in-app, email, push, SMS), File Storage Service, Import/Export Service, Reporting Service, Webhook Service
- **Status:** 35% complete

#### Data Sources
- **What exists:** Government scrapers (Balady, Najiz, REGA, Taqeem, NCNP), CRM enrichment pipeline (Excel-based), Linkedin discovery (manual), Notion databases (4)
- **What is partial:** All data is file-based (Excel, CSV, JSON). No live API integrations.
- **What is missing:** Gmail API, Outlook API, Google Calendar API, Outlook Calendar API, Slack API, ERP API, HubSpot API (read), Apollo API, Clearbit API, Hunter.io API, SFDA API, Etimad API, Saudi government open data APIs, Google Maps API, LinkedIn API
- **Status:** 25% complete

---

### 1.4 GAP ANALYSIS — Employee 360

| Feature | Status | Notes |
|---------|--------|-------|
| Employee Profile | ❌ Missing | No employee/user profile page or endpoint |
| Assigned Companies | ❌ Missing | No user-to-company assignment table |
| Assigned Contacts | ❌ Missing | No contact module at all |
| Portfolio Value | ❌ Missing | No revenue attribution to users |
| Revenue | ❌ Missing | No per-employee revenue calculation |
| Pipeline | ⚠️ Partial | Pipeline domain exists in-memory — no user association |
| Meetings | ❌ Missing | No calendar integration |
| Emails | ❌ Missing | No email integration |
| Calls | ❌ Missing | No telephony integration |
| Tasks | ❌ Missing | No task management |
| Documents | ❌ Missing | No document management |
| Contracts | ⚠️ Partial | Contract domain exists in-memory — no user association |
| Activities | ⚠️ Partial | Activity domain exists in-memory — no user association |
| Timeline | ⚠️ Partial | Timeline runtime exists — no frontend display |
| Calendar Intelligence | ❌ Missing | No calendar read capability |
| Email Intelligence | ❌ Missing | No email read capability |
| Performance KPIs | ❌ Missing | No KPI calculation engine |
| Productivity | ❌ Missing | No productivity tracking |
| AI Coach | ❌ Missing | No coaching agent |
| Relationship Graph | ❌ Missing | No per-employee graph queries |
| Daily/Weekly/Monthly Stats | ❌ Missing | No statistics aggregation |
| Forecast | ⚠️ Partial | Forecast domain in-memory — no employee-level forecast |

**Employee 360 Completion: 3%**

### 1.5 GAP ANALYSIS — Company 360

| Feature | Status | Notes |
|---------|--------|-------|
| Company Profile | ✅ Complete | Company domain with CRUD, branches, licenses |
| Organization Structure | ❌ Missing | No org chart or hierarchy |
| Decision Makers | ⚠️ Partial | Role inference in pipeline — not live in platform |
| Contacts | ❌ Missing | Contact module is empty `__init__.py` |
| Employees Assigned | ❌ Missing | No user-company assignment |
| Meetings | ❌ Missing | No calendar data |
| Emails | ❌ Missing | No email data |
| Calls | ❌ Missing | No call data |
| Notes | ❌ Missing | No notes/activity logging for companies |
| Contracts | ⚠️ Partial | Contract domain — InMemory |
| Invoices | ❌ Missing | No billing/invoice module |
| Proposals | ⚠️ Partial | Proposal domain — InMemory |
| Pipeline | ⚠️ Partial | Pipeline domain — InMemory |
| Revenue | ❌ Missing | No revenue tracking |
| Products | ❌ Missing | No product/service catalog |
| Projects | ❌ Missing | No project management |
| Timeline | ⚠️ Partial | Timeline runtime — no frontend |
| Relationship Graph | ⚠️ Partial | Neo4j schema — no data populated |
| Health Score | ❌ Missing | No health calculation |
| Risk Score | ❌ Missing | No risk calculation |
| Growth Score | ❌ Missing | No growth calculation |
| AI Insights | ❌ Missing | No AI insight generation |

**Company 360 Completion: 10%**

### 1.6 GAP ANALYSIS — Knowledge Graph

| Feature | Status | Notes |
|---------|--------|-------|
| Neo4j Schema | ✅ Complete | 7 node labels, 10 edge types |
| Company→Contact | ❌ Missing | No contacts in database |
| Company→Employee | ❌ Missing | No user-company assignment |
| Company→Meeting | ❌ Missing | No calendar integration |
| Company→Email | ❌ Missing | No email integration |
| Company→Task | ❌ Missing | No task module |
| Company→Contract | ❌ Missing | No contracts in PostgreSQL |
| Company→Invoice | ❌ Missing | No invoice module |
| Company→Product | ❌ Missing | No product module |
| Company→Project | ❌ Missing | No project module |
| Employee→Meeting | ❌ Missing | No calendar data |
| Employee→Email | ❌ Missing | No email data |
| Employee→Task | ❌ Missing | No task module |
| Relationship Discovery | ⚠️ Partial | BFS algorithm exists — no data |
| Shortest Path | ⚠️ Partial | Path finding exists — no data |
| Ego Network | ⚠️ Partial | Network analysis — no data |
| Competitor Inference | ⚠️ Partial | Keyword-based — no data |

**Knowledge Graph Completion: 15%**

### 1.7 GAP ANALYSIS — Dashboard

| Dashboard | Status | Notes |
|-----------|--------|-------|
| CEO Dashboard | ❌ Missing | No executive-level dashboard |
| Sales Director Dashboard | ❌ Missing | No director-level dashboard |
| Sales Manager Dashboard | ❌ Missing | No manager-level dashboard |
| Employee Dashboard | ❌ Missing | No per-employee dashboard |
| Company Dashboard | ❌ Missing | No per-company dashboard |

**Dashboard Completion: 0%**

### 1.8 GAP ANALYSIS — Integrations

| Integration | Status | Notes |
|-------------|--------|-------|
| Notion | ✅ Complete | 4 databases with scrapers — hardcoded tokens (FIXED) |
| Gmail | ❌ Missing | No Gmail API integration |
| Outlook | ❌ Missing | No Microsoft Graph API integration |
| Google Calendar | ❌ Missing | No Calendar API integration |
| Outlook Calendar | ❌ Missing | No Outlook Calendar API |
| Google Workspace | ❌ Missing | No full Workspace integration |
| Microsoft 365 | ❌ Missing | No full M365 integration |
| Slack | ❌ Missing | No Slack API integration |
| Excel/CSV Import | ⚠️ Partial | Manual pipeline scripts — no UI |
| ERP (Future) | ❌ Missing | No ERP integration planned |
| HubSpot | ❌ Missing | Commercial router has mock HubSpot ingestion |
| Apollo | ❌ Missing | No Apollo API integration |
| Clearbit | ❌ Missing | No Clearbit integration |

**Integrations Completion: 5%**

### 1.9 GAP ANALYSIS — AI Copilot

| Capability | Status | Notes |
|------------|--------|-------|
| "Show Company 360" | ❌ Missing | No endpoint, no data |
| "Show Employee 360" | ❌ Missing | No endpoint, no data |
| "Who owns this company?" | ❌ Missing | No employee-company assignment |
| "What happened last week?" | ❌ Missing | No activity timeline query |
| "Which customers are inactive?" | ❌ Missing | No activity tracking |
| "Which contracts expire soon?" | ❌ Missing | No contract alerts |
| "How many meetings did X have?" | ❌ Missing | No calendar data |
| "How many emails were sent yesterday?" | ❌ Missing | No email data |
| General Q&A | ❌ Missing | Mock only — no LLM |

**AI Copilot Completion: 2%**

---

### 1.10 PRODUCTION READINESS SUMMARY

| Layer | Readiness | Key Blockers |
|-------|-----------|--------------|
| **Security** | 30% | Rate limiting added, security headers added, SQL injection fixed. Missing: MFA, SSO, SOC2 controls |
| **Backend** | 40% | Architecture world-class. All commercial domains use InMemory repos. Contact/Search/Tenant modules empty. |
| **Frontend** | 15% | Architecture world-class. Zero app-level code. Mock data everywhere. Zero tests. |
| **Data Pipeline** | 60% | Working but fragile. Excel-based, hardcoded paths, duplicated code. |
| **Integrations** | 5% | Notion only (hardcoded tokens fixed). Zero email/calendar/slack/ERP. |
| **AI** | 2% | Mock agents only. No LLM integration. |
| **Knowledge Graph** | 15% | Neo4j schema exists. No data populated. |
| **Dashboard** | 0% | No dashboards. |
| **Employee 360** | 3% | No employee-facing features. |
| **Company 360** | 10% | Company domain exists, all enrichment is offline. |
| **Infrastructure** | 50% | Docker, K8s, Terraform exist. Monitoring, backup, DR missing. |
| **Tests** | 30% | Backend ~160 tests. Frontend: zero. |
| **Documentation** | 80% | Constitution, ADRs, DDD spec, benchmark reports all excellent. |

### **Overall Production Readiness: 12%**

---

## PART 2 — NEW IMPLEMENTATION ROADMAP

---

### 2.1 STRATEGIC VISION

**The goal is NOT to rebuild from scratch.**

The goal is to ***connect the dots*** — wire the existing architecture to real data, reuse every working module, refactor what's broken, build only what's missing.

**Principle:** Never duplicate architecture. Reuse existing modules. Refactor instead of rebuilding. Keep code clean. Follow current SalesOS architecture.

---

### 2.2 IMPLEMENTATION ORDER (Phased Execution)

```
PHASE 0 — Foundation Hardening (Week 1)     SECURITY + INFRASTRUCTURE
PHASE 1 — Core Data Platform (Weeks 2-4)    POSTGRESQL PERSISTENCE + CONTACTS
PHASE 2 — Integrations Engine (Weeks 5-8)   EMAIL + CALENDAR + NOTION + ERP
PHASE 3 — Employee 360 (Weeks 9-12)         EMPLOYEE DASHBOARD + ACTIVITIES
PHASE 4 — Company 360 (Weeks 13-16)         COMPANY DASHBOARD + INTELLIGENCE
PHASE 5 — Knowledge Graph (Weeks 17-20)     RELATIONSHIPS + GRAPH QUERIES
PHASE 6 — Revenue Intelligence (Weeks 21-24) PIPELINE + FORECAST + ANALYTICS
PHASE 7 — AI Copilot (Weeks 25-30)          REAL AI + NATURAL LANGUAGE
PHASE 8 — Executive Dashboards (Weeks 31-34) FULL DASHBOARD SUITE
PHASE 9 — Production Hardening (Weeks 35-38) MONITORING + SCALE + ENTERPRISE
```

---

### 2.3 PHASE 0 — Foundation Hardening (Week 1)

**Goal:** Secure the platform + establish production baseline.

| Item | Effort | Dependencies | Details |
|------|--------|--------------|---------|
| P0-001: Fix SQL injection (already done) | 1h | — | ✅ Field allowlists in search runtime |
| P0-005-008: Secrets → env vars (done) | 2h | — | ✅ Notion tokens moved to env |
| P0-009: Rate limiting (deployed) | 4h | — | ✅ Redis-based RateLimitMiddleware |
| P0-010: Security headers (deployed) | 1h | — | ✅ CSP, HSTS, XFO, X-XSS-Protection |
| P0-011: Tenant cross-validation | 2h | — | Validate tenant against JWT claims |
| P2-004: Empty runtime cleanup | 1h | — | Mark 6 PLANNED runtimes clearly |
| P2-005: Remove duplicate dependency | 0.1h | — | package.json |
| P2-013: Remove open-design/ fork | 1h | — | Not SalesOS code |
| P2-014: Rename sales-os/ | 2h | — | → salesos-notion-automation/ |
| P2-015: Move artifacts out of root | 1h | — | → output/ |
| P2-019: JWT secret required | 0.5h | — | Remove default |
| P2-020: Docker password required | 0.5h | — | Env var required |
| P2-016: Global exception handler (done) | 1h | — | ✅ Already implemented |
| P2-021: CORS tightening | 0.25h | — | Restrict methods/headers |
| P2-017: __pycache__ in .gitignore | 0.1h | — | |
| CI/CD Pipeline working | 8h | — | GitHub Actions with passing tests |
| Monitoring setup (Sentry init done) | 4h | Prometheus + Grafana + Sentry init |
| **Total** | ~30h | | |

---

### 2.4 PHASE 1 — Core Data Platform (Weeks 2-4)

**Goal:** Wire all data to live PostgreSQL. Build Contact module. Complete Entity Resolution.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 1** | PostgreSQL repositories for ALL commercial domains | 40h | Opportunity, Pipeline, Activity, Quote, Proposal, Contract, Forecast — replace InMemory with asyncpg |
| | Database migrations for all commercial tables | 8h | alembic revisions |
| | Contact module (full CRUD) | 24h | models, repos, schemas, service, router, tests |
| | **Total Sprint 1** | **72h** | |
| **Sprint 2** | Company enrichment pipeline automation | 24h | Wire Data Fabric to real pipeline → PostgreSQL |
| | Entity Resolution production wiring | 16h | Connect golden record pattern to live merges |
| | Government data import (Balady, Najiz, REGA, Taqeem, NCNP) | 32h | Import 10K+ records into PostgreSQL |
| | LinkedIn discovery pipeline automation | 16h | Auto-discover LinkedIn URLs for all companies |
| | **Total Sprint 2** | **88h** | |
| **Sprint 3** | Consolidated pipeline utilities (excel_utils, validation_engine already done) | 8h | Refactor pipeline scripts to use shared modules |
| | Archive 16 debug scripts in taqeem_scraper/ | 1h | Move to archive/ |
| | CRM data import (LeadOpportunity.csv → PostgreSQL) | 8h | Import 719+ CRM records |
| | Data quality dashboard (backend) | 16h | Quality scoring endpoint + aggregation |
| | **Total Sprint 3** | **33h** | |
| **Phase 1 Total** | **~193h** | | |

---

### 2.5 PHASE 2 — Integrations Engine (Weeks 5-8)

**Goal:** Read/write Gmail, Outlook, Google Calendar, Outlook Calendar. Notion sync.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 4** | Gmail API integration (read) | 24h | OAuth2, history watch, webhook, email parsing |
| | Email Intelligence Service | 16h | Sent/received count, response time, reply tracking, thread analysis |
| | Email storage schema + PostGIS for threading | 8h | alembic migration for emails table |
| | **Total Sprint 4** | **48h** | |
| **Sprint 5** | Outlook API integration (Microsoft Graph) | 24h | OAuth2, delta query, webhook, email parsing |
| | Unified Email Service (abstracts Gmail/Outlook) | 16h | Common EmailProvider, EmailMessage interface |
| | Email UI (inbox view, thread view, compose) | 24h | Frontend components |
| | **Total Sprint 5** | **64h** | |
| **Sprint 6** | Google Calendar API integration | 16h | Events list, webhook sync, meeting detection |
| | Outlook Calendar API integration | 16h | Events list, delta sync, meeting detection |
| | Calendar Intelligence Service | 16h | Meetings today/this week, duration, frequency, cancellations, upcoming |
| | Calendar UI (meeting list, timeline view) | 16h | Frontend components |
| | Notion Automation refactor (centralized client) | 8h | Use sales-os/notion_api.py across all scrapers |
| | **Total Sprint 6** | **72h** | |
| **Sprint 7** | Notification Service (in-app + email) | 24h | WebSocket push, email notifications |
| | Webhook Service for third-party events | 16h | Incoming webhooks receiver, outbound webhook dispatcher |
| | Slack integration (read + notify) | 16h | Bolt SDK, event subscriptions, slash commands |
| | **Total Sprint 7** | **56h** | |
| **Phase 2 Total** | **~240h** | | |

---

### 2.6 PHASE 3 — Employee 360 (Weeks 9-12)

**Goal:** Full employee view — profile, portfolio, activities, KPIs, AI Coach.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 8** | Employee profile page + endpoint | 16h | User detail, avatar, role, settings |
| | User-Company assignment (portfolios) | 16h | Assignment table + API + UI |
| | User-Contact assignment | 8h | Assignment table |
| | Portfolio Value + Revenue calculation | 16h | Revenue attribution to employee |
| | **Total Sprint 8** | **56h** | |
| **Sprint 9** | Activity aggregation per employee | 24h | Activities from timeline, filtered by user |
| | Task management (morning, per employee) | 16h | Task CRUD, assignment, status |
| | Document management (per employee) | 16h | File upload, storage, categorization |
| | Employee Timeline view (frontend) | 16h | Timeline UI filtered by employee |
| | **Total Sprint 9** | **72h** | |
| **Sprint 10** | Calendar Intelligence Dashboard (per employee) | 16h | Meetings today/week/month, duration, frequency, cancelled, upcoming |
| | Email Intelligence Dashboard (per employee) | 16h | Emails sent/received, replies, response time, daily activity |
| | Daily/Weekly/Monthly statistics | 16h | Aggregation jobs + endpoints |
| | Performance KPIs (calls, emails, meetings, tasks, deals) | 16h | KPI definitions, calculation engine, display |
| | **Total Sprint 10** | **64h** | |
| **Sprint 11** | Employee Forecast (per employee) | 16h | Pipeline forecast attribution |
| | Productivity scoring | 16h | Activity-based productivity calculation |
| | AI Coach (basic) | 24h | Suggestions based on activity gaps, missing follow-ups |
| | Relationship Graph (per employee) | 16h | Ego network: employee→companies→contacts→meetings→emails |
| | Employee 360 frontend page | 16h | Complete Employee 360 UI |
| | **Total Sprint 11** | **88h** | |
| **Phase 3 Total** | **~280h** | | |

---

### 2.7 PHASE 4 — Company 360 (Weeks 13-16)

**Goal:** Full company view — profile, org structure, decision makers, KPIs, health.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 12** | Company profile enhancement | 16h | Richer profile: org chart, hierarchy, parent/subsidiary |
| | Organization Structure model + graph | 24h | Department, role hierarchy, reporting lines |
| | Decision Makers identification | 16h | Role extraction from contacts, LinkedIn data |
| | **Total Sprint 12** | **56h** | |
| **Sprint 13** | Company Contacts (full module) | 24h | Contact CRUD, import, enrichment |
| | Company Employees (assignment) | 16h | Who from my team works with this account |
| | Company Meetings (aggregated) | 16h | All meetings involving this company |
| | Company Emails (aggregated) | 16h | All email threads with this company |
| | **Total Sprint 13** | **72h** | |
| **Sprint 14** | Company Contracts (live) | 24h | PostgreSQL contracts, expiry alerts |
| | Company Invoices | 24h | Invoice tracking, AR aging |
| | Company Proposals | 16h | Proposals live, send tracking |
| | Company Pipeline | 16h | Pipeline view filtered by company |
| | **Total Sprint 14** | **80h** | |
| **Sprint 15** | Company Health Score | 16h | Based on activity, communication, payment, engagement |
| | Company Risk Score | 16h | Churn risk, payment risk, inactivity risk |
| | Company Growth Score | 16h | Pipeline growth, employee growth, revenue trend |
| | Company AI Insights | 24h | Automated insights: "This company hasn't been contacted in 30 days" |
| | Company Timeline (frontend) | 16h | Complete timeline for company |
| | Company 360 frontend page | 16h | Complete Company 360 UI |
| | **Total Sprint 15** | **88h** | |
| **Phase 4 Total** | **~296h** | | |

---

### 2.8 PHASE 5 — Knowledge Graph (Weeks 17-20)

**Goal:** Build rich relationship graph across all entities.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 16** | Data population: Companies→Neo4j | 8h | Batch import companies to Neo4j |
| | Data population: Contacts→Neo4j | 8h | Batch import contacts |
| | Data population: Employees→Neo4j | 8h | Batch import user-company assignments |
| | Data population: Meetings→Neo4j | 8h | Import meetings from calendar |
| | **Total Sprint 16** | **32h** | |
| **Sprint 17** | Data population: Emails→Neo4j | 8h | Import email threads |
| | Data population: Contracts→Neo4j | 8h | Import contracts |
| | Data population: Tasks→Neo4j | 8h | Import tasks |
| | Data population: Deals→Neo4j | 8h | Import pipeline deals |
| | **Total Sprint 17** | **32h** | |
| **Sprint 18** | Graph query optimization | 16h | Cypher optimization, query benchmarking |
| | Relationship discovery endpoints | 16h | Path finding, mutual connections, influence chains |
| | Ego network APIs | 16h | Per-entity ego network |
| | Competitor inference (live) | 16h | Industry-based competitor detection |
| | **Total Sprint 18** | **64h** | |
| **Sprint 19** | Graph visualization (frontend) | 24h | D3.js/vis.js knowledge graph explorer |
| | Graph search (natural language) | 16h | "Show all companies connected to X via meetings" |
| | Graph analytics (centrality, community) | 24h | Network analysis for key influencers |
| | **Total Sprint 19** | **64h** | |
| **Phase 5 Total** | **~192h** | | |

---

### 2.9 PHASE 6 — Revenue Intelligence (Weeks 21-24)

**Goal:** Live pipeline, forecast, analytics, revenue brain.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 20** | Pipeline PostgreSQL (from InMemory) | 16h | PipelineRepository with asyncpg |
| | Pipeline visualization (Kanban + Table) | 24h | Drag-and-drop stage progression |
| | Pipeline analytics (velocity, conversion, aging) | 16h | Deal velocity, stage conversion %, aging |
| | **Total Sprint 20** | **56h** | |
| **Sprint 21** | Opportunity PostgreSQL | 16h | OpportunityRepository with asyncpg |
| | Opportunity scoring (BANT/CHAMP/MEDDIC) | 24h | Qualification scoring with AI |
| | Opportunity management UI | 16h | Create, edit, stage change, notes |
| | **Total Sprint 21** | **56h** | |
| **Sprint 22** | Forecast PostgreSQL | 16h | ForecastRepository |
| | Forecast calculation (commit/best/pipeline) | 16h | Multi-stage forecast with confidence |
| | Forecast analytics (trends, accuracy) | 16h | Historical accuracy, trend analysis |
| | **Total Sprint 22** | **48h** | |
| **Sprint 23** | Revenue Brain live wiring | 24h | Connect to real data, remove mock |
| | 19 KPI definitions + live calculation | 24h | Revenue KPIs, activity KPIs, pipeline KPIs |
| | Anomaly detection (basic) | 16h | Pipeline drop alerts, activity drop alerts |
| | Revenue dashboard | 16h | Executive revenue overview |
| | **Total Sprint 23** | **80h** | |
| **Phase 6 Total** | **~240h** | | |

---

### 2.10 PHASE 7 — AI Copilot (Weeks 25-30)

**Goal:** Real AI copilot answering natural language questions over live data.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 24** | LLM abstraction layer | 16h | OpenAI + Anthropic + Google interfaces, model switching, fallback |
| | Prompt management system | 16h | Templates, versioning, A/B testing |
| | Tool-calling framework | 24h | Function calling with CapabilityRegistry integration |
| | **Total Sprint 24** | **56h** | |
| **Sprint 25** | Agent memory (conversation history) | 16h | Message store, context window management |
| | ResearchAgent → real LLM | 16h | Company research via search + LLM |
| | MeetingAgent → real LLM | 8h | Meeting summary, action items |
| | NewsAgent → real | 8h | News API + LLM analysis |
| | **Total Sprint 25** | **48h** | |
| **Sprint 26** | Copilot natural language → structured queries | 24h | NL → SQL/Cypher/API calls via LLM |
| | "Show Company 360" query | 8h | Route to Company 360 endpoint |
| | "Show Employee 360" query | 8h | Route to Employee 360 endpoint |
| | "Who owns this company?" query | 8h | Account owner lookup |
| | "What happened last week?" query | 8h | Timeline aggregation + LLM summary |
| | **Total Sprint 26** | **56h** | |
| **Sprint 27** | "Which customers are inactive?" query | 8h | Activity analysis |
| | "Which contracts expire soon?" query | 8h | Contract expiry query |
| | "How many meetings did X have?" query | 8h | Calendar query |
| | "How many emails were sent yesterday?" query | 8h | Email query |
| | Copilot UI (chat panel wired to backend) | 16h | Replace setTimeout mock with real API call |
| | **Total Sprint 27** | **40h** | |
| **Sprint 28** | Multi-agent orchestration improvements | 24h | AgentCoordinator with real LLM routing |
| | Evaluation framework | 16h | Answer quality, hallucination detection |
| | Confidence scoring + calibration | 16h | LLM confidence, provenance tracking |
| | Safety filters + policy integration | 16h | PolicyEngine → copilot guardrails |
| | **Total Sprint 28** | **72h** | |
| **Sprint 29** | AI Agent frontend integration | 16h | Agent status, agent configuration UI |
| | Agent analytics (usage, satisfaction, quality) | 16h | Feedback loop, rating, improvement |
| | Document QA (upload a contract, ask questions) | 16h | RAG over documents |
| | **Total Sprint 29** | **48h** | |
| **Phase 7 Total** | **~320h** | | |

---

### 2.11 PHASE 8 — Executive Dashboards (Weeks 31-34)

**Goal:** Full dashboard suite for CEO, Sales Director, Manager, Employee, Company.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 30** | CEO Dashboard | 40h | Revenue, pipeline, forecast, KPIs, team performance, trends |
| | Sales Director Dashboard | 32h | Team pipeline, individual performance, forecast variance |
| | **Total Sprint 30** | **72h** | |
| **Sprint 31** | Sales Manager Dashboard | 32h | Daily activities, meetings, emails, deals, team view |
| | Employee Dashboard | 24h | Personal KPIs, tasks, meetings, emails, calls, forecast |
| | **Total Sprint 31** | **56h** | |
| **Sprint 32** | Company Dashboard | 24h | Company profile, health, pipeline, revenue, timeline |
| | Custom dashboard builder | 32h | Drag-and-drop widget selection |
| | Dashboard sharing + export | 16h | PDF export, email scheduling |
| | **Total Sprint 32** | **72h** | |
| **Sprint 33** | Charts upgrade (Recharts/D3) | 24h | Replace basic SVG charts |
| | Performance optimization (CDN, bundle analysis) | 16h | Next.js optimization, image optimization |
| | Mobile-responsive dashboards | 16h | Tablet/phone views |
| | **Total Sprint 33** | **56h** | |
| **Phase 8 Total** | **~256h** | | |

---

### 2.12 PHASE 9 — Production Hardening (Weeks 35-38)

**Goal:** Enterprise readiness — monitoring, scale, compliance.

| Sprint | Items | Effort | Details |
|--------|-------|--------|---------|
| **Sprint 34** | Prometheus + Grafana dashboards | 24h | API metrics, DB metrics, business metrics |
| | APM (Datadog/New Relic) setup | 16h | Traces, error tracking, performance monitoring |
| | Alerting (PagerDuty/email/Slack) | 16h | Critical alerts, SLA breaches |
| | **Total Sprint 34** | **56h** | |
| **Sprint 35** | Load testing (k6/Locust) | 24h | 100/1K/10K/100K user scenarios |
| | Performance optimization | 32h | Query optimization, caching, CDN, image optimization |
| | PgBouncer tuning | 8h | Connection pool optimization |
| | **Total Sprint 35** | **64h** | |
| **Sprint 36** | Backup/DR strategy | 16h | PostgreSQL backup, S3 snapshots, DR plan |
| | SOC2 readiness (evidence collection) | 24h | Audit logs, access reviews, compliance controls |
| | GDPR readiness (data deletion, export, consent) | 16h | User data management |
| | **Total Sprint 36** | **56h** | |
| **Sprint 37** | Documentation update | 16h | API docs, deployment guide, troubleshooting |
| | Frontend tests (runtime, hooks, components) | 40h | Jest + Testing Library |
| | End-to-end tests (Playwright/Cypress) | 24h | Critical user flows |
| | **Total Sprint 37** | **80h** | |
| **Sprint 38** | Final security audit | 16h | Penetration test, OWASP scan |
| | Performance benchmark final | 8h | Verify production readiness |
| | Go-live checklist | 8h | Stakeholder sign-off, migration plan |
| | **Total Sprint 38** | **32h** | |
| **Phase 9 Total** | **~288h** | | |

---

### 2.13 SPRINT PLAN SUMMARY

| Phase | Sprints | Weeks | Effort (Hours) | Focus |
|-------|---------|-------|-----------------|-------|
| **P0: Foundation** | — | 1 | 30 | Security + cleanup |
| **P1: Core Data** | S1-S3 | 3 | 193 | PostgreSQL persistence + contacts |
| **P2: Integrations** | S4-S7 | 4 | 240 | Email + Calendar + Notion + Slack |
| **P3: Employee 360** | S8-S11 | 4 | 280 | Employee profiles, activities, KPIs |
| **P4: Company 360** | S12-S15 | 4 | 296 | Company profiles, org, health, AI |
| **P5: Knowledge Graph** | S16-S19 | 4 | 192 | Neo4j population + graph queries |
| **P6: Revenue Intelligence** | S20-S23 | 4 | 240 | Pipeline, forecast, analytics |
| **P7: AI Copilot** | S24-S29 | 6 | 320 | Real LLM, tool calling, NL queries |
| **P8: Dashboards** | S30-S33 | 4 | 256 | CEO→Employee dashboards |
| **P9: Hardening** | S34-S38 | 5 | 288 | Monitoring, scale, compliance |
| **Total** | **38 sprints** | **39 weeks (~9 months)** | **~2,335h** | |

### 2.14 ESTIMATED TIMELINE

| Milestone | Date | Deliverable |
|-----------|------|-------------|
| **Foundation Complete** | Week 1 | Secure + clean repository |
| **Core Data Platform** | Week 4 | All commercial data in PostgreSQL, contacts module live |
| **Integrations Live** | Week 8 | Gmail, Outlook, Calendar connected |
| **Employee 360 MVP** | Week 12 | First employee 360 page live with real data |
| **Company 360 MVP** | Week 16 | Company 360 page with health, risk, growth scores |
| **Knowledge Graph Live** | Week 20 | Rich relationship graph across all entities |
| **Revenue Intelligence** | Week 24 | Pipeline, forecast, analytics on real data |
| **AI Copilot MVP** | Week 30 | Real LLM answer questions over live data |
| **Dashboard Suite** | Week 34 | Full CEO→Employee dashboard suite |
| **Production Ready** | **Week 39** | **Enterprise-ready GA** |

---

### 2.15 RISK ANALYSIS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Gmail/Outlook API rate limits** | High | Medium | Batch processing, exponential backoff, queue management |
| **Neo4j Community Edition scaling** | Medium | High | Start with single node, plan Enterprise for >100 users |
| **LLM costs for AI Copilot** | Medium | High | Token budgeting, caching, model tier selection |
| **Saudi government API changes** | Medium | High | Scraper tests in CI, alert on failure, maintain fallback |
| **Frontend complexity (0 tests → 100 tests)** | High | Medium | Phased test writing, prioritize runtime + hooks |
| **Data migration (Excel → PostgreSQL)** | Medium | Medium | Staged import, data quality checks, rollback plan |
| **Team capacity (single developer)** | High | Critical | Prioritize Phase 0-2, defer Phase 5-7 if needed |
| **Integration breakage (Google/MS API changes)** | Low | High | Abstraction layer (UnifiedEmailService) |
| **Scope creep** | High | Medium | Strict sprint boundaries, Constitution Article 8 |
| **User adoption** | Medium | High | Early feedback loops, Muhide-first deployment |

---

### 2.16 CRITICAL PATH

```
Week 1:  Foundation (Blocking)
  ↓
Week 2-4: Core Data (Blocking Phase 3-6)
  ↓
Week 5-8: Integrations (Blocking Phase 3-4)
  ↓
Week 9-12: Employee 360 (Blocking Phase 8)
  ↓
Week 13-16: Company 360 (Blocking Phase 5)
  ↓
Week 17-20: Knowledge Graph (Blocking Phase 6)
  ↓
Week 21-24: Revenue Intelligence (Blocking Phase 7)
  ↓
Week 25-30: AI Copilot (Blocking Phase 8)
  ↓
Week 31-34: Dashboards
  ↓
Week 35-39: Hardening → GA
```

**Fastest path to Muhide value:**
1. Phase 0 (Week 1) — Security + cleanup
2. Phase 1 (Weeks 2-4) — Core data in PostgreSQL
3. Phase 3 (Weeks 9-12) — Employee 360 + calendar/email intelligence
4. Phase 4 (Weeks 13-16) — Company 360
5. Phase 2 (Weeks 5-8) — Integrations (parallel with 3-4)

**Recommended parallel tracks:**
- **Track A** (Backend): Phase 1 → Phase 2 → Phase 6
- **Track B** (Frontend + Data): Phase 3 → Phase 4 → Phase 8
- **Track C** (AI): Phase 7

---

### 2.17 WHAT TO REUSE (DO NOT REWRITE)

| Component | Why Keep |
|-----------|----------|
| **Backend DDD modules** (Identity, Company, Entity Resolution) | Fully working with PostgreSQL |
| **All 27 runtime packages** (21 implemented) | Proven architecture, well-tested |
| **SDK (25+ modules)** | Production-quality, interface-first |
| **Event system** (CloudEvents, Kafka, PostgresEventStore) | Production-grade event infrastructure |
| **Frontend runtime (9 runtimes)** | Innovative, production-quality |
| **Frontend UI (17 components)** | Complete design system |
| **Frontend renderer (5-level schema renderer)** | Schema-driven, extensible |
| **Frontend workspace system** | Role-based workspace generation |
| **Frontend design language (18 semantic colors, 4 densities)** | Arabic-first, world-class |
| **Frontend hooks (14 hooks)** | Complete hook library |
| **Backend tests (~160)** | Architecture fitness + domain tests |
| **Government scrapers (5)** | Saudi market moat |
| **CRM pipeline scripts** | Working enrichment logic (refactor to shared modules) |
| **Backend intelligence layer** | Architecture is sound — wire to real data |
| **Neo4j schema (7 labels, 10 edges)** | Well-designed knowledge graph |
| **Infrastructure (Docker, K8s, Terraform)** | Production deployment ready |

### 2.18 WHAT TO BUILD (MINIMUM VIABLE)

| Module | Priority | Reason |
|--------|----------|--------|
| Contact module | P0 | Foundation — blocks Company 360 |
| PostgreSQL repositories (commercial) | P0 | Foundation — all data lost on restart |
| Gmail/Outlook integration | P1 | Core — Employee 360 needs email data |
| Google/Outlook Calendar integration | P1 | Core — Employee 360 needs meeting data |
| Employee 360 page | P1 | Muhide immediate value |
| Company 360 page | P1 | Muhide immediate value |
| AI Copilot (real LLM) | P2 | Differentiator |
| Dashboards | P2 | User adoption |
| Knowledge Graph population | P2 | Advanced analytics |

---

### 2.19 RECOMMENDED TEAM

| Role | Phase 0-2 | Phase 3-5 | Phase 6-9 |
|------|-----------|-----------|-----------|
| Backend (Python/FastAPI) | 1 FTE | 1 FTE | 1 FTE |
| Frontend (Next.js/React) | — | 1 FTE | 1 FTE |
| Data Engineering | 1 FTE (Phase 1) | — | — |
| AI/ML Engineer | — | — | 1 FTE (Phase 7) |
| DevOps | 0.5 FTE | 0.5 FTE | 0.5 FTE |

**Optimal team: 2-3 engineers (full-stack + data)**

---

## PART 3 — FINAL VERDICT

### Current State: **12% Production Ready**

### SalesOS Today Is:
The architecture of a **$50M company** with the code of a **pre-seed prototype**.

The DDD, the runtime composition, the event system, the design language, the SDK — these are genuinely world-class. The platform management documents (Constitution, ADRs, Quality Gates) are best-in-class.

But the **only thing that produces real business value today** is the data pipeline (scrapers + Excel enrichment), which is fragile, hardcoded, and disconnected from the platform.

### What Muhide Gets:

After **39 weeks (~9 months)** of focused execution:

1. **Employee 360** — Full employee profile, portfolio, activities, KPIs, calendar/email intelligence, AI coach, performance scoring, relationship graph
2. **Company 360** — Full company profile, org structure, decision makers, health/risk/growth scores, AI insights, timeline, contracts, pipeline
3. **Knowledge Graph** — Rich relationships across companies, employees, contacts, meetings, emails, tasks, contracts, invoices, products, projects
4. **Executive Dashboards** — CEO, Sales Director, Sales Manager, Employee, Company — all with real data
5. **AI Copilot** — Natural language over all company data: "Show Company 360", "Who owns this company?", "Which contracts expire soon?", "How many meetings did Ahmed have today?"
6. **Real Integrations** — Gmail, Outlook, Google Calendar, Outlook Calendar, Slack, ERP (future)
7. **Revenue Intelligence** — Live pipeline, forecast, analytics, anomaly detection

### What Not To Build (Reuse Existing):

| Feature | Where It Exists | Action |
|---------|----------------|--------|
| Identity/Auth | `app/modules/identity/` | Reuse (add refresh/password reset) |
| Company CRUD | `app/modules/company/` | Reuse |
| Entity Resolution | `app/modules/entity_resolution/` | Reuse |
| Event System | `sdk/events/` + runtime | Reuse |
| Timeline | `domains/timeline/` + runtime | Reuse |
| Search | `domains/search/` + runtime | Reuse (SQL injection fixed) |
| Feature Store | `runtime/feature_store/` | Reuse (wire to PostgreSQL) |
| Decision Engine | `runtime/decision_runtime/` | Reuse (wire to real data) |
| Pipeline Logic | `crm_enrichment.py` etc. | Refactor to shared modules |
| UI Components | `packages/ui/` | Reuse |
| Runtime System | `packages/runtime/` | Reuse |
| Design System | `packages/design-language/` | Reuse |

### Final Recommendation

> **Do NOT rebuild. Connect the dots.**
>
> The architecture is ready. The architecture has been waiting for data.
>
> Wire the scrapers → PostgreSQL. Wire PostgreSQL → API. Wire API → Frontend.
>
> Build Employee 360 first (Muhide sees immediate value). Build Company 360 second. Build AI Copilot third.
>
> **Ship real data or don't ship at all.**

---

*Report generated by Principal Architect — July 2, 2026*
*Confidential — Muhide Internal*
