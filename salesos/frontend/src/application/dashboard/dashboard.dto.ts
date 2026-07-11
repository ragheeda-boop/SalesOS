import type { DashboardWidget } from './widget.contract'

export interface DashboardDTO {
  generatedAt: string | null
  period: 'today' | 'week' | 'month' | 'quarter'
  totalTracked: number

  missionCenter: DashboardWidget<MissionCenterData> | null
  decisionQueue: DashboardWidget<DecisionQueueData> | null
  intelligenceFeed: DashboardWidget<IntelligenceFeedData> | null
  aiBrief: DashboardWidget<AIBriefData> | null
  marketPulse: DashboardWidget<MarketPulseData> | null
  recentActivity: DashboardWidget<RecentActivityData> | null
}

export interface MissionCenterData {
  companiesTracked: number
  activeDeals: number
  pipelineValue: number
  signalsToday: number
  decisionsPending: number
}

export interface DecisionItem {
  id: string
  companyId: string
  companyName: string
  type: 'opportunity' | 'risk' | 'recommendation'
  title: string
  priority: 'high' | 'medium' | 'low'
  dueBy?: string
  score: number
}

export interface DecisionQueueData {
  items: DecisionItem[]
  total: number
}

export interface SignalItem {
  id: string
  companyId: string
  companyName: string
  category: 'tender' | 'regulatory' | 'competitor' | 'financial' | 'news'
  title: string
  summary: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  source: string
  timestamp: string
  isUnseen: boolean
}

export interface IntelligenceFeedData {
  items: SignalItem[]
  total: number
  unseenCount: number
}

export interface AIBriefData {
  summary: string
  highlights: string[]
  generatedAt: string
}

export interface MarketTrend {
  name: string
  direction: 'up' | 'down' | 'stable'
  change: number
  description: string
}

export interface CompanyMover {
  companyId: string
  companyName: string
  scoreChange: number
  reason: string
}

export interface MarketPulseData {
  trends: MarketTrend[]
  topMovers: CompanyMover[]
}

export interface ActivityItem {
  id: string
  type: 'signal' | 'decision' | 'update' | 'note'
  title: string
  companyId?: string
  companyName?: string
  timestamp: string
}

export interface RecentActivityData {
  items: ActivityItem[]
  total: number
}
