export interface PipelineStage {
  id: string
  label: string
  deals: number
  value: number
  color: string
}

export interface StalledDeal {
  id: string
  companyName: string
  title: string
  stage: string
  value: number
  daysStalled: number
  reason?: string
}

export interface PipelineInsight {
  totalDeals: number
  totalValue: number
  weightedValue: number
  avgDealSize: number
  winRate: number
  stages: PipelineStage[]
  stalledDeals: StalledDeal[]
  bottlenecks: { stage: string; deals: number; avgDays: number }[]
}
