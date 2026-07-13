import type { DecisionContextData, NBAFeedItem } from '../../sdk/types'

export interface HealthMetric {
  id: string
  label: string
  value: number
  previousValue?: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  trendValue: number
  color: string
}

export interface HealthAlert {
  id: string
  type: 'warning' | 'critical' | 'info'
  message: string
  companyId: string
  companyName: string
  timestamp: string
}

export interface CompanyHealthViewProps {
  overallScore: number
  metrics: HealthMetric[]
  alerts: HealthAlert[]
  companyName: string
  decision?: DecisionContextData | null
  nbaItems?: NBAFeedItem[]
  isDecisionLoading?: boolean
  onAlertClick?: (alertId: string) => void
  onMetricClick?: (metricId: string) => void
}

export interface CompanyHealthData {
  overallScore: number
  metrics: HealthMetric[]
  alerts: HealthAlert[]
  companyName: string
}
