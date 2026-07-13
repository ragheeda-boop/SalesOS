import type { DecisionItem } from '@/application/dashboard/dashboard.dto'
import type { DecisionContextData, NBAFeedItem } from '../../sdk/types'

export interface DecisionQueueViewProps {
  items: DecisionItem[]
  total: number
  decision?: DecisionContextData | null
  nbaItems?: NBAFeedItem[]
  isDecisionLoading?: boolean
  onItemClick?: (id: string) => void
}
