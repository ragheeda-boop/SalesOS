import type { DecisionItem } from '@/application/dashboard/dashboard.dto'

export interface DecisionQueueViewProps {
  items: DecisionItem[]
  total: number
  onItemClick?: (id: string) => void
}
