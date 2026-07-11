import type { DashboardWidget, WidgetStatus } from './widget.contract'
import type {
  DashboardDTO,
  MissionCenterData,
  DecisionQueueData,
  IntelligenceFeedData,
  AIBriefData,
  MarketPulseData,
  RecentActivityData,
} from './dashboard.dto'

type WidgetId = 'missionCenter' | 'decisionQueue' | 'intelligenceFeed' | 'aiBrief' | 'marketPulse' | 'recentActivity'

const WIDGET_META: Record<WidgetId, { id: string; title: string }> = {
  missionCenter: { id: 'mission-center', title: 'Mission Center' },
  decisionQueue: { id: 'decision-queue', title: 'Decision Queue' },
  intelligenceFeed: { id: 'intelligence-feed', title: 'Intelligence Feed' },
  aiBrief: { id: 'ai-brief', title: 'AI Brief' },
  marketPulse: { id: 'market-pulse', title: 'Market Pulse' },
  recentActivity: { id: 'recent-activity', title: 'Recent Activity' },
}

export type WidgetMap = {
  missionCenter: DashboardWidget<MissionCenterData>
  decisionQueue: DashboardWidget<DecisionQueueData>
  intelligenceFeed: DashboardWidget<IntelligenceFeedData>
  aiBrief: DashboardWidget<AIBriefData>
  marketPulse: DashboardWidget<MarketPulseData>
  recentActivity: DashboardWidget<RecentActivityData>
}

export function deriveStatus(data: unknown, isLoading: boolean, isError: boolean): WidgetStatus {
  if (isLoading && !data) return 'loading'
  if (isLoading && data) return 'degraded'
  if (isError && !data) return 'error'
  if (isError && data) return 'degraded'
  if (!data) return 'loading'
  return 'ready'
}

function buildWidget<T>(
  id: WidgetId,
  data: T | null | undefined,
  isLoading: boolean,
  isError: boolean,
): DashboardWidget<T> {
  const meta = WIDGET_META[id]
  return {
    id: meta.id,
    title: meta.title,
    status: deriveStatus(data, isLoading, isError),
    lastUpdated: null,
    data: data ?? null,
    actions: [{ id: `${meta.id}.refresh`, label: 'Refresh', type: 'refresh' }],
  }
}

export function deriveWidgets(
  dto: DashboardDTO | undefined,
  isLoading: boolean,
  isError: boolean,
): WidgetMap {
  return {
    missionCenter: buildWidget('missionCenter', dto?.missionCenter?.data as MissionCenterData | null | undefined, isLoading, isError),
    decisionQueue: buildWidget('decisionQueue', dto?.decisionQueue?.data as DecisionQueueData | null | undefined, isLoading, isError),
    intelligenceFeed: buildWidget('intelligenceFeed', dto?.intelligenceFeed?.data as IntelligenceFeedData | null | undefined, isLoading, isError),
    aiBrief: buildWidget('aiBrief', dto?.aiBrief?.data as AIBriefData | null | undefined, isLoading, isError),
    marketPulse: buildWidget('marketPulse', dto?.marketPulse?.data as MarketPulseData | null | undefined, isLoading, isError),
    recentActivity: buildWidget('recentActivity', dto?.recentActivity?.data as RecentActivityData | null | undefined, isLoading, isError),
  }
}
