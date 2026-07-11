import type { ActivityItem } from '@/application/dashboard/dashboard.dto'

export interface RecentActivityViewProps {
  items: ActivityItem[]
  total: number
  onItemClick?: (id: string) => void
}
