# Next Best Action Architecture

> **الهدف:** تصميم محرك NBA — Decision Engine لـ Wave 2
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Phase 3 — NBA Architecture

---

## 1. Purpose

NBA is the **decision layer** that converts intelligence into commercial execution. It answers:

- **What should happen next?**
- **Why?**
- **What impact will it create?**

NBA is not a recommendation generator. It is a **Decision Engine** with a complete pipeline: Signal → Reasoning → Rules → Scoring → AI → Confidence → Action → Feedback → Learning.

## 2. Scope

| In Scope | Out of Scope |
|----------|-------------|
| Opportunity-level NBA (one per opportunity) | Cross-opportunity optimization (future) |
| Stage-based, time-based, signal-triggered actions | Territory assignment |
| Explainable recommendations | Black-box predictions |
| Feedback collection and learning | Automated execution (human approves) |
| Business rules + AI hybrid scoring | Pure AI-only decisions |

## 3. Decision Pipeline

```
Signal
  │  Incoming event: stage change, activity, signal, time trigger
  ▼
Normalization
  │  Standardize signal format, enrich with context (company, opportunity)
  ▼
Business Rules
  │  Stage-based rules, time-based rules, signal-based rules
  │  Output: candidate actions with rule scores
  ▼
Scoring Engine
  │  Opportunity scoring, urgency scoring, effort scoring
  │  Output: weighted candidate list
  ▼
AI Reasoning
  │  LLM evaluation of context, sentiment, competitor signals
  │  Output: AI-ranked candidates with explanations
  ▼
Risk Assessment
  │  Deal Health evaluation, risk factor detection
  │  Output: risk-adjusted scores
  ▼
Confidence Calculation
  │  Aggregate rule_score + ai_score + risk_adjustment
  │  Output: final confidence for each candidate
  ▼
Recommendation Ranking
  │  Sort by confidence, apply business constraints
  │  Output: Next Best Action + Alternatives
  ▼
Next Best Action
  │  The top recommendation with full evidence trail
  ▼
Feedback Collection
  │  User accepts, rejects, or modifies the recommendation
  ▼
Continuous Learning
  │  Feedback → adjust rules, retrain AI, update confidence
```

## 4. Inputs

| Input Source | Type | Trigger | Example |
|-------------|------|---------|---------|
| Opportunity Stage Change | Event | `opportunity.stage_changed` | Moving from Qualification to Discovery |
| Activity Logged | Event | `activity.logged` | Meeting completed, email sent |
| Company Signal | Event | `signal.detected` | New tender, license issued |
| Time Trigger | Schedule | Cron (daily) | Opportunity idle for 7+ days |
| Deal Health Change | Event | `deal_health.changed` | Health drops from Healthy to At Risk |
| Company Score Change | Event | `company.scored` | ICP score changes |
| User Request | API | `GET /opportunities/:id/nba` | User opens Opportunity Workspace |
| Manual Refresh | API | `POST /opportunities/:id/nba/refresh` | User clicks "Refresh" |

## 5. Pipeline Stages — Detailed

### 5.1 Normalization

```typescript
interface NormalizedSignal {
  source: 'stage_change' | 'activity' | 'signal' | 'time' | 'health' | 'score' | 'manual'
  entityType: 'opportunity' | 'company'
  entityId: string
  opportunityId?: string
  tenantId: string
  timestamp: string
  data: Record<string, unknown>
  context: {
    opportunity?: OpportunitySnapshot
    company?: CompanySnapshot
    recentActivities?: ActivitySummary[]
  }
}
```

**Responsibilities:**
- Fetch opportunity + company data from DB
- Fetch recent activities (last 14 days)
- Enrich with signals related to the company
- Standardize into uniform signal format

### 5.2 Business Rules

Rules are evaluated **sequentially**. Each rule produces a candidate action with a score.

```typescript
interface RuleCandidate {
  action: string
  ruleName: string
  score: number  // 0.0 to 1.0
  reason: string
  metadata: Record<string, unknown>
}
```

**Rule Categories:**

| Category | Example | Score |
|----------|---------|-------|
| **Stage-based** | Stage is `qualification` → "Send introduction email" | 0.9 |
| **Stage-based** | Stage is `proposal` → "Send proposal document" | 0.9 |
| **Time-based** | No activity for 14 days → "Send follow-up" | 0.7 + (days/100) |
| **Signal-based** | New competitor detected → "Prepare competitive brief" | 0.8 |
| **Health-based** | Health is `critical` → "Escalate to manager" | 0.95 |
| **Engagement-based** | High engagement → "Schedule demo" | 0.75 |
| **Milestone-based** | Approaching close date → "Review contract terms" | 0.85 |

### 5.3 Scoring Engine

```typescript
interface ScoredCandidate extends RuleCandidate {
  opportunityScore: number    // From Opportunity Scoring model
  urgencyScore: number        // Time sensitivity (close date proximity)
  effortScore: number         // Estimated effort (low effort = higher score)
  combinedScore: number       // Weighted: rule * 0.4 + opportunity * 0.25 + urgency * 0.2 + effort * 0.15
}
```

**Opportunity Scoring Model:**

| Factor | Weight | Source |
|--------|--------|--------|
| Deal Value | 25% | Opportunity.value |
| Stage Progression | 20% | Opportunity.stage + velocity |
| Engagement Level | 15% | Activity count (last 14 days) |
| Company ICP Score | 15% | Feature Store `icp_score` |
| Decision Maker Access | 10% | Contact relationship count |
| Timeline Pressure | 10% | Days to expectedCloseDate |
| Deal Health | 5% | Health score (healthy/at_risk/critical) |

### 5.4 AI Reasoning

AI evaluates when business rules produce low confidence (< 0.7) or when multiple rules conflict.

```typescript
interface AIEvaluation {
  candidates: ScoredCandidate[]
  analysis: string          // Natural language analysis of opportunity context
  aiRanked: string[]        // AI's ranking of candidate actions
  aiConfidence: number      // 0.0 to 1.0
  explanation: string       // Why AI ranked this way
  signalsUsed: string[]     // Signals that influenced AI
}
```

**When AI runs:**
- **Always** — if OpenAI API key is configured, AI evaluates all opportunities
- **Fallback** — if no OpenAI key, use rule-only scoring
- **Override** — AI can shift ranking by max ±0.2 from rule score

### 5.5 Risk Assessment

```typescript
interface RiskAssessment {
  overallRisk: 'low' | 'medium' | 'high'
  riskFactors: RiskFactor[]
  scoreAdjustment: number  // -0.3 to 0.0 (only reduces score)
}

interface RiskFactor {
  type: 'stagnation' | 'competition' | 'engagement_drop' | 'stakeholder_change' | 'budget_concern' | 'timeline_slip'
  severity: 'low' | 'medium' | 'high'
  description: string
}
```

**Risk Detection:**

| Factor | Detection Method | Trigger |
|--------|-----------------|---------|
| Stagnation | No activity for 7+ days | Time-based |
| Competition | Signal category = 'competitor' linked to company | Event-based |
| Engagement Drop | Activity count < 50% of previous period | Scheduled |
| Stakeholder Change | Contact change on opportunity account | Event-based |
| Budget Concern | Signal mentions budget, cost, pricing | Event-based |
| Timeline Slip | Expected close date pushed 2+ times | Event-based |

### 5.6 Confidence Calculation

```typescript
interface ConfidenceResult {
  finalScore: number           // 0.0 to 1.0
  components: {
    ruleScore: number          // From business rules
    aiScore: number            // From AI reasoning (0 if no AI)
    riskAdjustment: number     // From risk assessment (-0.3 to 0)
    finalScore: number
  }
  confidence: 'high' | 'medium' | 'low'
  // high: >= 0.8, medium: >= 0.5, low: < 0.5
}
```

### 5.7 Output

```typescript
interface NBAOutput {
  id: string
  opportunityId: string
  action: string
  reason: string
  evidence: Evidence[]
  confidence: number
  confidenceLabel: 'high' | 'medium' | 'low'
  source: 'rule' | 'ai' | 'hybrid'
  alternatives: NBAAlternative[]
  expectedImpact: {
    description: string
    estimatedRevenue?: number
    estimatedProbability?: number
  }
  estimatedEffort: {
    description: string
    estimatedMinutes: number
  }
  potentialRisks: RiskFactor[]
  dueBy?: string
  status: 'pending' | 'accepted' | 'dismissed' | 'completed'
  createdAt: string
  updatedAt: string
}
```

## 6. Caching Strategy

| Cache | TTL | Invalidation |
|-------|-----|-------------|
| NBA recommendation per opportunity | Until next trigger event | Stage change, activity, signal |
| Opportunity scoring factors | 1 hour | Company score change |
| Deal health status | 30 minutes | Activity event |
| Company snapshot | 1 hour | Company score change |

## 7. Permissions Model

| Action | Required Permission | Scope |
|--------|-------------------|-------|
| View NBA | `nba:read` | Own opportunities (rep), all (manager+) |
| Accept NBA | `nba:update` | Owner of opportunity |
| Dismiss NBA | `nba:update` | Owner of opportunity |
| Refresh NBA | `nba:update` | Owner of opportunity |
| Configure NBA rules | `nba:admin` | Tenant-level |

## 8. Explainability

Every NBA output MUST expose:

```typescript
interface Evidence {
  type: 'business_rule' | 'signal' | 'ai_analysis' | 'company_score' | 'activity'
  description: string
  source: string           // e.g., "Rule: stage-based (qualification → send intro email)"
  confidence: number
  timestamp: string
  data?: Record<string, unknown>  // Supporting data for audit
}
```

**Explainability Rules:**

1. Every recommendation includes `reason` (one-line summary) + `evidence[]` (detailed trail)
2. Every evidence item includes `type` and `source` so users know WHY
3. AI-sourced evidence includes `analysis` showing what the AI considered
4. Alternative options are shown with their scores so users see "why not X"
5. Confidence shows breakdown: rule score + AI score + risk adjustment

## 9. Telemetry & Auditability

| Event | Data Captured | Destination |
|-------|--------------|-------------|
| NBA Generated | opportunity_id, action, confidence, source, processing_time_ms | Event Runtime + Metrics |
| NBA Accepted | opportunity_id, action, user_id, time_to_accept | Event Runtime + Metrics |
| NBA Dismissed | opportunity_id, action, user_id, reason (optional) | Event Runtime + Metrics |
| NBA Error | opportunity_id, error_type, processing_time_ms | Error metrics + Sentry |
| NBA Latency | pipeline stage durations (normalization_ms, rules_ms, scoring_ms, ai_ms, risk_ms) | Histogram metrics |

**Audit Trail:** Every NBA generation is recorded as a domain event with full pipeline trace. Auditors can replay any NBA for any opportunity at any point in time.

## 10. Performance Budget

| Stage | Budget | Violation Action |
|-------|--------|-----------------|
| Normalization | < 50ms | Log warning |
| Business Rules | < 20ms | Log warning |
| Scoring | < 30ms | Log warning |
| AI Reasoning | < 2000ms | Timeout + fallback to rule-only |
| Risk Assessment | < 50ms | Log warning |
| Confidence Calculation | < 10ms | N/A |
| **Total (rule-only)** | **< 200ms** | Error metric |
| **Total (with AI)** | **< 3000ms** | Timeout + fallback to rule-only |

## 11. Failure Strategy

| Failure | Impact | Recovery |
|---------|--------|----------|
| AI timeout | NBA falls back to rule-only scoring | Retry AI on next trigger |
| DB connection failure | NBA cannot load opportunity context | Queue event for retry (Event Runtime DLQ) |
| All rules return empty | NBA returns `no_action_needed` status | Scheduled re-check next cycle |
| Invalid opportunity state | NBA returns error with explanation | Log + alert; no retry |
| Rate limit (AI) | NBA uses last known good recommendation | Re-check next cycle |

## 12. Event-Driven Architecture

```
Domain Events (Event Runtime)
  │
  ├── opportunity.created ─────────────► NBA: auto-assign playbook, generate initial NBA
  ├── opportunity.stage_changed ───────► NBA: recompute for this opportunity
  ├── activity.logged (opportunity) ───► NBA: update engagement score, recompute if stagnation cleared
  ├── company.signal.detected ─────────► NBA: if linked to opportunity, evaluate impact
  ├── company.scored ─────────────────► NBA: if ICP/Intent score changes, update opportunity score
  ├── deal_health.changed ────────────► NBA: if health degrades, generate risk-mitigation action
  └── time.trigger (daily) ────────────► NBA: scan all open opportunities for idle detection
```

**NBA as Event Runtime Subscriber:**

```python
@event_runtime.subscribe("opportunity.*", priority="EARLY")
async def on_opportunity_event(event: DomainEvent):
    nba = NBAEngine(session_factory, feature_store, event_runtime)
    await nba.recompute(opportunity_id=event.aggregate_id, tenant_id=event.tenant_id)
```

---

*NBA Architecture complete. Ready for Phase 4: NBA Blueprint.*
