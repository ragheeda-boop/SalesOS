# Decision Intelligence Platform Architecture

## Mission

The Decision Intelligence Platform is the centralized commercial reasoning engine for SalesOS. It is the single source of truth for every recommendation, score, and insight across the entire product. No business logic, scoring, or reasoning lives outside this platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Decision Engine                          │
│  (Orchestrator — receives context, coordinates engines)    │
├─────────────────────────────────────────────────────────────┤
│  Rule       │  Scoring   │  Evidence   │  Recommendation   │
│  Engine     │  Engine    │  Engine     │  Engine           │
├─────────────┴────────────┴─────────────┴───────────────────┤
│  Explainability     │  Feedback     │  Learning            │
│  Engine             │  Engine       │  Engine              │
├─────────────────────┴───────────────┴──────────────────────┤
│              Shared: Types, Contracts, Telemetry           │
└─────────────────────────────────────────────────────────────┘
```

## Responsibilities

| Component | Responsibility |
|-----------|---------------|
| Decision Engine | Orchestrates every decision: receive context → collect evidence → execute rules → invoke scoring → produce recommendation |
| Rule Engine | Pure business rules only — deterministic, versioned, auditable |
| Scoring Engine | Produces normalized scores (Company, Opportunity, Intent, Risk, etc.) — always explainable |
| Evidence Engine | Collects and validates evidence from all sources (signals, timeline, company DNA, search) |
| Recommendation Engine | Generates ranked recommendations with primary + alternatives, confidence, risk, impact |
| Explainability Engine | Answers: Why? Why now? Why this action? What evidence? Which rules? |
| Feedback Engine | Captures action outcomes (accepted/rejected/ignored) with revenue impact |
| Learning Engine | Tracks quality trends — no autonomous ML, just metrics to improve future decisions |

## Boundaries

- **NEVER** access UI or React
- **NEVER** call browser APIs
- **NEVER** contain presentation logic
- **NEVER** duplicate business rules from other domains
- **ALWAYS** be deterministic when rules apply
- **ALWAYS** expose evidence and confidence
- **ALWAYS** be reproducible

## Consumers

- NBA Widget (workspace widget)
- Pipeline Intelligence Widget
- Opportunity Workspace
- Company Intelligence
- Revenue Health Widget
- Forecast Intelligence
- Executive Dashboard
- Future AI Agents

## Providers

- Company Intelligence (Company DNA, signals, documents)
- Search SDK (search results, entities)
- Revenue Execution (opportunities, tasks, pipeline)
- Meeting Intelligence (meeting transcripts, action items)
- Email Intelligence (email signals)
- Work Intelligence (task completion data)

## Data Sources

| Source | Data | Freshness |
|--------|------|-----------|
| Company DNA | Firmographics, financial health, buying intent, risk | 24h |
| Signals | Hiring, expansion, government, news | Real-time |
| Timeline | All activities and events | Real-time |
| Pipeline | Opportunities, stages, values | Real-time |
| Meetings | Transcripts, action items, sentiment | After meeting |
| Emails | Communication patterns, intent signals | Real-time |
| Search | Entity resolution, discovery | On demand |
| Feedback | Previous decision outcomes | Real-time |

## Caching Strategy

- Rule results: cache per tenant until rules change (TTL: 1h)
- Scores: cache per entity with freshness-based invalidation (TTL: 15min for live, 1h for static)
- Evidence: no cache — always fresh
- Recommendations: cache per context (TTL: 5min, invalidate on new signal)
- Explainability: no cache — generated on demand

## Performance Budgets

| Operation | Budget | Notes |
|-----------|--------|-------|
| Decision evaluation (simple) | < 100ms | Rules + scoring only |
| Decision evaluation (complex) | < 500ms | With evidence collection |
| Recommendation generation | < 200ms | Cached scores |
| Explainability | < 100ms | Pre-computed |
| Score computation | < 50ms | Per entity |
| Evidence retrieval | < 200ms | With deduplication |

## Security

- All decisions require a valid tenant context
- Decision evaluation checks user permissions via Permission SDK
- Evidence access respects data access policies
- Feedback is tenant-isolated
- Audit log captures every decision with actor, timestamp, context

## Audit

Every decision is logged with:

```
{
  "decisionId": "uuid",
  "tenantId": "uuid",
  "actorId": "uuid",
  "context": { ... },
  "rulesApplied": ["rule1", "rule2"],
  "scores": { "company": 0.82, "intent": 0.75 },
  "evidence": [{ "source": "...", "confidence": 0.9 }],
  "recommendation": { "action": "...", "confidence": 0.85 },
  "outcome": null | "accepted" | "rejected",
  "timestamp": "ISO8601"
}
```

## Telemetry

| Metric | Purpose |
|--------|---------|
| decision.evaluation.count | Volume |
| decision.evaluation.latency | Performance |
| decision.evaluation.by_type | Usage patterns |
| recommendation.acceptance_rate | Quality |
| recommendation.by_source | Rule vs AI effectiveness |
| evidence.retrieval.latency | Source health |
| scoring.by_type | Scoring distribution |
| rule.evaluation.count | Rule usage |
| rule.conflict.rate | Rule quality |

## Failure Modes

| Mode | Behavior | Recovery |
|------|----------|----------|
| Evidence source unavailable | Return degraded recommendation with lower confidence | Retry on next evaluation |
| Rule evaluation error | Skip rule, log error, continue with remaining rules | Alert on repeated failure |
| Scoring failure | Return partial scores with warning | Async retry |
| AI provider unavailable | Fall back to rules-only mode | Circuit breaker |
| Cache miss | Fresh computation | Update cache |
| Tenant context invalid | Reject with 403 | User re-authentication |

## Explainability Contract

Every recommendation MUST expose:

```
{
  "why": "High buying intent (82/100) with strong relationship (70/100)",
  "whyNow": "New signal: hiring 120 engineers indicates expansion",
  "whyThisAction": "Meeting scored highest (85%) across all alternatives",
  "whyNotAlternative": [
    "Send proposal: 70% confidence — insufficient relationship maturity",
    "Call: 45% confidence — decision maker not available"
  ],
  "evidence": [
    { "source": "signals", "description": "Hiring 120 engineers", "confidence": 0.92, "freshness": "2h ago" },
    { "source": "dna", "description": "Buying intent score 82/100", "confidence": 0.88, "freshness": "6h ago" }
  ],
  "rulesApplied": ["high_intent_meeting", "expansion_signal_priority"],
  "aiReasoning": null | "LLM analysis of company context...",
  "confidence": 0.85,
  "risk": "low",
  "expectedImpact": { "revenue": 500000, "timeframe": "2 weeks" }
}
```
