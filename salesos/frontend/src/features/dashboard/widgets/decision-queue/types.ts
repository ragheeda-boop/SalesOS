import type { DecisionItem } from '@/application/dashboard/dashboard.dto'
import type { DecisionContextData, NBAFeedItem } from '@salesos/widget-sdk'

export interface DecisionQueueViewProps {
 items: DecisionItem[]
 total: number
 decision?: DecisionContextData | null
 nbaItems?: NBAFeedItem[]
 isDecisionLoading?: boolean
 onItemClick?: (id: string) => void
}
