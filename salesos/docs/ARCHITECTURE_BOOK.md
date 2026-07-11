# SalesOS Architecture Book

> **كتاب معمارية SalesOS** — المرجع الشامل لكل ما بُني عبر الموجات الأربع
>
> Version: v1.0 | Last Updated: 2026-07-11
> Author: Architecture Review Board | Status: 🟢 Published

---

## Table of Contents

- [Part 1: Engineering Platform](#part-1-engineering-platform)
- [Part 2: Product Architecture](#part-2-product-architecture)
- [Part 3: Domain Deep Dives](#part-3-domain-deep-dives)
- [Part 4: Infrastructure](#part-4-infrastructure)
- [Part 5: Architecture Decisions](#part-5-architecture-decisions)
- [Part 6: SDK & Extension Guide](#part-6-sdk--extension-guide)
- [Appendices](#appendices)

---

# Part 1: Engineering Platform

> **منصة الهندسة** — الأساس الذي تُبنى عليه كل منتجات SalesOS

## 1.1 Engineering Constitution

The SalesOS Engineering Constitution (`engineering-os/ENGINEERING_CONSTITUTION.md`) is the binding document that governs every aspect of development. It contains 9 Articles covering:

| Article | Focus | Key Rule |
|---------|-------|----------|
| **Article 1** | Code Quality & Review | Every PR needs 2 reviewers; no PR with critical security issues |
| **Article 2** | Quality & Testing | Minimum 85% unit test coverage; no new feature if quality drops |
| **Article 3** | Architecture | Cross-domain imports blocked; Repository Pattern mandatory; ADR for architectural changes |
| **Article 4** | Security | No secrets in code; all endpoints require auth; data encrypted at rest and in transit |
| **Article 5** | Documentation | Each agent maintains docs for their domain; every feature needs full doc chain |
| **Article 6** | Release & Deployment | All quality gates must pass; every release needs rollback strategy |
| **Article 7** | Data & Privacy | No production data in dev; KSA PDPL compliance; user data deletion rights |
| **Article 8** | Team Responsibility | Run lint/type/test before commit; report security flaws immediately |
| **Article 9** | Widget SDK Standard | All widgets use SDK; Container/View pattern mandatory; Contract tests required |

**Violation penalties** range from immediate PR block to security investigation and mandatory training.

**File reference:** `engineering-os/ENGINEERING_CONSTITUTION.md`

## 1.2 Architecture Compliance

Compliance is measured across 7 rules with weighted scoring:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Compliance Check                             │
├─────────────────────────────────────────────────────────────────┤
│ ARC-9.1: Container/View Pattern     20%                        │
│ ARC-3.2: No Cross-Domain Imports    20%                        │
│ ARC-3.3: Repository Pattern         15%                        │
│ DF-4.1:  No localStorage for Biz    10%                        │
│ DF-4.2:  Centralized API Client     10%                        │
│ DP-5.1:  Decision Platform Scoring  15%                        │
│ DP-5.2:  No Inline Scoring in Views 10%                        │
└─────────────────────────────────────────────────────────────────┘
```

**Current scores** (as of 2026-07-11):

| Domain | Score | Status |
|--------|-------|--------|
| Identity | 100% | 🟢 |
| Widget SDK | 100% | 🟢 |
| Company | 95% | 🟢 |
| Search | 90% | 🟡 |
| Scoring | 95% | 🟢 |
| CRM | 90% | 🟡 |
| AI | 85% | 🟡 |
| Timeline | 80% | 🟡 |
| Workflow | 50% | 🔴 |
| **OVERALL** | **87%** | **🟡** |

**Target:** 95% (per Engineering Constitution Article 2.1)

**Compliance check command:**
```bash
pwsh scripts/arch-compliance.ps1        # Full check
pwsh scripts/arch-compliance.ps1 -JsonOnly  # CI output
```

**File reference:** `docs/ARCHITECTURE_COMPLIANCE.md` | `scripts/arch-compliance.ps1`

## 1.3 Domain Boundaries (Bounded Contexts)

SalesOS follows Domain-Driven Design with 13 bounded contexts:

```
┌─────────────────────────────────────────────────────────────────┐
│                     SalesOS Platform                             │
│                                                                  │
│  CORE DOMAINS (Competitive Advantage):                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Company    │  │   Entity     │  │   Knowledge Graph    │   │
│  │ Intelligence │  │  Resolution  │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  SUPPORTING DOMAINS (Important, Standard Patterns):              │
│  ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐               │
│  │  CRM     │ │Activity│ │Scoring │ │   DNA    │               │
│  │          │ │ Engine │ │ Engine │ │ Profiles │               │
│  └──────────┘ └────────┘ └────────┘ └──────────┘               │
│                                                                  │
│  GENERIC DOMAINS (Best Practices, Off-the-Shelf):               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Identity │ │  Search  │ │ Workflow │ │ Billing  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
│                                                                  │
│  FUTURE DOMAINS:                                                 │
│  ┌──────────┐ ┌──────────┐                                      │
│  │Marketpl. │ │Data Lake │                                      │
│  └──────────┘ └──────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

**Key relationships:**

| Source | Target | Relationship |
|--------|--------|--------------|
| Identity → Company | Conformist | Company consumes tenant_id from Identity |
| Company → Entity Resolution | Partnership | ER enriches Company |
| Company → CRM | Conformist | CRM consumes Company as customer |
| Company → Knowledge Graph | Partnership | KG extends Company with relationships |
| AI → All | Open-Host | AI queries all contexts via published language |
| Workflow → All | Open-Host | Workflow triggers on events from all contexts |

**File reference:** `docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md`

## 1.4 Repository Pattern

Every domain service depends on repository interfaces, not databases:

```python
class Repository[T, TId]:
    async def get(self, id: TId) -> T: ...
    async def save(self, aggregate: T) -> None: ...
    async def delete(self, id: TId) -> None: ...
    async def exists(self, id: TId) -> bool: ...
```

**Key repositories:**

| Repository | Domain | Key Methods |
|------------|--------|-------------|
| `CompanyRepository` | Company Intelligence | `find_by_cr_number()`, `find_by_name()`, `find_expiring_licenses()` |
| `OpportunityRepository` | CRM | `find_by_company()`, `find_by_user()`, `aggregate_by_stage()` |
| `ActivityRepository` | Activity | `find_by_company()`, `count_by_type()` |
| `DomainEventStore` | Cross-cutting | `append()`, `read_stream()`, `read_all()` |

**Implementation:** Repositories are implemented in the Infrastructure Layer only. Domain Layer never knows about the database.

## 1.5 Cross-Domain Communication

Communication between domains follows strict rules:

1. **Internal calls** — via published interfaces (SDK/API)
2. **Domain events** — via Event Bus (in-memory Event Runtime → Kafka in Wave 3)
3. **CQRS** — Read models are separate from write models; eventual consistency is acceptable
4. **No cross-domain imports** — `features/` never imports from another `features/*` directory

```python
# ✅ Correct: Cross-domain via event
@event_runtime.subscribe("opportunity.*")
async def on_opportunity_event(event):
    nba = NBAEngine()
    await nba.recompute(opportunity_id=event.aggregate_id)

# ❌ Wrong: Direct cross-domain import
from features.company_intelligence import ...  # BLOCKED
```

## 1.6 Platform Kernel (`packages/platform/`)

The Platform Kernel is the shared runtime that every SalesOS package depends on. It owns cross-cutting concerns only.

```
packages/platform/
├── kernel/           # Bootstrap, registry, lifecycle
│   ├── platform.ts   # Platform bootstrap with dependency order
│   ├── registry.ts   # Global widget/command/capability registry
│   └── lifecycle.ts  # Lifecycle hooks
├── shared/           # Cross-cutting concerns
│   ├── telemetry/    # Metrics, tracing, performance
│   ├── permissions/  # PermissionResolver interface + default
│   ├── feature-flags/ # FeatureFlagResolver + tiered resolver
│   ├── cache/        # MemoryCache with TTL
│   ├── config/       # Runtime configuration provider
│   ├── events/       # EventBus interface
│   └── utils/        # ID generation, time utilities
├── contracts/        # Type definitions, interfaces, DTOs
│   ├── workspace/    # WidgetContract, permissions, provider
│   ├── search/       # SearchQuery, SearchResult, SearchEntity
│   ├── widgets/      # WidgetStatus, lifecycle events
│   ├── ai/           # Recommendation, Evidence, Decision, Score
│   └── revenue/      # Opportunity, Pipeline, Meeting, NBA, Playbook
└── testing/          # Mocks, factories, test utilities
```

**Dependency graph:**

```
kernel/ (zero deps)
  ├── shared/cache/       (zero deps)
  ├── shared/config/      (zero deps)
  ├── shared/telemetry/   (zero deps)
  ├── shared/permissions/ (zero deps)
  ├── shared/feature-flags/ (depends on: config)
  ├── shared/events/      (depends on: telemetry)
  └── shared/utils/       (zero deps)
       └── contracts/     (depends on: utils)
            └── testing/  (depends on: contracts)
```

**File reference:** `packages/platform/` | `docs/wave-2/02-PLATFORM_KERNEL_DESIGN.md`

## 1.7 Widget SDK

Widget SDK v1.0 is **Frozen** (Feature Freeze since 2026-07-10). Any change requires an ADR + Architecture Review Board approval.

### Core Functions

```typescript
// Dashboard Widget
createDashboardWidget({
  id: 'my-widget',
  component: MyWidget,
  providers: [MyProvider],
  permissions: { resource: 'my-domain', action: 'read' },
  featureFlag: 'my-widget-enabled',
})

// Standard Widget
createWidget({
  id: 'my-widget',
  component: MyWidget,
  container: MyWidgetContainer,
  view: MyWidgetView,  // Pure presentational component
})
```

### Mandatory Pattern

Every widget MUST follow the Container/View pattern:

```
WidgetName/
├── WidgetNameContainer.tsx  # Data fetching, business logic, SDK calls
├── WidgetNameView.tsx       # Pure presentational, no side effects
└── index.ts                 # Re-exports
```

### Mandatory Tests

Every widget MUST pass contract tests:

```typescript
describeWidgetContract(MyWidget, {
  name: 'MyWidget',
  states: ['loading', 'ready', 'degraded', 'error'],
  permissions: ['my-domain:read'],
})
```

### Frozen Components

| Component | Since | Status |
|-----------|-------|--------|
| `createWidget()` | 2026-07-10 | 🧊 Frozen |
| `createDashboardWidget()` | 2026-07-10 | 🧊 Frozen |
| SDK Types | 2026-07-10 | 🧊 Frozen |
| Lifecycle/Telemetry/Permissions/Flags | 2026-07-10 | 🧊 Frozen |
| Testing Utilities | 2026-07-10 | 🧊 Frozen |
| `REFERENCE_WIDGET_GUIDE.md` | 2026-07-10 | ✅ Published |
| `WidgetTemplate/` | 2026-07-10 | ✅ Published |

**File reference:** `frontend/docs/REFERENCE_WIDGET_GUIDE.md` | `frontend/docs/company-intelligence/REFERENCE_WIDGET_GUIDE.md`

### Widget Template Structure

Every new widget starts from `WidgetTemplate/` — never from scratch or by copying another widget:

```
WidgetTemplate/
├── WidgetTemplateContainer.tsx   # SDK calls, data fetching, Decision Platform
├── WidgetTemplateView.tsx        # Pure presentational, receives props only
├── WidgetTemplate.test.tsx       # Contract tests via describeWidgetContract()
├── WidgetTemplate.stories.tsx    # Storybook stories for all states
├── index.ts                      # Public exports
└── __tests__/
    └── WidgetTemplate.a11y.test.tsx  # Accessibility tests (WCAG AA)
```

### Widget Lifecycle

```
Mount → Provider Setup → Data Fetch → Render → User Interaction → Unmount
  │         │              │            │           │               │
  │    Permissions     Loading       View       NBA Accept/    Cleanup
  │    Feature Flags   State        Ready      Dismiss/etc.   Providers
  │    Config                                  Feedback
```

### 37 Widgets Currently Deployed

| Feature Area | Count | Widgets |
|-------------|-------|---------|
| Dashboard | 6 | AIBrief, IntelligenceFeed, RecentActivity, DecisionQueue, MarketPulse, MissionCenter |
| Company Intelligence | 10 | SmartTimeline, SignalsFeed, GoldenRecord, DecisionMakers, BuyingJourney, CompanyDNA, AIRecommendation, RelationshipGraph, DocumentIntelligence, GovernmentIntelligence |
| Revenue Execution | 19 | NBA, Pipeline (Kanban, List, Analytics, Health Map, Forecast), Meeting (PreBrief, PostSummary, ActionItems), Email (Inbox, Sentiment, Topics), Revenue Dashboard |
| Analytics | 1 | CommercialAnalytics |
| Search | 1 | SearchWidget |

## 1.8 Feature Flags & Permissions

### Feature Flags

```typescript
interface FeatureFlagResolver {
  isEnabled(flag: FeatureFlag): boolean
}

// Tier-based resolution
class TieredFeatureFlagResolver implements FeatureFlagResolver {
  // Checks user tier against flag's required tier
}
```

Used for phased rollout: internal → beta → enterprise.

### Permissions (RBAC)

| Role | Scope |
|------|-------|
| `ADMIN` | Full access to all tenant data and settings |
| `MANAGER` | Can manage data and users (except billing) |
| `USER` | Can view and create data |
| `API` | API-only access with limited scope |
| `AUDITOR` | Read-only access for compliance |

**Resource pattern:** `{domain}:{action}` (e.g., `opportunity:read`, `nba:admin`)

**Feature flag usage examples:**

| Flag | Scope | Description |
|------|-------|-------------|
| `nba-enabled` | tenant-level | Controls NBA engine availability per tenant |
| `pipeline-intelligence` | tier-based | `internal` → `beta` → `enterprise` rollout |
| `meeting-intelligence` | tier-based | Phase 1: internal only; Phase 2: all paying tenants |
| `rag-pipeline` | tenant-level | Wave 3 early adopters flag |

**File reference:** `backend/app/modules/identity/` | `frontend/src/lib/permissions/` | `packages/platform/shared/feature-flags/`

---

# Part 2: Product Architecture

> **معمارية المنتج** — كيف تترجم الرؤية إلى كود

## 2.1 Revenue Execution Bible

The Revenue Execution Bible (`REVENUE_EXECUTION_BIBLE.md`) defines the product vision and strategy. Key principles:

### Core Vision

> **Revenue Execution هي الطبقة التي تحوِّل معرفة SalesOS عن الشركات إلى صفقات وإيرادات ملموسة.**

### The Revenue Execution Workflow

```
Discover → Understand → Prioritize → Engage → Meet → Propose → Negotiate → Close → Expand
```

### Personas

| Persona | Pain Point | Success Metric |
|---------|-----------|---------------|
| Sales Rep | Doesn't know which opportunity to follow | Deals closed/month |
| Sales Manager | No real-time deal health visibility | Forecast accuracy |
| Customer Success | Can't see at-risk accounts | Retention rate |
| VP of Sales | Pipeline data arrives late | Revenue growth/Q |

### 5 Product Principles

1. **Actionable at Every Step** — Every screen ends with an action
2. **Intelligence Before Data** — Understand health before seeing numbers
3. **NBA-First** — Next Best Action is the first thing users see
4. **Moments That Matter** — Intelligence at decisive moments, not all moments
5. **Continuity with Wave 1** — Revenue Execution builds on Company Intelligence

**File reference:** `REVENUE_EXECUTION_BIBLE.md`

## 2.2 Wave 1: Foundation

> **الموجة الأولى: الأساس** — UI Kit, Design System, Foundation Components

### Deliverables

| Category | Count | Details |
|----------|-------|---------|
| Design System | 16 files | `@salesos/design-language` — all exported, deduplicated |
| UI Kit Restyle | 15 components | `@salesos/ui` restyled with MUHIDE tokens |
| Foundation Components | 22 components | a11y-optimized, bilingual (AR/EN) |
| Dashboard Layout | 1 layout | MUHIDE colors, responsive |
| Color Violations Remediated | 340+ | Hardcoded colors replaced with semantic tokens |

### Design Tokens

```
@salesos/design-language/
├── colors/          # MUHIDE palette with light/dark variants
├── typography/      # Viga + IBM Plex Sans/Arabic/Mono
├── spacing/         # Consistent spacing scale
├── shadows/         # Semantic shadow tokens
└── animations/      # Reduced motion support
```

### Accessibility Requirements (WCAG AA)

- Keyboard navigation for all components
- ARIA labels on interactive elements
- Reduced motion media query support
- Dark mode support
- RTL (Right-to-Left) for Arabic
- Color contrast ratios ≥ 4.5:1

### Frontend Architecture (Wave 1)

```
frontend/src/
├── app/             # Next.js App Router pages
├── components/      # Shared UI components
├── features/        # Feature domains (one per bounded context)
│   ├── dashboard/
│   ├── company-intelligence/
│   ├── search/
│   └── ...
├── lib/             # API client, hooks, utilities
├── mocks/           # Mock data for development
└── __tests__/       # Test infrastructure
```

## 2.3 Wave 2: Revenue Execution

> **الموجة الثانية: تنفيذ الإيرادات** — NBA, Opportunity, Pipeline, Meeting, Revenue

### Architecture

```
Wave 2 Layer
  │
  ├── Next Best Action Engine
  │     └── Decision Pipeline (12 stages)
  │
  ├── Opportunity Workspace
  │     ├── NBA Widget
  │     ├── Timeline Widget
  │     ├── Company Snapshot
  │     ├── Deal Health
  │     └── Playbook Engine
  │
  ├── Pipeline Intelligence
  │     ├── Kanban View
  │     ├── List View
  │     ├── Analytics (Velocity, Win Rate)
  │     ├── Health Map
  │     └── Forecast Engine
  │
  ├── Meeting Intelligence
  │     ├── Pre-Meeting (Brief, Talking Points)
  │     ├── During (Notes, Action Items)
  │     └── Post-Meeting (AI Summary, Follow-up)
  │
  ├── Email Intelligence
  │     ├── Sentiment Analysis
  │     ├── Topic Extraction
  │     ├── Urgency Detection
  │     └── Gmail/Outlook Connectors
  │
  └── Revenue Workspace
        ├── Executive Summary
        ├── Team Performance
        ├── AI Insights
        └── Revenue Goals
```

### NBA Decision Pipeline

The NBA Engine implements a 12-stage decision pipeline that transforms raw signals into actionable recommendations:

```
Signal (trigger event)
  │  Types: stage_change | activity | signal | time | health | score | manual
  ▼
1. Normalization
  │  Fetch opportunity + company context
  │  Fetch recent activities (14 days)
  │  Enrich with related signals
  │  Standardize into NormalizedSignal format
  ▼
2. Business Rules
  │  Evaluate 10+ deterministic rules:
  │  - Stage-based: qualification → "Send intro email" (0.9)
  │  - Time-based: idle 14 days → "Send follow-up" (0.7 + days/100)
  │  - Signal-based: new competitor → "Prepare competitive brief" (0.8)
  │  - Health-based: critical → "Escalate to manager" (0.95)
  │  - Engagement-based: high engagement → "Schedule demo" (0.75)
  ▼
3. Scoring Engine
  │  Weighted scoring: rule * 0.4 + opportunity * 0.25 + urgency * 0.2 + effort * 0.15
  │  Opportunity factors: value (25%), stage (20%), engagement (15%),
  │  ICP score (15%), decision maker access (10%), timeline (10%), health (5%)
  ▼
4. AI Reasoning (optional)
  │  Evaluates when rules produce low confidence (< 0.7) or conflict
  │  Can shift ranking by max ±0.2 from rule score
  │  Timeout after 2s → fallback to rule-only
  ▼
5. Risk Assessment
  │  6 detectors: stagnation, competition, engagement drop,
  │  stakeholder change, budget concern, timeline slip
  │  Score adjustment: -0.3 to 0.0 (only reduces)
  ▼
6. Confidence Calculation
  │  finalScore = ruleScore + aiScore + riskAdjustment
  │  high: ≥ 0.8 | medium: ≥ 0.5 | low: < 0.5
  ▼
7. Recommendation Ranking
  │  Sort candidates by confidence, apply business constraints
  ▼
8. NBA Output
  │  Top recommendation + alternatives + evidence trail + explainability
  ▼
9. Feedback Collection
  │  User accepts / dismisses / completes the recommendation
  ▼
10. Continuous Learning
  │  Feedback metrics → rule weight adjustment → accuracy improvement
```

### NBA Performance Budget

| Stage | Budget | Violation Action |
|-------|--------|-----------------|
| Normalization | < 50ms | Log warning |
| Business Rules | < 20ms | Log warning |
| Scoring | < 30ms | Log warning |
| AI Reasoning | < 2000ms | Timeout + fallback to rule-only |
| Risk Assessment | < 50ms | Log warning |
| Confidence Calculation | < 10ms | N/A |
| **Total (rule-only)** | **< 200ms** | Error metric |
| **Total (with AI)** | **< 3000ms** | Timeout + fallback |

### NBA Event-Driven Triggers

```
Domain Events (Event Runtime / Kafka)
  │
  ├── opportunity.created ─────────────► auto-assign playbook, generate initial NBA
  ├── opportunity.stage_changed ───────► recompute for this opportunity
  ├── activity.logged ────────────────► update engagement, recompute if stagnation cleared
  ├── company.signal.detected ─────────► evaluate impact if linked to opportunity
  ├── company.scored ─────────────────► update opportunity score if ICP/Intent changes
  ├── deal_health.changed ────────────► generate risk-mitigation action if health degrades
  └── time.trigger (daily) ────────────► scan all open opportunities for idle detection
```

### New Database Tables (Wave 2)

| Table | Purpose |
|-------|---------|
| `opportunities` | First-class opportunity entity with lifecycle |
| `opportunity_features` | NBA scoring data (parallel to `company_features`) |
| `playbooks` | Playbook definitions and stage mappings |
| `meetings` | Meeting records with intelligence data |
| `meeting_action_items` | Action items extracted from meetings |
| `emails` | Email records with metadata |
| `email_intelligence` | Sentiment, topics, urgency scores |
| `revenue_goals` | Target tracking per user/team/period |

### Key Frontend Components (Wave 2)

| Component | Function |
|-----------|----------|
| `NBAContainer` + `NBAView` | NBA recommendation display |
| `OpportunityWorkspace` | Full opportunity lifecycle |
| `PipelineKanban` | Drag-and-drop stage management |
| `PipelineAnalytics` | Velocity, conversion, win rate |
| `HealthMap` | Traffic light deal visualization |
| `PreMeetingBrief` | AI-generated meeting preparation |
| `PostMeetingSummary` | AI-generated meeting summary |
| `EmailSentimentBadge` | Sentiment indicator on emails |
| `RevenueDashboard` | Executive revenue overview |

**File reference:** `docs/wave-2/` (11 documents) | `CHANGELOG.md` (v0.6.0)

## 2.4 Wave 3: AI & Automation

> **الموجة الثالثة: الذكاء والأتمتة** — RAG, Workflow, Kafka, Analytics

### Wave Evolution

| Wave | Question | Theme |
|------|----------|-------|
| Wave 1 | "ما هي هذه الشركة؟" | Understand |
| Wave 2 | "ماذا أفعل الآن؟" | Execute |
| Wave 3 | "كيف يجري النظام العمل نيابة عني؟" | Automate |
| Wave 4 | "متى يحتاج النظام لتدخلي؟" | Autonomous |

### Sprint Breakdown

| Sprint | Focus | Duration |
|--------|-------|----------|
| Sprint 10 | RAG Pipeline + Vector Store | 3 weeks |
| Sprint 11 | Kafka Event Bus Migration | 3 weeks |
| Sprint 12 | Workflow Automation Engine | 3 weeks |
| Sprint 13 | Analytics & Reporting | 3 weeks |
| Sprint 14 | Integration & Polish | 2 weeks |

### RAG Pipeline (Sprint 10)

```
Document Ingestion → Document Processing → Chunking → Embedding
  → Vector Store (pgvector) → Retrieval (Hybrid) → Context Assembly
  → Generation (with Citations) → Citation Verification
```

**Key decisions:**
- **Vector store:** pgvector (PostgreSQL extension) — zero new infrastructure
- **Embedding model:** Self-hosted `intfloat/multilingual-e5-large` — Arabic quality + data sovereignty
- **Generation:** GPT-4o-mini primary, GPT-4o for complex cases
- **Search:** Hybrid (semantic + BM25 keyword) with Reciprocal Rank Fusion

### Kafka Event Bus (Sprint 11)

**Replacing in-memory Event Runtime (TD-002):**

| Feature | Old (Event Runtime) | New (Kafka) |
|---------|---------------------|-------------|
| Persistence | In-memory only | Disk-based, replayable |
| Delivery | At-most-once | Exactly-once |
| Schema | TypeScript only | Avro + Schema Registry |
| Consumer | Simple subscribers | Consumer groups + offset management |
| DLQ | Manual | Automatic with retry policies |

**Topic naming:** `salesos.{domain}.{event_type}.{version}`

**Key event types:**

| Event | Producer | Consumers |
|-------|----------|-----------|
| `opportunity.created` | Opportunity Service | NBA, Workflow, Search, Pipeline |
| `opportunity.stage_changed` | Opportunity Service | NBA, Workflow, Pipeline, Analytics |
| `activity.logged` | Activity Service | NBA, Timeline, Analytics |
| `deal_health.changed` | Deal Health Service | NBA, Workflow, Alerting |
| `company.signal.detected` | Signal Runtime | NBA, Company Intelligence |
| `nba.generated` | NBA Engine | Analytics, Audit |
| `workflow.completed` | Workflow Engine | Analytics, Monitoring |

### Workflow Automation (Sprint 12)

**Workflow = DAG of Actions.** Custom lightweight engine (Python + PostgreSQL):

```
Trigger (event/schedule/manual)
  └── Steps (DAG)
        ├── Action (email, crm, task, webhook, nba, delay)
        ├── Branch (if/else condition)
        └── Parallel (fan-out/fan-in)
```

**5 Starter Templates:**

| Template | Trigger | Steps |
|----------|---------|-------|
| Follow-Up | `deal_health.stagnation` | Delay → Email → Task → Delay → Email |
| Lead Nurturing | `opportunity.created` | Email → Delay → Task → Check Engagement |
| Deal Escalation | `deal_health.critical` | Update CRM → Alert → Urgent Task → Notify |
| Onboarding | Manual | Welcome → Task List → Delay → Check |
| Renewal Reminder | Schedule: 90d before expiry | Check → Reminder → Delay → Final Reminder |

### Analytics & Reporting (Sprint 13)

**Architecture:**
```
Operational DB → ETL Pipeline → Data Warehouse (Star Schema) → Cubes → Reports
```

**Data Warehouse:** Separate PostgreSQL instance (8 vCPU, 32GB, 500GB SSD) with:
- Staging layer (raw tables)
- Dimensions (time, company, user, opportunity)
- Facts (pipeline_snapshot, activity_fact, workflow_fact)
- Materialized views (pre-aggregated cubes)

**5 Cubes:** Pipeline Cube, Team Cube, Forecast Cube, Activity Cube, Workflow Cube

**7 Standard Reports:** Pipeline Health, Team Performance, Forecast Accuracy, Activity Analysis, Velocity Report, Win/Loss Analysis, Workflow Performance

### Infrastructure Additions (Wave 3)

| Service | Spec | Monthly Cost |
|---------|------|-------------|
| Document Ingestion | 2 vCPU, 4GB | $60 |
| Embedding Service | 4 vCPU, 8GB | $120 |
| RAG Retrieval | 2 vCPU, 4GB | $60 |
| RAG Generation | 2 vCPU, 4GB | $60 |
| Kafka Cluster (3 brokers) | 4 vCPU, 8GB each | $330 |
| Workflow Engine | 2 vCPU, 4GB | $130 |
| Data Warehouse | 8 vCPU, 32GB, 500GB | $400 |
| ETL Pipeline | 4 vCPU, 8GB | $60 |
| Redis Cache | 2 vCPU, 4GB | $80 |
| **Wave 3 Total** | | **~$1,740/mo** |
| LLM API costs | | ~$300/mo |

**File reference:** `docs/wave-3/` (7 documents)

## 2.5 Wave 4: Enterprise

> **الموجة الرابعة: المؤسسات** — SSO, Audit, API Keys, Admin, Telemetry, Demo

### Planned Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **Enterprise SSO** | SAML/OIDC single sign-on | 🟡 Planned |
| **Audit Log** | Comprehensive audit trail | 🟡 Planned |
| **API Keys** | Programmatic access management | 🟡 Planned |
| **Admin Portal** | Tenant administration | 🟡 Planned |
| **Telemetry** | Usage analytics and monitoring | 🟡 Planned |
| **Demo Mode** | Sandbox/demo environment | 🟡 Planned |
| **Marketplace** | Plugin ecosystem | 🔴 Future |
| **MCP Integration** | Model Context Protocol for external tools | 🔴 Future |
| **Multi-workspace** | Cross-entity workspace switching | 🔴 Future |

**File reference:** `frontend/docs/enterprise/ENTERPRISE_ARCHITECTURE.md`

## 2.6 Wave 5: Ecosystem (Future)

> **الموجة الخامسة: النظام البيئي** — Marketplace, Plugins, MCP

- **Marketplace** — Third-party plugin installation and management
- **Plugin SDK** — Extension API for external developers
- **MCP Integration** — Model Context Protocol for AI tool integration
- **Data Lake** — Advanced analytics and ML pipelines
- **Autonomous Sales Agent** — Wave 4 completion (human exception-only)

---

# Part 3: Domain Deep Dives

> **غوص معمق في المجالات** — تفاصيل كل نطاق من النظام

## 3.1 Identity & Auth

**Domain:** Generic | **Context:** BC-01 | **Compliance:** 100%

### Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Identity    │     │  Auth Service  │     │  Permission  │
│   Service    │────►│   (JWT/SSO)   │────►│  Resolver    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Tenant     │     │    User      │     │     RBAC     │
│   Repository │     │  Repository  │     │   Registry   │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Key Entities

- **Tenant** — Customer organization with isolated data and configuration
- **User** — Individual with role-based permissions within a tenant
- **UserRole** — ADMIN, MANAGER, USER, API, AUDITOR

### Authentication Flow

```
User → Login (email/password) → JWT issued (access + refresh)
  → Token stored in localStorage (standard pattern)
  → Every API call: Authorization: Bearer <token>
  → Refresh token when expired
```

### SSO (Future)

SAML/OIDC-based single sign-on for enterprise tenants. Planned for Wave 4.

### Security Architecture

- **JWT** — RS256 signed tokens with tenant context
- **Password hashing** — bcrypt with configurable cost factor
- **Rate limiting** — Per-tenant on all auth endpoints
- **CSRF protection** — Implemented on state-changing endpoints
- **Secrets** — All in environment variables; zero secrets in code

**File reference:** `backend/app/modules/identity/` | `backend/docs/adr/`

## 3.2 Company Intelligence

**Domain:** Core | **Context:** BC-02 | **Compliance:** 95%

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Company Intelligence                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Data Sources                    Ingestion Pipeline           │
│  ┌──────────┐                   ┌──────────────────┐         │
│  │ Balady   │──────────────────►│  Source Adapters  │         │
│  ├──────────┤                   └────────┬─────────┘         │
│  │ Taqeem   │────────────────────────────┤                   │
│  ├──────────┤                            ▼                   │
│  │ Ministry │──────────────────►┌──────────────────┐         │
│  ├──────────┤                   │  Entity           │         │
│  │ Other    │──────────────────►│  Resolution       │         │
│  └──────────┘                   └────────┬─────────┘         │
│                                          ▼                   │
│  Core Entities                    ┌──────────────────┐       │
│  ┌──────────────────┐             │  Golden Record    │       │
│  │ Company           │◄────────────┤                  │       │
│  │  - Branches       │             └──────────────────┘       │
│  │  - Licenses       │                                        │
│  │  - Contacts       │                                        │
│  └──────────────────┘                                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Entities

| Entity | Description | Invariants |
|--------|-------------|------------|
| **Company** | Legal entity with CR number | CR unique per tenant; at least one name |
| **Branch** | Physical location | Belongs to one company |
| **License** | Government permit | Has status, expiry, renewal tracking |
| **Contact** | Person associated with company | Can be primary contact |

### Entity Resolution

**Core differentiator.** Matching and merging duplicate company records from multiple government sources.

```python
# Business rule: auto-verify golden records
if company.source_ids >= 3 AND any source is government:
    mark as_golden_record = True
    set confidence_score = 0.95
```

**Event sourcing** is used for Entity Resolution only (full audit trail of merge/split decisions).

### Company Status Lifecycle

```
ACTIVE ←→ INACTIVE
  │           │
  ├── SUSPENDED
  ├── EXPIRED
  ├── LIQUIDATED (terminal)
  └── UNDER_RESTRUCTURING
```

**File reference:** `backend/domains/` | `docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md`

## 3.3 Search Domain

**Domain:** Generic | **Context:** — | **Compliance:** 90%

### Architecture

Search is a cross-cutting concern that serves all domains. It provides unified search across companies, opportunities, contacts, and documents.

```
┌─────────────────────────────────────────────────────────────┐
│                        Search SDK                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Search Query                    Search Results               │
│  ┌─────────────────────┐       ┌──────────────────────┐     │
│  │ query: string        │       │ items: SearchResult[] │     │
│  │ filters: Filter[]    │──────►│ total: number         │     │
│  │ scope: string        │       │ facets: SearchFacet[] │     │
│  │ sort: SortOption     │       │ page: number          │     │
│  │ page: number         │       │ page_size: number     │     │
│  └─────────────────────┘       └──────────────────────┘     │
│                                                               │
│  SearchEntityType: company | opportunity | contact | document │
│  ScopedSearch: withScope('company', id) → filter by company   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Search Capabilities

| Feature | Implementation | Status |
|---------|---------------|--------|
| Full-text search | PostgreSQL FTS (English + Arabic) | 🟢 |
| Semantic search | pgvector (hybrid with BM25) — Wave 3 | 🟡 Planned |
| Faceted search | By industry, city, status, stage | 🟢 |
| Autocomplete | Prefix-based suggest API | 🟢 |
| Scoped search | `withScope('company', id)` | 🟢 |
| Cross-entity search | Unified results across all entities | 🟢 |
| Arabic search | Arabic stemmer, normalized search | 🟢 |

### Technical Debt

- **TD-001:** Search currently uses in-memory repositories instead of PostgreSQL. Migration planned for Sprint 2.
- Current implementation works for MVP but does not scale beyond ~100K records.

**File reference:** `frontend/src/features/search/` | `frontend/docs/search/` | `backend/domains/search/`

## 3.4 Knowledge Graph

**Domain:** Core | **Context:** BC-08 | **Compliance:** — (Neo4j-backed)

### Architecture

The Knowledge Graph is stored in Neo4j and tracks entity relationships over time. It powers relationship discovery, competitive analysis, and network-based scoring.

```
┌─────────────────────────────────────────────────────────────┐
│                      Knowledge Graph                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Nodes                     Edges                               │
│  ┌──────────────┐         ┌──────────────────┐               │
│  │ Company      │────────►│ OWNS             │               │
│  ├──────────────┤         ├──────────────────┤               │
│  │ Contact      │────────►│ EMPLOYS          │               │
│  ├──────────────┤         ├──────────────────┤               │
│  │ License      │────────►│ HAS_LICENSE      │               │
│  ├──────────────┤         ├──────────────────┤               │
│  │ Address      │────────►│ LOCATED_AT       │               │
│  └──────────────┘         ├──────────────────┤               │
│                           │ COMPETES_WITH    │               │
│                           ├──────────────────┤               │
│                           │ SUPPLIES         │               │
│                           ├──────────────────┤               │
│                           │ PARTNERS_WITH    │               │
│                           └──────────────────┘               │
│                                                               │
│  Each edge has: weight, confidence, valid_from, valid_to      │
│  Temporal: edges can be deactivated (soft delete)             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Relationship Types

| Type | Source → Target | Description |
|------|----------------|-------------|
| `OWNS` | Company → Company | Corporate ownership |
| `SUBSIDIARY` | Company → Company | Subsidiary relationship |
| `EMPLOYS` | Company → Contact | Employment |
| `HAS_LICENSE` | Company → License | Government license |
| `COMPETES_WITH` | Company → Company | Competitive relationship |
| `SUPPLIES` | Company → Company | Supplier relationship |
| `PARTNERS_WITH` | Company → Company | Business partnership |
| `SAME_GROUP` | Company → Company | Same corporate group |
| `LOCATED_AT` | Company → Address | Physical location |
| `SHARES_DIRECTOR` | Company ↔ Company | Shared board member |

### Key Use Cases

1. **Competitive Analysis:** "Which companies compete with this account?"
2. **Supply Chain Discovery:** "Who are the suppliers in this industry?"
3. **Corporate Hierarchy:** "What is the ownership structure of this group?"
4. **Relationship Scoring:** "How strongly connected is this company to our existing customers?"

**File reference:** `backend/domains/` | `docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md` | `docker-compose.yml` (Neo4j)

## 3.5 Revenue Execution

**Domain:** Supporting | **Context:** BC-04 (CRM) | **Compliance:** 90%

### Core Entities

```
Opportunity
  ├── Playbook (what to do at each stage)
  ├── Task (follow-ups, reminders)
  ├── Meeting (customer interactions)
  ├── Email (communications)
  ├── Activity (calls, notes, events)
  ├── Pipeline (stage, probability, velocity)
  ├── Revenue Goal (target, forecast)
  └── Next Best Action (recommended step)
```

### Opportunity Lifecycle

```
Qualification → Discovery → Proposal → Negotiation → Closed Won
                                                    → Closed Lost
```

### Deal Health Model

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Stagnation | No activity for 7+ days | 🟡→🔴 |
| Competition | Competitor signal detected | 🟡 |
| Engagement Drop | Activity < 50% of previous period | 🟡 |
| Stakeholder Change | Contact change on account | 🟡 |
| Budget Concern | Signal mentions budget/cost | 🟡 |
| Timeline Slip | Close date pushed 2+ times | 🟡→🔴 |

### Opportunity Scoring

| Factor | Weight |
|--------|--------|
| Deal Value | 25% |
| Stage Progression | 20% |
| Engagement Level | 15% |
| Company ICP Score | 15% |
| Decision Maker Access | 10% |
| Timeline Pressure | 10% |
| Deal Health | 5% |

### Frontend Components

```
revenue-execution/
├── _providers/
│   └── DecisionProvider      # Decision Platform context
├── widgets/
│   ├── nba/                  # Next Best Action
│   ├── pipeline/             # Pipeline Intelligence
│   ├── meeting/              # Meeting Intelligence
│   ├── email/                # Email Intelligence
│   └── forecast/             # Forecast Engine
└── workspaces/
    ├── OpportunityWorkspace
    ├── PipelineWorkspace
    ├── MeetingWorkspace
    └── RevenueWorkspace
```

**File reference:** `docs/wave-2/` | `REVENUE_EXECUTION_BIBLE.md` | `frontend/src/features/revenue-execution/`

## 3.6 AI Platform

**Domain:** Core | **Context:** BC-09 | **Compliance:** 85%

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Platform                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐                │
│  │   RAG Pipeline    │    │   NBA Engine     │                │
│  │                   │    │                  │                │
│  │  Ingestion        │    │  Rules           │                │
│  │  Chunking         │    │  Scoring         │                │
│  │  Embedding        │    │  AI Reasoning    │                │
│  │  Retrieval        │    │  Confidence      │                │
│  │  Generation       │    │  Explainability  │                │
│  │  Citation Verify  │    │  Feedback        │                │
│  └────────┬─────────┘    └────────┬─────────┘                │
│           │                       │                          │
│  ┌────────▼────────────────────────▼─────────┐               │
│  │           Scoring Engine                    │               │
│  │  (Company Score, Intent Score, Risk Score)  │               │
│  └────────────────┬───────────────────────────┘               │
│                   │                                           │
│  ┌────────────────▼───────────────────────────┐               │
│  │           Decision Platform                  │               │
│  │  (Orchestrator + Explainability + Feedback) │               │
│  └────────────────────────────────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### RAG Pipeline Details

**Document Ingestion:** PDF, DOCX, HTML, EML, Meeting Notes, Signals
**Chunking:** Semantic (512 tokens, 10% overlap), Heading-based, Sentence-based, Fixed-size
**Embedding:** `intfloat/multilingual-e5-large` (self-hosted, 1024 dimensions)
**Vector Store:** pgvector with HNSW index, partitioned by tenant
**Hybrid Search:** Semantic (cosine) + Keyword (BM25) with Reciprocal Rank Fusion
**Generation:** GPT-4o-mini (primary), GPT-4o (complex cases), with citation verification

### Arabic Text Normalization

```python
def normalize_arabic(text):
    text = re.sub('[إأآا]', 'ا', text)     # Normalize Alef
    text = re.sub('ة', 'ه', text)          # Taa Marbuta → Ha
    text = re.sub('ى', 'ي', text)          # Alif Maqsura → Ya
    text = re.sub('[ًٌٍَُِّْ]', '', text)   # Remove diacritics
    text = re.sub('ـ', '', text)            # Remove Tatweel/Kashida
    return text.strip()
```

### Cache Strategy

| Level | Storage | TTL | Hit Rate Target |
|-------|---------|-----|-----------------|
| L1: In-memory | Redis | 24 hours | 60% |
| L2: Disk | pgvector | 7 days | 30% |
| **Total** | | | **> 90%** |

**File reference:** `docs/wave-3/02-AI_RAG_ARCHITECTURE.md` | `backend/domains/rag/` | `frontend/src/features/rag/`

## 3.7 Workflow Automation

**Domain:** Generic | **Context:** BC-10 | **Compliance:** 50%

### Engine Design

Custom lightweight DAG engine (Python + PostgreSQL):

**Trigger System:**
- Event-based (`opportunity.stage_changed`)
- Scheduled (cron: `"0 9 * * 1"`)
- Manual (user click)

**Action Types:**
- `send_email` — Via Email Intelligence service
- `update_crm` — Update opportunity stage or field
- `create_task` — Create follow-up task
- `trigger_nba` — Refresh NBA recommendation
- `webhook` — External API call
- `delay` — Wait before proceeding
- `condition` — If/else branching

### Monitoring

| Metric | Target |
|--------|--------|
| Execution start | < 1s from trigger |
| Step execution (email) | < 2s |
| Concurrent executions | 500+ per tenant |
| Success rate | > 90% |

**File reference:** `docs/wave-3/03-WORKFLOW_AUTOMATION.md` | `backend/domains/workflow/` | `frontend/src/features/automation/`

## 3.8 Analytics & Reporting

**Domain:** Supporting | **Compliance:** — (new in Wave 3)

### Architecture

```
Operational DB → ETL Pipeline (hourly/daily) → Data Warehouse → Cubes → Reports
Kafka Streams → Redis (real-time metrics) → WebSocket → Dashboard
```

### Star Schema

```
Dimensions: dim_date, dim_company, dim_user, dim_opportunity
Facts: fact_pipeline_snapshot, fact_activity, fact_workflow_execution
Cubes: mv_pipeline_cube, mv_team_cube, mv_forecast_cube, mv_activity_cube, mv_workflow_cube
```

### Reporting

- **Standard:** Pipeline Health, Team Performance, Forecast Accuracy, Activity Analysis, Velocity, Win/Loss, Workflow Performance
- **Custom:** Drag-and-drop report builder with dimension/measure/filter selection
- **Export:** PDF (Arabic RTL), CSV (UTF-8 BOM), Excel (multi-sheet), Scheduled Email
- **Performance:** Cube-based reports < 1s, custom < 3s, complex < 10s

**File reference:** `docs/wave-3/04-ANALYTICS_REPORTING.md` | `backend/domains/analytics/`

## 3.9 Notifications

**Domain:** Cross-cutting

Notification delivery across channels:

| Channel | Method | Use Case |
|---------|--------|----------|
| In-app | WebSocket | Real-time NBA updates |
| Email | SMTP/SendGrid | Scheduled reports, alerts |
| Slack | Webhook | Workflow failures, critical alerts |
| SMS | Twilio (planned) | Critical escalations |

**File reference:** `backend/domains/notifications/`

---

# Part 4: Infrastructure

> **البنية التحتية** — كيف يشغَّل النظام

## 4.1 Docker Architecture

### Service Topology (Development)

```
docker-compose.yml
│
├── postgres (pgvector/pgvector:pg16)     # Database + vector store
│   └── pgbouncer                         # Connection pooling
├── neo4j:5-community                     # Knowledge graph
├── redis:7-alpine                        # Cache + real-time
├── zookeeper                             # Kafka coordination
├── kafka (confluentinc/cp-kafka)         # Event bus
├── backend                               # FastAPI application
├── frontend                              # Next.js application
├── prometheus                            # Metrics collection
└── grafana                               # Visualization
```

### Production Topology

```
docker-compose.prod.yml
│
├── postgres + pgbouncer
├── neo4j
├── redis
├── kafka (3 brokers)
├── backend (multiple replicas)
├── frontend (static build + reverse proxy)
├── caddy                                  # TLS termination + reverse proxy
└── backup (scheduled, with S3 upload)
```

### Security

- Non-root users in all containers
- Healthchecks on all services
- `depends_on` with `condition: service_healthy`
- `restart: unless-stopped` on all services
- No secrets in Docker images (all via env_file)
- Database ports NOT exposed to public in production

**File reference:** `docker-compose.yml` | `docker-compose.prod.yml` | `docs/DOCKER_VALIDATION_REPORT.md`

## 4.2 Database Strategy

| Database | Version | Purpose | Persistence |
|----------|---------|---------|-------------|
| **PostgreSQL** (pgvector) | 16 | Primary DB + vector store | `pgdata` volume |
| **Neo4j** | 5-community | Knowledge graph | `neo4j_data` volume |
| **Redis** | 7-alpine | Cache, real-time aggregates, session store | `redis-data` volume |

### PostgreSQL Schema Strategy

- **Operational DB:** Normalized for transactions (OLTP)
- **Data Warehouse:** Star schema for analytics (OLAP) — separate instance (Wave 3)
- **pgvector extension:** Vector storage for RAG embeddings
- **HNSW index:** For fast similarity search on embeddings

### Neo4j Usage

Knowledge graph for entity relationships:
- Companies, contacts, licenses as nodes
- `OWNS`, `SUBSIDIARY`, `EMPLOYS`, `COMPETES_WITH` as edges
- Weighted, temporal relationships with confidence scores

### Migration Path

| TD ID | Item | Resolution |
|-------|------|------------|
| TD-001 | In-memory repos → PostgreSQL | Sprint 2 (Wave 3+) |
| TD-002 | Event bus → Kafka | Sprint 11 (Wave 3) |

### Connection Pooling

PgBouncer provides connection pooling for PostgreSQL:

```
Applications → PgBouncer (port 6432) → PostgreSQL (port 5432)
                    │
                    ├── Pool mode: transaction
                    ├── Max client conn: 100
                    ├── Default pool size: 25
                    ├── Reserve pool size: 5
                    └── Min pool size: 5
```

### Data Flow Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Transactional** | ACID writes to operational DB | Creating an opportunity |
| **Eventual consistency** | Async read model updates | Search index after company update |
| **Event sourcing** | Full audit trail via event stream | Entity resolution merge history |
| **CQRS** | Separate read/write models | Pipeline analytics from warehouse |
| **Stream processing** | Real-time aggregation | Pipeline value from Kafka → Redis |
| **Batch ETL** | Scheduled warehouse refresh | Daily cube materialization |

## 4.3 Event Bus

### Current State: In-memory Event Runtime (Wave 1-2)

- In-process event bus
- Simple subscriber list
- No persistence
- No replay capability

### Target State: Apache Kafka (Wave 3, Sprint 11)

- 3-broker cluster
- Avro schema registry
- Consumer groups with offset management
- Dead letter queue with retry
- Configurable retention (7-90 days)

### Migration Strategy: Dual-Run

```
Phase 1: Event Runtime + Kafka (both publishing)
Phase 2: Kafka primary, Event Runtime mirror
Phase 3: Kafka only, Event Runtime decommissioned
```

**File reference:** `docs/wave-3/05-KAFKA_EVENT_BUS.md`

## 4.4 Monitoring

### Current Stack

| Component | Purpose |
|-----------|---------|
| **Prometheus** | Metrics collection (pulls from all services) |
| **Grafana** | Visualization and dashboards |
| **Healthchecks** | Per-service health endpoints |

### Dashboards (Planned for Wave 3)

| Dashboard | Panels |
|-----------|--------|
| RAG Pipeline | Ingestion rate, embedding latency, retrieval p95, cache hit ratio, citation accuracy |
| Kafka Cluster | Broker health, consumer lag, produce/consume rate, DLQ count |
| Workflow Engine | Active executions, success rate, failure breakdown, SLA compliance |
| Analytics | Warehouse query performance, cube freshness, ETL health |
| Wave 3 Overview | All services health, cost tracking, error rate |

### Alert Rules (Planned)

| Alert | Condition | Severity |
|-------|-----------|----------|
| RAG latency high | p95 > 2s for 5 min | Warning |
| Citation accuracy low | < 85% for 30 min | Critical |
| Kafka consumer lag | > 100,000 for 5 min | Critical |
| Kafka broker down | Offline for 1 min | Critical |
| Workflow failure | > 10% for 15 min | Warning |

## 4.5 CI/CD

### Pipeline (GitHub Actions)

```
PR → Lint (ruff/mypy/eslint) → Test (pytest/jest) → Architecture Compliance
  → Build (Docker) → Deploy (Staging) → Smoke Tests → Release Gate
```

The CI pipeline is triggered on every PR and push to `main`. It runs the following stages in order:

**Stage 1 — Lint & Type Check:**
- `ruff check .` (Python: import sorting, code style, security)
- `mypy backend/` (Python: type correctness)
- `eslint frontend/` (TypeScript: code quality)
- `tsc --noEmit` (TypeScript: type checking)
- `pre-commit run --all-files` (consistency checks)

**Stage 2 — Test:**
- `pytest backend/tests/` (Python: unit + integration)
- `jest frontend/` (TypeScript: unit + component)
- Coverage threshold: 85% unit, 70% integration

**Stage 3 — Architecture Compliance:**
- `pwsh scripts/arch-compliance.ps1 -JsonOnly`
- Threshold: overall ≥ 95%

**Stage 4 — Build:**
- `docker compose build backend frontend`
- Image tags: `{branch}-{sha}` for staging, `v{semver}` for release

**Stage 5 — Deploy (Staging):**
- Docker Compose deployment to staging environment
- Database migrations run automatically
- Smoke tests verify health endpoints

### Pre-commit Hooks

Configured via `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy]
```

Run manually: `pre-commit run --all-files`

### Quality Gates

| Gate | Requirement | Verification Method |
|------|-------------|-------------------|
| Security | No auth gaps; no secrets in code | Security audit script + manual review |
| Architecture | Compliance ≥ 95% | `scripts/arch-compliance.ps1` |
| Performance | All endpoints within budget | `scripts/perf-baseline.ps1` |
| Testing | Unit ≥ 85%, Integration ≥ 70% | `scripts/coverage-runner.ps1` |
| CI/CD | Docker builds, migrations, lint pass | GitHub Actions status |
| Documentation | README, CHANGELOG, API docs updated | Manual review |
| Rollback | Migration reversible; rollback plan documented | Release checklist |

### Release Process

```
1. Feature complete → Code freeze
2. Run full test suite + compliance check
3. Deploy to staging → Smoke tests
4. Architecture Review Board sign-off
5. Security Review sign-off
6. Performance Review sign-off
7. Tag release (v{semver})
8. Deploy to production (gradual rollout)
9. Monitor for 24 hours
10. Announce to team
```

### Rollback Procedure

```bash
# 1. Revert database migration
docker compose exec postgres psql -U salesos -d salesos -c "SELECT migrate_down('{migration_id}')"

# 2. Deploy previous Docker image
export IMAGE_TAG=v0.5.0
docker compose -f docker-compose.prod.yml up -d

# 3. Verify health
curl https://your-domain/health

# 4. Notify team
```

**File reference:** `RELEASE_GATES.md` | `scripts/` | `.github/workflows/`

---

# Part 5: Architecture Decisions

> **قرارات معمارية** — الأساس المنطقي لكل خيار والمفاضلات

## 5.1 Wave 2 ADRs

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Opportunity storage | First-class `opportunities` table | Opportunity has its own lifecycle |
| NBA storage | `opportunity_features` table | Reuses Feature Store caching & versioning |
| NBA computation | Event-driven + Scheduled | Immediate recompute + idle detection |
| Activity model | Reuse Activity Runtime | Zero new infrastructure |
| Workspace architecture | `createWorkspaceProvider` per workspace | Consistent with Wave 1 |
| Permissions | Extended `opportunity.*` + `nba:*` | No new permission framework |
| AI reasoning | Hybrid rule + AI | Graceful degradation without AI key |

## 5.2 Wave 3 ADRs

### ADR-001: Vector Store — pgvector

**Choice:** pgvector (PostgreSQL extension) over Pinecone, Weaviate, Qdrant
**Rationale:** Zero new infrastructure, transactional consistency, team familiarity, hybrid search support
**Tradeoff:** Performance degrades beyond 10M vectors; HNSW index uses ~2GB RAM per 1M vectors

### ADR-002: Embedding Model — Self-Hosted E5

**Choice:** `intfloat/multilingual-e5-large` (self-hosted) over Cohere/OpenAI APIs
**Rationale:** Arabic quality, zero recurring cost, data sovereignty, 1024-dimension balance
**Tradeoff:** Requires 4 vCPU + 8GB RAM instance; ~50ms inference latency

### ADR-003: Event Bus — Apache Kafka

**Choice:** Kafka over RabbitMQ, SQS, Redis Streams
**Rationale:** Event sourcing support, exactly-once semantics, consumer groups, scalability
**Tradeoff:** Operational overhead (3 brokers), ~$330/mo additional cost, team training needed

### ADR-004: Workflow Engine — Custom DAG

**Choice:** Custom lightweight DAG engine over Temporal, Airflow, Camunda
**Rationale:** Sales-specific UX, no additional infrastructure, direct NBA/CRM integration
**Tradeoff:** 3 weeks development time, limited features vs Temporal

### ADR-005: Data Warehouse — Separate PostgreSQL

**Choice:** Separate PostgreSQL instance over ClickHouse, BigQuery
**Rationale:** Team familiarity, sufficient for Wave 3 (100-500 GB), star schema suitable
**Tradeoff:** Not ideal for heavy OLAP; may need ClickHouse migration in Wave 4

### ADR-006: LLM — GPT-4o-mini Primary

**Choice:** GPT-4o-mini (primary) + GPT-4o (complex) over Claude, self-hosted Llama
**Rationale:** 20x cheaper than GPT-4o, good Arabic support, tiered routing
**Tradeoff:** External API dependency, ~$200-300/mo cost, fallback needed

### ADR-007: Real-Time Analytics — Kafka → Redis → WebSocket

**Choice:** Kafka → Stream Processor → Redis → WebSocket over direct DB polling, SSE
**Rationale:** Low latency (< 100ms), Kafka integration, separation from batch ETL
**Tradeoff:** Limited to 5-10 critical metrics; additional streaming component

## 5.3 DDD ADRs

### ADR-DDD-01: Aggregates are Consistency Boundaries
**Decision:** Aggregates define transactional consistency. Changes to an aggregate are atomic. Cross-aggregate changes use eventual consistency via domain events.

### ADR-DDD-02: Event Sourcing for Entity Resolution Only
**Decision:** Entity Resolution uses event sourcing (full audit trail). All other contexts use ORM + audit logging.

### ADR-DDD-03: Domain Events via Kafka
**Decision:** All domain events published to Kafka topics. Each context has its own topic. Avro-serialized with Schema Registry.

### ADR-DDD-04: Read Models Separated from Write Models
**Decision:** CQRS pattern — write models are domain aggregates, read models are optimized for queries. Eventual consistency acceptable.

**File reference:** `docs/wave-3/07-ARCHITECTURE_DECISIONS.md` | `docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md` | `backend/docs/adr/`

---

# Part 6: SDK & Extension Guide

> **دليل SDK والإضافة** — كيفية بناء وإضافة وظائف جديدة

## 6.1 Widget SDK v1.0 (Frozen)

**Status:** 🧊 Feature Freeze since 2026-07-10

### Creating a New Widget

```typescript
// 1. Start from WidgetTemplate/
// 2. Decide: createWidget() or createDashboardWidget()
// 3. Implement Container/View pattern
// 4. Add contract tests
// 5. Add accessibility (WCAG AA minimum)
```

### Mandatory Requirements

- [ ] Uses `createWidget()` or `createDashboardWidget()` from SDK
- [ ] Container/View pattern: `*Container.tsx` + `*View.tsx`
- [ ] No cross-domain imports
- [ ] No localStorage for business data
- [ ] Uses `lib/api.ts` for all HTTP calls
- [ ] Uses Decision Platform for scoring/reasoning
- [ ] Contract tests with `describeWidgetContract()`
- [ ] Covers 4 states: ready, loading, degraded, error
- [ ] WCAG AA compliant
- [ ] Dark mode support
- [ ] RTL support

### Exception Process

Any change to the SDK requires:
1. New ADR proving a genuine gap discovered by a new widget
2. Architecture Review Board approval
3. Update `REFERENCE_WIDGET_GUIDE.md`
4. Update all existing widgets
5. Update contract tests

## 6.2 Adding a New Domain

### Backend

```
backend/domains/{domain}/
├── __init__.py
├── models.py         # Domain entities + value objects
├── repository.py     # Repository interface
├── service.py        # Application service
├── events.py         # Domain events
├── handlers.py       # Event handlers/subscribers
└── tests/
    └── test_{domain}.py
```

### Frontend

```
frontend/src/features/{domain}/
├── _providers/       # Context providers
├── widgets/          # Widget implementations
│   └── {WidgetName}/
│       ├── {WidgetName}Container.tsx
│       ├── {WidgetName}View.tsx
│       ├── index.ts
│       └── __tests__/
├── hooks/            # Custom hooks
├── lib/              # Domain-specific utilities
└── index.ts          # Public API
```

### Platform Kernel Registration

```typescript
// 1. Define contracts in packages/platform/contracts/{domain}/
// 2. Register in kernel/registry.ts
// 3. Add permissions to shared/permissions/
// 4. Add feature flags to shared/feature-flags/
// 5. Add event handlers to shared/events/
```

### Cross-Domain Communication

```typescript
// ✅ Correct: Publish event, let other domains subscribe
await eventBus.emit({
  type: 'domain.action_performed',
  data: { entityId, tenantId }
})

// ❌ Wrong: Direct import from another domain
import { something } from '../other-domain/'
```

## 6.3 Public API Conventions

- RESTful endpoints: `GET/POST/PUT/DELETE /{domain}/{id}`
- All endpoints require auth: `Authorization: Bearer <token>`
- Pagination: `?page=1&page_size=20` (returns `{ items, total, page, page_size }`)
- Error format: `{ error: { code, message, details } }`
- Bilingual support: Accept `Accept-Language: ar-SA` header
- Versioning: URL prefix `/v1/{domain}/...`

---

# Appendices

> **ملاحق** — مراجع سريعة وقوائم شاملة

## Appendix A: API Endpoint Registry

### Identity & Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/login` | User login |
| POST | `/v1/auth/register` | User registration |
| POST | `/v1/auth/refresh` | Refresh token |
| POST | `/v1/auth/logout` | User logout |
| GET | `/v1/auth/me` | Current user info |
| GET | `/v1/tenants` | List tenants |
| POST | `/v1/tenants` | Create tenant |

### Company Intelligence

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/companies` | List companies |
| GET | `/v1/companies/{id}` | Get company |
| POST | `/v1/companies` | Create company |
| PUT | `/v1/companies/{id}` | Update company |
| GET | `/v1/companies/{id}/branches` | Get branches |
| GET | `/v1/companies/{id}/licenses` | Get licenses |
| GET | `/v1/companies/{id}/contacts` | Get contacts |
| POST | `/v1/enrich` | Enrich company data |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/search` | Search entities |
| GET | `/v1/search/suggest` | Autocomplete suggestions |

### CRM / Revenue Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/opportunities` | List opportunities |
| POST | `/v1/opportunities` | Create opportunity |
| GET | `/v1/opportunities/{id}` | Get opportunity |
| PUT | `/v1/opportunities/{id}` | Update opportunity |
| POST | `/v1/opportunities/{id}/stage` | Change stage |
| GET | `/v1/opportunities/{id}/nba` | Next best action |
| POST | `/v1/opportunities/{id}/nba/refresh` | Refresh NBA |
| POST | `/v1/opportunities/{id}/nba/feedback` | Record NBA feedback |
| GET | `/v1/pipeline` | Pipeline overview |
| GET | `/v1/pipeline/analytics` | Pipeline analytics |
| GET | `/v1/meetings` | List meetings |
| POST | `/v1/meetings` | Create meeting |
| GET | `/v1/meetings/{id}` | Get meeting intelligence |
| GET | `/v1/emails` | List emails |
| POST | `/v1/emails/sync` | Sync emails (Gmail/Outlook) |
| GET | `/v1/revenue/dashboard` | Revenue dashboard |
| GET | `/v1/revenue/goals` | Revenue goals |
| POST | `/v1/revenue/goals` | Create goal |

### AI / RAG (Wave 3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/rag/query` | Query RAG pipeline |
| POST | `/v1/rag/ingest` | Ingest document |
| GET | `/v1/rag/documents/{id}` | Get document status |

### Workflow (Wave 3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/workflows` | List workflows |
| POST | `/v1/workflows` | Create workflow |
| PUT | `/v1/workflows/{id}` | Update workflow |
| POST | `/v1/workflows/{id}/activate` | Activate workflow |
| GET | `/v1/workflows/{id}/executions` | Execution history |

### Analytics (Wave 3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/reports` | List reports |
| POST | `/v1/reports` | Create custom report |
| GET | `/v1/reports/{id}/export` | Export report (PDF/CSV) |
| POST | `/v1/reports/schedule` | Schedule report delivery |

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/metrics` | Prometheus metrics |

### Runtime Endpoints (Security Notice)

**Note:** 7 runtime routers were found without authentication in the Production Audit (P6-C01). These are being remediated:

| Router | Endpoints | Status |
|--------|-----------|--------|
| UX Runtime | `/nav/*`, `/layout/*`, `/commands/*`, `/notifications/*`, `/theme/*`, `/viewer/*` | 🔴 Needs auth |
| Capability Framework | `/capabilities/*`, `/nav/*`, `/search/*` | 🔴 Needs auth |
| Action Engine | `/actions/*` (includes `/execute`) | 🔴 Needs auth |
| Extension API | `/hooks/*` | 🔴 Needs auth |
| Form Engine | `/generate`, `/*/validate` | 🔴 Needs auth |
| Plugin Sandbox | `/plugins/*` | 🔴 Needs auth |
| UI Schema Engine | `/viewer/*` | 🔴 Needs auth |

**File reference:** `backend/runtime/` | `docs/PRODUCTION_AUDIT_REPORT.md`

## Appendix B: Event Registry

### Domain Events

| Event | Version | Producer | Consumers | Schema |
|-------|---------|----------|-----------|--------|
| `company.created` | v1 | Company Service | Search, NBA, Analytics | [Avro] |
| `company.updated` | v1 | Company Service | Search, Knowledge Graph | [Avro] |
| `company.status_changed` | v1 | Company Service | CRM, Alerts | [Avro] |
| `company.merged` | v1 | Entity Resolution | Search, Analytics | [Avro] |
| `company.scored` | v1 | Scoring Engine | NBA, DNA | [Avro] |
| `company.signal_detected` | v1 | Signal Runtime | NBA, Company Intelligence | [Avro] |
| `opportunity.created` | v1 | Opportunity Service | NBA, Workflow, Search, Pipeline | [Avro] |
| `opportunity.stage_changed` | v1 | Opportunity Service | NBA, Workflow, Pipeline, Analytics | [Avro] |
| `opportunity.won` | v1 | Opportunity Service | Analytics, Revenue | [Avro] |
| `opportunity.lost` | v1 | Opportunity Service | Analytics, Revenue | [Avro] |
| `activity.logged` | v1 | Activity Service | NBA, Timeline, Analytics | [Avro] |
| `deal_health.changed` | v1 | Deal Health Service | NBA, Workflow, Alerting | [Avro] |
| `nba.generated` | v1 | NBA Engine | Analytics, Audit | [Avro] |
| `nba.feedback.recorded` | v1 | NBA Engine | Learning Engine, Analytics | [Avro] |
| `workflow.started` | v1 | Workflow Engine | Analytics, Monitoring | [Avro] |
| `workflow.completed` | v1 | Workflow Engine | Analytics, Monitoring | [Avro] |
| `workflow.failed` | v1 | Workflow Engine | Alerting, Analytics | [Avro] |

### Event Schema (Standard)

```json
{
  "event_id": "uuid",
  "event_type": "domain.action_performed",
  "event_version": 1,
  "aggregate_id": "uuid",
  "aggregate_type": "EntityName",
  "tenant_id": "uuid",
  "occurred_at": "ISO8601",
  "data": {},
  "metadata": {
    "correlation_id": "uuid",
    "causation_id": "uuid",
    "user_id": "uuid"
  }
}
```

**File reference:** `docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md` (Section 12)

## Appendix C: Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | Yes | `salesos` | PostgreSQL user |
| `POSTGRES_PASSWORD` | **Yes** | — | PostgreSQL password |
| `POSTGRES_DB` | No | `salesos` | PostgreSQL database name |
| `NEO4J_USER` | No | `neo4j` | Neo4j user |
| `NEO4J_PASSWORD` | Yes | — | Neo4j password |
| `REDIS_URL` | Yes | `redis://redis:6379` | Redis connection string |
| `KAFKA_BOOTSTRAP_SERVERS` | No | `kafka:9092` | Kafka bootstrap servers |
| `JWT_SECRET` | **Yes** | — | JWT signing secret (use `openssl rand -hex 32`) |
| `JWT_ALGORITHM` | No | `RS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `API_URL` | Yes | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Frontend API URL (public) |
| `OPENAI_API_KEY` | No | — | OpenAI API key (AI features) |
| `SENTRY_DSN` | No | — | Sentry error tracking DSN |
| `DOMAIN` | No | `localhost` | Production domain (Caddy TLS) |
| `BACKUP_RETENTION_DAYS` | No | `7` | Backup retention period |
| `S3_BUCKET` | No | — | S3 bucket for backups |
| `GRAFANA_PASSWORD` | Yes | — | Grafana admin password |
| `NOTIFY_WEBHOOK` | No | — | Notification webhook URL |

### Feature Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `nba-enabled` | tier | `internal` | NBA engine availability |
| `pipeline-intelligence` | tier | `beta` | Pipeline Intelligence workspace |
| `meeting-intelligence` | tier | `internal` | Meeting Intelligence |
| `email-intelligence` | tier | `internal` | Email Intelligence |
| `rag-pipeline` | tier | `internal` | RAG pipeline (Wave 3) |
| `workflow-engine` | tier | `internal` | Workflow automation (Wave 3) |
| `analytics-reporting` | tier | `internal` | Analytics & reporting (Wave 3) |
| `enterprise-sso` | tier | `enterprise` | SSO (Wave 4) |

**File reference:** `.env.example` | `.env.production.template`

## Appendix D: Migration History

### v0.1.0 — Company Intelligence Foundation
- Initial PostgreSQL schema
- Company CRUD + search
- Government data ingestion (Balady, Taqeem)

### v0.2.0 — Data Fabric
- Entity Resolution pipeline
- Feature Store
- Knowledge Graph (Neo4j)
- Hybrid Search (full-text + semantic)

### v0.3.0 — Dashboard & UI
- Widget SDK v1.0
- Dashboard workspace
- Design system (`@salesos/design-language`)
- Foundation components (22)

### v0.4.0 — Production Stabilization (Sprint 0.5)
- Password reset fix (no leak)
- Auth on unprotected routes
- Secrets cleanup
- Refresh Token Architecture
- Architecture violation fixes
- Security headers
- Docker validation

### v0.5.0 — Sprint 1: Product Foundation
- 22 Foundation components (a11y-optimized)
- 15 `@salesos/ui` restyled with MUHIDE tokens
- Design language 16 files, all exported
- Tailwind theme with MUHIDE palette
- Global CSS with semantic tokens, dark mode, RTL
- 340+ hardcoded color violations remediated

### v0.6.0 — Wave 2: Revenue Execution Platform
- NBA Engine (Decision Pipeline, 12 stages)
- Opportunity Workspace (CRUD, lifecycle, deals)
- Pipeline Intelligence (Kanban, Analytics, Health Map)
- Meeting Intelligence (Pre/During/Post)
- Email Intelligence (Sentiment, Topics, Urgency)
- Revenue Workspace (Executive Summary)
- 8 new database tables
- 12+ NBA API endpoints
- Platform Kernel contracts

### v0.7.0+ — Wave 3: AI & Automation (in development)
- Sprint 10: RAG Pipeline + Vector Store
- Sprint 11: Kafka Event Bus
- Sprint 12: Workflow Automation
- Sprint 13: Analytics & Reporting
- Sprint 14: Integration & Polish

**File reference:** `CHANGELOG.md` | `docs/DEPLOYMENT_REPORT_v0.7.md` | `docs/DEPLOYMENT_REPORT_v0.8.md`

## Appendix E: Architecture Health System

The Architecture Health system is a living measurement framework that tracks the quality of every domain across multiple dimensions. It feeds into the Engineering Dashboard and blocks releases if thresholds are breached.

### Health Dimensions

| Dimension | Weight | Measured By |
|-----------|--------|-------------|
| **Container/View Pattern** | 20% | File system scan: every widget directory has `*Container.*` + `*View.*` |
| **No Cross-Domain Imports** | 20% | `import` statement analysis across `features/` directories |
| **Repository Pattern** | 15% | Domain services depend on repository interfaces, not DB directly |
| **No localStorage for Business** | 10% | Scans for `localStorage.setItem` with business entity names |
| **Centralized API Client** | 10% | Detects direct `axios.*()` or `fetch()` outside `lib/api.ts` |
| **Decision Platform Scoring** | 15% | Verifies scoring widgets import from Decision Platform |
| **No Inline Scoring in Views** | 10% | View components never compute scores directly |

### Automation Script

```powershell
# scripts/arch-compliance.ps1
# Returns JSON with per-domain scores and overall compliance
pwsh scripts/arch-compliance.ps1 -JsonOnly
```

### CI Gate Configuration

```yaml
# .github/workflows/arch-compliance.yml
- name: Architecture Compliance Check
  run: pwsh scripts/arch-compliance.ps1 -JsonOnly > reports/arch-compliance.json
- name: Check Threshold
  run: |
    $report = Get-Content reports/arch-compliance.json | ConvertFrom-Json
    if ($report.overall_compliance -lt 95.0) {
      throw "Architecture compliance $($report.overall_compliance)% below 95%"
    }
```

### Nightly Full Scan

Every night at 02:00 AST, a full compliance scan runs and writes to `reports/arch-compliance-report.json`. If compliance drops below 90%, the Architecture Review Board is notified automatically.

## Appendix F: Performance Budgets

### API Endpoints

| Endpoint | p50 | p95 | p99 | Budget | Status |
|----------|-----|-----|-----|--------|--------|
| `GET /companies/{id}` | 45ms | 120ms | 250ms | 200ms | 🟢 |
| `POST /search` | 180ms | 450ms | 900ms | 500ms | 🟡 |
| `GET /timeline` | 90ms | 300ms | 600ms | 300ms | 🟡 |
| `POST /enrich` | 2.5s | 8s | 15s | 5s | 🔴 |

### Decision Platform

| Operation | Budget | Status |
|-----------|--------|--------|
| Decision evaluation (simple) | < 100ms | 🟢 |
| Decision evaluation (complex) | < 500ms | 🟡 |
| Recommendation generation | < 200ms | 🟢 |
| Score computation | < 50ms | 🟢 |
| Evidence retrieval | < 200ms | 🟡 |

### NBA Engine

| Stage | Budget | Violation Action |
|-------|--------|-----------------|
| Normalization | < 50ms | Log warning |
| Business Rules | < 20ms | Log warning |
| Scoring | < 30ms | Log warning |
| AI Reasoning | < 2000ms | Timeout + fallback |
| Risk Assessment | < 50ms | Log warning |
| **Total (rule-only)** | **< 200ms** | Error metric |
| **Total (with AI)** | **< 3000ms** | Timeout + fallback |

### Wave 3 Budgets

| Operation | Budget | Violation Action |
|-----------|--------|-----------------|
| RAG Retrieval (p95) | < 200ms | Alert |
| Embedding Generation | < 500ms per doc | Alert |
| Kafka Event Latency | < 100ms end-to-end | Alert |
| Workflow Execution Start | < 1s from trigger | Alert |
| Warehouse Query (standard) | < 2s | Optimize cube |
| Cube Refresh (full) | < 30 min | Partition tables |
| PDF Export (1000 rows) | < 10s | Queue async |

### Application

| Metric | Budget |
|--------|--------|
| Page load (initial) | < 2s |
| Page load (subsequent) | < 500ms |
| Widget render | < 200ms |
| API response (p50) | < 100ms |
| API response (p99) | < 500ms |
| NBA acceptance rate | > 60% |
| Opportunity to Close | -30% avg days |
| Meeting prep time | -50% |

**File reference:** `PERFORMANCE_BASELINE.md` | `docs/PERFORMANCE_OPTIMIZATION_REPORT.md`

---

> **نهاية كتاب معمارية SalesOS**
>
> *هذا وثيقة حية — تحدث مع كل إصدار وكل قرار معماري*
>
> **آخر تحديث:** 2026-07-11
> **الإصدار:** v1.0
> **المراجعة التالية:** Wave 3 Complete (est. 2026-10)
> **المسؤول:** Architecture Review Board
