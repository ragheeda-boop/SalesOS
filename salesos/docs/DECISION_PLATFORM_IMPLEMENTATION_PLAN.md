# Decision Intelligence Platform — Phased Implementation Plan

> Last updated: 2026-07-10
> Owner: Architecture Board
> Status: Phase 1 Complete

---

## Overview

This plan tracks the end-to-end implementation of the Decision Intelligence Platform — SalesOS's centralized commercial reasoning engine. Every recommendation, score, and insight across the product flows through this platform.

**Architecture Document**: `DECISION_PLATFORM_ARCHITECTURE.md`
**Package**: `packages/platform/decision/`
**npm scope**: `@salesos/decision-platform`

---

## Phase 1: Foundation ✅ COMPLETED

### Description

Built the complete TypeScript engine layer with 8 engines, 17+ contract types, shared utilities, testing helpers, audit logging, and telemetry. The platform is fully functional as an in-process library.

### What Was Built

| Component | File | LOC | Status |
|-----------|------|-----|--------|
| Contracts (17+ types) | `contracts/index.ts` | 168 | ✅ |
| Decision Engine (orchestrator) | `decision-engine/index.ts` | 533 | ✅ |
| Rule Engine (7 built-in rules, conflict detection) | `rule-engine/index.ts` | 386 | ✅ |
| Scoring Engine (8 score types, 40 factors) | `scoring-engine/index.ts` | 139 | ✅ |
| Evidence Engine (5 providers, dedup, freshness) | `evidence-engine/index.ts` | 272 | ✅ |
| Recommendation Engine (8 action types) | `recommendation-engine/index.ts` | 589 | ✅ |
| Explainability Engine (EN/AR bilingual) | `explainability-engine/index.ts` | 184 | ✅ |
| Feedback Engine (validation, stats) | `feedback-engine/index.ts` | 155 | ✅ |
| Learning Engine (trends, rule effectiveness) | `learning-engine/index.ts` | 224 | ✅ |
| Shared Utilities (10 functions) | `shared/index.ts` | 73 | ✅ |
| Telemetry Collector | `shared/telemetry.ts` | 45 | ✅ |
| Audit Logger | `shared/audit.ts` | 64 | ✅ |
| Testing Utilities (7 factories + 3 assertions) | `testing/index.ts` | 168 | ✅ |
| Architecture Document | `docs/DECISION_PLATFORM_ARCHITECTURE.md` | 174 | ✅ |
| Barrel Export | `index.ts` | 16 | ✅ |

**Total**: ~3,000 LOC across 14 files

### Key Decisions Made

| Decision | Rationale | ADR |
|----------|-----------|-----|
| All engines are stateless classes | Thread safety, easy testing | Implicit |
| In-memory stores (Map) for demo/dev | Faster iteration, replace with DB in Phase 2 | — |
| 8 action types in Recommendation Engine | Covers full B2B sales lifecycle | — |
| Bilingual explainability (EN/AR) | Saudi market requirement | — |
| Conflict detection in Rule Engine | Prevents contradictory actions | — |
| Factor-based scoring (40 factors) | Transparent, auditable scoring | — |

### Acceptance Criteria — All Met

- [x] All 17 contract types exported and type-safe
- [x] DecisionEngine.evaluate() returns complete DecisionResult with telemetry
- [x] Rule Engine detects and resolves conflicts (priority-based)
- [x] Scoring Engine produces 8 score types with explainable factors
- [x] Evidence Engine deduplicates and ranks by confidence
- [x] Recommendation Engine evaluates 8 action types with alternatives
- [x] Explainability Engine answers Why/WhyNow/WhyThisAction/WhyNotAlternative
- [x] Feedback Engine validates input and generates learning events
- [x] Learning Engine computes quality metrics and trends
- [x] Testing utilities create valid mocks for all types
- [x] Barrel export exposes everything via `@salesos/decision-platform`

---

## Phase 2: Backend Integration 🟡 NEXT

### Description

Create the Python/FastAPI backend layer that exposes the Decision Platform as HTTP API endpoints, persists decisions/feedback/learning events to PostgreSQL, and wires the TypeScript engines into the existing RevenueService.

### Key Deliverables

| # | Deliverable | Description | Depends On |
|---|-------------|-------------|------------|
| 2.1 | Python contracts (`decision/models.py`) | Pydantic models mirroring all 17 TypeScript contracts | — |
| 2.2 | PostgreSQL migrations (`alembic/versions/`) | Tables: `decisions`, `decision_scores`, `decision_evidence`, `decision_rules_applied`, `feedback`, `learning_events`, `audit_log` | — |
| 2.3 | Decision repository (`decision/repository.py`) | CRUD for decisions + feedback + learning events | 2.2 |
| 2.4 | FastAPI router: `POST /api/v1/decisions/evaluate` | Accepts DecisionContext, returns full DecisionResult | 2.1, 2.3 |
| 2.5 | FastAPI router: `POST /api/v1/decisions/batch` | Batch evaluation for multiple contexts | 2.4 |
| 2.6 | FastAPI router: `GET /api/v1/decisions/{id}` | Retrieve single decision | 2.3 |
| 2.7 | FastAPI router: `GET /api/v1/decisions/{id}/explain` | Retrieve explainability for a decision | 2.3 |
| 2.8 | FastAPI router: `GET /api/v1/decisions/history` | Decision history for a tenant | 2.3 |
| 2.9 | FastAPI router: `POST /api/v1/feedback` | Submit feedback on a decision | 2.3 |
| 2.10 | FastAPI router: `GET /api/v1/feedback/stats` | Feedback statistics for a tenant | 2.3 |
| 2.11 | FastAPI router: `GET /api/v1/learning/quality` | Quality metrics | 2.3 |
| 2.12 | FastAPI router: `GET /api/v1/learning/trends` | Learning trends over time | 2.3 |
| 2.13 | FastAPI router: `GET /api/v1/learning/rules` | Rule effectiveness metrics | 2.3 |
| 2.14 | FastAPI router: `GET /api/v1/rules` | List registered rules | — |
| 2.15 | RevenueService integration | Decision Engine consumes RevenueService data as evidence provider | 2.4 |
| 2.16 | Evidence provider registry | Pluggable providers: Company DNA, Signals, Timeline, Pipeline, Search | 2.4 |
| 2.17 | Caching layer (Redis) | Cache rule results (1h TTL), scores (15min TTL), recommendations (5min TTL) | 2.4 |
| 2.18 | Rate limiting per tenant | Per-tenant rate limits on evaluation endpoints | 2.4 |
| 2.19 | Authentication middleware | JWT validation on all decision endpoints | 2.4 |
| 2.20 | OpenAPI documentation | Auto-generated Swagger docs for all endpoints | 2.4 |

### API Endpoints Summary

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/api/v1/decisions/evaluate` | Evaluate a decision | `DecisionContext` | `DecisionResult` |
| `POST` | `/api/v1/decisions/batch` | Batch evaluate | `DecisionContext[]` | `DecisionResult[]` |
| `GET` | `/api/v1/decisions/{id}` | Get decision by ID | — | `DecisionResult` |
| `GET` | `/api/v1/decisions/{id}/explain` | Get explanation | — | `Explainability` |
| `GET` | `/api/v1/decisions/history` | Decision history | `?tenantId=&limit=` | `DecisionHistoryItem[]` |
| `POST` | `/api/v1/feedback` | Submit feedback | `Feedback` | `{ id, accepted }` |
| `GET` | `/api/v1/feedback/stats` | Feedback stats | `?tenantId=` | `FeedbackStats` |
| `GET` | `/api/v1/learning/quality` | Quality metrics | `?tenantId=` | `QualityMetrics` |
| `GET` | `/api/v1/learning/trends` | Learning trends | `?tenantId=` | `LearningTrend[]` |
| `GET` | `/api/v1/learning/rules` | Rule effectiveness | `?tenantId=` | `RuleEffectiveness[]` |
| `GET` | `/api/v1/rules` | List rules | `?category=` | `DecisionRule[]` |

### Database Schema

```sql
-- Core decision table
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    entity_id UUID,
    entity_type VARCHAR(20),
    context JSONB NOT NULL,
    recommendation JSONB NOT NULL,
    scores JSONB NOT NULL,
    rules_applied JSONB NOT NULL,
    evidence JSONB NOT NULL,
    explainability JSONB NOT NULL,
    telemetry JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    outcome VARCHAR(20),
    revenue_impact DECIMAL(12,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_decisions_tenant ON decisions(tenant_id);
CREATE INDEX idx_decisions_entity ON decisions(entity_id, entity_type);
CREATE INDEX idx_decisions_created ON decisions(created_at DESC);
CREATE INDEX idx_decisions_status ON decisions(status);

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID REFERENCES decisions(id),
    tenant_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    outcome VARCHAR(20) NOT NULL,
    reason TEXT,
    revenue_impact DECIMAL(12,2),
    time_to_execution INTEGER,
    actual_effort VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_tenant ON feedback(tenant_id);
CREATE INDEX idx_feedback_decision ON feedback(decision_id);

-- Learning events table
CREATE TABLE learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    decision_id UUID REFERENCES decisions(id),
    tenant_id UUID NOT NULL,
    metric VARCHAR(100) NOT NULL,
    value DECIMAL(5,4) NOT NULL,
    factors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_tenant ON learning_events(tenant_id);
CREATE INDEX idx_learning_type ON learning_events(type);

-- Audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    context JSONB NOT NULL,
    rules_applied JSONB NOT NULL,
    scores JSONB NOT NULL,
    evidence_count INTEGER,
    recommendation VARCHAR(100),
    confidence DECIMAL(5,4),
    outcome VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_log(tenant_id);
CREATE INDEX idx_audit_decision ON audit_log(decision_id);
```

### Effort Estimate

| Sprint | Deliverables | Points |
|--------|-------------|--------|
| Sprint 2.1 | 2.1–2.3 (models, migrations, repository) | 13 |
| Sprint 2.2 | 2.4–2.10 (core API endpoints) | 13 |
| Sprint 2.3 | 2.11–2.16 (learning API + evidence providers) | 10 |
| Sprint 2.4 | 2.17–2.20 (caching, security, docs) | 8 |
| **Total** | | **44 pts (4 sprints)** |

### Dependencies

- PostgreSQL instance available (currently single node)
- Redis deployment for caching (currently not deployed — see TD-003)
- RevenueService exists and is operational
- JWT authentication middleware exists

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Redis not deployed yet (TD-003) | High | Medium | In-memory cache for MVP, deploy Redis in parallel |
| PostgreSQL connection pool issues (Neo4j pattern) | Medium | High | Use connection pooling from day one (pgBouncer) |
| RevenueService API changes during integration | Medium | Medium | Pin interface contract via ADR before integration |
| Performance budget violations on cold evaluation | Low | High | Benchmark in Sprint 2.4, optimize hot paths |

### Acceptance Criteria

- [ ] All 11 API endpoints return correct contract types
- [ ] Pydantic models validate all 17 TypeScript contract types 1:1
- [ ] Decisions persist to PostgreSQL and are retrievable
- [ ] Feedback submission creates learning events automatically
- [ ] Evidence providers are pluggable and extensible
- [ ] All endpoints require JWT authentication
- [ ] Rate limiting enforced per tenant (100 req/min default)
- [ ] OpenAPI docs generated and accurate
- [ ] Response time < 500ms for complex decisions (with evidence)
- [ ] Response time < 100ms for simple decisions (rules + scoring only)
- [ ] Audit log captures every decision
- [ ] Integration with RevenueService returns real pipeline data as evidence

---

## Phase 3: Frontend Integration

### Description

Refactor existing widgets to consume decisions from the platform instead of computing scores/recommendations inline. Add decision context providers to the Revenue Execution workspace.

### Key Deliverables

| # | Deliverable | Description | Depends On |
|---|-------------|-------------|------------|
| 3.1 | DecisionProvider context | React context wrapping the Revenue Execution workspace with decision state | Phase 2 |
| 3.2 | `useDecision` hook | Custom hook: `useDecision(context) → { result, loading, error, explain }` | 3.1 |
| 3.3 | `useFeedback` hook | Custom hook: `useFeedback(decisionId) → { submit, stats }` | 3.1 |
| 3.4 | NBA Widget refactor | Replace direct API calls with DecisionEngine consumption | 3.2 |
| 3.5 | Explainability tooltip component | Renders Why/WhyNow/WhyThisAction/WhyNotAlternative in a tooltip/popover | 3.2 |
| 3.6 | Confidence badge component | Visual indicator: high (green) / medium (yellow) / low (red) | — |
| 3.7 | Score radar chart component | Visual radar of 8 score types for an entity | — |
| 3.8 | Decision history panel | Scrollable list of past decisions with outcomes | 3.2 |
| 3.9 | Feedback prompt component | "Was this helpful?" UI with accept/reject/ignore buttons | 3.3 |
| 3.10 | Company Intelligence integration | Wire company detail view to show decision scores | 3.2 |
| 3.11 | Opportunity Workspace integration | Wire opportunity detail to show decision-based recommendations | 3.2 |
| 3.12 | Loading/skeleton states | Consistent loading UIs for all decision-consuming components | — |

### Effort Estimate

| Sprint | Deliverables | Points |
|--------|-------------|--------|
| Sprint 3.1 | 3.1–3.3 (context + hooks) | 8 |
| Sprint 3.2 | 3.4–3.6 (NBA refactor + explainability UI) | 8 |
| Sprint 3.3 | 3.7–3.9 (radar chart + history + feedback) | 8 |
| Sprint 3.4 | 3.10–3.12 (workspace integrations + loading states) | 8 |
| **Total** | | **32 pts (4 sprints)** |

### Dependencies

- Phase 2 complete (API endpoints available)
- Foundation components from Sprint 1 (a11y-optimized)
- `@salesos/design-language` tokens available

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| NBA Widget refactor breaks existing UX | Medium | High | Feature-flag the migration, A/B test |
| Decision latency feels slow in UI | Medium | Medium | Optimistic rendering + skeleton loading |
| Explainability text too long for tooltips | Low | Low | Truncate with "Read more" expansion |

### Acceptance Criteria

- [ ] NBA Widget displays decisions from Decision Engine, not inline logic
- [ ] Explainability tooltip renders full Why/WhyNow/WhyThisAction
- [ ] Confidence badge correctly reflects confidence labels
- [ ] Feedback submission works end-to-end (UI → API → database)
- [ ] Company Intelligence shows 8 score types with radar chart
- [ ] Opportunity Workspace shows recommendation + alternatives
- [ ] All new components meet WCAG AA (keyboard nav, ARIA labels)
- [ ] Dark mode supported for all new components
- [ ] RTL layout supported for explainability text
- [ ] No TypeScript regressions

---

## Phase 4: Widget Migration

### Description

Migrate all 22 revenue-execution widgets to consume decisions from the platform. Remove any inline scoring, reasoning, or recommendation logic from widgets. Every widget becomes a pure consumer of the Decision Engine.

### Key Deliverables

| # | Deliverable | Description | Depends On |
|---|-------------|-------------|------------|
| 4.1 | Widget audit | Catalog every widget's current scoring/reasoning logic | — |
| 4.2 | Migration plan per widget | Document what each widget replaces with Decision Engine calls | 4.1 |
| 4.3 | NBA Widget (already done) | Completed in Phase 3 | Phase 3 |
| 4.4 | Pipeline Intelligence Widget | Migrate to use decision scores + recommendations | 3.2 |
| 4.5 | Revenue Health Widget | Migrate risk/revenue scoring to Decision Engine | 3.2 |
| 4.6 | Forecast Intelligence Widget | Migrate forecast scoring to Decision Engine | 3.2 |
| 4.7 | Company Overview Widget | Migrate company scores to Decision Engine | 3.2 |
| 4.8 | Activity Feed Widget | Migrate activity scoring to Decision Engine | 3.2 |
| 4.9 | Contact Intelligence Widget | Migrate relationship scoring to Decision Engine | 3.2 |
| 4.10 | Deal Velocity Widget | Migrate velocity scoring to Decision Engine | 3.2 |
| 4.11 | Risk Radar Widget | Migrate risk assessment to Decision Engine | 3.2 |
| 4.12 | Engagement Score Widget | Migrate engagement scoring to Decision Engine | 3.2 |
| 4.13 | Signal Timeline Widget | Migrate signal prioritization to Decision Engine | 3.2 |
| 4.14 | Remaining 11 widgets | Migrate each to Decision Engine consumption | 3.2 |
| 4.15 | Remove inline scoring code | Delete all scoring/reasoning logic from widget files | 4.4–4.14 |
| 4.16 | Widget contract tests | Each widget has `describeWidgetContract()` with decision mock | 4.4–4.14 |

### Migration Pattern

```typescript
// BEFORE (widget does its own scoring)
function PipelineWidget({ opportunityId }) {
  const [score, setScore] = useState(null)
  useEffect(() => {
    // Inline scoring logic — BAD
    const s = computeScore(opportunityData)
    setScore(s)
  }, [opportunityData])
}

// AFTER (widget consumes Decision Engine)
function PipelineWidget({ opportunityId }) {
  const { result, loading } = useDecision({
    tenantId,
    entityId: opportunityId,
    entityType: 'opportunity',
    metadata: { opportunityValue: dealValue },
  })

  if (loading) return <Skeleton />
  return <ScoreBadge confidence={result.recommendation.confidence} />
}
```

### Widget Registry

| # | Widget | Current Scoring | Decision Engine Score Type | Migration Complexity |
|---|--------|----------------|---------------------------|---------------------|
| 1 | NBA Widget | Inline rules | recommendation + all | Low (done in Phase 3) |
| 2 | Pipeline Intelligence | Inline pipeline score | opportunity + revenue | Medium |
| 3 | Revenue Health | Inline health check | revenue + risk | Medium |
| 4 | Forecast Intelligence | Inline forecast model | revenue + confidence | High |
| 5 | Company Overview | Inline company score | company + data_quality | Low |
| 6 | Activity Feed | Inline activity score | relationship + intent | Low |
| 7 | Contact Intelligence | Inline relationship score | relationship | Low |
| 8 | Deal Velocity | Inline velocity calc | opportunity + revenue | Medium |
| 9 | Risk Radar | Inline risk assessment | risk | Low |
| 10 | Engagement Score | Inline engagement score | relationship + intent | Low |
| 11 | Signal Timeline | Inline signal priority | intent + confidence | Low |
| 12–22 | Remaining widgets | Various inline | Various | Low–Medium |

### Effort Estimate

| Sprint | Deliverables | Points |
|--------|-------------|--------|
| Sprint 4.1 | 4.1–4.2 (audit + migration plan) | 5 |
| Sprint 4.2 | 4.4–4.6 (Pipeline, Revenue Health, Forecast) | 13 |
| Sprint 4.3 | 4.7–4.10 (Company, Activity, Contact, Deal Velocity) | 13 |
| Sprint 4.4 | 4.11–4.14 (Risk, Engagement, Signal, remaining 11) | 13 |
| Sprint 4.5 | 4.15–4.16 (cleanup + contract tests) | 8 |
| **Total** | | **52 pts (5 sprints)** |

### Dependencies

- Phase 3 complete (hooks and context available)
- All 22 widgets identified and cataloged
- Widget SDK v1.0 stable (currently frozen)

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Widget SDK frozen — cannot add decision-specific patterns | High | Medium | Use existing SDK patterns, no SDK changes needed |
| Some widgets have deeply coupled inline logic | Medium | Medium | Migrate incrementally, feature-flag each widget |
| Regression in widget rendering during migration | Medium | High | Visual regression tests for each widget |
| Performance degradation from additional API calls | Low | Medium | Use batch evaluation endpoint, client-side caching |

### Acceptance Criteria

- [ ] All 22 widgets consume decisions from the Decision Engine
- [ ] Zero inline scoring/reasoning code remains in widget files
- [ ] Each widget has a passing `describeWidgetContract()` test
- [ ] Visual regression tests pass for all migrated widgets
- [ ] No performance regression (widget load time within budget)
- [ ] Feature flags allow toggling old vs new behavior per widget
- [ ] All widgets support EN and AR explainability text
- [ ] Dark mode and RTL work for all migrated widgets

---

## Phase 5: Testing & Validation

### Description

Comprehensive testing of all engines, end-to-end decision evaluation, performance benchmarks, and explainability validation. This phase ensures the platform is production-ready.

### Key Deliverables

| # | Deliverable | Description | Depends On |
|---|-------------|-------------|------------|
| 5.1 | Decision Engine unit tests | Test evaluate(), evaluateBatch(), explain(), getHistory() | Phase 1 |
| 5.2 | Rule Engine unit tests | Test rule registration, evaluation, conflict detection, condition matching | Phase 1 |
| 5.3 | Scoring Engine unit tests | Test all 8 score types, factor weighting, normalization | Phase 1 |
| 5.4 | Evidence Engine unit tests | Test collection, deduplication, freshness, provider registry | Phase 1 |
| 5.5 | Recommendation Engine unit tests | Test all 8 action types, alternatives, risk assessment | Phase 1 |
| 5.6 | Explainability Engine unit tests | Test EN/AR output, Why/WhyNow/WhyThisAction generation | Phase 1 |
| 5.7 | Feedback Engine unit tests | Test validation, submission, stats computation | Phase 1 |
| 5.8 | Learning Engine unit tests | Test quality metrics, trends, rule effectiveness | Phase 1 |
| 5.9 | Integration tests: full pipeline | Context → Evidence → Rules → Scoring → Recommendation → Explainability | Phase 2 |
| 5.10 | Integration tests: feedback loop | Decision → Feedback → Learning Event → Quality Metrics | Phase 2 |
| 5.11 | Integration tests: API endpoints | All 11 FastAPI endpoints with realistic data | Phase 2 |
| 5.12 | Performance benchmarks | Verify all performance budgets from architecture doc | Phase 2 |
| 5.13 | Explainability validation | Human review of EN/AR explanations for quality | Phase 3 |
| 5.14 | Contract tests for frontend hooks | useDecision, useFeedback return correct shapes | Phase 3 |
| 5.15 | Widget contract tests | All 22 widgets pass describeWidgetContract() | Phase 4 |
| 5.16 | Load testing | 100 concurrent decision evaluations per tenant | Phase 2 |
| 5.17 | Security testing | Auth bypass, tenant isolation, injection attacks | Phase 2 |
| 5.18 | Regression test suite | Full regression suite runs on every PR | Phase 4 |

### Performance Budgets (from Architecture)

| Operation | Budget | Test Method |
|-----------|--------|-------------|
| Simple decision (rules + scoring) | < 100ms | Benchmark with 1000 iterations |
| Complex decision (with evidence) | < 500ms | Benchmark with mock evidence providers |
| Recommendation generation | < 200ms | Benchmark with cached scores |
| Explainability generation | < 100ms | Benchmark per decision |
| Score computation | < 50ms | Benchmark per entity |
| Evidence retrieval | < 200ms | Benchmark with deduplication |
| Concurrent evaluations (100/tenant) | < 2s p99 | Load test |

### Test Structure

```
packages/platform/decision/__tests__/
├── unit/
│   ├── decision-engine.test.ts
│   ├── rule-engine.test.ts
│   ├── scoring-engine.test.ts
│   ├── evidence-engine.test.ts
│   ├── recommendation-engine.test.ts
│   ├── explainability-engine.test.ts
│   ├── feedback-engine.test.ts
│   └── learning-engine.test.ts
├── integration/
│   ├── full-pipeline.test.ts
│   ├── feedback-loop.test.ts
│   └── api-endpoints.test.ts
├── performance/
│   ├── benchmarks.test.ts
│   └── load-test.test.ts
├── security/
│   ├── auth.test.ts
│   └── tenant-isolation.test.ts
└── contract/
    ├── hooks.test.ts
    └── widgets.test.ts
```

### Effort Estimate

| Sprint | Deliverables | Points |
|--------|-------------|--------|
| Sprint 5.1 | 5.1–5.8 (engine unit tests) | 13 |
| Sprint 5.2 | 5.9–5.11 (integration tests) | 10 |
| Sprint 5.3 | 5.12–5.13 (benchmarks + explainability validation) | 8 |
| Sprint 5.4 | 5.14–5.16 (contract + load tests) | 8 |
| Sprint 5.5 | 5.17–5.18 (security + regression) | 8 |
| **Total** | | **47 pts (5 sprints)** |

### Dependencies

- Phase 1 complete (all engines available for testing)
- Phase 2 complete (for integration and API tests)
- Phase 3 complete (for contract tests)
- Phase 4 complete (for widget contract tests)

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Explainability quality not good enough for AR | Medium | Medium | Human review, iterate on templates |
| Performance budgets violated under load | Low | High | Profile and optimize hot paths |
| Test flakiness from time-dependent logic | Medium | Low | Mock Date.now() consistently |
| Insufficient test coverage target (85% required) | Medium | High | Track coverage in CI, block PRs below threshold |

### Acceptance Criteria

- [ ] Unit test coverage ≥ 85% for all engines
- [ ] All integration tests pass end-to-end
- [ ] Performance budgets met for all operations
- [ ] Explainability text reviewed by domain expert (EN + AR)
- [ ] Load test: 100 concurrent evaluations complete within p99 budget
- [ ] Security: no auth bypass, no cross-tenant data leakage
- [ ] All widget contract tests pass
- [ ] Regression suite runs on every PR
- [ ] No Critical or High security findings

---

## Phase 6: AI Integration (Future)

### Description

When AI Agents are built, they consume decisions from this platform. AI becomes another evidence/scoring provider, not the decision maker. The Decision Platform remains the single source of truth for all reasoning.

### Key Deliverables

| # | Deliverable | Description | Depends On |
|---|-------------|-------------|------------|
| 6.1 | AI Evidence Provider | AI Agent outputs become evidence items fed into the Evidence Engine | Phase 2 evidence provider registry |
| 6.2 | AI Scoring Provider | AI-generated scores contribute to the Scoring Engine as additional factors | Phase 2 scoring extensibility |
| 6.3 | AI Reasoning Field | `Explainability.aiReasoning` field populated with LLM analysis | Phase 1 contract (already defined) |
| 6.4 | Hybrid Decision Mode | Decision Engine combines rule-based + AI evidence for hybrid recommendations | Phase 1 (source type already supports 'hybrid') |
| 6.5 | AI Confidence Calibration | Learning Engine tracks AI provider accuracy over time | Phase 1 learning engine |
| 6.6 | AI Provider Circuit Breaker | Fallback to rules-only mode when AI is unavailable | Phase 1 failure modes defined |
| 6.7 | AI Transparency Log | Every AI contribution logged with prompt, response, and confidence | Audit infrastructure from Phase 2 |
| 6.8 | AI Evaluation Framework | Measure AI provider quality: accuracy, latency, cost per decision | Learning Engine metrics |

### Architecture: AI as Evidence Provider

```
┌──────────────────────────────────────────────────────┐
│                   Decision Engine                     │
│                                                       │
│  Evidence Engine                                      │
│  ├── Company DNA Provider (existing)                  │
│  ├── Signal Provider (existing)                       │
│  ├── Timeline Provider (existing)                     │
│  ├── Pipeline Provider (existing)                     │
│  ├── Search Provider (existing)                       │
│  └── AI Agent Provider (future)  ← NEW               │
│                                                       │
│  Scoring Engine                                       │
│  ├── 40 existing factors (existing)                   │
│  └── AI-generated factors (future)  ← NEW             │
│                                                       │
│  Explainability                                       │
│  ├── Rule-based explanation (existing)                │
│  └── aiReasoning field (future)  ← ALREADY DEFINED   │
└──────────────────────────────────────────────────────┘
```

### Key Principle

> AI is a **contributor** to decisions, not the **decision maker**.
> The Decision Engine orchestrates all evidence sources (human, rules, AI)
> and produces the final recommendation. AI cannot override rules or
> bypass the explainability contract.

### Effort Estimate

| Sprint | Deliverables | Points |
|--------|-------------|--------|
| Sprint 6.1 | 6.1–6.2 (AI evidence + scoring providers) | 13 |
| Sprint 6.2 | 6.3–6.4 (AI reasoning + hybrid mode) | 8 |
| Sprint 6.3 | 6.5–6.6 (calibration + circuit breaker) | 8 |
| Sprint 6.4 | 6.7–6.8 (transparency log + evaluation framework) | 8 |
| **Total** | | **37 pts (4 sprints)** |

### Dependencies

- AI Agent infrastructure built (separate initiative)
- LLM provider selected and integrated
- Phase 2 complete (evidence provider registry)
- Phase 5 complete (testing infrastructure)

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI hallucination affects decision quality | High | High | AI is evidence only, never decision maker; confidence calibration |
| AI latency exceeds performance budgets | Medium | Medium | Async evaluation, cache AI results, circuit breaker |
| AI cost per decision too high | Medium | Medium | Batch AI calls, cache results, use smaller models for simple decisions |
| Regulatory requirements for AI transparency | Low | High | Full audit log of all AI contributions |

### Acceptance Criteria

- [ ] AI evidence items appear in Explainability with source tag
- [ ] AI reasoning field populated when AI provider available
- [ ] Circuit breaker triggers fallback to rules-only mode on AI failure
- [ ] Learning Engine tracks AI provider accuracy separately
- [ ] All decisions remain fully explainable with or without AI
- [ ] AI contribution logged with prompt, response, confidence, cost
- [ ] Performance budget maintained even with AI in the pipeline

---

## Summary

| Phase | Name | Status | Sprints | Points | Key Risk |
|-------|------|--------|---------|--------|----------|
| 1 | Foundation | ✅ Complete | — | ~20 | — |
| 2 | Backend Integration | 🟡 Next | 4 | 44 | Redis not deployed |
| 3 | Frontend Integration | ⬜ Planned | 4 | 32 | NBA refactor breaks UX |
| 4 | Widget Migration | ⬜ Planned | 5 | 52 | Deeply coupled inline logic |
| 5 | Testing & Validation | ⬜ Planned | 5 | 47 | Coverage target (85%) |
| 6 | AI Integration | ⬜ Future | 4 | 37 | AI hallucination |
| **Total** | | | **22** | **232** | |

### Critical Path

```
Phase 1 ✅ → Phase 2 → Phase 3 → Phase 4 → Phase 5
                                    ↗
                              Phase 6 (parallel with Phase 5)
```

### Quick Wins Available Now

1. **NBA Widget already benefits** from the Decision Engine in Phase 1
2. **Testing utilities** are ready for immediate use in any engine test
3. **Audit logging** works in-process before the database layer exists
4. **Explainability** is fully functional for any context passed to the engine

### Definition of Done (Platform Complete)

The Decision Intelligence Platform is considered **production-ready** when:

1. All 8 engines tested at ≥ 85% coverage
2. All 11 API endpoints deployed and documented
3. All 22 widgets consuming decisions from the platform
4. Zero inline scoring/reasoning in any widget
5. Performance budgets met under production load
6. Explainability validated by domain experts (EN + AR)
7. Security audit passed with zero Critical findings
8. Rollback plan documented and tested
