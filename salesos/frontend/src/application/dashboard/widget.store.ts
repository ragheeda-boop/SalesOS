import type { DashboardWidget, WidgetStatus } from './widget.contract'
import type {
 DashboardDTO,
 MissionCenterData,
 DecisionQueueData,
 IntelligenceFeedData,
 AIBriefData,
 MarketPulseData,
 RecentActivityData,
 PipelineDTOData,
 CompanyHealthDTOData,
} from './dashboard.dto'

type WidgetId = 'missionCenter' | 'decisionQueue' | 'intelligenceFeed' | 'aiBrief' | 'marketPulse' | 'recentActivity' | 'pipeline' | 'companyHealth'

const WIDGET_META: Record<WidgetId, { id: string; title: string }> = {
 missionCenter: { id: 'mission-center', title: 'Mission Center' },
 decisionQueue: { id: 'decision-queue', title: 'Decision Queue' },
 intelligenceFeed: { id: 'intelligence-feed', title: 'Intelligence Feed' },
 aiBrief: { id: 'ai-brief', title: 'AI Brief' },
 marketPulse: { id: 'market-pulse', title: 'Market Pulse' },
 recentActivity: { id: 'recent-activity', title: 'Recent Activity' },
 pipeline: { id: 'pipeline', title: 'Pipeline' },
 companyHealth: { id: 'company-health', title: 'Company Health' },
}

export type WidgetMap = {
 missionCenter: DashboardWidget<MissionCenterData>
 decisionQueue: DashboardWidget<DecisionQueueData>
 intelligenceFeed: DashboardWidget<IntelligenceFeedData>
 aiBrief: DashboardWidget<AIBriefData>
 marketPulse: DashboardWidget<MarketPulseData>
 recentActivity: DashboardWidget<RecentActivityData>
 pipeline: DashboardWidget<PipelineDTOData>
 companyHealth: DashboardWidget<CompanyHealthDTOData>
}

export function deriveStatus(data: unknown, isLoading: boolean, isError: boolean): WidgetStatus {
 if (isLoading && !data) return 'loading'
 if (isLoading && data) return 'degraded'
 if (isError && !data) return 'error'
 if (isError && data) return 'degraded'
 // Never spin forever when the request finished with empty/error payload.
 if (!data) return 'error'
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
 const from = <T,>(
 id: WidgetId,
 widget: DashboardWidget<T> | null | undefined,
 ): DashboardWidget<T> => {
 if (widget) {
 const status =
 isLoading && !widget.data
 ? 'loading'
 : widget.status === 'ready' || widget.status === 'error' || widget.status === 'degraded' || widget.status === 'loading'
 ? (isLoading && widget.data ? 'degraded' : widget.status)
 : deriveStatus(widget.data, isLoading, isError)
 return { ...widget, status }
 }
 return buildWidget(id, null, isLoading, isError)
 }

 return {
 missionCenter: from('missionCenter', dto?.missionCenter as DashboardWidget<MissionCenterData> | null | undefined),
 decisionQueue: from('decisionQueue', dto?.decisionQueue as DashboardWidget<DecisionQueueData> | null | undefined),
 intelligenceFeed: from('intelligenceFeed', dto?.intelligenceFeed as DashboardWidget<IntelligenceFeedData> | null | undefined),
 aiBrief: from('aiBrief', dto?.aiBrief as DashboardWidget<AIBriefData> | null | undefined),
 marketPulse: from('marketPulse', dto?.marketPulse as DashboardWidget<MarketPulseData> | null | undefined),
 recentActivity: from('recentActivity', dto?.recentActivity as DashboardWidget<RecentActivityData> | null | undefined),
 pipeline: from('pipeline', dto?.pipeline as DashboardWidget<PipelineDTOData> | null | undefined),
 companyHealth: from('companyHealth', dto?.companyHealth as DashboardWidget<CompanyHealthDTOData> | null | undefined),
 }
}
