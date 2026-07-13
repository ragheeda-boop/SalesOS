export interface Score {
  name: string
  value: number
  label: string
  weight: number
  type?: string
  metadata?: Record<string, unknown>
  factors?: Array<{ name: string; value: number; weight: number; description: string }>
}

export type ScoreType = 'buying_intent' | 'engagement' | 'fit_score' | 'custom'

export interface DecisionContext {
  tenantId?: string
  actorId: string
  opportunityId?: string
  entityId?: string
  entityType: string
  companyId?: string
  signalId?: string
  metadata?: Record<string, unknown>
}

export interface Recommendation {
  id?: string
  decisionId?: string
  actionLabel?: string
  action?: string
  reason?: string
  confidence?: number
  priority?: 'high' | 'medium' | 'low'
  entityType?: string
  entityId?: string
  scores?: Score[]
  explainability?: Explainability
  risks?: Array<{ description: string; level?: string }>
  alternatives?: Array<{ actionLabel?: string; reason?: string; confidence?: number }>
  createdAt?: string
}

export interface EvidenceItem {
  id?: string
  decisionId?: string
  type?: string
  source?: string
  description?: string
  data?: Record<string, unknown>
  confidence?: number
  timestamp?: string
  [key: string]: unknown
}

export interface DecisionResult {
  id: string
  decisionId?: string
  recommendation: Recommendation
  confidence: number
  action: string
  reasoning: string
  scores: Score[]
  explainability: Explainability
  evidence: EvidenceItem[]
}

export interface Explainability {
  factors: Array<{ name: string; value: number; description: string; impact: 'high' | 'medium' | 'low' }>
  summary: string
  why?: string
  expectedImpact?: string
  expectedTime?: string
}

export interface DecisionHistoryItem {
  id: string
  decisionId: string
  action: string
  outcome: string
  timestamp: string
  context?: Record<string, unknown>
}

export interface Feedback {
  id: string
  decisionId: string
  outcome: 'accepted' | 'rejected' | 'ignored'
  revenueImpact?: number
  createdAt: string
  tenantId?: string
}

export const decisionEngine = {
  evaluate: async (_context: DecisionContext): Promise<DecisionResult> => {
    throw new Error('Not implemented')
  },
  evaluateBatch: async (_contexts: DecisionContext[]): Promise<DecisionResult[]> => {
    throw new Error('Not implemented')
  },
  explain: async (_decisionId: string): Promise<Explainability | null> => {
    throw new Error('Not implemented')
  },
  getHistory: async (_tenantId: string, _limit?: number): Promise<DecisionHistoryItem[]> => {
    throw new Error('Not implemented')
  },
}

export class FeedbackEngine {
  async submit(_feedback: Feedback): Promise<{ id: string; accepted: boolean }> {
    throw new Error('Not implemented')
  }

  async getStats(_tenantId: string): Promise<{
    total: number
    accepted: number
    rejected: number
    ignored: number
    acceptanceRate: number
    totalRevenueImpact: number
    averageTimeToExecution: number | null
  }> {
    throw new Error('Not implemented')
  }
}

export class ScoringEngine {
  score(_type: ScoreType, _factors: Record<string, number>, _metadata?: Record<string, unknown>): Score {
    throw new Error('Not implemented')
  }
}
