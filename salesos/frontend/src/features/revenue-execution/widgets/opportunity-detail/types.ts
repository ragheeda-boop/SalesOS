import type { RevenueOpportunity, OpportunityStage } from '@/application/revenue-execution/opportunity.dto'
export interface OpportunityDetailViewProps { opportunity: RevenueOpportunity | null; onStageChange?: (id: string, stage: OpportunityStage) => void }
