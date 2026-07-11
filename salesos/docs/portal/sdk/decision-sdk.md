# Decision Intelligence Platform SDK

> **منصة القرار — محرك التوصيات، التسجيل، القواعد، التفسير**

Package: `@salesos/decision-platform` | Status: **Active** | Version: v1.0.0

The Decision Intelligence Platform is the centralized commercial reasoning engine. Every recommendation, score, and insight across SalesOS flows through this platform.

---

## Installation

```bash
npm install @salesos/decision-platform
```

---

## Full Pipeline Evaluation

```typescript
import { decisionEngine } from '@salesos/decision-platform'

const result = await decisionEngine.evaluate({
  tenantId: 'tenant_abc',
  actorId: 'user_123',
  entityId: 'company_456',
  entityType: 'company',
  metadata: {
    signalStrength: 'high',
    opportunityValue: 750000,
  },
})

console.log(result.recommendation.action)      // 'pursue' | 'nurture' | 'deprioritize'
console.log(result.recommendation.confidence)  // 0.78
console.log(result.explainability.why)         // "4 evidence items collected..."
```

---

## Standalone Scoring

```typescript
import { ScoringEngine } from '@salesos/decision-platform'

const scoring = new ScoringEngine()

const score = scoring.score('company', {
  financial_health: 0.85,
  growth_trend: 0.72,
  digital_presence: 0.65,
  hiring_trend: 0.90,
  procurement_maturity: 0.70,
})

console.log(score.value)       // 0.772 (weighted average)
console.log(score.label)       // 'Good'
console.log(score.factors)     // Detailed breakdown
```

---

## Standalone Rule Evaluation

```typescript
import { RuleEngine, createRule } from '@salesos/decision-platform'

const engine = new RuleEngine()

// Add custom rule
engine.register(createRule({
  name: 'Saudi Expansion Signal',
  description: 'Flag companies expanding in Saudi Arabia',
  action: 'flag_strategic',
  category: 'intent',
  priority: 80,
  conditions: { region: 'Saudi Arabia', hiringTrend: 'growing' },
}))

const result = await engine.evaluate(context, evidence)
console.log(result.rulesFired)
console.log(result.auditLog)
```

---

## Evidence Collection

```typescript
import { EvidenceEngine } from '@salesos/decision-platform'

const evidence = new EvidenceEngine()

const collected = await evidence.collect(context, [
  {
    type: 'signal',
    provider: { name: 'custom', confidence: 0.9, freshnessMax: 48 },
    data: [{ description: 'New government contract', timestamp: new Date().toISOString() }],
  },
])
```

---

## Feedback & Learning

```typescript
import { FeedbackEngine, LearningEngine } from '@salesos/decision-platform'

const feedback = new FeedbackEngine()
const learning = new LearningEngine()

// Submit feedback
await feedback.submit({
  decisionId: result.decisionId,
  tenantId: 'tenant_abc',
  actorId: 'user_123',
  outcome: 'accepted',
  revenueImpact: 50000,
  timestamp: new Date().toISOString(),
})

// Get quality metrics
const quality = await learning.getRecommendationQuality('tenant_abc')
console.log(quality.acceptanceRate)         // 0.69
console.log(quality.averageConfidence)      // 0.72

// Get trends
const trends = await learning.getTrends('tenant_abc')
trends.forEach(t => console.log(t.metric, t.trend))
```

---

## Explainability (Bilingual)

```typescript
import { ExplainabilityEngine } from '@salesos/decision-platform'

const explainer = new ExplainabilityEngine()

// English
const en = await explainer.explain(context, recommendation, scores, rules, evidence)

// Arabic
const ar = await explainer.explain(
  { ...context, metadata: { locale: 'ar' } },
  recommendation, scores, rules, evidence,
)
```

---

## Testing Utilities

```typescript
import {
  createMockContext,
  createMockRecommendation,
  createMockDecisionResult,
  assertValidRecommendation,
} from '@salesos/decision-platform/testing'

const mockResult = createMockDecisionResult({
  recommendation: createMockRecommendation({ action: 'meeting', confidence: 0.85 }),
})

assertValidRecommendation(mockResult.recommendation)
```

---

## Architecture

```
                        Decision Engine (Orchestrator)
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
   Rule Engine              Scoring Engine              Evidence Engine
   (7 built-in rules)       (8 score types)            (5 providers)
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                    Recommendation Engine
                    (8 action types)
                                   │
                    Explainability Engine
                    (EN/AR bilingual)
                                   │
                    Feedback + Learning Engines
```

---

## Related

| Resource | Link |
|----------|------|
| Decision Architecture | [Architecture](../../docs/DECISION_PLATFORM_ARCHITECTURE.md) |
| Blueprint | [Blueprint](../../docs/DECISION_PLATFORM_BLUEPRINT.md) |
| API Mapping | [API Mapping](../../docs/DECISION_PLATFORM_API_MAPPING.md) |
| Component Catalog | [Component Catalog](../../docs/DECISION_PLATFORM_COMPONENT_CATALOG.md) |
| Decision Engine Guide | [Engine Guide](../.../docs/DECISION_ENGINE_GUIDE.md) |
| Rule Engine Guide | [Rule Guide](../../docs/RULE_ENGINE_GUIDE.md) |
