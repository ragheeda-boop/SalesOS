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
