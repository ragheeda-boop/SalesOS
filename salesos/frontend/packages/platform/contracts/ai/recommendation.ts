export type SignalSource = 'stage_change' | 'activity' | 'company_signal' | 'time_trigger' | 'health_change' | 'score_change' | 'manual_refresh'
export type SignalEntityType = 'opportunity' | 'company'
export type OpportunityStage = 'qualification' | 'discovery' | 'proposal' | 'negotiation' | 'closed_won' | 'closed_lost'
export type RecommendationStatus = 'pending' | 'accepted' | 'dismissed' | 'completed'
export type ConfidenceLabel = 'high' | 'medium' | 'low'
export type RecommendationSource = 'rule' | 'ai' | 'hybrid'
export type EvidenceType = 'business_rule' | 'signal' | 'ai_analysis' | 'company_score' | 'activity' | 'risk_factor'
export type RiskLevel = 'low' | 'medium' | 'high'
export type RiskFactorType = 'stagnation' | 'competition' | 'engagement_drop' | 'stakeholder_change' | 'budget_concern' | 'timeline_slip'
export type ImpactCategory = 'revenue' | 'relationship' | 'risk_mitigation' | 'information_gathering'

export interface Evidence {
  id: string
  type: EvidenceType
  description: string
  source: string
  confidence: number
  timestamp: string
  data?: Record<string, unknown>
}

export interface Confidence {
  finalScore: number
  label: ConfidenceLabel
  components: {
    ruleScore: number
    aiScore: number
    opportunityScore: number
    urgencyScore: number
    riskAdjustment: number
  }
}

export interface Impact {
  description: string
  estimatedRevenue?: number
  estimatedProbability?: number
  category: ImpactCategory
}

export interface Risk {
  type: RiskFactorType
  level: RiskLevel
  description: string
  detectedAt: string
}

export interface Alternative {
  action: string
  reason: string
  confidence: number
  expectedImpact?: Impact
}

export interface Recommendation {
  id: string
  opportunityId: string
  action: string
  reason: string
  evidence: Evidence[]
  confidence: number
  confidenceLabel: ConfidenceLabel
  source: RecommendationSource
  alternatives: Alternative[]
  expectedImpact: Impact
  potentialRisks: Risk[]
  dueBy?: string
  status: RecommendationStatus
  createdAt: string
  updatedAt: string
}

export interface PipelineTrace {
  normalizationMs: number
  rulesMs: number
  scoringMs: number
  aiMs: number
  riskMs: number
  confidenceMs: number
  totalMs: number
}

export interface Feedback {
  id: string
  nbaId: string
  opportunityId: string
  userId: string
  action: 'accepted' | 'dismissed' | 'completed'
  reason?: string
  timestamp: string
}
