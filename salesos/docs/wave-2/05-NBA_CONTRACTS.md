# NBA Contracts

> **الهدف:** Strongly typed contracts لكل كيان في NBA Pipeline
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Phase 5 — NBA Contracts

---

## Signal Contract

```typescript
// contracts/ai/signal.ts

export type SignalSource = 'stage_change' | 'activity' | 'company_signal' | 'time_trigger' | 'health_change' | 'score_change' | 'manual_refresh'

export type SignalEntityType = 'opportunity' | 'company'

export interface NormalizedSignal {
  source: SignalSource
  entityType: SignalEntityType
  entityId: string
  opportunityId?: string
  tenantId: string
  timestamp: string  // ISO 8601
  data: Record<string, unknown>
  context: SignalContext
}

export interface SignalContext {
  opportunity?: OpportunitySnapshot
  company?: CompanySnapshot
  recentActivities: ActivitySummary[]
}

export interface OpportunitySnapshot {
  id: string
  name: string
  stage: OpportunityStage
  value: number
  currency: string
  health: 'healthy' | 'at_risk' | 'critical'
  expectedCloseDate?: string
  ownerId: string
  playbookId?: string
  createdAt: string
  updatedAt: string
}

export interface CompanySnapshot {
  id: string
  nameAr: string
  nameEn?: string
  industry?: string
  city?: string
  region?: string
  icpScore?: number
  employeesCount?: number
  annualRevenue?: number
}

export interface ActivitySummary {
  id: string
  type: ActivityType
  action: string
  timestamp: string
  description?: string
}

export type ActivityType = 'meeting' | 'email' | 'call' | 'task' | 'note' | 'stage_change'
export type OpportunityStage = 'qualification' | 'discovery' | 'proposal' | 'negotiation' | 'closed_won' | 'closed_lost'
```

## Recommendation Contract

```typescript
// contracts/ai/recommendation.ts

export interface Recommendation {
  id: string
  opportunityId: string
  action: string
  reason: string
  evidence: Evidence[]
  confidence: number
  confidenceLabel: 'high' | 'medium' | 'low'
  source: 'rule' | 'ai' | 'hybrid'
  alternatives: Alternative[]
  expectedImpact: Impact
  estimatedEffort: Effort
  potentialRisks: Risk[]
  dueBy?: string
  status: RecommendationStatus
  pipelineTrace: PipelineTrace
  createdAt: string
  updatedAt: string
}

export type RecommendationStatus = 'pending' | 'accepted' | 'dismissed' | 'completed'

export interface PipelineTrace {
  normalizationMs: number
  rulesMs: number
  scoringMs: number
  aiMs: number
  riskMs: number
  confidenceMs: number
  totalMs: number
}
```

## Decision Contract

```typescript
// contracts/ai/decision.ts

export interface Decision {
  id: string
  recommendationId: string
  opportunityId: string
  userId: string
  action: 'accepted' | 'dismissed' | 'modified'
  reason?: string
  timestamp: string
  metadata?: Record<string, unknown>
}
```

## Evidence Contract

```typescript
// contracts/ai/evidence.ts

export type EvidenceType = 'business_rule' | 'signal' | 'ai_analysis' | 'company_score' | 'activity' | 'risk_factor'

export interface Evidence {
  id: string
  type: EvidenceType
  description: string
  source: string    // e.g., "Rule: stage-based (qualification → send intro)"
  confidence: number
  timestamp: string
  data?: Record<string, unknown>
}

export interface EvidenceGroup {
  ruleEvidence: Evidence[]
  signalEvidence: Evidence[]
  aiEvidence: Evidence[]
  scoreEvidence: Evidence[]
  activityEvidence: Evidence[]
  riskEvidence: Evidence[]
}
```

## Confidence Contract

```typescript
// contracts/ai/confidence.ts

export interface Confidence {
  finalScore: number        // 0.0 to 1.0
  label: 'high' | 'medium' | 'low'
  components: {
    ruleScore: number
    aiScore: number
    opportunityScore: number
    urgencyScore: number
    riskAdjustment: number
    finalScore: number
  }
}
```

## Impact Contract

```typescript
// contracts/ai/impact.ts

export interface Impact {
  description: string
  estimatedRevenue?: number
  estimatedProbability?: number
  estimatedTimeSave?: number  // minutes
  category: 'revenue' | 'relationship' | 'risk_mitigation' | 'information_gathering'
}
```

## Alternative Contract

```typescript
// contracts/ai/alternative.ts

export interface Alternative {
  action: string
  reason: string
  confidence: number
  expectedImpact?: Impact
}
```

## Risk Contract

```typescript
// contracts/ai/risk.ts

export type RiskLevel = 'low' | 'medium' | 'high'
export type RiskFactorType = 'stagnation' | 'competition' | 'engagement_drop' | 'stakeholder_change' | 'budget_concern' | 'timeline_slip'

export interface Risk {
  type: RiskFactorType
  level: RiskLevel
  description: string
  detectedAt: string
  evidenceId?: string
}
```

## Feedback Contract

```typescript
// contracts/ai/feedback.ts

export interface Feedback {
  id: string
  nbaId: string
  opportunityId: string
  userId: string
  action: 'accepted' | 'dismissed' | 'completed'
  reason?: string
  timestamp: string
}

export interface FeedbackStats {
  totalRecommendations: number
  accepted: number
  dismissed: number
  completed: number
  acceptanceRate: number
  avgTimeToAccept: number  // hours
  dismissalReasons: { reason: string; count: number }[]
}
```

## Learning Event Contract

```typescript
// contracts/ai/learning.ts

export interface LearningEvent {
  id: string
  type: 'rule_weight_adjusted' | 'rule_added' | 'rule_removed' | 'ai_retrained'
  timestamp: string
  changes: {
    ruleName?: string
    oldValue?: number
    newValue?: number
    reason: string
  }[]
  triggeredBy: 'feedback_analysis' | 'manual' | 'scheduled'
}
```

## Next Best Action Contract (Full)

```typescript
// contracts/revenue/nba.ts

export interface NextBestAction {
  id: string
  opportunityId: string
  action: string
  reason: string
  evidence: Evidence[]
  confidence: number
  confidenceLabel: 'high' | 'medium' | 'low'
  source: 'rule' | 'ai' | 'hybrid'
  alternatives: Alternative[]
  expectedImpact: Impact
  estimatedEffort: Effort
  potentialRisks: Risk[]
  dueBy?: string
  status: RecommendationStatus
  pipelineTrace: PipelineTrace
  createdAt: string
  updatedAt: string
}

export interface Effort {
  description: string
  estimatedMinutes: number
  category: 'low' | 'medium' | 'high'
}
```

---

*NBA Contracts complete. Ready for Phase 6: NBA API Mapping.*
