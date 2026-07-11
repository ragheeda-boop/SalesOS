export type DecisionStatus = 'pending' | 'accepted' | 'dismissed' | 'completed' | 'failed'
export type ConfidenceLabel = 'high' | 'medium' | 'low'
export type DecisionSource = 'rule' | 'ai' | 'hybrid'
export type SignalSeverity = 'critical' | 'high' | 'medium' | 'low'
export type RiskLevel = 'critical' | 'high' | 'medium' | 'low'
export type EvidenceType = 'signal' | 'document' | 'timeline' | 'dna' | 'meeting' | 'email' | 'search' | 'government'
export type ScoreType = 'company' | 'opportunity' | 'intent' | 'relationship' | 'risk' | 'revenue' | 'data_quality' | 'confidence'
export type OutcomeValue = 'accepted' | 'rejected' | 'ignored'

export interface DecisionContext {
  tenantId: string
  actorId: string
  entityId?: string
  entityType?: 'company' | 'opportunity' | 'person'
  opportunityId?: string
  companyId?: string
  signalId?: string
  metadata?: Record<string, unknown>
}

export interface EvidenceItem {
  id: string
  type: EvidenceType
  description: string
  source: string
  confidence: number
  freshness: string
  timestamp: string
  severity?: SignalSeverity
  url?: string
  data?: Record<string, unknown>
}

export interface DecisionRule {
  id: string
  name: string
  description: string
  priority: number
  category: string
  version: string
  conditions: Record<string, unknown>
  action: string
  weight: number
}

export interface Score {
  type: ScoreType
  value: number
  confidence: number
  label: string
  factors: ScoreFactor[]
  timestamp: string
}

export interface ScoreFactor {
  name: string
  value: number
  weight: number
  description: string
  source: string
}

export interface Recommendation {
  id: string
  action: string
  actionLabel: string
  reason: string
  confidence: number
  confidenceLabel: ConfidenceLabel
  source: DecisionSource
  priority: number
  expectedRevenue?: number
  expectedEffort?: string
  expectedTime?: string
  businessImpact?: string
  alternatives: AlternativeRecommendation[]
  evidence: EvidenceItem[]
  risks: Risk[]
  status: DecisionStatus
  createdAt: string
  updatedAt: string
}

export interface AlternativeRecommendation {
  action: string
  actionLabel: string
  reason: string
  confidence: number
  expectedRevenue?: number
}

export interface Risk {
  type: string
  level: RiskLevel
  description: string
  mitigation?: string
}

export interface Explainability {
  why: string
  whyNow: string
  whyThisAction: string
  whyNotAlternative: string[]
  evidence: EvidenceItem[]
  rulesApplied: DecisionRule[]
  aiReasoning: string | null
  confidence: number
  risk: RiskLevel
  expectedImpact: {
    revenue: number
    timeframe: string
  }
}

export interface Feedback {
  decisionId: string
  tenantId: string
  actorId: string
  outcome: OutcomeValue
  reason?: string
  revenueImpact?: number
  timeToExecution?: number
  actualEffort?: string
  metadata?: Record<string, unknown>
  timestamp: string
}

export interface LearningEvent {
  id: string
  type: 'recommendation_quality' | 'acceptance_rate' | 'rule_effectiveness' | 'signal_usefulness' | 'evidence_quality'
  decisionId: string
  metric: string
  value: number
  factors: Record<string, number>
  timestamp: string
}

export interface DecisionResult {
  decisionId: string
  context: DecisionContext
  recommendation: Recommendation
  scores: Score[]
  rulesApplied: DecisionRule[]
  evidence: EvidenceItem[]
  explainability: Explainability
  telemetry: {
    evaluationTimeMs: number
    rulesTimeMs: number
    scoringTimeMs: number
    evidenceTimeMs: number
    recommendationTimeMs: number
  }
  timestamp: string
}

export interface DecisionHistoryItem {
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
