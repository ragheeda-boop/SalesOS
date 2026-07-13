import type { DecisionContextData, NBAFeedItem } from '../../sdk/types'

export interface PipelineStage {
  id: string
  name: string
  count: number
  value: number
  color: string
}

export interface PipelineDeal {
  id: string
  companyId: string
  companyName: string
  title: string
  stage: string
  value: number
  probability: number
  daysInStage: number
}

export interface PipelineViewProps {
  stages: PipelineStage[]
  deals: PipelineDeal[]
  totalValue: number
  dealCount: number
  decision?: DecisionContextData | null
  nbaItems?: NBAFeedItem[]
  isDecisionLoading?: boolean
  onDealClick?: (dealId: string) => void
}

export interface PipelineData {
  stages: PipelineStage[]
  deals: PipelineDeal[]
  totalValue: number
  dealCount: number
}
