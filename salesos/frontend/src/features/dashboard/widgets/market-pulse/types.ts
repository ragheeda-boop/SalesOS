import type { MarketTrend, CompanyMover } from '@/application/dashboard/dashboard.dto'

export interface MarketPulseViewProps {
  trends: MarketTrend[]
  topMovers: CompanyMover[]
  onTrendClick?: (name: string) => void
  onMoverClick?: (companyId: string) => void
}
