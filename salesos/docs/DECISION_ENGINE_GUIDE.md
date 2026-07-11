# Decision Engine Guide

> Practical guide for the SalesOS Decision Intelligence Platform orchestrator.

---

## 1. What the Decision Engine Is

The Decision Engine (`salesos/packages/platform/decision/decision-engine/index.ts`) is the central orchestrator of the SalesOS Decision Intelligence Platform. It takes a `DecisionContext` — describing what entity you're evaluating and why — and returns a fully scored, explained, and actionable `DecisionResult`.

The pipeline runs four stages in sequence:

1. **Evidence Collection** — extracts signals from context (metadata, entity type, company/opportunity IDs)
2. **Rule Application** — matches 4 built-in base rules against collected evidence
3. **Scoring** — computes weighted scores (confidence, company, revenue, relationship)
4. **Recommendation** — generates an action (pursue, nurture, deprioritize, accelerate) with risks and alternatives

Every evaluation is stored in an in-memory history map keyed by tenant, enabling `explain()` and `getHistory()` calls after the fact.

---

## 2. How to Use It

### Import

```ts
import { decisionEngine } from '@salesos/decision/decision-engine'
// or
import { DecisionEngine } from '@salesos/decision/decision-engine'
const decisionEngine = new DecisionEngine()
```

A singleton `decisionEngine` is exported by default.

### 2.1 `evaluate(context)` — Single Evaluation

```ts
const result = await decisionEngine.evaluate({
  tenantId: 'tenant-abc',
  actorId: 'user-123',
  companyId: 'company-456',
  entityType: 'company',
  entityId: 'entity-789',
  metadata: {
    signalStrength: 'high',
    opportunityValue: 750000,
  },
})
```

Returns a `DecisionResult` (see Section 4).

### 2.2 `evaluateBatch(contexts)` — Batch Evaluation

```ts
const contexts: DecisionContext[] = [
  { tenantId: 't1', actorId: 'u1', entityType: 'company', companyId: 'c1' },
  { tenantId: 't1', actorId: 'u1', entityType: 'opportunity', opportunityId: 'o1' },
  { tenantId: 't1', actorId: 'u1', entityType: 'person', entityId: 'p1' },
]

const results = await decisionEngine.evaluateBatch(contexts)
// results[0], results[1], results[2] — each a full DecisionResult
```

Internally calls `evaluate()` sequentially for each context. All results are stored in history.

### 2.3 `explain(decisionId)` — Get Explanation

```ts
const explanation = await decisionEngine.explain(result.decisionId)

if (explanation) {
  console.log('Why:', explanation.why)
  console.log('Why now:', explanation.whyNow)
  console.log('Why this action:', explanation.whyThisAction)
  console.log('Why not alternatives:', explanation.whyNotAlternative)
  console.log('Expected revenue impact:', explanation.expectedImpact.revenue)
  console.log('Timeframe:', explanation.expectedImpact.timeframe)
}
```

Returns `null` if the decision ID is not found (e.g., from a different engine instance or after eviction).

### 2.4 `getHistory(tenantId, limit?)` — Get Decision History

```ts
const history = await decisionEngine.getHistory('tenant-abc', 10)
// Returns up to 10 most recent decisions for this tenant

for (const item of history) {
  console.log(`${item.decisionId}: ${item.recommendation.action} (${item.recommendation.confidence})`)
}
```

- `limit` is optional — omit to get all decisions for the tenant.
- Results are ordered chronologically (oldest first).
- History is in-memory only — does not persist across process restarts.

---

## 3. Creating a DecisionContext

```ts
interface DecisionContext {
  tenantId: string        // Required. Isolates data by tenant.
  actorId: string         // Required. The user or system triggering the evaluation.
  entityId?: string       // Optional. The entity being evaluated.
  entityType?: 'company' | 'opportunity' | 'person'  // Optional. Affects scoring and rules.
  opportunityId?: string  // Optional. Links to a specific opportunity.
  companyId?: string      // Optional. Links to a specific company.
  signalId?: string       // Optional. Links to a specific signal.
  metadata?: Record<string, unknown>  // Optional. Arbitrary key-value pairs fed as evidence.
}
```

### Field Details

| Field | Required | Description |
|-------|----------|-------------|
| `tenantId` | **Yes** | Tenant identifier. Used to scope history and evidence. |
| `actorId` | **Yes** | Who is making this decision request (user ID or system ID). |
| `entityId` | No | ID of the entity under evaluation. Appears in explainability. |
| `entityType` | No | `'company'`, `'opportunity'`, or `'person'`. Controls which scores are generated and which rules fire. |
| `opportunityId` | No | Ties the decision to an opportunity. Generates a timeline evidence item. |
| `companyId` | No | Ties the decision to a company. Generates a company evidence item. |
| `signalId` | No | Reference to a triggering signal (for audit purposes). |
| `metadata` | No | Arbitrary data. Each non-null key becomes an evidence item. Use this for custom signals like `signalStrength`, `opportunityValue`, `hiringTrend`, etc. |

### How metadata Becomes Evidence

Every key in `metadata` is collected as an `EvidenceItem` of type `'signal'` with confidence `0.7`. The key and serialized value appear in the description. Example:

```ts
metadata: {
  opportunityValue: 750000,
  hiringTrend: 'growing',
  region: 'Riyadh',
}
```

Produces 3 evidence items with descriptions like `"opportunityValue: 750000"`.

---

## 4. Interpreting a DecisionResult

```ts
interface DecisionResult {
  decisionId: string           // Unique ID for this evaluation
  context: DecisionContext     // The input context (echoed back)
  recommendation: Recommendation  // The actionable recommendation
  scores: Score[]              // Array of computed scores
  rulesApplied: DecisionRule[] // Rules that were evaluated
  evidence: EvidenceItem[]     // All evidence collected
  explainability: Explainability  // Full explanation object
  telemetry: {                 // Performance timing
    evaluationTimeMs: number
    rulesTimeMs: number
    scoringTimeMs: number
    evidenceTimeMs: number
    recommendationTimeMs: number
  }
  timestamp: string            // ISO timestamp
}
```

### Recommendation

The most important part. Key fields:

| Field | Description |
|-------|-------------|
| `action` | One of: `pursue`, `nurture`, `deprioritize`, `accelerate` |
| `actionLabel` | Human-readable: `"Pursue Immediately"`, `"Nurture & Monitor"`, `"Deprioritize"`, `"Accelerate Deal"` |
| `confidence` | 0.0–1.0 score |
| `confidenceLabel` | `high` (>=0.7), `medium` (0.4–0.7), `low` (<0.4) |
| `priority` | 1 (high), 2 (medium), 3 (low) |
| `alternatives` | Other considered actions with their confidence |
| `risks` | Array of detected risks with mitigation suggestions |
| `status` | Always starts as `'pending'` |

### Action Mapping

| Score Range | Standard Action | Opportunity Action |
|-------------|----------------|--------------------|
| >= 0.7 | `pursue` | `accelerate` |
| 0.4–0.7 | `nurture` | `nurture` |
| < 0.4 | `deprioritize` | `deprioritize` |

### Scores Array

Each `Score` contains:

- `type` — `'confidence'`, `'company'`, `'revenue'`, or `'relationship'` (depends on `entityType`)
- `value` — 0.0–1.0
- `label` — Human-readable label
- `factors` — Breakdown of what contributed to this score

The **confidence score** is always present. Others depend on entity type:

| entityType | Scores Generated |
|------------|-----------------|
| `'company'` or undefined | `confidence`, `company` |
| `'opportunity'` | `confidence`, `company`, `revenue` |
| `'person'` | `confidence`, `relationship` |

### Risks

Risks are auto-detected:

| Risk | Trigger | Level |
|------|---------|-------|
| `low_confidence` | Score < 0.4 | high |
| `insufficient_data` | < 2 evidence items | medium |
| `no_rules_matched` | 0 rules applied | medium |

---

## 5. Error Handling

The Decision Engine is designed to never throw — it degrades gracefully:

```ts
try {
  const result = await decisionEngine.evaluate(context)
  // Always succeeds
} catch (error) {
  // Should not happen, but handle defensively
  console.error('Unexpected engine failure:', error)
}
```

**Edge cases handled internally:**

- **Empty context** — produces 1 default evidence item with confidence 0.3, low scores, and a `deprioritize` recommendation.
- **No entityType** — only generates the confidence score (no company/revenue/relationship scores).
- **Empty metadata** — evidence collection skips null/undefined values silently.
- **History miss** — `explain()` returns `null`, `getHistory()` returns an empty array.

---

## 6. Performance Considerations

The engine tracks timing in the `telemetry` field of every result:

```ts
result.telemetry.evaluationTimeMs    // Total time
result.telemetry.evidenceTimeMs      // Evidence collection
result.telemetry.rulesTimeMs         // Rule matching
result.telemetry.scoringTimeMs       // Score computation
result.telemetry.recommendationTimeMs // Recommendation generation
```

**Key performance facts:**

- All 4 base rules are evaluated on every call (no early exit).
- Scoring is O(evidence × rules) — keep both small for best performance.
- History is in-memory (`Map`) — O(1) lookups, but unbounded memory growth.
- `evaluateBatch` is sequential, not parallel — for N contexts, total time ≈ N × single eval time.

**Recommendations:**

- Keep `metadata` lean — only include keys that rules actually check.
- Use `getHistory()` with a `limit` to avoid large payload transfers.
- For high-throughput scenarios, consider batching calls via `evaluateBatch` rather than many individual `evaluate` calls.

---

## 7. Examples

### Example 1: Company Evaluation

```ts
const result = await decisionEngine.evaluate({
  tenantId: 'acme-corp',
  actorId: 'sarah-sales',
  companyId: 'comp-12345',
  entityType: 'company',
  entityId: 'comp-12345',
  metadata: {
    signalStrength: 'high',
    lastContactDays: 5,
    employeeCount: 500,
  },
})

console.log(result.recommendation.action)       // 'pursue'
console.log(result.recommendation.confidence)   // ~0.82
console.log(result.recommendation.risks)        // [] (no risks)

// Later, explain the decision:
const why = await decisionEngine.explain(result.decisionId)
console.log(why?.why)  // "4 evidence items were collected from context; 3 business rules matched"
```

### Example 2: Opportunity Acceleration

```ts
const result = await decisionEngine.evaluate({
  tenantId: 'acme-corp',
  actorId: 'ahmed-am',
  entityType: 'opportunity',
  opportunityId: 'opp-67890',
  companyId: 'comp-12345',
  metadata: {
    signalStrength: 'high',
    opportunityValue: 1200000,
    daysInPipeline: 14,
  },
})

// High-value opportunity + high intent = accelerate
console.log(result.recommendation.action)       // 'accelerate'
console.log(result.recommendation.actionLabel)  // 'Accelerate Deal'

// Check the revenue score:
const revenueScore = result.scores.find(s => s.type === 'revenue')
console.log(revenueScore?.label)  // 'High potential'
```

### Example 3: Low-Data Person Evaluation

```ts
const result = await decisionEngine.evaluate({
  tenantId: 'acme-corp',
  actorId: 'system-auto',
  entityType: 'person',
  entityId: 'person-99999',
  metadata: {
    lastInteractionDays: 90,
  },
})

console.log(result.recommendation.action)        // 'deprioritize'
console.log(result.recommendation.risks.length)  // 2 (low confidence + insufficient data)

// Get alternatives
result.recommendation.alternatives.forEach(alt => {
  console.log(`${alt.actionLabel}: ${alt.confidence}`)
})
// "Pursue: 0.6"
// "Deprioritize: 0.45"
// "Gather More Evidence: 0.6"
```

### Example 4: Batch Evaluation + History

```ts
const contexts: DecisionContext[] = [
  {
    tenantId: 'acme-corp',
    actorId: 'sarah-sales',
    entityType: 'company',
    companyId: 'comp-001',
    metadata: { signalStrength: 'high' },
  },
  {
    tenantId: 'acme-corp',
    actorId: 'sarah-sales',
    entityType: 'opportunity',
    opportunityId: 'opp-002',
    metadata: { opportunityValue: 800000 },
  },
  {
    tenantId: 'acme-corp',
    actorId: 'sarah-sales',
    entityType: 'person',
    entityId: 'person-003',
  },
]

const results = await decisionEngine.evaluateBatch(contexts)

// Review all results
for (const r of results) {
  console.log(`${r.context.entityType}: ${r.recommendation.action} (${r.recommendation.confidence})`)
}

// Check tenant history
const history = await decisionEngine.getHistory('acme-corp', 2)
console.log(`${history.length} recent decisions`)  // 2
```
