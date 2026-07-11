import type { RevenueOpportunity } from '@/application/revenue-execution/opportunity.dto'
export interface OpportunityListViewProps { opportunities: RevenueOpportunity[]; onSelect?: (opp: RevenueOpportunity) => void }
