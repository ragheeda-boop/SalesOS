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

function resolveFromDto<T>(
 id: WidgetId,
 widget: DashboardWidget<T> | null | undefined,
 isLoading: boolean,
 isError: boolean,
): DashboardWidget<T> {
 if (!widget) {
 return buildWidget<T>(id, null, isLoading, isError)
 }
 if (isLoading && !widget.data) {
 return { ...widget, status: 'loading' }
 }
 if (isLoading && widget.data) {
 return { ...widget, status: 'degraded' }
 }
 // Prefer API-reported status (e.g. error with null data) over infinite loading.
 if (widget.status === 'error' || widget.status === 'ready' || widget.status === 'degraded') {
 return widget
 }
 return { ...widget, status: deriveStatus(widget.data, isLoading, isError) }
}

export function deriveWidgets(
 dto: DashboardDTO | undefined,
 isLoading: boolean,
 isError: boolean,
): WidgetMap {
 return {
 missionCenter: resolveFromDto('missionCenter', dto?.missionCenter, isLoading, isError),
 decisionQueue: resolveFromDto('decisionQueue', dto?.decisionQueue, isLoading, isError),
 intelligenceFeed: resolveFromDto('intelligenceFeed', dto?.intelligenceFeed, isLoading, isError),
 aiBrief: resolveFromDto('aiBrief', dto?.aiBrief, isLoading, isError),
 marketPulse: resolveFromDto('marketPulse', dto?.marketPulse, isLoading, isError),
 recentActivity: resolveFromDto('recentActivity', dto?.recentActivity, isLoading, isError),
 pipeline: resolveFromDto('pipeline', dto?.pipeline, isLoading, isError),
 companyHealth: resolveFromDto('companyHealth', dto?.companyHealth, isLoading, isError),
 }
}
