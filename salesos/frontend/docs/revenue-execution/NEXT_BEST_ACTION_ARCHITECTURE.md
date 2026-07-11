# Next Best Action Engine — Architecture

> SalesOS Wave 2 · Revenue Execution Platform
> Last Updated: 2026-07-10

---

## Vision

The Next Best Action Engine is the single most important component in SalesOS. It transforms intelligence into action. Every company in the system produces one clear answer:

> **What should I do next with this company?**

---

## Inputs

| Source | Widget | Data Used |
|--------|--------|-----------|
| Company DNA | `companyDNA` | Industry, size, buying intent, risk, relationship strength |
| AI Recommendation | `aiRecommendation` | Recommended action, reasoning, confidence, revenue, risks |
| Timeline | `smartTimeline` | Recent events, signals, meetings |
| Signals | `signalsFeed` | Active signals with severity |
| Decision Makers | `decisionMakers` | Connected decision makers, influence levels |

---

## Output

```typescript
interface NextBestAction {
  // Primary
  actionId: string
  actionLabel: string
  actionType: 'call' | 'meeting' | 'demo' | 'proposal' | 'follow_up' | 'event' | 'review' | 'custom'
  reasoning: string        // Natural language explanation
  confidence: number       // 0–1

  // Business impact
  expectedRevenue: number
  expectedImpact: 'low' | 'medium' | 'high'
  estimatedTime: string

  // Context
  contextSummary: string   // Why now — key trigger events
  triggerEvent?: string    // The specific event that triggered this

  // Risk
  risks: string[]
  alternatives: { actionLabel: string; confidence: number }[]

  // Execution
  playbookId?: string
  createsOpportunity: boolean
  defaultAssignee?: string
}
```

---

## Scoring

```
nba_score = 0.35 * buying_intent
          + 0.20 * relationship_strength
          + 0.15 * signal_recency
          + 0.15 * ai_confidence
          + 0.10 * decision_maker_access
          + 0.05 * revenue_potential_normalized
```

Thresholds:
- `≥ 0.80`: **Critical** — immediate action required
- `≥ 0.60`: **High** — action this week
- `≥ 0.40`: **Medium** — action this month
- `< 0.40`: **Low** — monitor

---

## Widget Architecture

```
NBAContainer (createWidget)
  └── NBAView
       ├── Priority Badge (Critical/High/Medium/Low)
       ├── Action Card (primary CTA)
       │    ├── Icon + Action Label
       │    ├── Reasoning (NL)
       │    ├── Confidence Gauge
       │    ├── Revenue + Time
       │    └── Execute Button → creates Opportunity/Task
       ├── Context Section
       │    ├── Trigger Event
       │    └── Context Summary
       ├── Risk Section
       ├── Alternatives
       └── Metadata (score breakdown, data freshness)
```

---

## Execution Flow

```
User clicks "Execute"
  → CreateOpportunityModal opens
    → Pre-filled from NBA data
      → User confirms
        → Opportunity created in pipeline
          → Task created for assignee
            → Telemetry: opportunity.created
```

---

## Widget Config

| Property | Value |
|----------|-------|
| ID | `nextBestAction` |
| Grid | `span 4` |
| Min Height | `420px` |
| Refresh | `60s` |
| Permissions | `company:nba:read` |
| Feature Flag | `enabled` |
