import type { Recommendation } from '../ai/recommendation'

export type OpportunityStage = 'qualification' | 'discovery' | 'proposal' | 'negotiation' | 'closed_won' | 'closed_lost'
export type OpportunityHealth = 'healthy' | 'at_risk' | 'critical'

export interface Opportunity {
  id: string
  companyId: string
  name: string
  stage: OpportunityStage
  value: number
  currency: string
  probability: number
  health: OpportunityHealth
  expectedCloseDate?: string
  ownerId: string
  playbookId?: string
  nba?: Recommendation
  createdAt: string
  updatedAt: string
}

export interface StageMetrics {
  count: number
  value: number
  conversionRate: number
}

export interface PipelineSummary {
  totalValue: number
  weightedValue: number
  totalCount: number
  byStage: Record<string, StageMetrics>
  winRate: number
  avgDealSize: number
  velocityDays: number
}

export interface HealthMapItem {
  opportunityId: string
  name: string
  health: OpportunityHealth
  owner: string
  value: number
  stage: OpportunityStage
}

export interface HealthMap {
  healthy: number
  atRisk: number
  critical: number
  opportunities: HealthMapItem[]
}
