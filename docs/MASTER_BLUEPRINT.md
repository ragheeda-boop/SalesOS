# SalesOS — MASTER BLUEPRINT V5.0

> **Enterprise Business Intelligence Operating System — المرجع المعماري الرسمي**
> Version 5.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## 1. PRODUCT VISION

### Mission Statement
Improve measurable commercial outcomes for enterprise organizations through explainable decision intelligence.

### Vision
The definitive **Business Intelligence Operating System** for the Middle East — starting with Saudi Arabia, expanding to GCC and MENA — powering every commercial decision with complete company intelligence, AI-native decision support, and automated revenue workflows.

### Core Thesis
Enterprise organizations lack a platform that:
1. **Preserves ownership** of business facts across all commercial domains
2. **Transforms facts** into explainable, actionable knowledge
3. **Measures performance** systematically across revenue, operations, and intelligence
4. **Delivers recommendations** that are traceable, contextual, and optional

### Positioning
SalesOS is **not** a CRM. CRM is a feature, not the product.

SalesOS is a **Business Intelligence Operating System** where Revenue is the first capability, not the only one. The platform is designed to serve any commercial intelligence domain — Revenue, Marketing, Customer Success, Partner Operations, Talent Intelligence, and beyond.

### Revenue Architecture
- **Not a CRM.** CRM is one capability among many.
- **BIOS = Data + Intelligence + Automation + Developer + Marketplace**
- Monetization: SaaS tiers (Free → Enterprise) + Marketplace (20% rev share) + Data Enrichment + Knowledge Packs
- TAM: 100M+ companies, 2,000+ enterprise customers, $50M+ ARR target by Year 3

---

## 2. PLATFORM PHILOSOPHY

### 2.1 The Principle: Everything is a Platform

SalesOS is not a monolithic application. It is a **platform of platforms**, each designed as an independent product with its own lifecycle, API surface, and commercial model.

```
Commercial Platform
        ↓
Intelligence Platform
        ↓
Automation Platform
        ↓
Enterprise Platform
        ↓
Developer Platform
        ↓
Intelligence Fabric
```

Each platform consumes capabilities from the layer below and exposes capabilities to the layer above.

### 2.2 Four-Layer Architecture

| Layer | Name | Description | Example |
|-------|------|-------------|---------|
| Layer 4 | **Applications** | End-user experiences, UIs, dashboards | Company 360, Deal Room, AI Copilot |
| Layer 3 | **Business Capabilities** | Domain-specific products | Company Intelligence, Pipeline, GTM |
| Layer 2 | **Platform Services** | Horizontal infrastructure capabilities | Data Fabric, Intelligence Fabric, Workflow |
| Layer 1 | **Kernel** | Frozen, foundational, immutable | Identity, Events, Search, Timeline |

---

## 3. LAYER 1 — KERNEL (Frozen)

### 3.1 Kernel Modules

```
salesos/
├── identity/              # Tenant + User + Auth + API Keys
├── company/               # Organization + Contact + License + Branch + CR
├── search/                # QueryParser → Planner → Execution → Ranking
├── timeline/              # Append-only event history (universal)
├── sdk/                   # Platform SDK (events, audit, telemetry, cache)
├── events/                # CloudEvents 1.0 framework
├── metadata/              # Entity/Field metadata registry
└── capability_registry/   # Capability declaration system
```

**Status:** ✅ Frozen. No direct code additions without ADR + Benchmark + Architecture Review.

### 3.2 Kernel Characteristics
- **Replaceability**: Every kernel capability replaceable without changing contracts
- **SDK Sovereignty**: No module bypasses SDK for cross-cutting concerns
- **Domain Events**: Every change generates CloudEvents 1.0
- **Frozen Interface Protection**: Breaking requires formal ADR

---

## 4. LAYER 2 — PLATFORM SERVICES

### 4.1 Data Fabric

The Data Fabric is the foundational intelligence layer. It owns all data movement, transformation, and storage across the platform.

```
Sources
   │
   ▼
Collectors (Scrapers, APIs, Webhooks, Uploads)
   │
   ▼
Normalizers (Schema mapping, field standardization, Arabic/English)
   │
   ▼
Entity Resolution (Universal Entity ID, golden record merge)
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│                 KNOWLEDGE GRAPH (Neo4j)                    │
│  Company ──Contact ──Deal ──Activity ──Revenue ──Forecast │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                  FEATURE STORE                            │
│  Growth Rate │ Funding Score │ Hiring Velocity            │
│  ICP Score   │ Intent Score  │ Revenue Score              │
│  → Computed once, consumed everywhere                    │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL (OLTP) │ Data Lake (Iceberg) │ Cache (Redis) │
└─────────────────────────────────────────────────────────┘
```

**Components:**
| Component | Status | Priority |
|-----------|--------|----------|
| Collectors (Scrapers) | ✅ 6 sources | P0 |
| Normalizers | ❌ Missing | P0 |
| Entity Resolution | ❌ Missing | P0 |
| Knowledge Graph | 🟡 Neo4j configured, zero data | P1 |
| Feature Store | ❌ Missing | P1 |
| Data Lake (Iceberg) | ❌ Missing | P2 |
| Semantic Cache | ❌ Missing | P2 |

### 4.2 Intelligence Fabric

The Intelligence Fabric is the AI/ML runtime layer. It owns all intelligence — from scoring to reasoning to autonomous execution.

```
┌─────────────────────────────────────────────────────────────┐
│                     INTELLIGENCE FABRIC                       │
├─────────────────────────────────────────────────────────────┤
│  REVENUE BRAIN                                                │
│  Central intelligence: Signals → Timeline → CRM → Meetings   │
│  → Emails → AI → Knowledge → Forecast → Recommendations      │
│  Output: Next Best Action for every user                      │
├─────────────────────────────────────────────────────────────┤
│  AGENT RUNTIME                                                │
│  Planner → Memory → Executor → Tools → Policies              │
│  Retries → Budgets → Observability                            │
├─────────────────────────────────────────────────────────────┤
│  PROMPT STUDIO                                                │
│  Prompt Packs → Versioning → Testing → Evaluation → Rollback │
│  → A/B Testing                                                │
├─────────────────────────────────────────────────────────────┤
│  AI GOVERNANCE PORTAL                                         │
│  Model Costs → Latency → Accuracy → Hallucination → Eval     │
│  → Prompt Versions → Memory Usage → Budgets                   │
├─────────────────────────────────────────────────────────────┤
│  AI PLAYGROUND                                                │
│  Experiment: Prompt × Model × Temperature × Memory × Context │
│  → Approve → Deploy                                           │
├─────────────────────────────────────────────────────────────┤
│  EXPERIMENT ENGINE                                            │
│  A/B tests: Sequence A → Sequence B → Measure → Auto-select  │
├─────────────────────────────────────────────────────────────┤
│  SIMULATION ENGINE                                            │
│  "If we send 5000 emails: predicted replies, meetings, rev"  │
└─────────────────────────────────────────────────────────────┘
```

| Component | Status | Priority |
|-----------|--------|----------|
| Revenue Brain | ❌ Missing | P0 |
| Agent Runtime | ❌ Missing | P1 |
| Prompt Studio | ❌ Missing | P1 |
| AI Governance Portal | ❌ Missing | P2 |
| AI Playground | ❌ Missing | P2 |
| Experiment Engine | ❌ Missing | P2 |
| Simulation Engine | ❌ Missing | P2 |

### 4.3 AI Layer Stack

```
┌─────────────────────────────────────────────────────────────┐
│              REVENUE BRAIN (P0)                               │
│  Next Best Action per user per context                        │
├─────────────────────────────────────────────────────────────┤
│              AGENT RUNTIME (P1)                               │
│  Planner → Researcher → Retriever → Analyst → Manager        │
├─────────────────────────────────────────────────────────────┤
│              AI MEMORY (P1)                                   │
│  Company memory with importance decay, semantic recall        │
├─────────────────────────────────────────────────────────────┤
│              AI COPILOT (P1)                                  │
│  Natural language → Query → Summarize → Recommend            │
├─────────────────────────────────────────────────────────────┤
│              COMPANY DNA (P1)                                 │
│  Multi-dimensional profile: Size, Digital, Culture, Buying   │
├─────────────────────────────────────────────────────────────┤
│              SCORING ENGINE (P1)                              │
│  Fit score, Risk score, Engagement score, ICP score          │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 AI Providers

| Provider | Model | Purpose | Status |
|----------|-------|---------|--------|
| OpenAI | GPT-4o | Complex reasoning, Agent OS | ✅ Configured |
| OpenAI | GPT-4o-mini | Simple queries, Entity resolution | ✅ Configured |
| OpenAI | text-embedding-3-small | Embeddings | ✅ Configured |
| OpenAI | text-embedding-3-large | Company DNA embeddings | 🟡 Planned |
| Anthropic | Claude 3.5 Sonnet | Enterprise fallback | 🟡 Planned |

### 4.5 RAG Architecture

```
[User Query] → [Semantic Cache (pre-filter)] → [SearchPlanner]
                                                   ↓
                     [Retrieve: PgVector + Neo4j + Feature Store]
                                                   ↓
                                              [Fuse: RRF]
                                                   ↓
                                         [Rerank: Cross-encoder]
                                                   ↓
                                      [LLM: Generate + Cite + Score]
```

Semantic Cache saves 40-70% LLM cost on repeated queries.

### 4.6 Other Platform Services

| Service | Description | Status |
|---------|-------------|--------|
| Workflow Engine | Trigger → Condition → Action | ❌ Missing |
| Business Rules Studio | Visual rules builder (no-code) | ❌ Missing |
| Events Bus | CloudEvents 1.0 (in-memory → Kafka) | 🟡 In-memory only |
| Timeline Service | Universal append-only timeline for any entity | ✅ Kernel |
| Search Service | Keyword + Semantic + Graph fused via RRF | ✅ Kernel |
| Cache Service | Redis (configured, unused) | 🟡 Unused |
| Notification Engine | Email, Slack, Webhook, In-app | ❌ Missing |
| Feature Store | Computed features, single source of truth | ❌ Missing |
| Semantic Cache | Embedding-based query cache | ❌ Missing |

---

## 5. LAYER 3 — BUSINESS CAPABILITIES

### 5.1 Capability Registry (replaces Module Registry)

A **Capability** is a self-contained business product with a full surface area:

```
Capability {
  API          — REST + GraphQL + Events
  UI           — Pages, components, dashboard widgets
  Database     — Schema, migrations, projections
  Workflow     — Triggers, actions, automations
  Permissions  — RBAC roles, policies, scopes
  AI           — Prompts, models, scoring, memory
  Reports      — KPIs, charts, exports, dashboards
  Events       — CloudEvents emitted and consumed
  Metrics      — Usage, performance, business impact
}
```

### 5.2 Capabilities by Domain

| Capability | Domain | Layer | Status |
|------------|--------|-------|--------|
| **Company Intelligence** | Commercial | CORE | 🟡 Partial |
| Opportunity Management | Commercial | CORE | ✅ Complete |
| Quote Management | Commercial | CORE | ✅ Complete |
| Proposal Generation | Commercial | CORE | 🟡 Partial |
| Contract Management | Commercial | CORE | 🟡 Partial |
| Pipeline Intelligence | Revenue | CORE | ✅ Complete |
| Forecast | Revenue | CORE | ✅ Complete |
| Analytics & KPIs | Revenue | CORE | ✅ Complete |
| Recommendation | Decision | CORE | ✅ Complete |
| GTM Intelligence | GTM | CORE | ❌ Missing |
| Marketing Intelligence | Marketing | EXTEND | ❌ Missing |
| Customer Success | Success | EXTEND | ❌ Missing |
| Partner Intelligence | Partner | EXTEND | ❌ Missing |
| Talent Intelligence | Talent | EXTEND | ❌ Missing |
| Activity Intelligence | Activity | CORE | ❌ Missing |
| Deal Room | Revenue | APP | ❌ Missing |
| Company 360 | Commercial | APP | ❌ Missing |

### 5.3 Capability Maturity Model

```
Level 0: ❌ Missing — Not started
Level 1: 🟡 Partial — Backend SDK + domain tests (in-memory)
Level 2: ✅ Backend — PostgreSQL repos + full test suite + API
Level 3: 🟢 Complete — UI + AI + Workflow + Permissions + Reports
Level 4: 🌟 Market-Ready — Docs + Demo + Pricing + Marketplace
```

---

## 6. LAYER 4 — APPLICATIONS

### 6.1 Application Portfolio

| Application | Description | Status |
|-------------|-------------|--------|
| **Company 360** | Unified company profile (all data + AI) | ❌ Missing |
| **Deal Room** | Pipeline workspace with AI coaching | ❌ Missing |
| **AI Copilot** | Natural language company intelligence | ❌ Missing |
| **Revenue Dashboard** | KPIs, forecasts, trends | ❌ Missing |
| **ICP Builder** | Visual ideal customer profile designer | ❌ Missing |
| **GTM Builder** | Territory, sequence, playbook designer | ❌ Missing |
| **Email Studio** | Multi-channel sequence builder | ❌ Missing |
| **Business Rules Studio** | No-code rules and scoring designer | ❌ Missing |
| **Prompt Studio** | Prompt management and testing UI | ❌ Missing |
| **AI Governance** | Cost, accuracy, model management UI | ❌ Missing |
| **Signal Marketplace** | Browse, purchase, install Signal Packs | ❌ Missing |
| **Knowledge Pack Manager** | Install and manage Industry Knowledge Packs | ❌ Missing |
| **Customer Health Console** | Health scores for companies, deals, pipelines | ❌ Missing |
| **Tenant Admin Console** | Workspace management, billing, audit logs | ❌ Missing |

### 6.2 Frontend Architecture (Planned)

```
Stack: Next.js 15 + React 19 + TypeScript 5
UI: shadcn/ui + Radix + Tailwind 4
State: Zustand + TanStack Query
Forms: React Hook Form + Zod
Data: TanStack Table + Recharts + D3
```

---

## 7. OPERATING SYSTEM API

SalesOS exposes **four** API surfaces, each serving a different consumer:

```
┌─────────────────────────────────────────────────────────────┐
│                    OPERATING SYSTEM API                        │
├─────────────────────────────────────────────────────────────┤
│  REST API     — Standard CRUD + search + batch               │
│                Consumers: Frontend, Integrations, Scripts    │
├─────────────────────────────────────────────────────────────┤
│  GraphQL      — Flexible query + mutation + subscription     │
│                Consumers: Internal apps, Custom dashboards   │
├─────────────────────────────────────────────────────────────┤
│  MCP Server   — Model Context Protocol (Anthropic standard)  │
│                Consumers: AI agents, Cursor, Copilot, IDEs   │
│                Enables SalesOS as tool/knowledge source      │
│                for any AI agent ecosystem                     │
├─────────────────────────────────────────────────────────────┤
│  Agent SDK    — Python SDK for agent developers              │
│                Consumers: Custom agents, workflow builders   │
│                Includes: Auth, Context, Tools, Memory, Events│
└─────────────────────────────────────────────────────────────┘
```

**MCP Server** makes SalesOS a knowledge + tools source for any AI agent (not just our UI). This is a key differentiator from traditional CRMs.

---

## 8. KNOWLEDGE PACKS (Industry-Specific)

Instead of flat "Industry Packs," every Knowledge Pack is a portable bundle:

```
Healthcare Pack {
  Ontology     — Industry-specific entities and relationships
  Signals      — Healthcare-specific buying signals
  Scoring      — ICP scoring calibrated for healthcare
  Prompts      — Domain-optimized LLM prompts
  Workflows    — Healthcare sales workflows and sequences
  Dashboards   — Pre-built KPI dashboards
  Reports      — Industry-specific report templates
  AI Memory    — Domain-specific memory schemas
  Competitors  — Pre-loaded competitor intelligence
}
```

| Pack | Status | Priority |
|------|--------|----------|
| Healthcare | ❌ Missing | P2 |
| Construction | ❌ Missing | P2 |
| Financial Services | ❌ Missing | P2 |
| Technology | ❌ Missing | P2 |
| Education | ❌ Missing | P3 |
| Retail | ❌ Missing | P3 |

---

## 9. REVENUE GRAPH

The Revenue Graph is the most important graph in the system. It is not just a Knowledge Graph — it is a **typed, weighted, temporal graph** connecting every revenue-relevant entity.

```
Company ──has──→ Contact
Company ──has──→ Deal
Deal    ──has──→ Activity
Company ──has──→ Campaign
Contact ──has──→ Interaction
Deal    ──has──→ Revenue
Revenue ──has──→ Forecast

Graph Properties:
- Typed edges (owns, targets, generates, converts)
- Weighted edges (relevance, probability, influence)
- Temporal edges (time-bounded relationships)
- Bidirectional traversal (up/down hierarchy)
```

---

## 10. SIGNAL MARKETPLACE

Signals are not hard-coded. Each Industry Pack (and third-party developers) can contribute new Signals.

```
Signal {
  id: str
  name: str
  description: str
  source: str (Balady | Taqeem | NCNP | LinkedIn | ...)
  condition: Expression (Growth > 20% AND Hiring > 10)
  weight: float (0.0 - 1.0)
  confidence: float
  industry_tags: [str]
  pack_id: str (optional)
  is_public: bool
}
```

| Feature | Status |
|---------|--------|
| Signal Registry | ❌ Missing |
| Signal Evaluation Engine | ❌ Missing |
| Signal Marketplace UI | ❌ Missing |
| Third-party Signal SDK | ❌ Missing |

---

## 11. UNIVERSAL TIMELINE

Not just Company Timeline. Every entity has a timeline.

```
Entity Timeline {
  id: UUID
  entity_type: str (company | deal | contact | meeting | campaign | task | workflow | ai)
  entity_id: UUID
  events: [TimelineEvent]
  ╰─ timestamp, event_type, actor, payload, source, confidence
}
```

The Kernel Timeline service already supports this. The UI and queries are missing.

---

## 12. TECHNICAL ARCHITECTURE

### 12.1 Stack

| Layer | Technology | Status |
|-------|-----------|--------|
| Backend Framework | FastAPI (Python 3.12) | ✅ |
| ORM | SQLAlchemy 2.0 (async) | ✅ |
| Database | PostgreSQL 16 + pgvector | ✅ |
| Graph DB | Neo4j 5.x | ✅ Configured |
| Events | Kafka (in-process EventBus for now) | 🟡 In-memory |
| Cache | Redis 7 | 🟡 Configured, unused |
| Search | PostgreSQL trigram + pgvector HNSW | ✅ |
| Frontend | Next.js 15 + React 19 | ❌ No source |
| UI Library | shadcn/ui + Radix + Tailwind 4 | ❌ No source |
| State | Zustand | ❌ No source |
| SDK | Custom SalesOS SDK | ✅ Complete |
| Auth | JWT (RS256) + bcrypt + RBAC | ✅ |
| Data Lake | Apache Iceberg + MinIO/S3 + DuckDB/Spark | ❌ Missing |
| CI/CD | GitHub Actions | ❌ Missing |

### 12.2 Architecture Pattern

**Layer 1: Platform Monolith** (Current)
- Single deployment, capability-isolated via directory + import rules
- All repositories in-memory

**Layer 2: Modular Monolith** (Phase II Target)
- PostgreSQL persistence for all domains
- Module-isolated with strict import boundaries
- Internal EventBus for domain events

**Layer 3: Event-Driven Services** (Phase IV Target)
- Domain services extracted per business capability
- Kafka event backbone
- Each service independently deployable

### 12.3 Event-Driven Architecture

```
[Command] → [Handler] → [Domain Event] → [EventBus] → [Projections]
                                                ↓
                          [Timeline] [Neo4j] [Feature Store] [Search]
```

### 12.4 Deployment Architecture

```
[User] → CloudFront/CDN → [Next.js] → [FastAPI] → [PostgreSQL + pgvector]
                                          ↓
                    [Neo4j] [Redis] [Kafka] [MinIO/S3] [Feature Store]
```

| Environment | Purpose | Status |
|-------------|---------|--------|
| Dev | Local `docker compose up` | ✅ |
| Staging | CI/CD auto-deploy | ❌ Missing |
| Production | Blue/Green with canary | ❌ Missing |
| DR | Cross-region failover | ❌ Missing |

---

## 13. RUNTIME ARCHITECTURE

### 13.1 Runtime Flow (Request Lifecycle)

Every user request traverses a deterministic path through the platform:

```
[User / Agent / API Consumer]
            │
            ▼
┌──────────────────────┐
│    API GATEWAY        │  ← Rate limit, AuthN, TLS termination, routing
│  (CloudFront → Nginx) │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    IDENTITY           │  ← Tenant resolution, AuthZ, RBAC, API key validation
│  (Tenant Context)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    CAPABILITY ROUTER  │  ← Route to capability: Company 360, Pipeline, Search, AI, etc.
│  (Capability Registry)│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    WORKFLOW ENGINE    │  ← Trigger? Condition? Action? Simulation?
│  (If configured)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    AI RUNTIME         │  ← Semantic Cache → RAG → LLM → Eval
│  (Prompt Studio)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    DATA FABRIC        │  ← Feature Store, Revenue Graph, Entity Resolution
│  (Read/Write)         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    REVENUE BRAIN      │  ← Next Best Action computation
│  (Decision Engine)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    RECOMMENDATION     │  ← Evidence chain, confidence, alternatives
│  (Decision Context)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    EVENTS             │  ← Every mutation → CloudEvent → Timeline → Projections
│  (EventBus + Kafka)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    ANALYTICS          │  ← KPIs, Metrics, Business impact
│  (Async, eventual)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    STORAGE            │  ← PostgreSQL, Neo4j, Redis, Data Lake
│  (Persistence Layer)  │
└──────────────────────┘
```

### 13.2 Execution Model — Search

```
[User types query]
       │
       ▼
[Search API Gateway] → [Parse: Arabic/English] → [SearchPlanner]
       │                                                   │
       ├── [Keyword: PostgreSQL trigram] ◄────────────────┤
       ├── [Semantic: pgvector HNSW] ◄───────────────────┤
       ├── [Graph: Neo4j traversal] ◄────────────────────┤
       │                                                   │
       ▼                                                   ▼
[RRF Fusion] → [Rerank: Cross-encoder] → [Format: SearchResult]
       │
       ▼
[Timeline: log search event] → [Metrics: increment search_count]
       │
       ▼
[Return to User]
```

### 13.3 Execution Model — AI Query

```
[User asks: "What companies in Riyadh are hiring?"]
       │
       ▼
[Semantic Cache: check cache] — [HIT → Return cached]
       │ MISS
       ▼
[SearchPlanner: plan retrieval]
       │
       ├── [Feature Store: hiring_score > 0.7, city=Riyadh]
       ├── [Knowledge Graph: companies in Riyadh]
       ├── [Timeline: recent hiring events]
       │
       ▼
[RRF Fusion] → [Build Context]
       │
       ▼
[LLM: GPT-4o-mini with context + prompt]
       │
       ▼
[Eval: confidence, hallucination check]
       │
       ▼
[Semantic Cache: store result]
       │
       ▼
[Audit: log query + response]
       │
       ▼
[Return to User]
```

### 13.4 Execution Model — Workflow

```
[Trigger: CompanyCreated / SignalDetected / Schedule]
       │
       ▼
[Workflow Engine: resolve conditions]
       │
       ▼
[Simulation Engine: "If we execute this, what happens?"]
       ├── Predict: replies, meetings, revenue
       ├── Risk: compliance, rate limits, negative response
       └── Recommendation: proceed / modify / abort
       │
       ▼
[Execute Action: Email / Webhook / Update Record / AI Agent]
       │
       ▼
[Event: WorkflowExecuted → Timeline → Metrics]
```

### 13.5 Error Handling & Resilience

| Pattern | Implementation | Status |
|---------|---------------|--------|
| Circuit Breaker | SDK provides `@circuit_breaker` decorator | 🟡 Not used |
| Retry with Backoff | SDK provides retry utilities | 🟡 Not used |
| Dead Letter Queue | Kafka DLQ (planned) | ❌ Missing |
| Fallback | Cache fallback for each data source | ❌ Missing |
| Graceful Degradation | Capability-level feature flags | ❌ Missing |
| Rate Limiting | Per-tenant rate limiter (Redis) | ❌ Missing |
| Bulkhead Isolation | Per-capability thread pool/semaphore | ❌ Missing |
| Timeout Propagation | Configurable timeouts per capability | ❌ Missing |

### 13.6 Observability Model

```
[Every Request] → [Trace ID: propagated across all services]
       │
       ├── [Log: structured JSON via structlog]
       ├── [Metric: latency, count, error rate, business KPI]
       ├── [Trace: Jaeger/OpenTelemetry spans]
       └── [Audit: immutable record for compliance]
```

| Observatory | Implementation | Status |
|-------------|---------------|--------|
| Distributed Tracing | OpenTelemetry SDK configured | 🟡 Not instrumented |
| Structured Logging | structlog configured | ✅ |
| Business KPIs | Emitted as metrics after each request | ❌ Missing |
| AI Cost Tracking | Per-request token count → cost | ❌ Missing |
| SLA Dashboard | Uptime, latency p95/p99, error rate | ❌ Missing |
| Tenant-level Metrics | Per-tenant usage, limits, billing | ❌ Missing |

### 13.7 Digital Twin Runtime

```
[Every Workspace has a Digital Twin]
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                    DIGITAL TWIN                            │
├──────────────────────────────────────────────────────────┤
│  Current State   — Real-time mirror of workspace data     │
│  Predicted State — Forecast at N-days/weeks/months       │
│  Risks           — Deals at risk, churn risk, compliance  │
│  Scenarios       — "What if we change this?" simulation   │
│  Recommendations — Next Best Action from Revenue Brain    │
│  Forecasts       — Pipeline, revenue, growth trajectories │
│  Outcomes        — Actual vs predicted (model feedback)   │
└──────────────────────────────────────────────────────────┘
```

The Digital Twin is **not** a separate system. It is the read-side projection of all platform data, continuously computed by the Revenue Brain and rendered through the Universal Timeline + Feature Store + Knowledge Graph.

### 13.8 Runtime Data Flow (Event-Driven)

```
[User Action] → [Domain Service] → [Domain Event] → [EventBus]
                                                          │
                                          ┌───────────────┼────────────────┐
                                          ▼               ▼                ▼
                                   [Timeline]     [Feature Store]   [Knowledge Graph]
                                   Append event   Recompute features Update relations
                                          │               │                │
                                          ▼               ▼                ▼
                                   [Analytics]    [Digital Twin]     [Search Index]
                                   Update KPIs    Refresh state      Rebuild index
                                                          │
                                                          ▼
                                                   [Revenue Brain]
                                                   Recompute Next Best Action
```

---

## 14. DIGITAL TWIN ENGINE

### 14.1 Concept

Every SalesOS workspace has a **Digital Twin** — a real-time computational mirror that knows not just what happened, but **what will happen**.

The Digital Twin transforms SalesOS from an operational system into a **Decision Intelligence system**.

### 14.2 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      DIGITAL TWIN ENGINE                       │
├──────────────────────────────────────────────────────────────┤
│  STATE MANAGER                                                 │
│  Maintains current workspace state from event stream           │
│  Every mutation → state update → version bump                  │
├──────────────────────────────────────────────────────────────┤
│  PREDICTOR                                                     │
│  ML models trained on historical data + feature store          │
│  Outputs: forecast, growth trajectory, churn probability       │
├──────────────────────────────────────────────────────────────┤
│  RISK DETECTOR                                                 │
│  Rule-based + AI: deal risk, churn risk, compliance risk       │
│  Each risk has: probability, impact, mitigation                │
├──────────────────────────────────────────────────────────────┤
│  SCENARIO SIMULATOR                                            │
│  "What if we close Deal X?" → recalculate pipeline, forecast   │
│  "What if we send 5000 emails?" → simulate outcomes           │
├──────────────────────────────────────────────────────────────┤
│  RECOMMENDATION ENGINE                                         │
│  Revenue Brain output: Next Best Action                        │
│  Each recommendation: action, expected impact, confidence      │
├──────────────────────────────────────────────────────────────┤
│  FEEDBACK LOOP                                                 │
│  Actual outcome vs predicted outcome → model retraining        │
│  Continuous improvement loop                                   │
└──────────────────────────────────────────────────────────────┘
```

### 14.3 Digital Twin Schema

```
DigitalTwin {
  workspace_id: UUID
  snapshot_id: UUID (incremented on each mutation)
  state: {
    companies: { total, active, by_industry, by_region }
    pipeline: { total_value, weighted_value, stages, velocity }
    forecast: { current, projected, confidence_interval }
    health: { overall, companies, deals, activities }
  }
  predictions: {
    next_30_days: { new_deals, closed_won, revenue }
    next_90_days: { growth_rate, churn_risk, hiring_trend }
    next_12_months: { annual_recurring_revenue, expansion }
  }
  risks: [
    { type: deal_churn, entity_id, probability, impact, mitigation }
    { type: pipeline_stagnation, stage, days_stalled, action }
  ]
  scenarios: {
    "close_deal_X": { revenue_delta, pipeline_impact, forecast_change }
    "increase_email_volume_2x": { reply_rate, meetings, cost }
  }
  recommendations: [
    {
      action: "reach_out_to_company_X",
      expected_value: 50000,
      confidence: 0.85,
      context: "Hiring surge + funding + ICP match"
    }
  ]
}
```

### 14.4 State: V5 NEW

| Component | Status | Priority |
|-----------|--------|----------|
| State Manager | ❌ Missing | P0 |
| Predictor (ML) | ❌ Missing | P1 |
| Risk Detector | ❌ Missing | P1 |
| Scenario Simulator | ❌ Missing | P2 |
| Recommendation Engine | 🟡 Existing (needs expansion) | P1 |
| Feedback Loop | ❌ Missing | P2 |

---

## 15. FIVE-YEAR ROADMAP (2026–2030)

### 2026: Revenue OS 🟢 ACTIVE

| Quarter | Theme | Key Deliverables |
|---------|-------|-----------------|
| Q3 2026 | Platform Foundation | PostgreSQL persistence, Frontend MVP, Company 360, CI/CD |
| Q4 2026 | Data Fabric | Entity resolution, Feature Store, Knowledge Graph, Data Lake v1 |

**Exit Criteria:** Platform can persist, search, and display company intelligence for 10 enterprise customers.

### 2027: AI OS ⏳ Planned

| Quarter | Theme | Key Deliverables |
|---------|-------|-----------------|
| Q1 2027 | Intelligence Fabric | Revenue Brain, AI Copilot, Scoring Engine, Semantic Cache |
| Q2 2027 | Agent Runtime | AI Agents, Prompt Studio, AI Governance Portal |
| Q3 2027 | Business Rules | Business Rules Studio, Workflow Engine, Simulation Engine |
| Q4 2027 | Digital Twin | Digital Twin Engine v1, Scenario Simulator, Risk Detector |

**Exit Criteria:** 50+ enterprise customers, AI features driving 30%+ of user actions.

### 2028: Business OS ⏳ Planned

| Quarter | Theme | Key Deliverables |
|---------|-------|-----------------|
| Q1 2028 | GTM Intelligence | GTM Builder, Territory Management, Playbook Engine |
| Q2 2028 | Marketing Intelligence | Campaign Management, Attribution, Multi-channel |
| Q3 2028 | Customer Success | Health Engine, Expansion Intelligence, Churn Prevention |
| Q4 2028 | Partner Intelligence | Partner Portal, Co-selling, Revenue Sharing |

**Exit Criteria:** Full commercial suite covering GTM → Marketing → Sales → Customer Success.

### 2029: Marketplace ⏳ Planned

| Quarter | Theme | Key Deliverables |
|---------|-------|-----------------|
| Q1 2029 | Developer Platform | MCP Server GA, Agent SDK GA, Plugin Framework |
| Q2 2029 | Signal Marketplace | Third-party Signals, Industry Packs, Developer Portal |
| Q3 2029 | Knowledge Packs | Healthcare Pack, Construction Pack, Financial Services Pack |
| Q4 2029 | Ecosystem | 50+ plugins, 100+ signals, 10+ Knowledge Packs |

**Exit Criteria:** 30% of revenue from Marketplace. Developer ecosystem self-sustaining.

### 2030: Enterprise Platform ⏳ Planned

| Quarter | Theme | Key Deliverables |
|---------|-------|-----------------|
| Q1 2030 | Global Scale | Multi-region deployment (EU, KSA, UAE, US) |
| Q2 2030 | Enterprise SSO | SAML/OIDC, SCIM, Compliance Suite |
| Q3 2030 | AI Trust | SOC 2 Type II, AI Audit, Explainability Dashboard |
| Q4 2030 | Platform Maturity | 99.99% SLA, 1000+ customers, $50M+ ARR |

**Exit Criteria:** Platform operating across 4 regions, 1000+ enterprise customers, $50M ARR.

---

## 16. GOVERNANCE

### 14.1 Constitution (10 Immutable Articles)

1. **Replaceability** — Every capability replaceable without changing contracts
2. **SDK Sovereignty** — No module bypasses SDK for cross-cutting concerns
3. **Domain Events** — Every domain change generates CloudEvents 1.0
4. **Testability Without UI** — Every service testable via Repository interface
5. **Measurement Before Optimization** — Benchmark before adding technology
6. **Evidence Over Trends** — Tech decisions by numbers, not hype
7. **Frozen Interface Protection** — Breaking frozen interfaces requires ADR
8. **Business Over Technology** — Domain drives stack, not reverse
9. **Microservice Isolation Readiness** — Every module extractable to service
10. **Data Sovereignty (AI)** — Data is system of record, AI is consumer

### 14.2 Platform Principles (V4 Additions)

11. **Platform-First Design** — Every feature built as a platform capability before becoming an application
12. **Capability Surface Completeness** — Every capability has API + UI + DB + Workflow + Permissions + AI + Events
13. **API Plurality** — All capabilities exposed via REST + GraphQL + MCP + Agent SDK
14. **Knowledge Portability** — All domain knowledge packaged in portable, installable Knowledge Packs
15. **Revenue Graph Primacy** — The Revenue Graph is the authoritative relationship store for all commercial entities
16. **Feature Store Singularity** — Every computed feature computed once, consumed everywhere
17. **Semantic Cache First** — Every LLM query passes through semantic cache before model invocation
18. **Timeline Universality** — Every entity has an append-only timeline
19. **Simulation Before Execution** — Every workflow simulated before production execution
20. **Next Best Action** — Every user interaction guided by the Revenue Brain

### 14.3 Runtime Principles (V5 Additions)

21. **Deterministic Request Path** — Every request follows the documented Runtime Flow. No capability bypasses the runtime layer.
22. **Digital Twin Every Workspace** — Every workspace has a Digital Twin. No workspace operates blind to its future state.
23. **Observability by Default** — Every request produces a trace, a log, and a metric. No silent execution.
24. **Resilience Patterns Mandatory** — Every capability implements Circuit Breaker, Retry, Timeout, and Fallback.
25. **Decision Intelligence over Reporting** — Every dashboard displays not just what happened, but what to do about it.
26. **Feedback Loop Completeness** — Every prediction has an actual outcome recorded. Every model has a feedback loop.
27. **Capability over Module** — The term "Module" is deprecated. All platform components are Capabilities with full surface area.

### 14.4 Terminology: Capability replaces Module

Effective V5, the term **"Module"** is deprecated across all documentation, code, and conversation. All platform components are now referred to as **Capabilities**.

A Capability has a defined surface area:
- Domain (bounded context)
- API (REST + GraphQL + Events)
- UI (pages, components, widgets)
- AI (prompts, models, scoring, memory)
- Workflow (triggers, actions, automations)
- Events (CloudEvents produced and consumed)
- Analytics (KPIs, metrics, business impact)
- Permissions (RBAC roles, policies, scopes)
- Documentation (ADRs, README, API docs)
- Tests (unit, integration, performance)
- Monitoring (traces, logs, metrics, alerts)

### 14.5 Document Hierarchy (V5 Updated)

1. `docs/PROJECT_MANIFEST.md` — How we build (supreme governing document)
2. `docs/MASTER_BLUEPRINT.md` — What we build (authoritative reference)
3. `docs/RUNTIME_ARCHITECTURE.md` — How it runs at runtime (execution model)
4. `docs/PROJECT_STATUS.md` — Where we are (completion tracker)
5. `docs/CAPABILITY_CATALOG.md` — Complete registry of every capability
6. `docs/EVENT_CATALOG.md` — Every event, producer, consumer
7. `docs/AI_CATALOG.md` — Every AI asset (agent, prompt, model, tool)
8. `docs/DOMAIN_MAP.md` — Bounded contexts and their relationships
9. `docs/DATA_CONTRACTS.md` — Data contracts for all integrations
10. `docs/QUALITY_GATE.md` — Pre-merge acceptance criteria
11. `docs/DECISION_LOG.md` — Architecture decision history
12. `docs/ROADMAP_5_YEARS.md` — 2026–2030 strategic plan
13. `docs/PRODUCT_BACKLOG.md` — Epic → Capability → Feature → Story → Task linkage
14. Platform Constitution (`platform/CONSTITUTION.md`)

### 14.6 Decision Framework (EPC)

1. Did customer outcomes improve?
2. Is the feature actually used?
3. Did it generate economic value?
4. Is the platform stable?

---

## 15. COMPLETION SUMMARY (V5)

| Layer / Domain | V3 | V4 | V5 | Key Gap |
|----------------|----|----|----|---------|
| Layer 1: Kernel | 90% | 90% | 85% | PostgreSQL repos (gap widens as scope grows) |
| Layer 2: Platform Services | 30% | 5% | 3% | Data Fabric, Intelligence Fabric, Runtime Architecture all missing |
| Layer 3: Business Capabilities | 70% | 30% | 25% | Capability surface expansion reveals more gaps |
| Layer 4: Applications | 2% | 0% | 0% | No frontend code |
| Operating System API | 30% | 10% | 5% | REST-only; GraphQL, MCP, Agent SDK, Runtime all missing |
| Knowledge Packs | — | 0% | 0% | Not started |
| Signal Marketplace | — | 0% | 0% | Not started |
| Digital Twin Engine | — | — | 0% | **V5 NEW.** All 6 components missing |
| Runtime Architecture | — | — | 0% | **V5 NEW.** All resilience patterns missing |
| **Overall** | **28%** | **22%** | **12%** | V5 widened the gap to reveal true platform scope |

**Note:** Completion % drops with each version — not because regressions, but because the architecture team is discovering the true scope of the platform. 12% is the most honest assessment in the project's history.

---

*This Master Blueprint V5.0 is the authoritative reference for all SalesOS development. It supersedes all prior versions. Every architecture decision, implementation plan, and code review must align with this document.*
