# Decision Intelligence Platform — REST API Mapping

> **Status**: Draft
> **Last updated**: 2026-07-11
> **SDK source**: `packages/platform/decision/contracts/index.ts`
> **Base URL**: `/api/v1/decision`

This document maps every REST endpoint the Decision Intelligence Platform backend must expose. All request/response types are derived from the TypeScript SDK contracts. Backend engineers use this as the implementation reference.

---

## Table of Contents

- [Global Conventions](#global-conventions)
- [Decision Evaluation](#decision-evaluation)
- [Recommendations](#recommendations)
- [Scores](#scores)
- [Evidence](#evidence)
- [Feedback](#feedback)
- [Rules](#rules)
- [Learning](#learning)
- [Error Format](#error-format)
- [SDK Integration Notes](#sdk-integration-notes)

---

## Global Conventions

### Authentication

Every endpoint requires:

| Header | Description |
|--------|-------------|
| `Authorization` | `Bearer <jwt>` — identifies the user |
| `X-Tenant-Id` | Tenant identifier (also accepted as query/body param `tenantId`) |

The `tenantId` in request bodies and query params **must** match the `X-Tenant-Id` header. Mismatches return `403`.

### Rate Limiting

| Endpoint group | Limit | Window |
|----------------|-------|--------|
| `POST /evaluate` | 100 requests | 1 minute |
| `POST /batch` | 20 requests | 1 minute (counts as 1 per item above 10) |
| All other `POST` | 60 requests | 1 minute |
| All `GET` | 300 requests | 1 minute |

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 97
X-RateLimit-Reset: 1720720800
```

### Pagination

All list endpoints accept standard pagination:

| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | integer | `20` | `100` |
| `offset` | integer | `0` | — |

### Timestamps

All timestamps are ISO 8601 strings in UTC: `2026-07-11T14:30:00.000Z`

### Content-Type

All requests and responses use `application/json`.

---

## Decision Evaluation

### `POST /evaluate`

Evaluate a single decision context through the full Decision Engine pipeline.

**Purpose**: Entry point for all decision requests. Runs evidence collection → rule evaluation → scoring → recommendation generation → explainability in one call.

**Auth**: Required (tenant + user)
**Rate limit**: 100/min

#### Request

```json
// DecisionContext (from contracts/index.ts)
{
  "tenantId": "tenant_abc123",
  "actorId": "user_456",
  "entityId": "company_789",
  "entityType": "company",
  "opportunityId": "opp_101",
  "companyId": "company_789",
  "signalId": "sig_202",
  "metadata": {
    "signalStrength": "high",
    "source": "website_visit",
    "pageCount": 5
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenantId` | string | **yes** | Tenant scope |
| `actorId` | string | **yes** | User triggering the decision |
| `entityId` | string | no | Target entity ID |
| `entityType` | `"company" \| "opportunity" \| "person"` | no | Type of entity |
| `opportunityId` | string | no | Opportunity context |
| `companyId` | string | no | Company context |
| `signalId` | string | no | Signal context |
| `metadata` | Record<string, unknown> | no | Arbitrary key-value context |

#### Response — `200 OK`

```json
{
  "decisionId": "a1b2c3d4-...",
  "context": { "..." : "echo of request" },
  "recommendation": {
    "id": "a1b2c3d4-...",
    "action": "pursue",
    "actionLabel": "Pursue Immediately",
    "reason": "Based on 4 evidence items and 3 rules, the combined score is 78%.",
    "confidence": 0.78,
    "confidenceLabel": "high",
    "source": "hybrid",
    "priority": 1,
    "businessImpact": "Impact level: High",
    "alternatives": [
      {
        "action": "deprioritize",
        "actionLabel": "Deprioritize",
        "reason": "Conservative approach to focus resources elsewhere",
        "confidence": 0.22
      },
      {
        "action": "gather_evidence",
        "actionLabel": "Gather More Evidence",
        "reason": "Delay decision until more data is available",
        "confidence": 0.6
      }
    ],
    "evidence": [ "..." ],
    "risks": [],
    "status": "pending",
    "createdAt": "2026-07-11T14:30:00.000Z",
    "updatedAt": "2026-07-11T14:30:00.000Z"
  },
  "scores": [
    {
      "type": "confidence",
      "value": 0.78,
      "confidence": 0.83,
      "label": "High",
      "factors": [
        {
          "name": "evidence_strength",
          "value": 0.83,
          "weight": 0.6,
          "description": "Average confidence of collected evidence items",
          "source": "decision-engine.evidence"
        },
        {
          "name": "rule_alignment",
          "value": 0.7,
          "weight": 0.4,
          "description": "Average weight of applicable rules",
          "source": "decision-engine.rules"
        }
      ],
      "timestamp": "2026-07-11T14:30:00.000Z"
    },
    {
      "type": "company",
      "value": 0.78,
      "confidence": 0.83,
      "label": "Strong",
      "factors": [ "..." ],
      "timestamp": "2026-07-11T14:30:00.000Z"
    }
  ],
  "rulesApplied": [
    {
      "id": "rule-data-quality",
      "name": "Data Quality Gate",
      "description": "Ensure minimum data quality before action",
      "priority": 0,
      "category": "quality",
      "version": "1.0.0",
      "conditions": { "minConfidence": 0.3 },
      "action": "validate",
      "weight": 1.0
    }
  ],
  "evidence": [
    {
      "id": "uuid-...",
      "type": "signal",
      "description": "signalStrength: \"high\"",
      "source": "context.metadata",
      "confidence": 0.7,
      "freshness": "current",
      "timestamp": "2026-07-11T14:30:00.000Z",
      "data": { "key": "signalStrength", "rawValue": "high" }
    }
  ],
  "explainability": {
    "why": "4 evidence items were collected from context; 3 business rules matched",
    "whyNow": "Decision requested at 2026-07-11T14:30:00.000Z for entity company_789",
    "whyThisAction": "The 'pursue' action was recommended with 78% confidence based on combined scoring",
    "whyNotAlternative": [
      "Deprioritize: confidence 22% — Conservative approach to focus resources elsewhere",
      "Gather More Evidence: confidence 60% — Delay decision until more data is available"
    ],
    "evidence": [ "..." ],
    "rulesApplied": [ "..." ],
    "aiReasoning": null,
    "confidence": 0.78,
    "risk": "low",
    "expectedImpact": {
      "revenue": 78000,
      "timeframe": "30 days"
    }
  },
  "telemetry": {
    "evaluationTimeMs": 12,
    "rulesTimeMs": 2,
    "scoringTimeMs": 3,
    "evidenceTimeMs": 4,
    "recommendationTimeMs": 2
  },
  "timestamp": "2026-07-11T14:30:00.000Z"
}
```

#### Implementation Notes

- The `decisionId` is generated server-side. The SDK's `DecisionEngine.evaluate()` generates it with `crypto.randomUUID()`.
- The engine stores every result in history keyed by `decisionId` and `tenantId`. The backend must persist this to PostgreSQL (not in-memory).
- `telemetry` values inform performance monitoring. Log them to the telemetry pipeline.
- `explainability.aiReasoning` is `null` in rule-only mode. When AI reasoning is enabled, it contains the LLM's chain-of-thought string.

---

### `POST /batch`

Batch evaluate multiple decision contexts in a single request.

**Purpose**: Bulk operations — e.g., daily NBA refresh for all accounts in a pipeline stage. The SDK processes sequentially; the backend should parallelize internally.

**Auth**: Required (tenant + user)
**Rate limit**: 20/min (each item beyond 10 counts as 1 request)

#### Request

```json
[
  { "tenantId": "tenant_abc123", "actorId": "user_456", "entityId": "company_001", "entityType": "company" },
  { "tenantId": "tenant_abc123", "actorId": "user_456", "entityId": "company_002", "entityType": "company" },
  { "tenantId": "tenant_abc123", "actorId": "user_456", "entityId": "opp_003",   "entityType": "opportunity" }
]
```

| Field | Type | Required |
|-------|------|----------|
| (root) | DecisionContext[] | **yes**, max 50 items per request |

#### Response — `200 OK`

```json
{
  "results": [
    { "decisionId": "...", "context": "...", "recommendation": "...", "scores": "...", "..." : "..." },
    { "decisionId": "...", "context": "...", "recommendation": "...", "scores": "...", "..." : "..." },
    { "decisionId": "...", "context": "...", "recommendation": "...", "scores": "...", "..." : "..." }
  ],
  "summary": {
    "total": 3,
    "succeeded": 3,
    "failed": 0,
    "totalTimeMs": 38
  }
}
```

#### Implementation Notes

- Reject requests with more than 50 contexts (return `400`).
- If individual evaluations fail, include them in the results array with `status: "failed"` and an `error` field. Do not fail the entire batch.
- Consider queueing batches > 10 items to an async worker and returning a `202 Accepted` with a `batchId` for polling.

---

### `GET /:id/explain`

Retrieve the explainability record for a past decision.

**Purpose**: After a user sees a recommendation, they can click "Why?" to get the full reasoning chain. This endpoint retrieves the stored `Explainability` for that decision.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Path Params

| Param | Type | Required |
|-------|------|----------|
| `id` | string | **yes** — the `decisionId` |

#### Response — `200 OK`

```json
{
  "decisionId": "a1b2c3d4-...",
  "explainability": {
    "why": "3 evidence items were collected from context; 2 business rules matched",
    "whyNow": "Decision requested at 2026-07-11T14:30:00.000Z for entity company_789",
    "whyThisAction": "The 'nurture' action was recommended with 55% confidence based on combined scoring",
    "whyNotAlternative": [
      "Pursue: confidence 75% — If additional evidence is gathered, pursuing may become viable",
      "Deprioritize: confidence 45% — Conservative approach to focus resources elsewhere",
      "Gather More Evidence: confidence 60% — Delay decision until more data is available"
    ],
    "evidence": [ "..." ],
    "rulesApplied": [ "..." ],
    "aiReasoning": "The entity shows moderate intent signals but limited recent engagement...",
    "confidence": 0.55,
    "risk": "medium",
    "expectedImpact": {
      "revenue": 55000,
      "timeframe": "90 days"
    }
  }
}
```

#### Error Responses

| Status | Condition |
|--------|-----------|
| `404` | Decision ID not found or belongs to a different tenant |

#### Implementation Notes

- The explainability is computed at evaluation time and stored with the `DecisionResult`. This is a pure lookup, not a re-evaluation.
- The `aiReasoning` field may be `null`. The frontend should handle this gracefully (hide the "AI Reasoning" section).

---

### `GET /history`

Retrieve paginated decision history for a tenant.

**Purpose**: Powers the Decision History view — shows what decisions were made, when, and what the outcomes were.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tenantId` | string | **yes** | — | Tenant scope |
| `limit` | integer | no | `20` | Max results (1–100) |
| `offset` | integer | no | `0` | Skip N results |
| `entityType` | string | no | — | Filter by entity type |
| `outcome` | string | no | — | Filter by outcome (`accepted`, `rejected`, `ignored`, `null`) |
| `from` | string | no | — | ISO 8601 start date |
| `to` | string | no | — | ISO 8601 end date |

#### Response — `200 OK`

```json
{
  "items": [
    {
      "decisionId": "a1b2c3d4-...",
      "context": {
        "tenantId": "tenant_abc123",
        "actorId": "user_456",
        "entityId": "company_789",
        "entityType": "company"
      },
      "recommendation": {
        "action": "pursue",
        "actionLabel": "Pursue Immediately",
        "confidence": 0.78
      },
      "outcome": "accepted",
      "revenueImpact": 12500,
      "createdAt": "2026-07-11T14:30:00.000Z",
      "updatedAt": "2026-07-11T16:45:00.000Z"
    }
  ],
  "total": 142
}
```

#### Implementation Notes

- The SDK's `DecisionEngine.getHistory()` returns the simplified `DecisionHistoryItem` shape. The backend should query from persisted data, not the in-memory store.
- `outcome` is `null` when no feedback has been submitted yet.
- Order by `createdAt` descending (most recent first).

---

## Recommendations

### `GET /recommendations`

Get active recommendations for a tenant, optionally filtered by entity.

**Purpose**: Powers the Next Best Action widget and recommendation lists. Returns `Recommendation` objects with full detail including evidence, risks, and alternatives.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tenantId` | string | **yes** | — | Tenant scope |
| `entityId` | string | no | — | Filter by entity |
| `entityType` | string | no | — | Filter by entity type |
| `status` | string | no | `pending` | Filter by status: `pending`, `accepted`, `dismissed`, `completed`, `failed` |
| `limit` | integer | no | `20` | Max results |
| `offset` | integer | no | `0` | Skip N results |

#### Response — `200 OK`

```json
{
  "items": [
    {
      "id": "a1b2c3d4-...",
      "action": "pursue",
      "actionLabel": "Pursue Immediately",
      "reason": "Based on 4 evidence items and 3 rules, the combined score is 78%.",
      "confidence": 0.78,
      "confidenceLabel": "high",
      "source": "hybrid",
      "priority": 1,
      "expectedRevenue": null,
      "expectedEffort": null,
      "expectedTime": null,
      "businessImpact": "Impact level: High",
      "alternatives": [
        {
          "action": "deprioritize",
          "actionLabel": "Deprioritize",
          "reason": "Conservative approach to focus resources elsewhere",
          "confidence": 0.22
        }
      ],
      "evidence": [ "..." ],
      "risks": [],
      "status": "pending",
      "createdAt": "2026-07-11T14:30:00.000Z",
      "updatedAt": "2026-07-11T14:30:00.000Z"
    }
  ],
  "total": 8
}
```

#### Implementation Notes

- This endpoint aggregates from stored `DecisionResult` objects where `recommendation.status` matches the query filter.
- The SDK's `Recommendation` interface includes `alternatives`, `evidence`, and `risks` as nested arrays. The backend must serialize these fully.
- When `status` is not provided, default to `pending` — most consumers only want actionable recommendations.
- Consider adding a `sort` param (default: `priority asc, confidence desc`).

---

## Scores

### `GET /scores`

Get all scores for a specific entity.

**Purpose**: Powers score display in entity headers, list views, and health dashboards. Returns the full `Score[]` array with factors.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `tenantId` | string | **yes** | Tenant scope |
| `entityId` | string | **yes** | Target entity |
| `entityType` | string | **yes** | Entity type: `company`, `opportunity`, `person` |

#### Response — `200 OK`

```json
{
  "scores": [
    {
      "type": "confidence",
      "value": 0.78,
      "confidence": 0.83,
      "label": "High",
      "factors": [
        {
          "name": "evidence_strength",
          "value": 0.83,
          "weight": 0.6,
          "description": "Average confidence of collected evidence items",
          "source": "decision-engine.evidence"
        },
        {
          "name": "rule_alignment",
          "value": 0.7,
          "weight": 0.4,
          "description": "Average weight of applicable rules",
          "source": "decision-engine.rules"
        }
      ],
      "timestamp": "2026-07-11T14:30:00.000Z"
    },
    {
      "type": "company",
      "value": 0.78,
      "confidence": 0.83,
      "label": "Strong",
      "factors": [
        {
          "name": "context_completeness",
          "value": 0.8,
          "weight": 0.5,
          "description": "Completeness of available context",
          "source": "decision-engine.context"
        },
        {
          "name": "entity_type_match",
          "value": 1.0,
          "weight": 0.5,
          "description": "Whether entity type is specified",
          "source": "decision-engine.context"
        }
      ],
      "timestamp": "2026-07-11T14:30:00.000Z"
    }
  ]
}
```

#### Score Types Reference

| `type` | When present | `label` values |
|--------|-------------|----------------|
| `confidence` | Always | `High`, `Medium`, `Low` |
| `company` | `entityType = "company"` or omitted | `Strong`, `Moderate`, `Weak` |
| `revenue` | `entityType = "opportunity"` | `High potential`, `Moderate potential` |
| `relationship` | `entityType = "person"` | `Strong`, `Developing`, `Weak` |

#### Implementation Notes

- Scores should be returned from the most recent evaluation for the entity. If no evaluation exists, compute on-the-fly or return empty.
- Each `Score` has a `factors` array that explains what contributes to the score. The frontend renders these as breakdown bars.
- `factors[].source` indicates which engine produced the factor — useful for debugging.

---

## Evidence

### `GET /evidence`

Get evidence items for a specific entity.

**Purpose**: Powers evidence panels in entity detail views. Shows all signals, documents, and data points that informed decisions.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tenantId` | string | **yes** | — | Tenant scope |
| `entityId` | string | **yes** | — | Target entity |
| `entityType` | string | **yes** | — | Entity type |
| `type` | string | no | — | Filter by evidence type |
| `limit` | integer | no | `20` | Max results |
| `offset` | integer | no | `0` | Skip N results |

#### Evidence Type Filter Values

| `type` value | Description |
|-------------|-------------|
| `signal` | Real-time signals (hiring, expansion, website visits) |
| `document` | Documents and entity metadata |
| `timeline` | Timeline events and activities |
| `dna` | Company DNA data (firmographics, financial health) |
| `meeting` | Meeting transcripts and action items |
| `email` | Email communication signals |
| `search` | Search and entity resolution results |
| `government` | Government filings and public records |

#### Response — `200 OK`

```json
{
  "items": [
    {
      "id": "uuid-...",
      "type": "signal",
      "description": "signalStrength: \"high\"",
      "source": "context.metadata",
      "confidence": 0.7,
      "freshness": "current",
      "timestamp": "2026-07-11T14:30:00.000Z",
      "severity": "medium",
      "url": "https://...",
      "data": {
        "key": "signalStrength",
        "rawValue": "high"
      }
    },
    {
      "id": "uuid-...",
      "type": "document",
      "description": "Entity type identified: company",
      "source": "context.entityType",
      "confidence": 1.0,
      "freshness": "current",
      "timestamp": "2026-07-11T14:30:00.000Z"
    }
  ],
  "total": 4
}
```

#### Implementation Notes

- Evidence items are collected per evaluation. For entity-level queries, the backend should return the union of evidence from the most recent evaluation(s) or from the entity's evidence index.
- `freshness` is a label: `current` (< 1h), `recent` (< 24h), `stale` (< 7d), `outdated` (> 7d).
- `severity` is optional — only present for signal-type evidence with risk implications.
- `url` is optional — deep link back to the source (e.g., email thread, meeting recording).

---

## Feedback

### `POST /feedback`

Submit feedback on a past decision. Drives the learning loop.

**Purpose**: After a user acts on (or ignores) a recommendation, they submit feedback. This feeds into `FeedbackEngine` → `LearningEngine` for quality metrics and trend analysis.

**Auth**: Required (tenant + user)
**Rate limit**: 60/min

#### Request

```json
{
  "decisionId": "a1b2c3d4-...",
  "tenantId": "tenant_abc123",
  "actorId": "user_456",
  "outcome": "accepted",
  "reason": "Proceeded with the deal — strong signals from hiring data",
  "revenueImpact": 12500,
  "timeToExecution": 3600,
  "actualEffort": "low",
  "metadata": {
    "dealStage": "proposal_sent",
    "competitorInvolved": false
  },
  "timestamp": "2026-07-11T16:45:00.000Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decisionId` | string | **yes** | The decision being rated |
| `tenantId` | string | **yes** | Must match auth tenant |
| `actorId` | string | **yes** | User submitting feedback |
| `outcome` | `"accepted" \| "rejected" \| "ignored"` | **yes** | What happened |
| `reason` | string | no | Free-text explanation |
| `revenueImpact` | number | no | Dollar impact (≥ 0) |
| `timeToExecution` | number | no | Seconds to execute (≥ 0) |
| `actualEffort` | string | no | `low`, `medium`, `high` |
| `metadata` | Record<string, unknown> | no | Arbitrary context |
| `timestamp` | string | **yes** | When the outcome occurred |

#### Response — `200 OK`

```json
{
  "id": "fb-uuid-...",
  "accepted": true
}
```

#### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Validation failed — missing required fields, invalid outcome, negative revenue/time |
| `404` | `decisionId` not found |

The response returns `accepted: false` for validation failures (matching the SDK's `FeedbackEngine.submit()` behavior), but the HTTP status is still `200`. For stricter REST semantics, the backend may return `400` instead.

#### Implementation Notes

- The SDK's `FeedbackEngine.validateFeedback()` checks: `decisionId`, `tenantId`, `actorId` required; `outcome` must be one of three values; `revenueImpact` and `timeToExecution` must be ≥ 0.
- On acceptance, the backend should also emit a `LearningEvent` of type `acceptance_rate` to the `LearningEngine`.
- `timestamp` should reflect when the outcome actually happened, not when the API was called.

---

### `GET /feedback/stats`

Get aggregated feedback statistics for a tenant.

**Purpose**: Powers the Decision Quality dashboard. Shows acceptance rates, revenue impact, and execution time trends.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `tenantId` | string | **yes** | Tenant scope |

#### Response — `200 OK`

```json
{
  "total": 142,
  "accepted": 98,
  "rejected": 31,
  "ignored": 13,
  "acceptanceRate": 0.69,
  "totalRevenueImpact": 1250000,
  "averageTimeToExecution": 7200
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total` | number | Total feedback records |
| `accepted` | number | Count of accepted outcomes |
| `rejected` | number | Count of rejected outcomes |
| `ignored` | number | Count of ignored outcomes |
| `acceptanceRate` | number | `accepted / total` (0.0–1.0) |
| `totalRevenueImpact` | number | Sum of all `revenueImpact` values |
| `averageTimeToExecution` | number \| null | Mean seconds to execute (`null` if no time data) |

#### Implementation Notes

- Maps directly to `FeedbackEngine.getStats()` → `FeedbackStats` interface.
- `averageTimeToExecution` is `null` when no feedback includes `timeToExecution`. The frontend should display "N/A" in this case.
- Consider caching this endpoint with a 5-minute TTL since it aggregates over all historical data.

---

## Rules

### `GET /rules`

List all registered decision rules.

**Purpose**: Powers the Rules Administration view. Shows what rules exist, their priorities, and categories.

**Auth**: Required (tenant + user, admin role recommended)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | string | no | Filter by category (`intent`, `risk`, `engagement`, `quality`, etc.) |

#### Response — `200 OK`

```json
{
  "rules": [
    {
      "id": "rule-high-intent",
      "name": "High Intent Signal",
      "description": "Trigger when entity shows strong buying intent",
      "priority": 1,
      "category": "intent",
      "version": "1.0.0",
      "conditions": { "signalStrength": "high" },
      "action": "accelerate",
      "weight": 0.9
    },
    {
      "id": "rule-risk-check",
      "name": "Risk Assessment",
      "description": "Evaluate risk level for the entity",
      "priority": 2,
      "category": "risk",
      "version": "1.0.0",
      "conditions": { "entityType": ["company", "opportunity"] },
      "action": "assess_risk",
      "weight": 0.7
    },
    {
      "id": "rule-engagement",
      "name": "Engagement Recency",
      "description": "Check how recently the entity was engaged",
      "priority": 3,
      "category": "engagement",
      "version": "1.0.0",
      "conditions": { "maxDaysSinceContact": 30 },
      "action": "re_engage",
      "weight": 0.5
    },
    {
      "id": "rule-data-quality",
      "name": "Data Quality Gate",
      "description": "Ensure minimum data quality before action",
      "priority": 0,
      "category": "quality",
      "version": "1.0.0",
      "conditions": { "minConfidence": 0.3 },
      "action": "validate",
      "weight": 1.0
    }
  ]
}
```

#### Implementation Notes

- Rules are tenant-scoped in production. The current SDK uses shared `BASE_RULES` — the backend must extend this to support per-tenant rule sets.
- `conditions` is a `Record<string, unknown>` — the backend should store and return it as JSONB.
- `version` follows semver. Rule evaluation should be deterministic for a given version.

---

### `POST /rules`

Register a new decision rule.

**Purpose**: Allows admin users to create custom rules that extend the base rule set. New rules take effect on the next evaluation.

**Auth**: Required (tenant + user, admin role required)
**Rate limit**: 60/min

#### Request

```json
{
  "name": "Churn Risk Alert",
  "description": "Trigger when engagement drops below threshold",
  "priority": 2,
  "category": "risk",
  "version": "1.0.0",
  "conditions": {
    "daysSinceLastContact": { "gte": 60 },
    "engagementScore": { "lt": 0.3 }
  },
  "action": "flag_churn_risk",
  "weight": 0.85
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **yes** | Human-readable name |
| `description` | string | **yes** | What the rule does |
| `priority` | number | **yes** | Higher = evaluated first (0 = lowest) |
| `category` | string | **yes** | Rule category |
| `version` | string | **yes** | Semver version |
| `conditions` | Record<string, unknown> | **yes** | Rule conditions (JSON) |
| `action` | string | **yes** | Action identifier to trigger |
| `weight` | number | **yes** | 0.0–1.0, influence on scoring |

#### Response — `201 Created`

```json
{
  "id": "rule-uuid-...",
  "name": "Churn Risk Alert",
  "description": "Trigger when engagement drops below threshold",
  "priority": 2,
  "category": "risk",
  "version": "1.0.0",
  "conditions": {
    "daysSinceLastContact": { "gte": 60 },
    "engagementScore": { "lt": 0.3 }
  },
  "action": "flag_churn_risk",
  "weight": 0.85
}
```

#### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | Missing required fields, weight outside 0.0–1.0, invalid version format |
| `409` | Rule with same `name` and `category` already exists |

#### Implementation Notes

- The `id` is generated server-side.
- New rules are added to the tenant's rule set and immediately available for evaluation.
- Rule changes should be audited. Log the creation event to `AuditLogger`.
- Consider a `PUT /rules/:id` endpoint for updating existing rules (not in current SDK).

---

## Learning

### `GET /learning/quality`

Get recommendation quality metrics for a tenant.

**Purpose**: Powers the Quality Metrics dashboard. Shows how well the Decision Engine is performing over time.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `tenantId` | string | **yes** | Tenant scope |

#### Response — `200 OK`

```json
{
  "averageConfidence": 0.72,
  "averageAcceptanceRate": 0.69,
  "totalRecommendations": 142,
  "highConfidenceRate": 0.58,
  "mediumConfidenceRate": 0.31,
  "lowConfidenceRate": 0.11
}
```

| Field | Type | Description |
|-------|------|-------------|
| `averageConfidence` | number | Mean confidence across all recommendations (0.0–1.0) |
| `averageAcceptanceRate` | number | Mean acceptance rate from feedback (0.0–1.0) |
| `totalRecommendations` | number | Total recommendations generated |
| `highConfidenceRate` | number | Proportion with confidence ≥ 0.8 |
| `mediumConfidenceRate` | number | Proportion with confidence 0.5–0.79 |
| `lowConfidenceRate` | number | Proportion with confidence < 0.5 |

#### Implementation Notes

- Maps directly to `LearningEngine.getRecommendationQuality()` → `QualityMetrics`.
- When `totalRecommendations` is 0, all rates return `0`.
- The three confidence rate fields should sum to approximately 1.0 (floating point tolerance).

---

### `GET /learning/trends`

Get week-over-week learning trends for a tenant.

**Purpose**: Shows whether the Decision Engine is improving or degrading. Each metric compares the current 7-day window against the previous 7-day window.

**Auth**: Required (tenant + user)
**Rate limit**: 300/min

#### Query Params

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `tenantId` | string | **yes** | Tenant scope |

#### Response — `200 OK`

```json
{
  "trends": [
    {
      "metric": "acceptance_rate",
      "currentValue": 0.71,
      "previousValue": 0.64,
      "trend": "up",
      "changePercent": 10.94
    },
    {
      "metric": "recommendation_quality",
      "currentValue": 0.68,
      "previousValue": 0.72,
      "trend": "down",
      "changePercent": -5.56
    },
    {
      "metric": "rule_effectiveness",
      "currentValue": 0.75,
      "previousValue": 0.74,
      "trend": "stable",
      "changePercent": 1.35
    },
    {
      "metric": "signal_usefulness",
      "currentValue": 0.62,
      "previousValue": 0.58,
      "trend": "up",
      "changePercent": 6.90
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `metric` | string | Metric name |
| `currentValue` | number | Average value in the last 7 days |
| `previousValue` | number | Average value in the 7 days before that |
| `trend` | `"up" \| "down" \| "stable"` | Direction of change (> 5% = up/down, else stable) |
| `changePercent` | number | Percentage change (positive = improvement) |

#### Implementation Notes

- Maps directly to `LearningEngine.getTrends()` → `LearningTrend[]`.
- The `stable` threshold is 5% — changes smaller than 5% are considered noise.
- `changePercent` can be negative (degradation) or positive (improvement).
- If no data exists for either window, all values are `0` and trend is `stable`.

---

## Error Format

All error responses follow a consistent shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "decisionId is required",
    "details": [
      {
        "field": "decisionId",
        "message": "decisionId is required"
      }
    ]
  }
}
```

| HTTP Status | `code` | When |
|-------------|--------|------|
| `400` | `VALIDATION_ERROR` | Missing/invalid request fields |
| `401` | `UNAUTHORIZED` | Missing or invalid auth token |
| `403` | `FORBIDDEN` | Tenant mismatch or insufficient role |
| `404` | `NOT_FOUND` | Resource does not exist |
| `409` | `CONFLICT` | Duplicate resource (e.g., rule name) |
| `429` | `RATE_LIMITED` | Too many requests — retry after `Retry-After` header |
| `500` | `INTERNAL_ERROR` | Server error |

---

## SDK Integration Notes

### Type Alignment

All request/response types map 1:1 to the TypeScript SDK contracts in `packages/platform/decision/contracts/index.ts`. The backend must serialize these exactly — no field renaming, no nesting changes.

| SDK Type | API Usage | Notes |
|----------|-----------|-------|
| `DecisionContext` | Request body for `/evaluate`, `/batch` | `tenantId` also in header |
| `DecisionResult` | Response from `/evaluate`, `/batch` | Full result including telemetry |
| `DecisionHistoryItem` | Response from `/history` | Simplified shape — no full scores/evidence |
| `Recommendation` | Response from `/recommendations` | Full shape with alternatives, risks |
| `Score` | Response from `/scores` | Array with factors |
| `EvidenceItem` | Response from `/evidence` | Filterable by type |
| `Feedback` | Request body for `/feedback` | Server adds `id` and `createdAt` |
| `FeedbackStats` | Response from `/feedback/stats` | Aggregated stats |
| `DecisionRule` | Request/response for `/rules` | `conditions` is JSON |
| `Explainability` | Response from `/:id/explain` | Full reasoning chain |
| `QualityMetrics` | Response from `/learning/quality` | Aggregated metrics |
| `LearningTrend` | Response from `/learning/trends` | Week-over-week comparison |

### Engine Mapping

Each API group maps to a specific SDK engine:

| API Group | SDK Engine | File |
|-----------|------------|------|
| `/evaluate`, `/batch`, `/history` | `DecisionEngine` | `decision-engine/index.ts` |
| `/:id/explain` | `ExplainabilityEngine` | `explainability-engine/index.ts` |
| `/recommendations` | `RecommendationEngine` | `recommendation-engine/index.ts` |
| `/scores` | `ScoringEngine` | `scoring-engine/index.ts` |
| `/evidence` | `EvidenceEngine` | `evidence-engine/index.ts` |
| `/feedback`, `/feedback/stats` | `FeedbackEngine` | `feedback-engine/index.ts` |
| `/rules` | `RuleEngine` | `rule-engine/index.ts` |
| `/learning/*` | `LearningEngine` | `learning-engine/index.ts` |

### Persistence Requirements

The SDK engines use in-memory `Map` storage. The backend **must** replace these with PostgreSQL tables:

| Table | Engine | Key |
|-------|--------|-----|
| `decision_results` | DecisionEngine | `decisionId` (PK), `tenantId` (index) |
| `decision_history` | DecisionEngine | `tenantId` (index), `createdAt` |
| `recommendations` | RecommendationEngine | `id` (PK), `tenantId` (index), `status` (index) |
| `scores` | ScoringEngine | composite (`entityId`, `type`) |
| `evidence_items` | EvidenceEngine | composite (`entityId`, `type`) |
| `feedback_records` | FeedbackEngine | `id` (PK), `tenantId` (index), `decisionId` (index) |
| `decision_rules` | RuleEngine | `id` (PK), `category` (index) |
| `learning_events` | LearningEngine | `tenantId` (index), `type` (index), `timestamp` |

### Tenant Isolation

Every query **must** include `tenantId` as a filter. Cross-tenant data access is a critical security violation (per Engineering Constitution Article 4.1).

### Telemetry Pipeline

The `telemetry` field in `DecisionResult` should be forwarded to the observability stack:

```json
{
  "decisionId": "...",
  "tenantId": "...",
  "evaluationTimeMs": 12,
  "rulesTimeMs": 2,
  "scoringTimeMs": 3,
  "evidenceTimeMs": 4,
  "recommendationTimeMs": 2,
  "timestamp": "2026-07-11T14:30:00.000Z"
}
```

Log these to the telemetry pipeline for performance monitoring and alerting on latency regressions.

### Audit Logging

All write operations (`POST /evaluate`, `POST /feedback`, `POST /rules`) must emit audit events via `AuditLogger`. Each audit entry should include:

- `actorId` — who performed the action
- `tenantId` — tenant scope
- `action` — what was done (`decision.evaluated`, `feedback.submitted`, `rule.created`)
- `resourceId` — the affected resource ID
- `timestamp` — when it happened
