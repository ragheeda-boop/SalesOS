export interface Score {
  name: string
  value: number
  label: string
  weight: number
}

export type ScoreType = 'buying_intent' | 'engagement' | 'fit_score' | 'custom'

export interface DecisionContext {
  tenantId?: string
  actorId: string
  opportunityId?: string
  entityId?: string
  entityType: string
}

export interface DecisionResult {
  id: string
  recommendation: string
  confidence: number
  action: string
  reasoning: string
  scores: Score[]
  explainability: Explainability
}

export interface Explainability {
  factors: Array<{ name: string; value: number; description: string; impact: 'high' | 'medium' | 'low' }>
  summary: string
}

export interface DecisionHistoryItem {
  id: string
  decisionId: string
  action: string
  outcome: string
  timestamp: string
}

export interface Feedback {
  id: string
  decisionId: string
  outcome: 'accepted' | 'rejected' | 'ignored'
  revenueImpact?: number
  createdAt: string
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
