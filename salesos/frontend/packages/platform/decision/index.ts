/**
 * STUB — NOT PRODUCTION-READY (GA Wave 6 / AI honesty)
 *
 * `decisionEngine` and `FeedbackEngine` throw on every call.
 * Do not wire into GA navigation or market as a live Decision Engine.
 * Prefer Decision Center API (`/api/v1/...`) when available.
 * Tracking: PROD-W6-001, TD-S0-07, docs/audit/ga-engineering-audit/AI_HONESTY.md
 */
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

const STUB_MSG =
  'STUB: @salesos decision package is not implemented — not production-ready (see AI_HONESTY.md)'

export const decisionEngine = {
  evaluate: async (_context: DecisionContext): Promise<DecisionResult> => {
    throw new Error(STUB_MSG)
  },
  evaluateBatch: async (_contexts: DecisionContext[]): Promise<DecisionResult[]> => {
    throw new Error(STUB_MSG)
  },
  explain: async (_decisionId: string): Promise<Explainability | null> => {
    throw new Error(STUB_MSG)
  },
  getHistory: async (_tenantId: string, _limit?: number): Promise<DecisionHistoryItem[]> => {
    throw new Error(STUB_MSG)
  },
}

export class FeedbackEngine {
  async submit(_feedback: Feedback): Promise<{ id: string; accepted: boolean }> {
    throw new Error(STUB_MSG)
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
    throw new Error(STUB_MSG)
  }
}

export class ScoringEngine {
  score(type: ScoreType, factors: Record<string, number>, metadata?: Record<string, unknown>): Score {
    const entries = Object.entries(factors)
    if (entries.length === 0) {
      return {
        name: type,
        value: 0.5,
        label: type === 'engagement' ? 'تفاعل' : type === 'buying_intent' ? 'نية الشراء' : type === 'fit_score' ? 'ملاءمة' : type,
        weight: 1.0,
      }
    }

    const total = entries.reduce((sum, [, v]) => sum + Math.max(0, Math.min(1, v)), 0)
    const value = Math.round((total / entries.length) * 100) / 100

    const typeLabels: Record<ScoreType, string> = {
      buying_intent: 'نية الشراء',
      engagement: 'تفاعل',
      fit_score: 'ملاءمة',
      custom: 'مخصص',
    }

    return {
      name: type,
      value: Math.max(0, Math.min(1, value)),
      label: (metadata?.label as string) || typeLabels[type] || type,
      weight: 1.0,
      type,
      factors: entries.map(([name, v]) => ({
        name,
        value: Math.max(0, Math.min(1, v)),
        weight: 1 / entries.length,
        description: `${name}: ${Math.round(v * 100)}%`,
      })),
    }
  }
}
