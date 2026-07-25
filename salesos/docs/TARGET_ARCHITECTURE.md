# SalesOS — TARGET ARCHITECTURE

> **Sprint 0 Deliverable: Architecture Reconciliation**
> This document captures the **approved target architecture** as defined by the ratified Engineering Constitution, ADRs, Project Bible, Master Blueprint, and SES.
> Date: 2026-07-17 | Classification: Confidential
> Status: ✅ References ratified documents only

---

## Table of Contents

1. [Authority Hierarchy](#1-authority-hierarchy)
2. [Architecture Vision](#2-architecture-vision)
3. [Four-Layer Platform Model](#3-four-layer-platform-model)
4. [Domain Boundaries (Target)](#4-domain-boundaries-target)
5. [Pattern Mandates](#5-pattern-mandates)
6. [Widget SDK Target State](#6-widget-sdk-target-state)
7. [Decision Platform Target State](#7-decision-platform-target-state)
8. [Quality Gates (Target)](#8-quality-gates-target)
9. [Frozen Interfaces Register](#9-frozen-interfaces-register)
10. [Performance Budgets (Target)](#10-performance-budgets-target)
11. [Build Order (Approved)](#11-build-order-approved)
12. [Architecture Compliance Rules (Target)](#12-architecture-compliance-rules-target)

---

## 1. Authority Hierarchy

The approved architecture is defined by these documents in order of authority:

| Rank | Document | Source | Status |
|------|----------|--------|--------|
| 1 | **PROJECT_BIBLE.md** v2.0.0 | `docs/PROJECT_BIBLE.md` | Ratified |
| 2 | **ENGINEERING_CONSTITUTION.md** v1.0 | `engineering-os/ENGINEERING_CONSTITUTION.md` | Ratified |
| 3 | **MASTER_BLUEPRINT.md** V5.0 | `docs/MASTER_BLUEPRINT.md` | Published |
| 4 | **ARCHITECTURE_BOOK.md** v1.0 | `salesos/docs/ARCHITECTURE_BOOK.md` | Published |
| 5 | **SALESOS_DOMAIN_DRIVEN_DESIGN.md** v1.0 | `salesos/docs/SALESOS_DOMAIN_DRIVEN_DESIGN.md` | Published |
| 6 | **DOMAIN_MAP.md** v1.0 | `docs/DOMAIN_MAP.md` | Published |
| 7 | **ADRs** (ADR-001, ADR-002, ADR-003, ADR-0030, ADR-0031) | `engineering-os/adr/` + `docs/adr/` | Accepted |
| 8 | **ENGINEERING_IMPLEMENTATION_SPEC.md** | `engineering-os/ENGINEERING_IMPLEMENTATION_SPEC.md` | Published |
| 9 | **DECISION_PLATFORM_ARCHITECTURE.md** | `salesos/docs/DECISION_PLATFORM_ARCHITECTURE.md` | Published |
| 10 | **RUNTIME_ARCHITECTURE.md** | `salesos/docs/RUNTIME_ARCHITECTURE.md` | Published |

---

## 2. Architecture Vision

### 2.1 Core Thesis (PROJECT_BIBLE §1)

SalesOS is **not a CRM**. CRM is a feature, not the product. SalesOS is a **Business Intelligence Operating System (BIOS)** where:

1. Every company interaction generates intelligence automatically
2. Every decision is informed by data, not intuition
3. Every workflow is automated without code
4. Every team member has AI assistance built into their workflow
5. Every insight respects data sovereignty and privacy

### 2.2 Platform Philosophy (MASTER_BLUEPRINT §2)

**"Everything is a Platform"** — SalesOS is not a monolithic application. It is a platform of platforms:

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

### 2.3 Revenue Architecture (PROJECT_BIBLE §1, MASTER_BLUEPRINT §1)

- **Not a CRM.** CRM is one capability among many.
- **BIOS** = Data + Intelligence + Automation + Developer + Marketplace
- **Monetization**: SaaS tiers (Free → Enterprise) + Marketplace (20% rev share) + Data Enrichment + Knowledge Packs
- **TAM**: 100M+ companies, 2,000+ enterprise customers, $50M+ ARR target by Year 3

---

## 3. Four-Layer Platform Model

(Per MASTER_BLUEPRINT V5.0 §2.2)

| Layer | Name | Description | Maturity Target |
|-------|------|-------------|-----------------|
| Layer 4 | **Applications** | End-user experiences, UIs, dashboards | GA ready |
| Layer 3 | **Business Capabilities** | Domain-specific products | GA ready |
| Layer 2 | **Platform Services** | Horizontal infrastructure capabilities | GA ready |
| Layer 1 | **Kernel** | Frozen, foundational, immutable | ✅ Frozen |

### 3.1 Layer 1 — Kernel (Frozen)

(Per MASTER_BLUEPRINT §3)

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

**Target characteristics:**
- **Replaceability**: Every kernel capability replaceable without changing contracts
- **SDK Sovereignty**: No module bypasses SDK for cross-cutting concerns
- **Domain Events**: Every change generates CloudEvents 1.0
- **Frozen Interface Protection**: Breaking requires formal ADR

### 3.2 Layer 2 — Platform Services

(Per MASTER_BLUEPRINT §4)

| Service | Target State | Priority |
|---------|-------------|----------|
| Data Fabric | Unified ingestion, transformation, storage | P0 |
| Feature Store | Entity features with real-time computation | P1 |
| Knowledge Graph | Neo4j-based relationship intelligence | P1 |
| Revenue Graph | Revenue data model + analytics | P1 |
| Semantic Cache | AI response caching | P2 |
| Entity Resolution | Golden record merging pipeline | P0 |
| Workflow Engine | Visual workflow builder + execution | P0 |
| Notifications | Real-time push + email templates | P1 |

### 3.3 Layer 3 — Business Capabilities

(Per MASTER_BLUEPRINT §5)

| Capability | Target State | Priority |
|-----------|-------------|----------|
| Company Intelligence | Full 360° company profiles | P0 |
| Opportunity Management | Pipeline + deal management | P0 |
| Pipeline Intelligence | AI-powered pipeline analytics | P0 |
| Forecast | ML-based revenue forecasting | P1 |
| Analytics & KPIs | Dashboards with trend indicators | P1 |
| GTM Intelligence | Go-to-market intelligence | P2 |
| Customer Success | Churn prediction + health scoring | P1 |

### 3.4 Layer 4 — Applications

(Per MASTER_BLUEPRINT §6)

| Application | Target State | Priority |
|------------|-------------|----------|
| Executive Dashboard | Cross-domain intelligence workspace | P0 |
| Company 360 | Full company profile with all tabs | P0 |
| Employee 360 | Employee intelligence workspace | P1 |
| Deal Room | Collaborative deal workspace | P1 |
| AI Copilot | Conversational AI assistant | P0 |
| Search | Universal cross-domain search | P0 |
| Admin Portal | System administration | P1 |

---

## 4. Domain Boundaries (Target)

(Per DOMAIN_MAP.md, SALESOS_DOMAIN_DRIVEN_DESIGN.md, ARCHITECTURE_BOOK §3)

### 4.1 13 Bounded Contexts

| # | Context | Type | Key Aggregate | Status Target |
|---|---------|------|-------------|---------------|
| BC-01 | Identity & Access | Generic | Tenant, User | ✅ Frozen |
| BC-02 | Company Intelligence | **Core** | Company | ✅ Production |
| BC-03 | Entity Resolution | **Core** | GoldenRecord | ✅ Production |
| BC-04 | CRM | Supporting | Opportunity | ✅ Production |
| BC-05 | Activity Engine | Supporting | Activity | ✅ Production |
| BC-06 | Scoring Engine | Supporting | CompanyScore | ✅ Production |
| BC-07 | Company DNA | Supporting | DnaProfile | 🟡 In Development |
| BC-08 | Knowledge Graph | **Core** | GraphNode | 🟡 In Development |
| BC-09 | AI Platform | **Core** | AiQuery | 🟡 In Development |
| BC-10 | Workflow Engine | Generic | WorkflowDefinition | 🔴 Not Started |
| BC-11 | Marketplace | Generic | PluginListing | 🟡 In Development |
| BC-12 | Data Lake | Supporting | DataPipeline | 🔴 Not Started |
| BC-13 | Billing | Generic | Subscription | 🔴 Not Started |

### 4.2 Context Relationships (Target)

- **Conformist**: Most contexts consume-from Kernel (Identity, Company, Search, Timeline)
- **Partnership**: Entity Resolution ↔ Company Intelligence (bidirectional)
- **Open-Host**: AI Platform + Workflow Engine (query all)
- **Separate-Way**: Marketplace, Billing (independent lifecycles)

### 4.3 Context Mapping Rules

(Per SALESOS_DOMAIN_DRIVEN_DESIGN.md)

1. **Aggregates** are consistency boundaries — cross-aggregate changes via events only
2. **Event sourcing** for Entity Resolution only; ORM + audit logging for all other contexts
3. **Domain events** via Kafka (Avro + Schema Registry) — target state
4. **CQRS**: Read models separate from write models
5. **Repository Pattern**: Every domain service depends on repository interfaces, never on infrastructure

---

## 5. Pattern Mandates

(Per ENGINEERING_CONSTITUTION, PROJECT_BIBLE §4, ARCHITECTURE_BOOK §1.2)

### 5.1 Mandatory Patterns

| Pattern | Mandate | Reference | Enforcement |
|---------|---------|-----------|-------------|
| Repository Pattern | Every domain service depends on repository interfaces | Constitution Art. 3.3 | CI compliance check |
| Container/View | Every widget has data/rendering separation | Constitution Art. 9.1 | Widget contract tests |
| No Cross-Domain Imports | Features never import from other features | Constitution Art. 3.2 | CI compliance check |
| Centralized API Client | All HTTP via `lib/api.ts` | DF-4.2 | Compliance script |
| Decision Platform for Scoring | All scoring via `useDecision()` or ScoringEngine | DP-5.1 | Compliance script |
| No Inline Scoring in Views | Views never compute scores directly | DP-5.2 | Compliance script |
| No localStorage for Business Data | Business entities use API-backed persistence | DF-4.1 | Compliance script |

### 5.2 Prohibited Patterns

| Anti-Pattern | Reason | Reference |
|-------------|--------|-----------|
| Direct axios calls outside `api.ts` | Bypasses auth interceptors, error handling | Project Bible §12.2 |
| Inline scoring in View components | Violates Container/View separation | Constitution Art. 9.1 |
| Cross-domain imports | Violates bounded context isolation | Constitution Art. 3.2 |
| `any` types in production code | Type safety violation | Project Bible §4 |
| Files > 600 lines | Maintainability | Project Bible §12.2.7 |
| Secrets in source code | Security | Constitution Art. 4.1 |
| unauthenticated endpoints | Security | Constitution Art. 4.2 |

### 5.3 Developer Workflow (Target)

(Per PROJECT_BIBLE §8, IMPLEMENTATION_ROADMAP)

```
Product Goal → Architecture (ADR) → Blueprint → Implementation → QA → Release
```

**No code is written before ADR + Blueprint are complete.**

---

## 6. Widget SDK Target State

(Per ADR-003, ENGINEERING_CONSTITUTION Art. 9, REFERENCE_WIDGET_GUIDE.md)

### 6.1 Frozen API Surface

The following are **frozen** and cannot be modified without new ADR:

| Component | Status |
|-----------|--------|
| `createWidget<T>(config: WidgetConfig<T>)` | 🧊 Frozen |
| `createDashboardWidget<T>(config: DashboardWidgetConfig<T>)` | 🧊 Frozen |
| `WidgetConfig<T>` — type definition | 🧊 Frozen |
| `WidgetData` — type definition | 🧊 Frozen |
| `WidgetState` — type definition (ready, loading, degraded, error) | 🧊 Frozen |
| Widget lifecycle hooks | 🧊 Frozen |
| Widget telemetry contract | 🧊 Frozen |
| Widget permissions contract | 🧊 Frozen |
| Widget feature flag contract | 🧊 Frozen |
| `describeWidgetContract()` — testing utility | 🧊 Frozen |
| All mock utilities for widget testing | 🧊 Frozen |

### 6.2 Mandatory Widget Architecture

(Per ADR-003, Constitution Art. 9.1)

```
WidgetName/
├── WidgetNameContainer.tsx   # Data fetching, business logic, SDK calls
├── WidgetNameView.tsx        # Pure presentational, no side effects
└── index.ts                  # Public exports
```

### 6.3 Mandatory Widget Contract Tests

(Per Constitution Art. 9.2)

```typescript
describeWidgetContract(MyWidget, {
  name: 'MyWidget',
  states: ['loading', 'ready', 'degraded', 'error'],
  permissions: ['view:widget'],
  featureFlag: 'my-widget',
})
```

### 6.4 Single Canonical SDK

The target architecture requires a **single canonical Widget SDK**. Only one `createWidget()` may exist. The SDK must be:

1. The single source of truth for widget creation
2. Feature-frozen (per ADR-003) — new gaps proven by concrete widget needs
3. The only path for widget testing via `describeWidgetContract()`
4. Used by both Dashboard and Workspace contexts

### 6.5 Widget Count target

- Dashboard: 6 widgets
- Company Intelligence: ~10 widgets
- Revenue Execution: ~19 widgets
- Total: 35-40 widgets — all passing contract tests

---

## 7. Decision Platform Target State

(Per ADR-002, DECISION_PLATFORM_ARCHITECTURE.md, ARCHITECTURE_BOOK §4)

### 7.1 Components

| Engine | Responsibility | Target Status |
|--------|---------------|---------------|
| Decision Engine | Orchestrator — receive context, coordinate sub-engines | ✅ Production |
| Rule Engine | Pure deterministic business rules | ✅ Production |
| Scoring Engine | Normalized scores (Company, Opportunity, Intent, Risk) | ✅ Production |
| Evidence Engine | Collect/validate evidence from all sources | ✅ Production |
| Recommendation Engine | Ranked recommendations with primary + alternatives + confidence | ✅ Production |
| Explainability Engine | Answers: Why? Why now? Why this action? What evidence? | ✅ Production |
| Feedback Engine | Captures action outcomes with revenue impact | ✅ Production |
| Learning Engine | Quality trend tracking — no autonomous ML | ⚠️ Partial |

### 7.2 Boundaries (Target)

- NEVER access UI
- NEVER call browser APIs
- NEVER contain presentation logic
- ALWAYS be deterministic when rules apply
- ALWAYS expose evidence and confidence
- Simple decision < 100ms, complex < 500ms
- Score computation < 50ms

### 7.3 DecisionProvider Integration

(Per VIO-105 resolution target)

- Available in **all** feature contexts: Dashboard, Company Intelligence, Revenue Execution
- Used via `useDecision()` hook
- Single source of truth for all decisions, recommendations, and scores

---

## 8. Quality Gates (Target)

(Per ENGINEERING_CONSTITUTION Art. 6, ARCHITECTURE_BOOK §4.5, PROJECT_BIBLE §16)

### 8.1 Pre-Merge Gates

| Gate | Requirement | Verification |
|------|-------------|-------------|
| Security | No auth gaps, no secrets in code | `scripts/security-audit.ps1` |
| Architecture | Compliance ≥ 95% | `scripts/arch-compliance.ps1` |
| Performance | All endpoints within budget | `scripts/perf-baseline.ps1` |
| Testing | Unit ≥ 85%, Integration ≥ 70% | `scripts/coverage-runner.ps1` |
| CI/CD | Docker builds, migrations, lint pass | GitHub Actions |
| Documentation | README, CHANGELOG, API docs updated | Manual check |
| Rollback | Migration reversible; plan documented | Release checklist |

### 8.2 Release Gates (Target)

| Gate | Criteria |
|------|----------|
| Architecture Review | All domain compliance ≥ 95% |
| Code Review | 2 reviewers minimum (1 code + 1 domain) |
| Security Review | Zero critical/high vulnerabilities |
| Performance Review | All p95 within 2x budget |
| QA | 100% test pass rate |
| Documentation | Full doc chain complete |

### 8.3 Target Metrics

| Metric | Target | Source |
|--------|--------|--------|
| Unit Test Coverage | ≥ 85% | Constitution Art. 2.1 |
| Integration Test Coverage | ≥ 70% | ARCHITECTURE_BOOK App. F |
| Architecture Compliance | ≥ 95% | Constitution Art. 2.1 |
| Security Posture | ≥ 9.5/10 | ENGINEERING_DASHBOARD |
| Performance Score | ≥ 9/10 | FINAL_PERFORMANCE_REPORT |
| File Size Limit | ≤ 600 lines | PROJECT_BIBLE §12.2.7 |
| Production Readiness | ≥ 9/10 | ENGINEERING_DASHBOARD |

---

## 9. Frozen Interfaces Register

(Per PROJECT_BIBLE §17 decision log, ADR-003, ARCHITECTURE_BOOK §3)

| Interface | ADR | Frozen Since | Modification Required |
|-----------|-----|-------------|----------------------|
| Identity Domain API contracts | ADR-001 | 2026-07-10 | New ADR + Architecture Review Board |
| Widget SDK v1.0 API surface | ADR-003 | 2026-07-10 | New ADR proving genuine gap + ARB approval |
| `createWidget()` / `createDashboardWidget()` | ADR-003 | 2026-07-10 | New ADR + ARB approval |
| SDK Types | ADR-003 | 2026-07-10 | New ADR + ARB approval |
| Widget Lifecycle / Telemetry / Permissions / Flags | ADR-003 | 2026-07-10 | New ADR + ARB approval |
| `describeWidgetContract()` + mocks | ADR-003 | 2026-07-10 | New ADR + ARB approval |
| Kernel Layer services | MASTER_BLUEPRINT §3 | 2026-07-10 | New ADR + Benchmark + Architecture Review |

**Exception Process**: Changing any frozen interface requires:
1. New ADR proving a genuine gap
2. Architecture Review Board approval
3. Update of REFERENCE_WIDGET_GUIDE.md
4. Update of all existing widgets
5. Update of contract tests

---

## 10. Performance Budgets (Target)

(Per ARCHITECTURE_BOOK Appendix F, DECISION_PLATFORM_ARCHITECTURE.md)

| Endpoint | p50 Target | p95 Target | p99 Target |
|----------|-----------|-----------|-----------|
| GET /companies/{id} | < 50ms | < 100ms | < 200ms |
| POST /search | < 50ms | < 100ms | < 200ms |
| GET /dashboard | < 100ms | < 200ms | < 500ms |
| GET /timeline | < 50ms | < 100ms | < 300ms |
| POST /enrich | < 100ms | < 500ms (async) | < 3s |
| POST /decision/evaluate | < 50ms | < 100ms | < 500ms |
| GET /pipeline/summary | < 50ms | < 100ms | < 200ms |
| Simple decision | < 50ms | < 100ms | < 200ms |
| Complex decision (with AI) | < 500ms | < 1s | < 3s |
| Score computation | < 25ms | < 50ms | < 100ms |
| Widget render | < 100ms | < 200ms | < 500ms |
| Page load (LCP) | < 1.5s | < 2s | < 3s |

**Lighthouse targets**: Performance > 90, Accessibility > 95, Best Practices > 90

---

## 11. Build Order (Approved)

(Per docs/vnext/IMPLEMENTATION_PLAN.md, work-orders/WO-*)

### Phase 0: Platform Stabilization (Sprints 1-2)

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| Sprint 1 | Security & Critical Fixes | Auth gaps closed, middleware body bug fixed, parameterized Cypher |
| Sprint 2 | Infrastructure & Performance | Terraform state, N+1 fixes, pagination for 12+ endpoints, Redis singleton |

### Phase 1: Design System V2 (Sprints 3-4)

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| Sprint 3 | Design System Consolidation | Login migration, missing form components, Badge fix, CSS var standardization |
| Sprint 4 | Design System Expansion | Storybook, a11y assertions, visual regression, EmptyState, Drawer, Breadcrumb |

### Phase 2: Foundation Features (Sprints 5-6)

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| Sprint 5 | Settings & Dashboard | Consolidated Settings UI, tenant settings, widget-level data fetching |
| Sprint 6 | Search & Companies | Keyset pagination, cross-domain search federation, company comparison |

### Phase 3: Intelligence Features (Sprints 7-8)

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| Sprint 7 | Company 360 & Employee 360 | Dedicated Company 360 view, firmographics pipeline, employee 360 page, skills taxonomy |
| Sprint 8 | Knowledge Graph & Signals | Interactive graph explorer, relationship browser, signal detection engine |

### Phase 4: Revenue & Pipeline (Sprints 9-10)

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| Sprint 9 | Pipeline & CRM | Contracts UI, Email intelligence, Proposals, Quotes, Playbooks |
| Sprint 10 | Revenue & Forecast | ML forecasting, pipeline analysis, quota management, territory management |

### Phase 5: AI Platform (Sprints 11-12)

| Sprint | Focus | Key Deliverables |
|--------|-------|-----------------|
| Sprint 11 | Agent Runtime | Decision Engine implementation, Kafka activation |
| Sprint 12 | AI Evaluation | Evaluation framework, prompt registry refinement |

### Phase 6: Enterprise & Scale (Sprints 13-22)

| Sprint | Focus |
|--------|-------|
| 13-14 | Admin Portal & Multi-Tenancy |
| 15-16 | Data Fabric & Connectors |
| 17-18 | Notifications & Real-time |
| 19-20 | Arabic/RTL i18n, Accessibility |
| 21-22 | Performance, Load Testing, Hardening |

---

## 12. Architecture Compliance Rules (Target)

(Per ARCHITECTURE_COMPLIANCE.md, ENGINEERING_CONSTITUTION Art. 3)

### 12.1 Compliance Rules (Weighted)

| # | Rule | Weight | Check Method |
|---|------|--------|-------------|
| ARC-9.1 | Container/View Pattern | 20% | Every widget has `*Container.*` + `*View.*` |
| ARC-3.2 | No Cross-Domain Imports | 20% | `features/` never imports from another `features/*` |
| ARC-3.3 | Repository Pattern | 15% | Domain services depend on repository interfaces, not DB |
| DF-4.1 | No localStorage for Business Data | 10% | Business entities use API-backed persistence |
| DF-4.2 | Centralized API Client | 10% | All HTTP calls go through `lib/api.ts` |
| DP-5.1 | Decision Platform for Scoring | 15% | All scoring/reasoning uses `useDecision()` or ScoringEngine |
| DP-5.2 | No Inline Scoring in Views | 10% | View components never compute scores directly |

### 12.2 Per-Domain Compliance Targets

| Domain | Target | Due |
|--------|--------|-----|
| Identity | 100% | ✅ Achieved |
| Widget SDK | 100% | Sprint 3 (Sprint 0 ADR) |
| Company | 95% | ✅ Achieved |
| Search | 95% | Sprint 2 |
| Scoring | 95% | ✅ Achieved |
| CRM | 95% | Sprint 3 |
| AI | 95% | Sprint 12 |
| Timeline | 95% | Sprint 7 |
| Workflow | 95% | Sprint 11 |
| **OVERALL** | **95%+** | Sprint 12 |

### 12.3 Violation Severity Classification

| Severity | Definition | Resolution SLA |
|----------|-----------|---------------|
| 🔴 Critical | Security vulnerability, data loss, frozen interface violation | Immediate block |
| 🟡 High | Pattern violation, file > 600 lines, missing compliance | 1 Sprint |
| 🟡 Medium | Code smell, partial compliance, minor violation | 2 Sprints |
| 🟢 Low | Cleanup, documentation gap, unused code | Scheduled maintenance |

### 12.4 Penalty Matrix

(Per ENGINEERING_CONSTITUTION)

| Violation | Action |
|-----------|--------|
| Critical security issue in PR | PR blocked + security investigation |
| Cross-domain import | Immediate PR block + audit of prior PRs |
| Secret in code | Security investigation + secret rotation + mandatory training |
| Architecture change without ADR | Change reverted + ADR written + impact review |
| Widget SDK violation | Immediate PR block |
| Unregistered technical debt | Added to current sprint |

---

## Appendix: Document References

| Reference | Document | Section |
|-----------|----------|---------|
| [PB-§1] | PROJECT_BIBLE.md | Executive Vision |
| [PB-§4] | PROJECT_BIBLE.md | Engineering Principles |
| [PB-§8] | PROJECT_BIBLE.md | Development Workflow |
| [PB-§12] | PROJECT_BIBLE.md | Feature Development Rules |
| [PB-§16] | PROJECT_BIBLE.md | Release Standards |
| [PB-§17] | PROJECT_BIBLE.md | Decision Log |
| [EC-Art.2] | ENGINEERING_CONSTITUTION.md | Quality & Testing |
| [EC-Art.3] | ENGINEERING_CONSTITUTION.md | Architecture |
| [EC-Art.4] | ENGINEERING_CONSTITUTION.md | Security |
| [EC-Art.6] | ENGINEERING_CONSTITUTION.md | Release |
| [EC-Art.9] | ENGINEERING_CONSTITUTION.md | Widget SDK |
| [ADR-001] | engineering-os/adr/ADR-001-modular-monolith-foundation.md | Modular Monolith |
| [ADR-002] | engineering-os/adr/ADR-002-executive-intelligence-workspace.md | Dashboard as Projection |
| [ADR-003] | engineering-os/adr/ADR-003-widget-sdk-v1-freeze.md | Widget SDK Freeze |
| [MB-§2] | MASTER_BLUEPRINT.md | Platform Philosophy |
| [MB-§3] | MASTER_BLUEPRINT.md | Layer 1 — Kernel |
| [MB-§4] | MASTER_BLUEPRINT.md | Layer 2 — Platform Services |
| [IMP] | docs/vnext/IMPLEMENTATION_PLAN.md | 22-Sprint Build Plan |
| [FR] | docs/vnext/FEATURE_ROADMAP.md | Feature Roadmap |
