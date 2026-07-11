# Decision Intelligence Platform — Component Catalog

> `@salesos/decision-platform` v1.0.0
> Last updated: 2026-07-11
> Source: `packages/platform/decision/`

---

## 1. Package Overview

The Decision Intelligence Platform is the centralized commercial reasoning engine for SalesOS. It provides a modular pipeline for evaluating business contexts, applying rules, computing scores, collecting evidence, generating actionable recommendations, producing explainable outputs, capturing feedback, and tracking learning signals.

**Architecture**: Each engine is a standalone class with no circular dependencies. Engines are composed via the orchestrating `DecisionEngine` or used independently for targeted concerns.

**Entry point**: `packages/platform/decision/index.ts`

---

## 2. Exports Table

Every symbol exported from `packages/platform/decision/index.ts`:

| Export Name | Type | Module Location | Description |
|---|---|---|---|
| `DecisionStatus` | type alias | `contracts` | Union: `'pending' \| 'accepted' \| 'dismissed' \| 'completed' \| 'failed'` |
| `ConfidenceLabel` | type alias | `contracts` | Union: `'high' \| 'medium' \| 'low'` |
| `DecisionSource` | type alias | `contracts` | Union: `'rule' \| 'ai' \| 'hybrid'` |
| `SignalSeverity` | type alias | `contracts` | Union: `'critical' \| 'high' \| 'medium' \| 'low'` |
| `RiskLevel` | type alias | `contracts` | Union: `'critical' \| 'high' \| 'medium' \| 'low'` |
| `EvidenceType` | type alias | `contracts` | Union: `'signal' \| 'document' \| 'timeline' \| 'dna' \| 'meeting' \| 'email' \| 'search' \| 'government'` |
| `ScoreType` | type alias | `contracts` | Union: `'company' \| 'opportunity' \| 'intent' \| 'relationship' \| 'risk' \| 'revenue' \| 'data_quality' \| 'confidence'` |
| `OutcomeValue` | type alias | `contracts` | Union: `'accepted' \| 'rejected' \| 'ignored'` |
| `DecisionContext` | interface | `contracts` | Input context for a decision evaluation |
| `EvidenceItem` | interface | `contracts` | A single piece of evidence supporting a decision |
| `DecisionRule` | interface | `contracts` | A business rule with conditions and actions |
| `Score` | interface | `contracts` | A computed score with factors and confidence |
| `ScoreFactor` | interface | `contracts` | Individual factor within a score |
| `Recommendation` | interface | `contracts` | The primary recommendation output |
| `AlternativeRecommendation` | interface | `contracts` | An alternative to the primary recommendation |
| `Risk` | interface | `contracts` | A risk item attached to a recommendation |
| `Explainability` | interface | `contracts` | Full explainability output for a decision |
| `Feedback` | interface | `contracts` | User feedback on a decision outcome |
| `LearningEvent` | interface | `contracts` | A learning signal for analytics and improvement |
| `DecisionResult` | interface | `contracts` | Complete result of a decision evaluation |
| `DecisionHistoryItem` | interface | `contracts` | Summary of a historical decision |
| `DecisionEngine` | class | `decision-engine` | Orchestrating engine — evaluates context through the full pipeline |
| `decisionEngine` | constant | `decision-engine` | Singleton instance of `DecisionEngine` |
| `RuleEngine` | class | `rule-engine` | Standalone rule evaluation with conflict detection |
| `ScoringEngine` | class | `scoring-engine` | Standalone multi-dimensional scoring |
| `EvidenceEngine` | class | `evidence-engine` | Evidence collection, deduplication, and storage |
| `RecommendationEngine` | class | `recommendation-engine` | Multi-action recommendation generation |
| `ExplainabilityEngine` | class | `explainability-engine` | Natural-language explainability (English + Arabic) |
| `FeedbackEngine` | class | `feedback-engine` | Feedback capture, validation, and statistics |
| `LearningEngine` | class | `learning-engine` | Learning signal aggregation, trends, and analytics |
| `generateId` | function | `shared` | Generates a prefixed unique ID (`prefix_ts_rand`) |
| `nowISO` | function | `shared` | Returns `new Date().toISOString()` |
| `clamp` | function | `shared` | Clamps a number between min/max (default 0-1) |
| `weightedAverage` | function | `shared` | Computes weighted average from `{value, weight}[]` |
| `confidenceLabel` | function | `shared` | Maps 0-1 to `'high' \| 'medium' \| 'low'` |
| `categorizeRisk` | function | `shared` | Maps 0-1 to `'critical' \| 'high' \| 'medium' \| 'low'` |
| `hoursAgo` | function | `shared` | Returns hours elapsed since an ISO timestamp |
| `freshnessLabel` | function | `shared` | Maps hours to `'fresh' \| 'recent' \| 'stale' \| 'expired'` |
| `deduplicateBy` | function | `shared` | Deduplicates an array by a key function with optional conflict resolver |
| `paginate` | function | `shared` | Paginates an array, returns `{items, total, page, hasMore}` |
| `telemetry` | constant | `shared/telemetry` | Singleton instance of `TelemetryCollector` |
| `TelemetryCollector` | class | `shared/telemetry` | Collects, flushes, and summarizes timing/value telemetry events |
| `auditLogger` | constant | `shared/audit` | Singleton instance of `AuditLogger` |
| `AuditLogger` | class | `shared/audit` | Logs every `DecisionResult` for audit trail and compliance |

---

## 3. Engine Catalog

### 3.1 DecisionEngine (Orchestrator)

> Source: `decision-engine/index.ts`
> Export status: **Ready**

The top-level orchestrator. Calls evidence collection, rule evaluation, scoring, recommendation generation, and explainability in sequence. Maintains an in-memory decision history per tenant.

**Constructor**

```ts
new DecisionEngine()
```

No parameters. State is held in-memory (two Maps: `history` and `historyByTenant`).

**Methods**

| Method | Signature | Description |
|---|---|---|
| `evaluate` | `(context: DecisionContext) => Promise<DecisionResult>` | Runs the full pipeline: collect evidence, apply rules, compute scores, generate recommendation, build explainability. Stores the result in history. Returns a complete `DecisionResult` with telemetry timings. |
| `evaluateBatch` | `(contexts: DecisionContext[]) => Promise<DecisionResult[]>` | Sequentially evaluates multiple contexts. Returns an array of results in order. |
| `explain` | `(decisionId: string) => Promise<Explainability \| null>` | Retrieves the explainability object for a previously evaluated decision. Returns `null` if not found. |
| `getHistory` | `(tenantId: string, limit?: number) => Promise<DecisionHistoryItem[]>` | Returns decision history for a tenant, optionally limited to the last N entries. |

**Built-in rules** (applied internally by the orchestrator):

| Rule ID | Category | Action | Weight | Description |
|---|---|---|---|---|
| `rule-high-intent` | intent | `accelerate` | 0.9 | Fires on high signal strength or >3 evidence items |
| `rule-risk-check` | risk | `assess_risk` | 0.7 | Fires for company/opportunity entity types |
| `rule-engagement` | engagement | `re_engage` | 0.5 | Always applied |
| `rule-data-quality` | quality | `validate` | 1.0 | Always applied (gate rule) |

---

### 3.2 RuleEngine

> Source: `rule-engine/index.ts`
> Export status: **Ready**

Standalone rule engine with condition matching, conflict detection, and audit logging. Supports complex condition operators (gt, lt, gte, lte, contains, in).

**Constructor**

```ts
new RuleEngine()
```

Pre-loads 7 built-in rules on instantiation.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `register` | `(rule: DecisionRule) => void` | Registers a single rule. Throws if a rule with the same ID already exists. |
| `registerMany` | `(rules: DecisionRule[]) => void` | Registers multiple rules. Silently skips duplicates. |
| `getRule` | `(id: string) => DecisionRule \| undefined` | Returns a copy of the rule with the given ID. |
| `listRules` | `(category?: string) => DecisionRule[]` | Returns all rules, or filtered by category. |
| `getVersion` | `() => string` | Returns the engine version (`'1.0.0'`). |
| `evaluate` | `(context: DecisionContext, evidence: EvidenceItem[]) => Promise<RuleEvaluationResult>` | Evaluates all registered rules against the context and evidence. Returns fired/skipped/conflicted rules plus an audit log. |

**Built-in rules** (auto-registered):

| Rule ID | Category | Priority | Action | Condition |
|---|---|---|---|---|
| `rule_expired_license` | risk | 90 | `flag_as_risk` | `licenseStatus === 'expired'` |
| `rule_high_revenue` | opportunity | 85 | `flag_high_priority` | `opportunityValue > 500000` |
| `rule_no_decision_maker` | risk | 80 | `flag_as_risk` | `decisionMakersCount <= 0` |
| `rule_government_tender` | strategic | 75 | `flag_strategic` | `hasGovernmentContracts === true` |
| `rule_high_hiring_growth` | intent | 70 | `flag_intent_signal` | `hiringTrend === 'growing'` |
| `rule_relationship_strength` | relationship | 65 | `flag_strong_relationship` | `relationshipScore > 0.7` |
| `rule_low_confidence` | warning | 60 | `flag_warning` | `evidenceConfidence < 0.4` |

**Exported interfaces**

| Interface | Fields | Description |
|---|---|---|
| `RuleEvaluationResult` | `rulesApplied`, `rulesFired`, `rulesConflicted`, `rulesSkipped`, `auditLog` | Complete output of `RuleEngine.evaluate()` |
| `RuleConflict` | `ruleA`, `ruleB`, `resolution`, `winner` | Describes a conflict between two rules and how it was resolved |

**Exported function**

| Function | Signature | Description |
|---|---|---|
| `createRule` | `(overrides: Partial<DecisionRule> & Pick<DecisionRule, 'name' \| 'description' \| 'action'>) => DecisionRule` | Factory function that generates a `DecisionRule` with sensible defaults. Auto-generates an ID. |

---

### 3.3 ScoringEngine

> Source: `scoring-engine/index.ts`
> Export status: **Ready**

Standalone scoring engine. Supports 8 score types, each with a predefined factor configuration.

**Constructor**

```ts
new ScoringEngine()
```

No parameters.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `score` | `(type: ScoreType, factors: Record<string, number>, metadata?: Record<string, unknown>) => Score` | Computes a single score of the given type. Maps raw factor values to the predefined config, normalizes to 0-1, computes weighted value and confidence. Throws on unknown type. |
| `scoreAll` | `(factors: Record<string, Record<string, number>>) => Score[]` | Computes scores for all provided types in a single call. Returns an array of `Score` objects. |

**Score type to factor configurations**

| Score Type | Factors (name: weight) |
|---|---|
| `company` | financial_health: 0.3, growth_trend: 0.2, digital_presence: 0.15, hiring_trend: 0.15, procurement_maturity: 0.2 |
| `opportunity` | stage_weight: 0.3, estimated_value: 0.15, buying_intent: 0.25, relationship_strength: 0.2, confidence: 0.1 |
| `intent` | signal_activity: 0.3, hiring_trend: 0.2, government_exposure: 0.15, expansion_potential: 0.2, digital_engagement: 0.15 |
| `relationship` | connection_count: 0.3, decision_maker_access: 0.25, interaction_recency: 0.2, meeting_frequency: 0.15, email_engagement: 0.1 |
| `risk` | risk_level_raw: 0.3, financial_volatility: 0.2, market_volatility: 0.15, competitive_threat: 0.15, regulatory_exposure: 0.2 |
| `revenue` | estimated_value: 0.35, win_probability: 0.3, expansion_potential: 0.2, cross_sell: 0.15 |
| `data_quality` | freshness: 0.3, source_count: 0.2, conflict_count: 0.25, completeness: 0.25 |
| `confidence` | data_quality: 0.4, evidence_count: 0.3, source_reliability: 0.3 |

**Exports**

| Name | Type | Description |
|---|---|---|
| `SCORE_CONFIGS` | constant | The full factor configuration map (`Record<ScoreType, FactorConfig[]>`) |
| `generateId` | function | Generates a base36 timestamp + random ID |

---

### 3.4 EvidenceEngine

> Source: `evidence-engine/index.ts`
> Export status: **Ready**

Collects evidence from multiple source types, deduplicates by content, ranks by confidence, and stores per tenant/entity.

**Constructor**

```ts
new EvidenceEngine()
```

No parameters. In-memory store.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `collect` | `(context: DecisionContext, sources?: EvidenceSource[]) => Promise<EvidenceCollectionResult>` | Collects evidence from provided sources or built-in providers. Deduplicates, ranks by confidence, stores results. Returns items with metadata. |
| `getRecent` | `(tenantId: string, entityId: string, limit?: number) => Promise<EvidenceItem[]>` | Retrieves the most recent evidence items for a tenant/entity, ranked by confidence. Default limit: 50. |

**Built-in providers**

| Provider | Confidence | Freshness Max (hours) |
|---|---|---|
| `signals` | 0.85 | 24 |
| `company_dna` | 0.90 | 24 |
| `timeline` | 0.80 | 1 |
| `search` | 0.75 | 1 |
| `documents` | 0.85 | 24 |

**Evidence type to provider mapping**

| Evidence Type | Provider |
|---|---|
| `signal` | signals |
| `document` | documents |
| `timeline` | timeline |
| `dna` | company_dna |
| `meeting` | timeline |
| `email` | timeline |
| `search` | search |
| `government` | signals |

**Exported interfaces**

| Interface | Fields | Description |
|---|---|---|
| `EvidenceProvider` | `name`, `confidence`, `freshnessMax` | Defines a named evidence source with reliability parameters |
| `EvidenceSource` | `type`, `provider`, `data` | A typed batch of records from a provider |
| `EvidenceCollectionResult` | `items`, `deduplicated`, `totalSources`, `averageConfidence`, `collectionTimeMs` | Output of `EvidenceEngine.collect()` |

---

### 3.5 RecommendationEngine

> Source: `recommendation-engine/index.ts`
> Export status: **Ready**

Generates actionable recommendations by evaluating 8 predefined action types against scores, rules, and evidence. Selects the best action, provides alternatives, and assesses risks.

**Constructor**

```ts
new RecommendationEngine()
```

No parameters.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `generate` | `(context: DecisionContext, scores: Score[], rulesApplied: DecisionRule[], evidence: EvidenceItem[]) => Promise<Recommendation>` | Evaluates all action definitions, ranks by score, and returns the top recommendation with alternatives, risks, and impact estimates. |

**Registered action types**

| Action | Action Label | Primary Signal | Min Thresholds |
|---|---|---|---|
| `meeting` | Arrange Meeting | intent >= 0.6, relationship >= 0.5 | High intent + relationship |
| `send_proposal` | Send Proposal | relationship >= 0.6, intent >= 0.5 | Strong relationship |
| `call` | Make Call | intent 0.3-0.75 | Medium intent (re-engagement) |
| `follow_up` | Follow Up | intent >= 0.2 | Any positive intent |
| `demo` | Product Demo | intent >= 0.4, company >= 0.4 | Qualified entity |
| `nurture` | Nurture | intent <= 0.5, relationship <= 0.6 | Early stage |
| `escalate` | Escalate | revenue >= 0.6, risk >= 0.4 | High-value + risk |
| `research` | Research | data_quality <= 0.6 | Low data quality |

---

### 3.6 ExplainabilityEngine

> Source: `explainability-engine/index.ts`
> Export status: **Ready**

Generates human-readable explainability narratives in English and Arabic (locale: `context.metadata.locale === 'ar'`).

**Constructor**

```ts
new ExplainabilityEngine()
```

No parameters.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `explain` | `(context: DecisionContext, recommendation: Recommendation, scores: Score[], rulesApplied: DecisionRule[], evidence: EvidenceItem[]) => Promise<Explainability>` | Produces a full explainability object with `why`, `whyNow`, `whyThisAction`, `whyNotAlternative`, top evidence, applied rules, confidence, risk, and expected impact. |

**Output fields**

| Field | Description |
|---|---|
| `why` | Top scores and evidence summary |
| `whyNow` | Recent signals and triggered rules |
| `whyThisAction` | Why this action was chosen over alternatives |
| `whyNotAlternative` | Per-alternative rejection rationale |
| `evidence` | Top 5 evidence items by confidence |
| `rulesApplied` | Copy of all applied rules |
| `aiReasoning` | `null` (reserved for future AI integration) |
| `confidence` | Inherited from recommendation |
| `risk` | Highest risk level from recommendation risks |
| `expectedImpact` | Revenue estimate and timeframe |

---

### 3.7 FeedbackEngine

> Source: `feedback-engine/index.ts`
> Export status: **Ready**

Captures user feedback on decisions, validates input, and computes aggregate statistics.

**Constructor**

```ts
new FeedbackEngine()
```

No parameters. In-memory store.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `submit` | `(feedback: Feedback) => Promise<{id: string; accepted: boolean}>` | Validates and stores feedback. Returns `{id, accepted: true}` on success, `{id: '', accepted: false}` on validation failure. Also emits a `LearningEvent`. |
| `getByDecision` | `(decisionId: string) => Promise<Feedback \| null>` | Retrieves feedback for a specific decision ID. |
| `getByTenant` | `(tenantId: string, limit?: number) => Promise<Feedback[]>` | Retrieves feedback for a tenant. Default limit: 50. |
| `getStats` | `(tenantId: string) => Promise<FeedbackStats>` | Computes acceptance rate, revenue impact, and execution time stats for a tenant. |

**Exported interfaces**

| Interface | Fields | Description |
|---|---|---|
| `FeedbackRecord` | extends `Feedback` + `id`, `createdAt` | Internal record with generated fields |
| `FeedbackStats` | `total`, `accepted`, `rejected`, `ignored`, `acceptanceRate`, `totalRevenueImpact`, `averageTimeToExecution` | Aggregate statistics |

**Validation rules**

| Field | Rule |
|---|---|
| `decisionId` | Required |
| `tenantId` | Required |
| `actorId` | Required |
| `outcome` | Must be `'accepted'`, `'rejected'`, or `'ignored'` |
| `revenueImpact` | Cannot be negative (if provided) |
| `timeToExecution` | Cannot be negative (if provided) |

---

### 3.8 LearningEngine

> Source: `learning-engine/index.ts`
> Export status: **Ready**

Aggregates learning events to compute quality metrics, rule effectiveness, signal usefulness, and time-based trends.

**Constructor**

```ts
new LearningEngine()
```

No parameters. In-memory store.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `record` | `(event: LearningEvent) => Promise<void>` | Records a learning event (no tenant scoping). |
| `recordWithTenant` | `(event: LearningEvent, tenantId: string) => Promise<void>` | Records a learning event scoped to a tenant. |
| `getRecommendationQuality` | `(tenantId: string) => Promise<QualityMetrics>` | Computes average confidence, acceptance rate, and confidence distribution. |
| `getAcceptanceRate` | `(tenantId: string, days?: number) => Promise<number>` | Acceptance rate over a rolling window (default 30 days). |
| `getRuleEffectiveness` | `(tenantId: string) => Promise<RuleEffectiveness[]>` | Per-rule application count, acceptance rate, and average confidence. |
| `getSignalUsefulness` | `(tenantId: string) => Promise<SignalUsefulness[]>` | Per-signal frequency and correlation with acceptance. |
| `getTrends` | `(tenantId: string) => Promise<LearningTrend[]>` | Week-over-week trends for acceptance rate, recommendation quality, rule effectiveness, and signal usefulness. |

**Exported interfaces**

| Interface | Fields | Description |
|---|---|---|
| `QualityMetrics` | `averageConfidence`, `averageAcceptanceRate`, `totalRecommendations`, `highConfidenceRate`, `mediumConfidenceRate`, `lowConfidenceRate` | Aggregate recommendation quality metrics |
| `RuleEffectiveness` | `ruleId`, `ruleName`, `timesApplied`, `acceptanceRate`, `averageConfidence` | Per-rule effectiveness breakdown |
| `SignalUsefulness` | `signalType`, `frequency`, `correlationWithAcceptance` | Per-signal usage and effectiveness |
| `LearningTrend` | `metric`, `currentValue`, `previousValue`, `trend`, `changePercent` | Week-over-week trend for a metric |

---

## 4. Contract Catalog

All TypeScript types and interfaces defined in `contracts/index.ts`.

### 4.1 Type Aliases

| Type | Values |
|---|---|
| `DecisionStatus` | `'pending'`, `'accepted'`, `'dismissed'`, `'completed'`, `'failed'` |
| `ConfidenceLabel` | `'high'`, `'medium'`, `'low'` |
| `DecisionSource` | `'rule'`, `'ai'`, `'hybrid'` |
| `SignalSeverity` | `'critical'`, `'high'`, `'medium'`, `'low'` |
| `RiskLevel` | `'critical'`, `'high'`, `'medium'`, `'low'` |
| `EvidenceType` | `'signal'`, `'document'`, `'timeline'`, `'dna'`, `'meeting'`, `'email'`, `'search'`, `'government'` |
| `ScoreType` | `'company'`, `'opportunity'`, `'intent'`, `'relationship'`, `'risk'`, `'revenue'`, `'data_quality'`, `'confidence'` |
| `OutcomeValue` | `'accepted'`, `'rejected'`, `'ignored'` |

### 4.2 Interfaces

#### DecisionContext

Input context for a decision evaluation.

```ts
interface DecisionContext {
  tenantId: string              // Required. Multi-tenant isolation key.
  actorId: string               // Required. Who initiated the decision.
  entityId?: string             // Optional. The entity being evaluated.
  entityType?: 'company' | 'opportunity' | 'person'  // Optional. Entity classification.
  opportunityId?: string        // Optional. Linked opportunity.
  companyId?: string            // Optional. Linked company.
  signalId?: string             // Optional. Triggering signal.
  metadata?: Record<string, unknown>  // Optional. Arbitrary context data.
}
```

#### EvidenceItem

A single piece of evidence supporting a decision.

```ts
interface EvidenceItem {
  id: string                    // Unique identifier.
  type: EvidenceType            // Category of evidence.
  description: string           // Human-readable description.
  source: string                // Origin of the evidence.
  confidence: number            // 0-1 confidence score.
  freshness: string             // Freshness label.
  timestamp: string             // ISO 8601 timestamp.
  severity?: SignalSeverity     // Optional severity level.
  url?: string                  // Optional reference URL.
  data?: Record<string, unknown>  // Optional raw data payload.
}
```

#### DecisionRule

A business rule with conditions and actions.

```ts
interface DecisionRule {
  id: string                    // Unique rule identifier.
  name: string                  // Human-readable name.
  description: string           // What the rule does.
  priority: number              // Higher = evaluated first.
  category: string              // Rule category (risk, intent, etc.).
  version: string               // Semver version string.
  conditions: Record<string, unknown>  // Condition map (supports operators).
  action: string                // Action to take when rule fires.
  weight: number                // 0-1 importance weight.
}
```

**Condition operators** (used in `RuleEngine`):

| Operator | Syntax | Description |
|---|---|---|
| Equality | `{ field: value }` | Exact match |
| Array inclusion | `{ field: [a, b, c] }` | Value in array |
| Greater than | `{ field: { gt: n } }` | `value > n` |
| Less than | `{ field: { lt: n } }` | `value < n` |
| Greater or equal | `{ field: { gte: n } }` | `value >= n` |
| Less or equal | `{ field: { lte: n } }` | `value <= n` |
| Contains | `{ field: { contains: "str" } }` | String includes |
| In list | `{ field: { in: [...] } }` | Value in list |

#### Score

A computed score with factors and confidence.

```ts
interface Score {
  type: ScoreType              // Which dimension was scored.
  value: number                // 0-1 normalized score.
  confidence: number           // 0-1 confidence in the score.
  label: string                // Human-readable label.
  factors: ScoreFactor[]       // Contributing factors.
  timestamp: string            // ISO 8601 timestamp.
}
```

#### ScoreFactor

Individual factor within a score.

```ts
interface ScoreFactor {
  name: string                 // Factor name.
  value: number                // 0-1 normalized value.
  weight: number               // Relative importance.
  description: string          // What this factor measures.
  source: string               // Data source.
}
```

#### Recommendation

The primary recommendation output.

```ts
interface Recommendation {
  id: string                   // Unique recommendation ID.
  action: string               // Action key (meeting, call, demo, etc.).
  actionLabel: string          // Human-readable action label.
  reason: string               // Explanation of why this action.
  confidence: number           // 0-1 confidence in recommendation.
  confidenceLabel: ConfidenceLabel  // 'high' | 'medium' | 'low'.
  source: DecisionSource       // How the recommendation was generated.
  priority: number             // 1 (highest) to 4 (lowest).
  expectedRevenue?: number     // Optional revenue estimate.
  expectedEffort?: string      // Estimated effort level.
  expectedTime?: string        // Estimated time to execute.
  businessImpact?: string      // Business impact description.
  alternatives: AlternativeRecommendation[]  // Alternative actions.
  evidence: EvidenceItem[]     // Supporting evidence.
  risks: Risk[]                // Associated risks.
  status: DecisionStatus       // Current status.
  createdAt: string            // ISO 8601 timestamp.
  updatedAt: string            // ISO 8601 timestamp.
}
```

#### AlternativeRecommendation

An alternative to the primary recommendation.

```ts
interface AlternativeRecommendation {
  action: string               // Action key.
  actionLabel: string          // Human-readable label.
  reason: string               // Why this is an alternative.
  confidence: number           // 0-1 confidence.
  expectedRevenue?: number     // Optional revenue estimate.
}
```

#### Risk

A risk item attached to a recommendation.

```ts
interface Risk {
  type: string                 // Risk category identifier.
  level: RiskLevel             // 'critical' | 'high' | 'medium' | 'low'.
  description: string          // What the risk is.
  mitigation?: string          // How to mitigate.
}
```

#### Explainability

Full explainability output for a decision.

```ts
interface Explainability {
  why: string                  // Why this recommendation was made.
  whyNow: string               // Why now is the right time.
  whyThisAction: string        // Why this specific action.
  whyNotAlternative: string[]  // Why alternatives were rejected.
  evidence: EvidenceItem[]     // Supporting evidence.
  rulesApplied: DecisionRule[] // Rules that fired.
  aiReasoning: string | null   // Reserved for AI (currently null).
  confidence: number           // 0-1 overall confidence.
  risk: RiskLevel              // Highest risk level.
  expectedImpact: {
    revenue: number            // Estimated revenue impact.
    timeframe: string          // Expected timeframe.
  }
}
```

#### Feedback

User feedback on a decision outcome.

```ts
interface Feedback {
  decisionId: string           // Which decision this feedback is about.
  tenantId: string             // Tenant isolation.
  actorId: string              // Who provided the feedback.
  outcome: OutcomeValue        // 'accepted' | 'rejected' | 'ignored'.
  reason?: string              // Optional explanation.
  revenueImpact?: number       // Optional actual revenue impact.
  timeToExecution?: number     // Optional time to execute (ms).
  actualEffort?: string        // Optional actual effort description.
  metadata?: Record<string, unknown>  // Optional extra data.
  timestamp: string            // ISO 8601 timestamp.
}
```

#### LearningEvent

A learning signal for analytics and improvement.

```ts
interface LearningEvent {
  id: string                   // Unique event ID.
  type: 'recommendation_quality' | 'acceptance_rate' | 'rule_effectiveness' | 'signal_usefulness' | 'evidence_quality'
  decisionId: string           // Linked decision.
  metric: string               // Metric name.
  value: number                // Metric value.
  factors: Record<string, number>  // Contributing factors.
  timestamp: string            // ISO 8601 timestamp.
}
```

#### DecisionResult

Complete result of a decision evaluation.

```ts
interface DecisionResult {
  decisionId: string           // Unique decision ID.
  context: DecisionContext     // The input context.
  recommendation: Recommendation  // The primary recommendation.
  scores: Score[]              // All computed scores.
  rulesApplied: DecisionRule[] // Rules that were evaluated/applied.
  evidence: EvidenceItem[]     // Collected evidence.
  explainability: Explainability  // Full explainability output.
  telemetry: {
    evaluationTimeMs: number   // Total evaluation time.
    rulesTimeMs: number        // Rule evaluation time.
    scoringTimeMs: number      // Scoring time.
    evidenceTimeMs: number     // Evidence collection time.
    recommendationTimeMs: number  // Recommendation generation time.
  }
  timestamp: string            // ISO 8601 timestamp.
}
```

#### DecisionHistoryItem

Summary of a historical decision.

```ts
interface DecisionHistoryItem {
  decisionId: string
  context: DecisionContext
  recommendation: {
    action: string
    actionLabel: string
    confidence: number
  }
  outcome: OutcomeValue | null
  revenueImpact: number | null
  createdAt: string
  updatedAt: string
}
```

---

## 5. Utility Catalog

Shared utility functions from `shared/index.ts`.

| Function | Signature | Description |
|---|---|---|
| `generateId` | `(prefix?: string) => string` | Generates `{prefix}_{base36Timestamp}_{random}`. Default prefix: `'dec'`. |
| `nowISO` | `() => string` | Returns `new Date().toISOString()`. |
| `clamp` | `(value: number, min?: number, max?: number) => number` | Clamps a number. Defaults: min=0, max=1. |
| `weightedAverage` | `(factors: {value: number; weight: number}[]) => number` | Computes weighted average. Returns 0 if total weight is 0. |
| `confidenceLabel` | `(value: number) => 'high' \| 'medium' \| 'low'` | >= 0.7 = high, >= 0.4 = medium, else low. |
| `categorizeRisk` | `(value: number) => 'critical' \| 'high' \| 'medium' \| 'low'` | >= 0.8 = critical, >= 0.6 = high, >= 0.3 = medium, else low. |
| `hoursAgo` | `(isoString: string) => number` | Returns hours elapsed since the given ISO timestamp. |
| `freshnessLabel` | `(hours: number) => 'fresh' \| 'recent' \| 'stale' \| 'expired'` | < 1h = fresh, < 24h = recent, < 168h = stale, else expired. |
| `deduplicateBy` | `<T>(items, keyFn, keepFn?) => T[]` | Deduplicates by key. Optional conflict resolver keeps one. |
| `paginate` | `<T>(items, page, limit) => {items, total, page, hasMore}` | Paginates an array (1-indexed pages). |

---

## 6. Telemetry and Audit Catalog

### TelemetryCollector

> Source: `shared/telemetry.ts`

Collects timing and value telemetry events. Provides a singleton `telemetry` instance.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `record` | `(name: string, value: number, tags?: Record<string, string \| number \| boolean>) => void` | Records a telemetry event with a name, numeric value, and optional tags. |
| `flush` | `() => TelemetryEvent[]` | Returns all buffered events and clears the buffer. |
| `getEvents` | `() => TelemetryEvent[]` | Returns a copy of all buffered events without clearing. |
| `summary` | `() => Record<string, {count, avg, min, max}>` | Groups events by name and computes count, avg, min, max. |

**TelemetryEvent interface**

```ts
interface TelemetryEvent {
  name: string
  value: number
  tags: Record<string, string | number | boolean>
  timestamp: string
}
```

### AuditLogger

> Source: `shared/audit.ts`

Logs every `DecisionResult` for audit trail and compliance. Provides a singleton `auditLogger` instance.

**Methods**

| Method | Signature | Description |
|---|---|---|
| `log` | `(result: DecisionResult) => void` | Logs a decision result with extracted scores, rule IDs, and recommendation. |
| `updateOutcome` | `(decisionId: string, outcome: string) => void` | Updates the outcome field on an existing audit entry. |
| `getByTenant` | `(tenantId: string) => AuditEntry[]` | Returns all audit entries for a tenant. |
| `getByDecision` | `(decisionId: string) => AuditEntry \| undefined` | Returns the audit entry for a specific decision. |
| `getAll` | `() => AuditEntry[]` | Returns all audit entries. |
| `getRecent` | `(limit?: number) => AuditEntry[]` | Returns the most recent N entries (default 50), newest first. |

**AuditEntry interface**

```ts
interface AuditEntry {
  decisionId: string
  tenantId: string
  actorId: string
  context: DecisionContext
  rulesApplied: string[]
  scores: Record<string, number>
  evidenceCount: number
  recommendation: string
  confidence: number
  outcome: string | null
  timestamp: string
}
```

---

## 7. Testing Catalog

Mock factories and assertion helpers from `testing/index.ts`.

### Mock Factories

| Function | Signature | Description |
|---|---|---|
| `createMockContext` | `(overrides?) => DecisionContext` | Creates a test context with `tenantId: 'tenant_test'`, `actorId: 'actor_test'`, `entityType: 'company'`. |
| `createMockEvidence` | `(overrides?) => EvidenceItem` | Creates a test evidence item with type `'signal'`, confidence 0.85. |
| `createMockRule` | `(overrides?) => DecisionRule` | Creates a test rule with category `'test'`, priority 50, weight 1.0. |
| `createMockScore` | `(overrides?) => Score` | Creates a test score of type `'company'`, value 0.75, confidence 0.85. |
| `createMockRecommendation` | `(overrides?) => Recommendation` | Creates a test recommendation with action `'meeting'`, confidence 0.85. |
| `createMockFeedback` | `(overrides?) => Feedback` | Creates a test feedback with outcome `'accepted'`. |
| `createMockLearningEvent` | `(overrides?) => LearningEvent` | Creates a test learning event of type `'recommendation_quality'`. |
| `createMockDecisionResult` | `(overrides?) => DecisionResult` | Creates a fully populated test decision result with all sub-objects. |

### Assertion Helpers

| Function | Description |
|---|---|
| `assertValidRecommendation(rec)` | Validates that a `Recommendation` has all required fields, confidence in [0,1], and correct types. |
| `assertValidScore(score)` | Validates that a `Score` has value in [0,1] and at least one factor. |
| `assertValidExplainability(exp)` | Validates that an `Explainability` has all required string/array fields. |

> **Note**: Assertion helpers use `expect` from the test framework (Jest). Import them alongside your test runner.

---

## 8. Quick Reference: Common Usage Patterns

### Full pipeline evaluation

```ts
import { DecisionEngine } from '@salesos/decision-platform'

const engine = new DecisionEngine()
const result = await engine.evaluate({
  tenantId: 't_123',
  actorId: 'u_456',
  entityId: 'company_789',
  entityType: 'company',
  metadata: { opportunityValue: 750000 },
})
// result.recommendation.action
// result.scores, result.explainability, result.telemetry
```

### Standalone scoring

```ts
import { ScoringEngine } from '@salesos/decision-platform'

const scoring = new ScoringEngine()
const score = scoring.score('opportunity', {
  stage_weight: 0.8,
  estimated_value: 0.6,
  buying_intent: 0.9,
  relationship_strength: 0.7,
  confidence: 0.85,
})
```

### Standalone rule evaluation

```ts
import { RuleEngine, createRule } from '@salesos/decision-platform'

const ruleEngine = new RuleEngine()
ruleEngine.register(createRule({
  name: 'Custom Rule',
  description: 'A custom business rule',
  action: 'flag_priority',
  conditions: { customField: { gt: 100 } },
  priority: 75,
  category: 'custom',
}))

const result = await ruleEngine.evaluate(context, evidence)
// result.rulesFired, result.rulesConflicted, result.auditLog
```

### Evidence collection

```ts
import { EvidenceEngine } from '@salesos/decision-platform'

const evidence = new EvidenceEngine()
const collected = await evidence.collect(context, [
  {
    type: 'signal',
    provider: { name: 'custom', confidence: 0.9, freshnessMax: 48 },
    data: [{ description: 'New signal', timestamp: new Date().toISOString() }],
  },
])
```

### Feedback and learning loop

```ts
import { FeedbackEngine, LearningEngine } from '@salesos/decision-platform'

const feedback = new FeedbackEngine()
const learning = new LearningEngine()

await feedback.submit({
  decisionId: 'dec_123',
  tenantId: 't_123',
  actorId: 'u_456',
  outcome: 'accepted',
  revenueImpact: 50000,
  timestamp: new Date().toISOString(),
})

const stats = await feedback.getStats('t_123')
// stats.acceptanceRate, stats.totalRevenueImpact
```

### Explainability (English + Arabic)

```ts
import { ExplainabilityEngine } from '@salesos/decision-platform'

const explainer = new ExplainabilityEngine()

// English
const en = await explainer.explain(context, recommendation, scores, rules, evidence)

// Arabic (set locale in context metadata)
const ar = await explainer.explain(
  { ...context, metadata: { locale: 'ar' } },
  recommendation, scores, rules, evidence,
)
// ar.why starts with Arabic text
```

---

*Generated from source code at `packages/platform/decision/`*
*For questions, contact the SalesOS Architecture team.*
