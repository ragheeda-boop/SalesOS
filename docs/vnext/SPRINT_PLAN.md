# SalesOS vNext — Sprint Plan

> **Author**: Chief Software Architect
> **Status**: Draft
> **Version**: v1.0
> **Last Updated**: 2026-07-16

---

## Overview

18 phases covering platform stabilization through production hardening. Each phase is 1-2 sprints (2-4 weeks). Estimated total: 16-20 sprints (~8-10 months).

---

## Phase 0: Platform Stabilization — Fix Criticals

**Duration**: 1 sprint (2 weeks)
**Dependencies**: None
**Risk**: High if delayed — all downstream phases depend on a stable foundation

### Objectives
- Eliminate all P0 security vulnerabilities
- Fix middleware body consumption bug to enable HTTP load testing
- Eliminate N+1 query patterns in workspace and NBA paths
- Implement Agent Runtime to unblock AI phase
- Begin backend AI test coverage

### Deliverables

| Deliverable | Items | Effort |
|-------------|-------|--------|
| Security fixes | SEC-001 (webhooks auth), SEC-003 (GraphQL auth), SEC-004 (JWKS fix), SEC-005 (Grafana default) | 4 days |
| Middleware fix | PERF-01 (body cache middleware) | 3 days |
| N+1 fixes | PERF-02 (workspace loop), PERF-03 (NBA feed) | 6 days |
| Agent Runtime v1 | AI-02 (basic runtime with lifecycle + execution) | 2 weeks |
| AI tests (start) | AI-01 (first 30% coverage on reasoning + guardrails) | 1 week |
| Quick wins | DSG-03 (muted text contrast), DSG-06 (duplicate Card), PERF-10/11 (print/console.debug) | 2 days |

### Dependencies
- None — Phase 0 is fully independent

### Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-0.1 | Webhooks router requires valid JWT |
| G-0.2 | GraphQL endpoint requires valid JWT |
| G-0.3 | JWKS endpoint returns valid keys, not empty symmetric key |
| G-0.4 | Middleware chain passes request body to route handlers intact |
| G-0.5 | Workspace listing runs in O(1) queries (verified by perf scan) |
| G-0.6 | NBA feed runs in O(1) queries (verified by perf scan) |
| G-0.7 | Agent Runtime can register, execute, and complete an agent |
| G-0.8 | Backend AI test coverage ≥ 30% |
| G-0.9 | `--text-muted` contrast ≥ 4.5:1 (WCAG AA pass) |

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Middleware fix breaks existing middlewares | Medium | Full regression test on all middleware before deploy |
| Agent Runtime scope too large for 1 sprint | High | Scope to lifecycle + single-agent execution; defer orchestration |

---

## Phase 1: Design System V2

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 0 (middleware fix for testing)
**Risk**: Low — primarily frontend work

### Objectives
- Fix all design audit issues
- Publish `@salesos/design-language@2.0.0-alpha`
- Implement missing form components (Checkbox, Radio, Switch, Textarea, DatePicker)
- Enforce CSS variable usage via ESLint rule + codemod

### Deliverables

| Deliverable | Items | Effort |
|-------------|-------|--------|
| Token fixes | DSG-01 (login page MUHIDE tokens), DSG-02 (chart colors), DSG-03 (muted text) | 5 days |
| New components | Checkbox, Radio, Switch, Textarea, DatePicker (DSG-04) | 5 days |
| CSS variable migration | DSG-05 (ESLint rule + codemod) | 1 week |
| Component cleanup | DSG-06 (duplicate Card removal) | 0.5 day |
| Token package v2.0-alpha | Published `@salesos/design-language@2.0.0-alpha` | 2 days |

### Dependencies
- Phase 0 complete (for CI pipeline stability)
- Design team sign-off on component specs

### Acceptance Criteria
| Gate | Criteria |
|------|----------|
| G-1.1 | Login page uses MUHIDE CSS variables and `@salesos/ui` components |
| G-1.2 | Chart color palette starts with orange `#F57C1E`, exported as `--chart-*` tokens |
| G-1.3 | `--text-muted` passes WCAG AA (≥4.5:1) |
| G-1.4 | Checkbox, Radio, Switch, Textarea, DatePicker available in `@salesos/ui` with ARIA + RTL + error states |
| G-1.5 | ESLint rule blocks Tailwind color classes in page components |
| G-1.6 | `@salesos/design-language@2.0.0-alpha` published with changelog |

### Risks
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Component scope creep | Medium | Ship P0 components only; P2 components deferred to Phase 10+ |
| Token changes break existing pages | Medium | Comprehensive visual regression test suite before/after |

---

## Phase 2: Dashboard

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 1 (for updated UI components), Phase 0 (for backend stability)
**Risk**: Low — dashboard is already 95% complete

### Objectives
- Resolve remaining dashboard polish items
- Ensure Widget SDK v1.1 is consumed correctly by all widgets
- Add missing loading/empty states to all dashboard widgets
- Fix NBA feed N+1 (carried forward if incomplete)

### Deliverables
- Dashboard page audit: loading, empty, error states for all widgets
- Widget SDK compatibility pass
- NBA feed performance verified

### Acceptance Criteria
- All widgets show skeleton loading states
- Empty states use `<EmptyState>` component for all widget types
- NBA feed p95 < 100ms

---

## Phase 3: Companies

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 0-2
**Risk**: Low — Companies domain is 90% complete

### Objectives
- Implement bulk operations (bulk edit, bulk delete, bulk export)
- Add advanced filtering UI
- Implement keyset pagination on all company list endpoints
- Fix `search_by_filters` double-query pattern

### Deliverables
- Bulk operations API + UI
- Advanced filter component
- Keyset pagination on `/companies`, `/companies/search`, `/companies/filter`

### Acceptance Criteria
- Bulk operations support select-all-on-page and select-all-across-pages
- Advanced filters support: industry, size, region, created date range, status
- Company list endpoints use keyset pagination (no OFFSET)
- p95 < 100ms for company search at 100k+ records

---

## Phase 4: Company360

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 3 (Companies baseline)
**Risk**: Medium — requires integration across multiple domains

### Objectives
- Complete Company 360 view (currently 80%)
- Integrate knowledge graph data into 360 view
- Add activity timeline (90% complete, needs polish)
- Ensure Decision Platform integration is functional

### Deliverables
- Unified Company 360 page with all domain data
- Knowledge Graph insights panel
- Activity timeline with filtering
- Decision Platform recommendations in context

### Acceptance Criteria
- Company 360 shows data from: Companies, CRM, Timeline, Enrichment, Entity Resolution, Knowledge Graph
- Timeline loads < 200ms p95
- Knowledge Graph insights are contextual (company-specific)
- Decision Platform provides at least 3 recommendation types

---

## Phase 5: Employees

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 0
**Risk**: Medium — Employee domain is 70% complete (lagging)

### Objectives
- Complete employee signals collection and analysis
- Integrate employee scoring with Decision Platform
- Implement employee search with pagination
- Add employee bulk operations

### Deliverables
- Employee signals pipeline (collection → analysis → scoring)
- Employee scoring integrated with Decision Platform
- Employee list with keyset pagination
- Employee bulk operations

### Acceptance Criteria
- Employee signals collected from 3+ sources (CRM activity, timeline events, workflow completions)
- Employee score integrated into Decision Platform decision context
- Employee search p95 < 100ms
- All employee list endpoints paginated

---

## Phase 6: Employee360

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 5 (Employees baseline)
**Risk**: Medium — requires Employee + Timeline + Scoring integration

### Objectives
- Complete Employee 360 view (currently 75%)
- Integrate employee signals and scoring
- Add employee activity timeline
- Add performance insights panel

### Deliverables
- Unified Employee 360 page
- Employee signals dashboard
- Activity timeline (employee-specific)
- Performance insights with Decision Platform

### Acceptance Criteria
- Employee 360 shows: profile, signals, scoring, timeline, performance
- Timeline loads < 200ms p95
- Performance insights include: trend analysis, peer comparison, risk flags

---

## Phase 7: Pipeline

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 3 (Companies), Phase 4 (Company360)
**Risk**: Medium — Pipeline domain needs advanced forecasting

### Objectives
- Implement advanced pipeline forecasting
- Add pipeline analytics dashboard
- Build pipeline stage management with drag-and-drop
- Integrate with Decision Platform for deal scoring

### Deliverables
- Pipeline forecasting (ML-backed, not just weighted)
- Pipeline analytics dashboard
- Drag-and-drop stage management
- Deal scoring via Decision Platform

### Acceptance Criteria
- Forecasting accuracy within ±15% of actual (measured after 1 quarter)
- Analytics dashboard: conversion rates, velocity, stage duration
- Drag-and-drop follows interaction patterns (commit → save pattern)
- Deal score displayed on each deal card

---

## Phase 8: Revenue

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 7 (Pipeline)
**Risk**: High — Revenue domain is 75% with gaps in forecasting, quota, territory

### Objectives
- Implement revenue forecasting with ML models
- Build quota management module
- Territory planning (initial implementation)
- Revenue analytics dashboard

### Deliverables
- Revenue forecasting engine
- Quota management (assignment, tracking, attainment)
- Territory planning (assignment, coverage analysis)
- Revenue dashboard: ARR, NRR, churn, expansion

### Acceptance Criteria
- Forecasting supports: by-rep, by-region, by-product, total
- Quota management: set quotas, track attainment %, forecast attainment
- Territory planning: assign accounts to reps, coverage gap analysis
- Revenue dashboard refreshes < 500ms p95

---

## Phase 9: Decision Center

**Duration**: 1-2 sprints (2-4 weeks)
**Dependencies**: Phase 0 (Agent Runtime), Phase 3-8 (domain data)
**Risk**: Medium — builds on Decision Platform which is strong

### Objectives
- Build Decision Center UI — unified interface for all decisions
- Add decision audit trail
- Implement decision feedback loop
- Add decision templates for common scenarios
- Implement multi-provider voting for high-stakes decisions (P1)

### Deliverables
- Decision Center page
- Audit trail per decision (input, reasoning, confidence, provider)
- Feedback mechanism (thumbs up/down + comment)
- Decision templates: lead qualification, deal progression, renewal risk, pricing
- Multi-provider ensemble for >$100K deals

### Acceptance Criteria
- Decision Center shows decisions across all domains
- Audit trail includes: input context, reasoning path, confidence, provider used, alternatives
- Feedback tracked and fed into evaluation framework
- 4+ decision templates operational
- Ensemble mode invokes 2+ providers for high-stakes decisions

---

## Phase 10: Search

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 0 (middleware, pagination), Phase 3 (Companies)
**Risk**: Low — Search domain is 92% complete

### Objectives
- Add keyset pagination to all search endpoints
- Implement `@cached` on search endpoints
- Add search analytics (query logging, popular searches, zero-result queries)
- Add Arabic search improvements

### Deliverables
- Paginated search with cursor support
- Cached search results
- Search analytics dashboard
- Arabic search improvements (normalization, stemming, stop words)

### Acceptance Criteria
- All search endpoints paginated with keyset cursor
- Search p50 < 5ms, p95 < 50ms at 100k+ companies
- Search analytics show: top 10 queries, zero-result rate, average latency
- Arabic search accuracy within 90% of English search

---

## Phase 11: Copilot

**Duration**: 1 sprint (2 weeks)
**Dependencies**: Phase 0 (Agent Runtime), Phase 9 (Decision Center), Phase 10 (Search)
**Risk**: Medium — depends on Agent Runtime readiness

### Objectives
- Fix `search_companies` tool returning empty
- Implement copilot feedback mechanism
- Add tool call observability (success rate, latency, result count)
- Support Arabic copilot interactions
- Add conversation branching

### Deliverables
- Working `search_companies` tool
- Copilot feedback (thumbs up/down + comment)
- Tool telemetry dashboard
- Arabic copilot support (RTL, Arabic NLP, Saudi context)
- Conversation branching UI

### Acceptance Criteria
- `search_companies` returns populated results with < 1s latency
- Feedback submission rate > 10% of copilot interactions (target)
- Tool telemetry shows: success rate, p50/p95/p99 latency, result count distribution
- Arabic copilot handles RTL text, Arabic questions, Saudi business context
- Branch points allow users to explore alternatives without losing context

---

## Phase 12: Knowledge

**Duration**: 2 sprints (4 weeks)
**Dependencies**: Phase 0 (Agent Runtime), Phase 3 (Companies)
**Risk**: High — Knowledge Graph runtime (1,087 lines) needs refactoring first

### Objectives
- Decompose 1,087-line `knowledge_graph_runtime` (ARC-03)
- Migrate vectors from `ARRAY(FLOAT)` to native `VECTOR(n)` (ARC-13)
- Implement embedding cache (AI-05)
- Implement hybrid retrieval (vector + BM25 with RRF)
- Implement real Data Fabric connectors (AI-08)

### Deliverables
- Decomposed knowledge graph runtime (service + repository + router)
- PGVector native type with HNSW index
- Embedding cache with LRU eviction
- Hybrid retrieval combining vector similarity + BM25
- 3+ real Data Fabric connectors (replace mock)

### Acceptance Criteria
- `knowledge_graph_runtime/` split into modules, each < 500 lines
- PGVector query speed improved ~50x on similarity search
- Embedding cache hit rate > 40%
- Hybrid retrieval F1 score > 0.85
- Data Fabric connectors return real data from CRM, ERP, market feeds

---

## Phase 13: Automation

**Duration**: 1-2 sprints (2-4 weeks)
**Dependencies**: Phase 0 (Agent Runtime), Phase 9 (Decision Center)
**Risk**: Medium — Workflow engine needs advanced features

### Objectives
- Implement advanced workflow branching and conditional logic
- Add webhook authentication (SEC-001 — carry forward safety)
- Implement scheduled jobs
- Build workflow template library
- Add workflow analytics

### Deliverables
- Advanced workflow engine (conditionals, loops, parallel branches)
- Authenticated webhooks
- Scheduled job system
- Workflow templates: lead assignment, deal escalation, renewal reminders
- Workflow analytics dashboard

### Acceptance Criteria
- Workflow engine supports: IF/ELSE conditions, FOR loops, parallel branches, timeouts
- Webhooks require authentication (JWT or HMAC signature)
- Scheduled jobs support: cron expressions, one-time delays, recurring intervals
- 5+ workflow templates pre-built
- Analytics show: active workflows, completion rate, average duration, failure rate

---

## Phase 14: Analytics

**Duration**: 1-2 sprints (2-4 weeks)
**Dependencies**: Phase 7 (Pipeline), Phase 8 (Revenue), Phase 13 (Automation)
**Risk**: Medium — requires data from multiple domains

### Objectives
- Build unified analytics platform
- Implement custom report builder
- Add dashboard sharing and scheduling
- Add export to PDF/CSV
- Implement analytics API with proper pagination

### Deliverables
- Analytics platform with domain-specific dashboards
- Custom report builder (drag-and-drop metrics + dimensions)
- Dashboard sharing (with permissions) + scheduled email reports
- Export engine (PDF for visual, CSV for data)
- Analytics API with keyset pagination

### Acceptance Criteria
- Analytics platform supports: Sales, Revenue, Pipeline, Employee, Automation domains
- Report builder supports: date range, filters, grouping, aggregation, visualization type
- Scheduled reports delivered via email on configurable cadence
- PDF exports include all chart elements and data tables
- API paginated with keyset cursor, p95 < 200ms

---

## Phase 15: Marketplace

**Duration**: 1-2 sprints (2-4 weeks)
**Dependencies**: Phase 1 (Design System), Phase 2 (Dashboard/Widget SDK)
**Risk**: High — new feature with no existing implementation

### Objectives
- Build plugin registry and manifest validation
- Implement plugin lifecycle management
- Build internal plugin marketplace UI
- Support widget plugins and backend plugins
- Add plugin sandboxing

### Deliverables
- Plugin system (registry, manifest, lifecycle)
- Plugin marketplace UI
- 2+ internal plugins (e.g., Slack integration, Salesforce connector)
- Plugin sandboxing for widget (iframe) and backend (import-restricted) plugins

### Acceptance Criteria
- Plugin manifest validated on install (name, version, hooks, permissions)
- Plugin lifecycle: Install → Disable → Enable → Active → Uninstall
- Marketplace UI: browse, install, configure, uninstall
- Widget plugins render in isolated iframe
- Backend plugins restricted by import policy

---

## Phase 16: Administration

**Duration**: 1-2 sprints (2-4 weeks)
**Dependencies**: Phase 0 (Security), Phase 8 (Revenue/Quota), Phase 5 (Employees)
**Risk**: Medium — Admin domain is 75% complete

### Objectives
- Complete admin UI (currently partial)
- Implement persistent admin stores (SEC-002 fix)
- Add tenant management UI
- Add feature flag management UI
- Add audit log viewer
- Implement centralized configuration management

### Deliverables
- Full admin UI: users, roles, permissions, settings
- Persistent admin stores (PostgreSQL-backed)
- Tenant management: create, configure, suspend, delete
- Feature flag management: enable/disable per tenant, rollout percentage
- Audit log viewer with filtering and export
- Centralized config editor (YAML-based)

### Acceptance Criteria
- Admin stores survive restart (PostgreSQL-backed, not in-memory)
- Tenant management supports: provisioning, configuration, suspension, deletion
- Feature flags: per-tenant enable/disable, gradual rollout, CI integration test
- Audit log shows: user, action, resource, timestamp, IP, outcome
- Config editor validates YAML before saving

---

## Phase 17: Production Hardening

**Duration**: 1-2 sprints (2-4 weeks)
**Dependencies**: All preceding phases
**Risk**: Low — primarily testing, performance, and documentation

### Objectives
- Achieve 100% keyset pagination compliance
- Achieve backend AI test coverage ≥ 85%
- Add API contract tests (provider + consumer)
- Performance optimization and load testing
- Complete documentation
- Final security sweep

### Deliverables

| Deliverable | Items | Effort |
|-------------|-------|--------|
| Pagination compliance | All list endpoints verified keyset-paginated | 1 week |
| AI test coverage | Coverage ≥ 85% on intelligence module | 2 weeks |
| Contract tests | Provider + consumer tests for all API endpoints | 2 weeks |
| Performance validation | Full load test suite + regression detection | 2 weeks |
| Documentation | API docs, admin guide, user guides updated | 1 week |
| Security sweep | Full pentest, dependency audit, config audit | 1 week |
| Technical debt review | Resolve all remaining P1 items or defer with ADR | 1 week |

### Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-17.1 | 100% list endpoints use keyset pagination (verified by automated scan) |
| G-17.2 | Backend AI test coverage ≥ 85% |
| G-17.3 | Every endpoint has provider contract test; every frontend API client has consumer contract test |
| G-17.4 | All endpoints within performance budget at 100k+ tenant data scale |
| G-17.5 | Documentation coverage: all endpoints documented, user guides complete |
| G-17.6 | Security pentest passes with 0 critical, 0 high findings |
| G-17.7 | Technical debt register: 0 P0, 0 P1 items |
| G-17.8 | Total tests ≥ 3,000 |

---

## Phase Dependency Graph

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 17
                 │                      │            │
                 │                      ▼            │
                 │                 Phase 5 ──► Phase 6│
                 │                      │            │
                 │                      ▼            │
                 │                 Phase 7 ──► Phase 8│
                 │                      │            │
                 ▼                      ▼            ▼
            Phase 9 ◄──── Phase 0 ──► Phase 10 ──► Phase 11
                 │                                    │
                 ▼                                    │
           Phase 12 ◄─────────────────────────────────┘
                 │
                 ▼
           Phase 13 ◄──── Phase 9
                 │
                 ▼
           Phase 14 ◄──── Phase 7, 8, 13
                 │
                 ▼
           Phase 15 ◄──── Phase 1, 2
                 │
                 ▼
           Phase 16 ◄──── Phase 0, 5, 8
                 │
                 ▼
           Phase 17
```

---

## Resource Requirements

| Role | Allocation | Phases |
|------|-----------|--------|
| Backend Engineers | 3-4 FTE | All phases |
| Frontend Engineers | 2-3 FTE | Phases 1-6, 9, 11, 14-16 |
| AI/ML Engineers | 1-2 FTE | Phases 0, 9, 11-13 |
| DevOps/Infrastructure | 1 FTE | Phases 0, 10, 17 |
| QA Engineers | 1 FTE | Phases 2-17 (continuous) |
| Designers | 1 FTE | Phases 1, 3-6, 9, 11, 15-16 |
| Technical Writer | 0.5 FTE | Phases 2-17 (continuous) |

---

## Key Milestones

| Milestone | Phase | Target Sprint | Date |
|-----------|-------|---------------|------|
| Critical security fixes deployed | 0 | Sprint 1 | Week 2 |
| Agent Runtime operational | 0 | Sprint 1-2 | Week 4 |
| Design System V2 alpha published | 1 | Sprint 3 | Week 6 |
| All domains ≥ 90% completion | 3-6 | Sprint 7 | Week 14 |
| Decision Center live | 9 | Sprint 10 | Week 20 |
| Knowledge Graph V2 | 12 | Sprint 14 | Week 28 |
| Marketplace first release | 15 | Sprint 17 | Week 34 |
| Production Hardening complete | 17 | Sprint 20 | Week 40 |
| **vNext GA Launch** | — | Sprint 20 | **Week 40** |
