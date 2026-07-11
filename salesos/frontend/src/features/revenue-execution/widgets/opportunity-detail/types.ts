import type { RevenueOpportunity } from '@/application/revenue-execution/opportunity.dto'
export interface OpportunityDetailViewProps { opportunity: RevenueOpportunity | null; onStageChange?: (id: string, stage: any) => void }
