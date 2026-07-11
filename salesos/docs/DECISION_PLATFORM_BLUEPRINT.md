# Decision Intelligence Platform — Technical Blueprint

> Version: 1.0.0
> Status: Active
> Last Updated: 2026-07-10
> Package: `@salesos/decision-platform`

---

## 1. System Overview

### 1.1 Purpose

The Decision Intelligence Platform is the centralized commercial reasoning engine for SalesOS. It is the **single source of truth** for every recommendation, score, and insight across the entire product. No business logic, scoring, or reasoning lives outside this platform.

The platform answers three questions for every entity in the system:

1. **What should we do?** → Recommendation Engine
2. **Why should we do it?** → Explainability Engine
3. **How confident are we?** → Scoring Engine + Evidence Engine

### 1.2 Key Design Principles

| Principle | Meaning |
|-----------|---------|
| **Explainable** | Every recommendation exposes `why`, `whyNow`, `whyThisAction`, `whyNotAlternative`. No black-box decisions. |
| **Auditable** | Every evaluation is logged with actor, timestamp, rules applied, evidence used, and outcome. Reproducible. |
| **Deterministic** | Given identical inputs, the platform produces identical outputs. No randomness, no external API calls during evaluation. |
| **No React** | Zero UI dependencies. Pure TypeScript. Can run in Node.js, browser, edge workers, or test environments. |
| **Tenant-Isolated** | All state is partitioned by `tenantId`. No cross-tenant data leakage. |
| **Fail-Degraded** | Missing evidence sources lower confidence rather than crash. Missing rules skip rather than throw. |

### 1.3 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SalesOS Frontend                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │NBA Widget│ │Pipeline  │ │Company   │ │Revenue   │ │Executive │    │
│  │          │ │Intelli.  │ │Intelli.  │ │Health    │ │Dashboard │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │
│       └─────────────┴────────────┴─────────────┴────────────┘          │
│                              │ consumes                                 │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                    @salesos/decision-platform                           │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Decision Engine (Orchestrator)                 │  │
│  │  evaluate() → collectEvidence → applyRules → score → recommend   │  │
│  └──────┬──────────────┬──────────────┬──────────────┬──────────────┘  │
│         │              │              │              │                  │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐ ┌────▼────────────┐  │
│  │Rule Engine  │ │Scoring     │ │Evidence    │ │Recommendation   │  │
│  │             │ │Engine      │ │Engine      │ │Engine           │  │
│  │7 built-in   │ │8 score     │ │5 providers │ │8 action types   │  │
│  │rules        │ │types       │ │dedup+rank  │ │scored+ranked    │  │
│  └─────────────┘ └────────────┘ └────────────┘ └─────────────────┘  │
│                                                                        │
│  ┌──────────────────┐ ┌───────────────┐ ┌────────────────────────┐   │
│  │Explainability    │ │Feedback       │ │Learning                │   │
│  │Engine            │ │Engine         │ │Engine                  │   │
│  │why/whyNow/whyNot│ │submit+stats   │ │trends+effectiveness    │   │
│  │bilingual ar/en   │ │revenue impact │ │signal usefulness       │   │
│  └──────────────────┘ └───────────────┘ └────────────────────────┘   │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Shared: generateId, clamp, weightedAverage, confidenceLabel,    │  │
│  │          freshnessLabel, deduplicateBy, paginate                 │  │
│  │  Telemetry: TelemetryCollector (in-memory event buffer)         │  │
│  │  Audit: AuditLogger (decision history + outcome tracking)       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   Data Providers     │
                    │                      │
                    │  Company DNA         │
                    │  Signals             │
                    │  Timeline            │
                    │  Search              │
                    │  Documents           │
                    │  Meetings            │
                    │  Emails              │
                    │  Pipeline            │
                    └─────────────────────┘
```

---

## 2. Module Map

### 2.1 Package Structure

```
packages/platform/decision/
├── index.ts                    # Public API barrel export
├── package.json                # @salesos/decision-platform v1.0.0
├── contracts/
│   └── index.ts                # All TypeScript types and interfaces
├── decision-engine/
│   └── index.ts                # Orchestrator: evaluate(), evaluateBatch(), explain(), getHistory()
├── rule-engine/
│   └── index.ts                # Rule registry, condition matching, conflict detection
├── scoring-engine/
│   └── index.ts                # 8 score types, factor configs, weighted computation
├── evidence-engine/
│   └── index.ts                # Provider-based evidence collection, dedup, freshness
├── recommendation-engine/
│   └── index.ts                # 8 action definitions, risk assessment, impact estimation
├── explainability-engine/
│   └── index.ts                # Bilingual (ar/en) explanation generation
├── feedback-engine/
│   └── index.ts                # Feedback submission, validation, stats
├── learning-engine/
│   └── index.ts                # Quality metrics, rule effectiveness, signal usefulness, trends
├── shared/
│   ├── index.ts                # Utility functions
│   ├── telemetry.ts            # TelemetryCollector class
│   └── audit.ts                # AuditLogger class
├── testing/
│   └── index.ts                # Mock factories + assertion helpers
└── __tests__/                  # Test suite (to be populated)
```

### 2.2 Module Responsibilities

#### `contracts` — Type Definitions

The single source of truth for every type crossing module boundaries. No module defines its own public types — all come from contracts.

| Type | Purpose |
|------|---------|
| `DecisionContext` | Input: tenantId, actorId, entity identifiers, metadata |
| `EvidenceItem` | Single evidence record with type, confidence, freshness |
| `DecisionRule` | Versioned business rule with conditions and action |
| `Score` | Normalized score (0-1) with factors, label, confidence |
| `ScoreFactor` | Individual factor contributing to a score |
| `Recommendation` | Primary action + alternatives, risks, confidence |
| `AlternativeRecommendation` | Rejected alternative with reason |
| `Risk` | Identified risk with level and mitigation |
| `Explainability` | Full explanation: why, whyNow, whyThisAction, whyNotAlternative |
| `Feedback` | User outcome: accepted/rejected/ignored + revenue impact |
| `LearningEvent` | Quality metric event for trend tracking |
| `DecisionResult` | Complete evaluation output with all components |
| `DecisionHistoryItem` | Lightweight history record |

Type aliases: `DecisionStatus`, `ConfidenceLabel`, `DecisionSource`, `SignalSeverity`, `RiskLevel`, `EvidenceType`, `ScoreType`, `OutcomeValue`.

#### `decision-engine` — Orchestrator

The central coordinator. Receives a `DecisionContext`, orchestrates the full evaluation pipeline, and returns a `DecisionResult`.

**State held:**
- `history: Map<string, DecisionResult>` — all evaluations by decision ID
- `historyByTenant: Map<string, string[]>` — decision ID lists per tenant

**API surface:**
```typescript
class DecisionEngine {
  evaluate(context: DecisionContext): Promise<DecisionResult>
  evaluateBatch(contexts: DecisionContext[]): Promise<DecisionResult[]>
  explain(decisionId: string): Promise<Explainability | null>
  getHistory(tenantId: string, limit?: number): Promise<DecisionHistoryItem[]>
}
```

**Singleton export:** `decisionEngine` — pre-instantiated for convenience.

#### `rule-engine` — Business Rules

Deterministic, versioned, auditable business rules. Evaluates conditions against evidence and context.

**State held:**
- `registry: Map<string, DecisionRule>` — registered rules by ID
- `version: string` — current rule set version

**Built-in rules (7):**

| ID | Category | Priority | Action | Condition |
|----|----------|----------|--------|-----------|
| `rule_expired_license` | risk | 90 | flag_as_risk | licenseStatus = 'expired' |
| `rule_high_revenue` | opportunity | 85 | flag_high_priority | opportunityValue > 500000 |
| `rule_no_decision_maker` | risk | 80 | flag_as_risk | decisionMakersCount <= 0 |
| `rule_government_tender` | strategic | 75 | flag_strategic | hasGovernmentContracts = true |
| `rule_high_hiring_growth` | intent | 70 | flag_intent_signal | hiringTrend = 'growing' |
| `rule_relationship_strength` | relationship | 65 | flag_strong_relationship | relationshipScore > 0.7 |
| `rule_low_confidence` | warning | 60 | flag_warning | evidenceConfidence < 0.4 |

**Condition operators:** `=`, `!=`, `gt`, `lt`, `gte`, `lte`, `contains`, `in`, array inclusion.

**Conflict detection:** When two rules in the same category fire with conflicting actions, resolution is priority-based → weight-based → version-based.

**API surface:**
```typescript
class RuleEngine {
  register(rule: DecisionRule): void
  registerMany(rules: DecisionRule[]): void
  getRule(id: string): DecisionRule | undefined
  listRules(category?: string): DecisionRule[]
  getVersion(): string
  evaluate(context: DecisionContext, evidence: EvidenceItem[]): Promise<RuleEvaluationResult>
}
```

**Output:** `RuleEvaluationResult` with `rulesApplied`, `rulesFired`, `rulesConflicted`, `rulesSkipped`, and full `auditLog`.

#### `scoring-engine` — Score Computation

Produces normalized scores (0–1) across 8 dimensions. Each score type has a fixed factor configuration with weights that sum to 1.0.

**Score types and factors:**

| Type | Factors | Weight Distribution |
|------|---------|-------------------|
| `company` | financial_health, growth_trend, digital_presence, hiring_trend, procurement_maturity | 0.30 / 0.20 / 0.15 / 0.15 / 0.20 |
| `opportunity` | stage_weight, estimated_value, buying_intent, relationship_strength, confidence | 0.30 / 0.15 / 0.25 / 0.20 / 0.10 |
| `intent` | signal_activity, hiring_trend, government_exposure, expansion_potential, digital_engagement | 0.30 / 0.20 / 0.15 / 0.20 / 0.15 |
| `relationship` | connection_count, decision_maker_access, interaction_recency, meeting_frequency, email_engagement | 0.30 / 0.25 / 0.20 / 0.15 / 0.10 |
| `risk` | risk_level_raw, financial_volatility, market_volatility, competitive_threat, regulatory_exposure | 0.30 / 0.20 / 0.15 / 0.15 / 0.20 |
| `revenue` | estimated_value, win_probability, expansion_potential, cross_sell | 0.35 / 0.30 / 0.20 / 0.15 |
| `data_quality` | freshness, source_count, conflict_count, completeness | 0.30 / 0.20 / 0.25 / 0.25 |
| `confidence` | data_quality, evidence_count, source_reliability | 0.40 / 0.30 / 0.30 |

**Confidence formula:** `coverage(0.6) + avgValue(0.4)` where coverage = `min(factorCount / 3, 1)`.

**Labels:** excellent (>=0.9), good (>=0.7), moderate (>=0.5), low (>=0.3), poor (<0.3).

**API surface:**
```typescript
class ScoringEngine {
  score(type: ScoreType, factors: Record<string, number>, metadata?: Record<string, unknown>): Score
  scoreAll(factors: Record<string, Record<string, number>>): Score[]
}
```

#### `evidence-engine` — Evidence Collection

Collects, normalizes, deduplicates, and ranks evidence from multiple providers.

**Built-in providers (5):**

| Provider | Confidence | Freshness Max (hours) | Maps to Evidence Types |
|----------|-----------|----------------------|----------------------|
| `signals` | 0.85 | 24 | signal, government |
| `company_dna` | 0.90 | 24 | dna |
| `timeline` | 0.80 | 1 | timeline, meeting, email |
| `search` | 0.75 | 1 | search |
| `documents` | 0.85 | 24 | document |

**Freshness decay:** Evidence older than `freshnessMax` hours has confidence halved (`confidence * 0.5`).

**Freshness labels:** fresh (<1h), recent (<24h), stale (<168h), expired (>=168h).

**Deduplication:** Key = `type::normalizedDescription`. Higher confidence wins on collision.

**State held:**
- `store: Map<string, EvidenceItem[]>` — keyed by `${tenantId}::${entityId}`

**API surface:**
```typescript
class EvidenceEngine {
  collect(context: DecisionContext, sources?: EvidenceSource[]): Promise<EvidenceCollectionResult>
  getRecent(tenantId: string, entityId: string, limit?: number): Promise<EvidenceItem[]>
}
```

#### `recommendation-engine` — Action Scoring

Evaluates 8 possible actions against current scores, rules, and evidence. Returns the highest-scoring action as the primary recommendation with alternatives.

**Action definitions (8):**

| Action | Label | Score Formula (simplified) | Min Thresholds |
|--------|-------|---------------------------|----------------|
| `meeting` | Arrange Meeting | intent×0.4 + relationship×0.35 + revenue×0.25 | intent>=0.6, relationship>=0.5 |
| `send_proposal` | Send Proposal | relationship×0.45 + intent×0.3 + revenue×0.25 | relationship>=0.6, intent>=0.5 |
| `call` | Make Call | intent×0.4 + relationship×0.35 | intent 0.3–0.75 |
| `follow_up` | Follow Up | intent×0.3 + dataQuality×0.2 + 0.25 | intent>=0.2 |
| `demo` | Product Demo | intent×0.35 + company×0.35 + relationship×0.2 | intent>=0.4, company>=0.4 |
| `nurture` | Nurture | (1-intent)×0.4 + (1-relationship)×0.3 + 0.15 | intent<=0.5, relationship<=0.6 |
| `escalate` | Escalate | revenue×0.45 + risk×0.35 + intent×0.2 | revenue>=0.6, risk>=0.4 |
| `research` | Research | (1-dataQuality)×0.6 + 0.2 | dataQuality<=0.6 |

**Risk assessment layers:**
1. Global risks: overall_risk (score>0.7→critical, >0.5→medium), conflicting signals (>2 high-severity), data quality (<0.3), readiness mismatch (high intent + low relationship), no rules triggered
2. Per-action risks: each action definition contributes its own risks (e.g., `meeting` flags insufficient_data when dataQuality<0.4)

**Priority determination:**
- P1: score>=0.8 AND intent>=0.7
- P2: score>=0.65 AND revenue>=0.5
- P3: score>=0.5
- P4: everything else

**API surface:**
```typescript
class RecommendationEngine {
  generate(
    context: DecisionContext,
    scores: Score[],
    rulesApplied: DecisionRule[],
    evidence: EvidenceItem[],
  ): Promise<Recommendation>
}
```

#### `explainability-engine` — Human-Readable Explanations

Generates bilingual (Arabic/English) explanations for every recommendation.

**Locale detection:** Checks `context.metadata?.locale === 'ar'`.

**Explanation components:**

| Field | Source | Logic |
|-------|--------|-------|
| `why` | Top 3 scores + top 2 evidence | "Recommendation to {action} due to {reason}. Key scores: {scores}. Primary evidence: {evidence}." |
| `whyNow` | Recent signals (≤30 days) + top 2 triggered rules | "Right now due to recent signal: {signals} and triggered rules: {rules}." |
| `whyThisAction` | Top score + alternatives count + expected revenue | "This action is optimal because {reason}. Compared against {N} alternatives." |
| `whyNotAlternative` | Each alternative | "{action} was not chosen because {reason}. Confidence: X% vs Y%." |

**API surface:**
```typescript
class ExplainabilityEngine {
  explain(
    context: DecisionContext,
    recommendation: Recommendation,
    scores: Score[],
    rulesApplied: DecisionRule[],
    evidence: EvidenceItem[],
  ): Promise<Explainability>
}
```

#### `feedback-engine` — Outcome Tracking

Captures user responses to recommendations and computes aggregate statistics.

**Validation rules:**
- `decisionId`, `tenantId`, `actorId` — required
- `outcome` — must be `accepted`, `rejected`, or `ignored`
- `revenueImpact` — non-negative if provided
- `timeToExecution` — non-negative if provided

**Learning event emission:** On successful submission, emits a `LearningEvent` of type `acceptance_rate` with `value = 1` (accepted), `0` (rejected), or `0.5` (ignored).

**State held:**
- `feedbackStore: Map<string, FeedbackRecord>` — all feedback by ID
- `eventsByTenant: Map<string, LearningEvent[]>` — learning events per tenant

**Stats computed:**
```typescript
interface FeedbackStats {
  total: number
  accepted: number
  rejected: number
  ignored: number
  acceptanceRate: number        // accepted / total
  totalRevenueImpact: number
  averageTimeToExecution: number | null
}
```

**API surface:**
```typescript
class FeedbackEngine {
  submit(feedback: Feedback): Promise<{ id: string; accepted: boolean }>
  getByDecision(decisionId: string): Promise<Feedback | null>
  getByTenant(tenantId: string, limit?: number): Promise<Feedback[]>
  getStats(tenantId: string): Promise<FeedbackStats>
}
```

#### `learning-engine` — Quality Metrics

Tracks decision quality over time. No autonomous ML — pure metrics to improve future decisions.

**Event types tracked:**
- `recommendation_quality` — confidence scores over time
- `acceptance_rate` — from FeedbackEngine emissions
- `rule_effectiveness` — per-rule acceptance correlation
- `signal_usefulness` — per-signal-type acceptance correlation

**Metrics computed:**

| Metric | Method |
|--------|--------|
| `QualityMetrics` | average confidence, acceptance rate, high/med/low confidence distribution |
| `RuleEffectiveness[]` | per-rule: times applied, acceptance rate, average confidence |
| `SignalUsefulness[]` | per-signal: frequency, correlation with acceptance |
| `LearningTrend[]` | 7-day window: current vs previous period, trend direction, % change |

**Trend computation:** `currentValue` vs `previousValue` with 5% threshold for up/down/stable classification.

**State held:**
- `store: StoredEvent[]` — all learning events with tenantId

**API surface:**
```typescript
class LearningEngine {
  record(event: LearningEvent): Promise<void>
  recordWithTenant(event: LearningEvent, tenantId: string): Promise<void>
  getRecommendationQuality(tenantId: string): Promise<QualityMetrics>
  getAcceptanceRate(tenantId: string, days?: number): Promise<number>
  getRuleEffectiveness(tenantId: string): Promise<RuleEffectiveness[]>
  getSignalUsefulness(tenantId: string): Promise<SignalUsefulness[]>
  getTrends(tenantId: string): Promise<LearningTrend[]>
}
```

#### `shared` — Utilities

| Function | Signature | Purpose |
|----------|-----------|---------|
| `generateId` | `(prefix?: string) => string` | `prefix_timestamp32_random32` format |
| `nowISO` | `() => string` | Current ISO timestamp |
| `clamp` | `(value, min?, max?) => number` | Clamp to [0, 1] by default |
| `weightedAverage` | `(factors: {value, weight}[]) => number` | Weighted mean |
| `confidenceLabel` | `(value) => 'high' \| 'medium' \| 'low'` | >=0.7 high, >=0.4 medium, else low |
| `categorizeRisk` | `(value) => RiskLevel` | >=0.8 critical, >=0.6 high, >=0.3 medium, else low |
| `hoursAgo` | `(isoString) => number` | Hours elapsed since timestamp |
| `freshnessLabel` | `(hours) => string` | fresh/recent/stale/expired |
| `deduplicateBy` | `(items, keyFn, keepFn?) => T[]` | Dedup with optional conflict resolver |
| `paginate` | `(items, page, limit) => PaginatedResult` | Offset-based pagination |

#### `shared/telemetry` — Event Collection

In-memory telemetry buffer. Records named metrics with numeric values and string/number/boolean tags.

```typescript
class TelemetryCollector {
  record(name: string, value: number, tags?: Record<string, string | number | boolean>): void
  flush(): TelemetryEvent[]          // drain and return all events
  getEvents(): TelemetryEvent[]      // read without draining
  summary(): Record<string, { count, avg, min, max }>  // aggregate stats
}
```

**Singleton:** `telemetry` — shared across all modules.

#### `shared/audit` — Decision Audit Log

Immutable log of every decision evaluation with outcome tracking.

```typescript
class AuditLogger {
  log(result: DecisionResult): void
  updateOutcome(decisionId: string, outcome: string): void
  getByTenant(tenantId: string): AuditEntry[]
  getByDecision(decisionId: string): AuditEntry | undefined
  getAll(): AuditEntry[]
  getRecent(limit?: number): AuditEntry[]
}
```

**Singleton:** `auditLogger` — shared across all modules.

#### `testing` — Mock Factories + Assertions

| Factory | Creates |
|---------|---------|
| `createMockContext(overrides?)` | `DecisionContext` with test defaults |
| `createMockEvidence(overrides?)` | `EvidenceItem` |
| `createMockRule(overrides?)` | `DecisionRule` |
| `createMockScore(overrides?)` | `Score` |
| `createMockRecommendation(overrides?)` | `Recommendation` with Arabic labels |
| `createMockFeedback(overrides?)` | `Feedback` |
| `createMockLearningEvent(overrides?)` | `LearningEvent` |
| `createMockDecisionResult(overrides?)` | Complete `DecisionResult` |

| Assertion | Validates |
|-----------|-----------|
| `assertValidRecommendation(rec)` | id, action, confidence in [0,1], confidenceLabel, reason, alternatives[], evidence[], risks[] |
| `assertValidScore(score)` | value in [0,1], factors[] non-empty |
| `assertValidExplainability(exp)` | why, whyNow, whyThisAction strings, arrays present |

### 2.3 Module Dependencies

```
contracts ← (no dependencies — pure types)
shared ← contracts (imports types for audit)
shared/telemetry ← (no dependencies)
shared/audit ← contracts
rule-engine ← contracts
scoring-engine ← contracts
evidence-engine ← contracts
recommendation-engine ← contracts
explainability-engine ← contracts
feedback-engine ← contracts
learning-engine ← contracts
decision-engine ← contracts, shared, (delegates to each engine)
testing ← contracts
```

**Dependency direction:** All modules depend only on `contracts`. No module depends on another engine module. The `decision-engine` orchestrator imports all engines but no engine imports another engine.

### 2.4 Public API Surface

The barrel export at `index.ts` exposes:

```typescript
// Types
export * from './contracts'

// Engines
export { DecisionEngine, decisionEngine } from './decision-engine'
export { RuleEngine } from './rule-engine'
export { ScoringEngine } from './scoring-engine'
export { EvidenceEngine } from './evidence-engine'
export { RecommendationEngine } from './recommendation-engine'
export { ExplainabilityEngine } from './explainability-engine'
export { FeedbackEngine } from './feedback-engine'
export { LearningEngine } from './learning-engine'

// Shared utilities
export {
  generateId, nowISO, clamp, weightedAverage,
  confidenceLabel, categorizeRisk, hoursAgo,
  freshnessLabel, deduplicateBy, paginate,
} from './shared'

// Telemetry & Audit
export { telemetry, TelemetryCollector } from './shared/telemetry'
export { auditLogger, AuditLogger } from './shared/audit'
```

---

## 3. Data Flow

### 3.1 Decision Evaluation Flow

The complete evaluation pipeline executed by `DecisionEngine.evaluate()`:

```
Input: DecisionContext
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 1: Generate decisionId                 │
│   crypto.randomUUID()                       │
│   Record evaluationStart = performance.now() │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 2: Collect Evidence                    │
│   collectEvidence(context)                  │
│   • Extract metadata key→value pairs        │
│   • Extract entityType, companyId,          │
│     opportunityId as evidence items         │
│   • Fallback: single "no evidence" item     │
│   • Record evidenceTimeMs                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 3: Apply Rules                         │
│   applyRules(context, evidence)             │
│   • Iterate BASE_RULES (4 rules)            │
│   • Quality rules: always applied           │
│   • Intent rules: check evidence signals    │
│   • Risk rules: check entityType            │
│   • Engagement rules: always applied        │
│   • Sort by priority desc, weight desc      │
│   • Record rulesTimeMs                      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 4: Compute Scores                      │
│   computeScores(context, evidence, rules)   │
│   • evidenceConfidence = avg(evidence.conf) │
│   • ruleWeight = avg(rules.weight)          │
│   • combinedScore = evidence×0.6 + rule×0.4 │
│   • Generate confidence score (always)      │
│   • Generate company score (if company)     │
│   • Generate revenue score (if opportunity) │
│   • Generate relationship score (if person) │
│   • Record scoringTimeMs                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 5: Generate Recommendation             │
│   generateRecommendation(ctx, evidence,     │
│     scores, rules, decisionId)              │
│   • Extract confidence score value          │
│   • Determine action: pursue/nurture/       │
│     deprioritize (or accelerate for opp)    │
│   • Build risks from confidence, evidence   │
│     count, rule count                       │
│   • Build alternatives (opposite actions)   │
│   • Record recommendationTimeMs             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 6: Build Explainability                │
│   buildExplainability(ctx, evidence, rules, │
│     recommendation, scores)                 │
│   • why: evidence + rules summary           │
│   • whyNow: timestamp + entity reference    │
│   • whyThisAction: action + confidence      │
│   • whyNotAlternative: from alternatives    │
│   • expectedImpact: revenue + timeframe     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 7: Assemble DecisionResult             │
│   { decisionId, context, recommendation,    │
│     scores, rulesApplied, evidence,         │
│     explainability, telemetry, timestamp }  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 8: Store in History                    │
│   history.set(decisionId, result)           │
│   historyByTenant[tenantId].push(id)        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
Output: DecisionResult
```

### 3.2 Evidence Collection Flow (EvidenceEngine.collect)

```
Input: DecisionContext + optional EvidenceSource[]
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 1: Determine data source               │
│   If sources provided → use external data   │
│   If no sources → generate synthetic items  │
│     from BUILTIN_PROVIDERS × matching types │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 2: Extract EvidenceItems               │
│   For each record in each source:           │
│   • Extract description (or fallback)       │
│   • Extract source, timestamp, severity     │
│   • Normalize confidence to [0, 1]          │
│   • Apply freshness decay if stale          │
│   • Collect remaining fields into data{}    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 3: Deduplicate                         │
│   Key = type::normalizeText(description)    │
│   Higher confidence wins on collision       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 4: Rank by Confidence                  │
│   Sort descending by confidence             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 5: Store for entity                    │
│   Append to store[tenantId::entityId]       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
Output: EvidenceCollectionResult
  { items, deduplicated, totalSources,
    averageConfidence, collectionTimeMs }
```

### 3.3 Scoring Computation Flow (ScoringEngine.score)

```
Input: ScoreType + factor values + optional metadata
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 1: Load SCORE_CONFIGS[type]            │
│   Get factor definitions with weights       │
│   Throw if unknown type                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 2: Normalize factors                   │
│   For each configured factor:               │
│   • raw = input[name] ?? 0                  │
│   • normalized = clamp(raw, 0, 1)           │
│   • Build ScoreFactor with weight, desc     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 3: Weighted aggregation                │
│   value = Σ(factor.value × factor.weight)   │
│           / Σ(factor.weight)                │
│   clamped to [0, 1]                         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 4: Compute confidence                  │
│   coverage = min(factorCount / 3, 1)        │
│   avgValue = weighted average               │
│   confidence = coverage×0.6 + avgValue×0.4  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
Output: Score
  { type, value, confidence, label, factors,
    timestamp }
```

### 3.4 Recommendation Generation Flow (RecommendationEngine.generate)

```
Input: DecisionContext + Score[] + DecisionRule[] + EvidenceItem[]
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 1: Score all 8 actions                 │
│   For each ACTION_DEFINITION:               │
│   • evaluate() → 0 to 0.95                  │
│   • Filter out score = 0                    │
│   • Sort descending by score                │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 2: Handle no-action case               │
│   If no actions scored > 0:                 │
│   → Return default "nurture" recommendation │
│     with confidence 0.3                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 3: Select primary + alternatives       │
│   primary = highest scored action           │
│   alternatives = next 3 scored actions      │
│   Each alternative gets: action, label,     │
│     reason, confidence, expectedRevenue     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 4: Assess global risks                 │
│   • overall_risk (score > 0.7 or > 0.5)    │
│   • conflicting_signals (>2 high severity)  │
│   • data_quality (< 0.3)                    │
│   • readiness_mismatch (high intent, low    │
│     relationship)                           │
│   • no_rules (no rules triggered)           │
│   Plus primary action's own risks           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 5: Select relevant evidence            │
│   • Keyword match per action type           │
│   • Fill remaining from unmatched evidence  │
│   • Limit to 5 items                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 6: Build Recommendation                │
│   • Determine source: hybrid/rule/ai        │
│   • Determine priority: P1-P4               │
│   • Build human-readable reason             │
│   • Attach expected revenue/effort/time     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
Output: Recommendation
```

### 3.5 Feedback Processing Flow

```
Input: Feedback { decisionId, outcome, ... }
  │
  ▼
┌─────────────────────────────────────────────┐
│ Step 1: Validate                            │
│   Check: decisionId, tenantId, actorId      │
│   Check: outcome ∈ {accepted, rejected,     │
│           ignored}                          │
│   Check: revenueImpact >= 0                 │
│   Check: timeToExecution >= 0               │
│   If invalid → return { id: '', accepted: false } │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 2: Store                               │
│   Generate UUID, timestamp                  │
│   Store in feedbackStore                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Step 3: Emit LearningEvent                  │
│   type: 'acceptance_rate'                   │
│   value: 1 (accepted) / 0 (rejected) /     │
│          0.5 (ignored)                      │
│   factors: { revenueImpact, timeToExec }    │
│   Store in eventsByTenant[tenantId]         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
Output: { id, accepted: true }
```

---

## 4. State Management

### 4.1 Engine State Inventory

| Engine | State | Type | Lifetime | Scope |
|--------|-------|------|----------|-------|
| `DecisionEngine` | `history` | `Map<string, DecisionResult>` | Process | All decisions |
| `DecisionEngine` | `historyByTenant` | `Map<string, string[]>` | Process | Tenant→decisions |
| `RuleEngine` | `registry` | `Map<string, DecisionRule>` | Process (mutable) | All rules |
| `EvidenceEngine` | `store` | `Map<string, EvidenceItem[]>` | Process | Tenant::Entity→evidence |
| `FeedbackEngine` | `feedbackStore` | `Map<string, FeedbackRecord>` | Process | All feedback |
| `FeedbackEngine` | `eventsByTenant` | `Map<string, LearningEvent[]>` | Process | Tenant→events |
| `LearningEngine` | `store` | `StoredEvent[]` | Process | All learning events |
| `TelemetryCollector` | `events` | `TelemetryEvent[]` | Process (drainable) | All telemetry |
| `AuditLogger` | `entries` | `AuditEntry[]` | Process | All audit entries |

### 4.2 In-Memory vs Persistent Storage

**Current state (v1.0.0):** All state is in-memory. This is intentional for:

- **Determinism:** No external I/O during evaluation
- **Testability:** Tests run with zero infrastructure
- **Performance:** Sub-millisecond state access
- **SDK bundling:** No database driver dependencies

**Future migration path:**

| Engine | In-Memory Now | Persistent Future | Trigger |
|--------|--------------|-------------------|---------|
| DecisionEngine | `Map` | PostgreSQL `decisions` table | Multi-instance deployment |
| RuleEngine | `Map` | PostgreSQL `rules` table + cache | Rule editing UI |
| EvidenceEngine | `Map` | Redis (ephemeral) + PostgreSQL (history) | High-volume evidence |
| FeedbackEngine | `Map` | PostgreSQL `feedback` table | Production analytics |
| LearningEngine | `Array` | PostgreSQL `learning_events` table | Trend analysis at scale |
| TelemetryCollector | `Array` | OpenTelemetry export | Observability stack |
| AuditLogger | `Array` | PostgreSQL `audit_log` table | Compliance requirements |

### 4.3 Caching Strategy

| Data | TTL | Invalidation | Notes |
|------|-----|-------------|-------|
| Rule evaluation results | 1 hour | Rule registry change | Per-tenant cache key |
| Scores | 15 min (live) / 1 hour (static) | New signal arrives | Per-entity cache key |
| Evidence | No cache | — | Always fresh collection |
| Recommendations | 5 min | New signal for same entity | Per-context cache key |
| Explainability | No cache | — | Generated on demand from existing data |

**Cache key format:** `${tenantId}:${entityType}:${entityId}:${decisionType}`

---

## 5. Integration Points

### 5.1 Frontend Consumption (Widgets)

Widgets import the platform as a TypeScript SDK. The SDK runs in the browser with zero server dependency for evaluation.

```typescript
// Widget usage pattern
import { DecisionEngine, createMockContext } from '@salesos/decision-platform'

const engine = new DecisionEngine()

// Evaluate a decision
const result = await engine.evaluate({
  tenantId: user.tenantId,
  actorId: user.id,
  companyId: company.id,
  entityType: 'company',
  metadata: { locale: 'ar', opportunityValue: 500000 },
})

// Render in widget
<Widget>
  <ConfidenceBadge value={result.recommendation.confidence} />
  <ActionCard action={result.recommendation} />
  <ExplainabilityPanel explainability={result.explainability} />
  <EvidenceList evidence={result.evidence} />
  <RiskIndicator risks={result.recommendation.risks} />
</Widget>
```

**Widget integration pattern:**

```
Widget Component
  │
  ├── useDecision(context) → DecisionResult
  │     ├── DecisionEngine.evaluate(context)
  │     ├── TelemetryCollector.record('widget.evaluate', latency)
  │     └── AuditLogger.log(result)
  │
  ├── useFeedback(decisionId) → submit Feedback
  │     └── FeedbackEngine.submit(feedback)
  │
  └── useExplainability(decisionId) → Explainability
        └── DecisionEngine.explain(decisionId)
```

### 5.2 Backend Wrapping (FastAPI)

The Python backend wraps the TypeScript SDK logic. Two approaches:

**Option A: Direct TypeScript SDK import (recommended)**
```python
# FastAPI endpoint wraps the SDK evaluation
from decision_platform import DecisionEngine

engine = DecisionEngine()

@router.post("/api/v1/decisions/evaluate")
async def evaluate_decision(context: DecisionContext):
    result = await engine.evaluate(context)
    return DecisionResultResponse(result)
```

**Option B: REST API wrapper**
```python
# FastAPI exposes the platform as REST endpoints
@router.post("/api/v1/decisions/evaluate")
async def evaluate_decision(request: EvaluateRequest):
    # Forward to TypeScript service or embed SDK
    result = await decision_service.evaluate(request.context)
    return result

@router.post("/api/v1/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    result = await feedback_engine.submit(feedback)
    return result

@router.get("/api/v1/decisions/{decisionId}/explain")
async def explain_decision(decisionId: str):
    result = await decision_engine.explain(decisionId)
    return result

@router.get("/api/v1/learning/{tenantId}/quality")
async def get_quality_metrics(tenantId: str):
    return await learning_engine.get_recommendation_quality(tenantId)
```

### 5.3 Future AI Agent Integration

AI agents will consume the platform through two interfaces:

**Agent as consumer (reads recommendations):**
```typescript
// Agent fetches recommendations for a portfolio
const results = await engine.evaluateBatch(
  companies.map(c => ({
    tenantId: agent.tenantId,
    actorId: agent.id,
    companyId: c.id,
    entityType: 'company' as const,
  }))
)

// Agent selects top recommendations for autonomous action
const highConfidence = results
  .filter(r => r.recommendation.confidence >= 0.8)
  .filter(r => r.recommendation.risks.every(r => r.level !== 'critical'))
```

**Agent as provider (feeds evidence):**
```typescript
// Agent submits enriched evidence to the platform
const sources: EvidenceSource[] = [{
  type: 'signal',
  provider: { name: 'ai_agent_enrichment', confidence: 0.80, freshnessMax: 12 },
  data: agent.enrichedSignals,
}]

const evidenceResult = await evidenceEngine.collect(context, sources)
```

**Agent feedback loop:**
```typescript
// Agent records outcome of autonomous action
await feedbackEngine.submit({
  decisionId: result.decisionId,
  tenantId: agent.tenantId,
  actorId: agent.id,
  outcome: 'accepted',
  revenueImpact: 250000,
  timeToExecution: 3600, // 1 hour
})
```

---

## 6. Deployment Strategy

### 6.1 TypeScript SDK (Frontend Bundle)

The platform ships as a TypeScript package bundled with the frontend.

**Bundle characteristics:**
- **Zero runtime dependencies** — only TypeScript peer dependency
- **Tree-shakeable** — import only needed engines
- **No external API calls** during evaluation
- **No React/UI dependencies** — pure computation

**Bundle size budget:**

| Module | Estimated Size | Included by Default |
|--------|---------------|-------------------|
| contracts | ~3 KB | Yes (types only, erased) |
| shared | ~2 KB | Yes |
| rule-engine | ~4 KB | Yes |
| scoring-engine | ~3 KB | Yes |
| evidence-engine | ~4 KB | Yes |
| recommendation-engine | ~6 KB | Yes |
| explainability-engine | ~3 KB | Yes |
| feedback-engine | ~2 KB | Yes |
| learning-engine | ~3 KB | Yes |
| decision-engine | ~4 KB | Yes |
| testing | ~4 KB | Test only |
| **Total** | **~34 KB** | **~30 KB (excl. testing)** |

### 6.2 Python Backend (Service Layer)

The Python backend wraps the SDK logic for server-side evaluation, batch processing, and persistent storage.

**Responsibilities:**
- Expose REST API for external consumers
- Persistent storage for decisions, feedback, learning events
- Tenant isolation enforcement
- Rate limiting and authentication
- Batch evaluation for portfolios
- Webhook delivery for high-confidence recommendations

**Storage schema (future):**

```sql
-- Decisions table
CREATE TABLE decisions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    entity_id UUID,
    entity_type VARCHAR(20),
    recommendation JSONB NOT NULL,
    scores JSONB NOT NULL,
    rules_applied JSONB NOT NULL,
    evidence JSONB NOT NULL,
    explainability JSONB NOT NULL,
    telemetry JSONB NOT NULL,
    outcome VARCHAR(20),
    revenue_impact DECIMAL(12,2),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY,
    decision_id UUID REFERENCES decisions(id),
    tenant_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    outcome VARCHAR(20) NOT NULL,
    reason TEXT,
    revenue_impact DECIMAL(12,2),
    time_to_execution INTEGER,
    created_at TIMESTAMPTZ NOT NULL
);

-- Learning events table
CREATE TABLE learning_events (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    type VARCHAR(30) NOT NULL,
    decision_id UUID,
    metric VARCHAR(50) NOT NULL,
    value DECIMAL(5,4) NOT NULL,
    factors JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

-- Rules table (for dynamic rule management)
CREATE TABLE rules (
    id VARCHAR(100) PRIMARY KEY,
    tenant_id UUID,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL,
    category VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    conditions JSONB NOT NULL,
    action VARCHAR(100) NOT NULL,
    weight DECIMAL(3,2) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

### 6.3 Testing Strategy

**Test pyramid:**

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲         10% — Full pipeline with real data
                 ╱──────╲
                ╱ Integr.╲       30% — Engine-to-engine interaction
               ╱──────────╲
              ╱   Unit     ╲     60% — Individual engine methods
             ╱──────────────╲
```

**Unit tests per engine:**

| Engine | Test Focus | Key Assertions |
|--------|-----------|---------------|
| `rule-engine` | Condition matching, conflict detection, priority ordering | All 7 built-in rules fire correctly; conflicts resolve by priority |
| `scoring-engine` | Weighted computation, label thresholds, confidence formula | All 8 score types; clamp behavior; factor coverage |
| `evidence-engine` | Dedup, freshness decay, provider defaults | Dedup keeps highest confidence; stale evidence penalty |
| `recommendation-engine` | Action scoring, risk assessment, alternative ranking | 8 actions scored correctly; risks match thresholds |
| `explainability-engine` | Bilingual output, explanation completeness | Arabic/English toggle; all fields populated |
| `feedback-engine` | Validation, stats computation | Invalid feedback rejected; stats accurate |
| `learning-engine` | Trend computation, metric aggregation | 7-day window trends; empty state handling |
| `decision-engine` | Full pipeline integration | evaluate() returns complete DecisionResult; history stored |
| `shared` | Utility correctness | clamp, weightedAverage, deduplicateBy, paginate |
| `telemetry` | Record, flush, summary | Events stored; flush drains; summary accurate |
| `audit` | Log, updateOutcome, queries | Entries stored; outcome updated; tenant filtering |

**Contract tests (using `testing/` module):**
```typescript
describe('DecisionPlatform Contract', () => {
  it('evaluate returns valid DecisionResult', async () => {
    const engine = new DecisionEngine()
    const context = createMockContext()
    const result = await engine.evaluate(context)
    
    assertValidRecommendation(result.recommendation)
    result.scores.forEach(assertValidScore)
    assertValidExplainability(result.explainability)
    
    expect(result.telemetry.evaluationTimeMs).toBeGreaterThan(0)
    expect(result.evidence.length).toBeGreaterThan(0)
    expect(result.rulesApplied.length).toBeGreaterThan(0)
  })
})
```

**Performance regression tests:**
```typescript
describe('Performance Budgets', () => {
  it('simple evaluation < 100ms', async () => {
    const engine = new DecisionEngine()
    const start = performance.now()
    await engine.evaluate(createMockContext())
    expect(performance.now() - start).toBeLessThan(100)
  })
})
```

---

## Appendix A: Performance Budgets

| Operation | Budget | Measurement Point |
|-----------|--------|-------------------|
| Decision evaluation (simple) | < 100ms | `DecisionEngine.evaluate()` |
| Decision evaluation (complex) | < 500ms | With external evidence sources |
| Recommendation generation | < 200ms | `RecommendationEngine.generate()` |
| Explainability generation | < 100ms | `ExplainabilityEngine.explain()` |
| Score computation | < 50ms | `ScoringEngine.score()` |
| Evidence retrieval | < 200ms | `EvidenceEngine.collect()` |
| Rule evaluation | < 20ms | `RuleEngine.evaluate()` |
| Feedback submission | < 10ms | `FeedbackEngine.submit()` |
| Batch evaluation (100 items) | < 5s | `DecisionEngine.evaluateBatch()` |

## Appendix B: Failure Modes

| Mode | Behavior | Recovery |
|------|----------|----------|
| Evidence source unavailable | Return degraded recommendation with lower confidence | Retry on next evaluation |
| Rule evaluation error | Skip rule, log error, continue with remaining rules | Alert on repeated failure |
| Scoring failure | Return partial scores with warning | Async retry |
| AI provider unavailable | Fall back to rules-only mode | Circuit breaker |
| Cache miss | Fresh computation | Update cache |
| Tenant context invalid | Reject with 403 | User re-authentication |
| Empty evidence | Return default "nurture" with confidence 0.3 | Collect more data |
| Conflicting rules | Priority-based resolution, audit logged | Review rule configuration |

## Appendix C: Security

- All decisions require a valid `tenantId` in `DecisionContext`
- Decision evaluation checks user permissions via Permission SDK
- Evidence access respects data access policies
- Feedback is tenant-isolated
- Audit log captures every decision with actor, timestamp, context
- No secrets in code — all credentials via environment variables
- All data encrypted at rest (AES-256) and in transit (TLS 1.3)

## Appendix D: Telemetry Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| `decision.evaluation.count` | counter | Volume tracking |
| `decision.evaluation.latency` | histogram | Performance monitoring |
| `decision.evaluation.by_type` | counter | Usage patterns by entity type |
| `recommendation.acceptance_rate` | gauge | Quality signal |
| `recommendation.by_source` | counter | Rule vs AI effectiveness |
| `evidence.retrieval.latency` | histogram | Source health |
| `scoring.by_type` | counter | Score distribution |
| `rule.evaluation.count` | counter | Rule usage frequency |
| `rule.conflict.rate` | gauge | Rule quality indicator |
| `feedback.submitted` | counter | Feedback volume |
| `feedback.revenue_impact` | histogram | Revenue tracking |
