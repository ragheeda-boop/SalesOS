export type OpportunityStage = 'identified' | 'qualifying' | 'developing' | 'proposing' | 'negotiating' | 'closing' | 'won' | 'lost'
export type OpportunitySource = 'nba' | 'manual' | 'import' | 'signal'

export const STAGES: OpportunityStage[] = ['identified', 'qualifying', 'developing', 'proposing', 'negotiating', 'closing', 'won', 'lost']

export const STAGE_LABEL: Record<OpportunityStage, string> = {
  identified: 'تم التحديد', qualifying: 'قيد التأهيل', developing: 'قيد التطوير',
  proposing: 'قيد العرض', negotiating: 'قيد التفاوض', closing: 'قيد الإغلاق', won: 'فوز', lost: 'خسارة',
}

export const STAGE_WEIGHT: Record<OpportunityStage, number> = {
  identified: 0.10, qualifying: 0.25, developing: 0.45,
  proposing: 0.65, negotiating: 0.80, closing: 0.90, won: 1.0, lost: 0,
}

export interface OpportunityNote {
  id: string
  text: string
  createdAt: string
  author: string
}

export interface RevenueOpportunity {
  id: string
  companyId: string
  companyName: string
  title: string
  source: OpportunitySource
  sourceActionId?: string
  estimatedValue: number
  confidence: number
  winProbability: number
  stage: OpportunityStage
  createdAt: string
  expectedCloseDate?: string
  stageChangedAt?: string
  buyingIntent: number
  relationshipStrength: number
  riskLevel: 'low' | 'medium' | 'high'
  assignee?: string
  team?: string[]
  tags: string[]
  notes: OpportunityNote[]
  lastActivityAt?: string
}

export function calculateWinProbability(opportunity: {
  stage: OpportunityStage
  buyingIntent: number
  relationshipStrength: number
  nbaConfidence: number
  signalActivity: number
}): number {
  return Math.min(1,
    0.30 * STAGE_WEIGHT[opportunity.stage] +
    0.25 * opportunity.buyingIntent +
    0.20 * opportunity.relationshipStrength +
    0.15 * opportunity.signalActivity +
    0.10 * opportunity.nbaConfidence
  )
}
