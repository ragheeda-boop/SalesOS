export interface MissionMetricProps {
  label: string
  value: string | number
  valueClassName?: string
  icon?: string
  trend?: { direction: 'up' | 'down' | 'stable'; value: number }
  ariaLabel?: string
}

export interface MissionActionProps {
  id: string
  title: string
  priority: 'high' | 'medium' | 'low'
  companyName?: string
  dueBy?: string
  onAction?: (id: string) => void
}

export interface MissionProgressProps {
  value: number
  max: number
  label: string
  barClassName?: string
}

export interface MissionCenterViewProps {
  companiesTracked: number
  activeDeals: number
  pipelineValue: number
  signalsToday: number
  decisionsPending: number
  totalTracked?: number
}
