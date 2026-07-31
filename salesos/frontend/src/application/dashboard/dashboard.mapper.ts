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
  CompanyEngagementDTO,
  EmailMetricsDTO,
  CalendarMetricsDTO,
  FollowupDashboardDTO,
  CompanyScoringData,
} from "./dashboard.dto";
import type { DashboardWidget, WidgetStatus } from "./widget.contract";

function parseWidget<T>(
  raw: Record<string, unknown> | null | undefined,
): DashboardWidget<T> | null {
  if (!raw) return null;
  return {
    id: String(raw.id ?? ""),
    title: String(raw.title ?? ""),
    status: (raw.status as WidgetStatus) ?? "ready",
    lastUpdated: raw.lastUpdated ? String(raw.lastUpdated) : null,
    data: (raw.data as T) ?? null,
    actions: Array.isArray(raw.actions)
      ? (raw.actions as DashboardWidget<T>["actions"])
      : [],
  };
}

export function mapDashboard(raw: unknown): DashboardDTO {
  const data = (raw ?? {}) as Record<string, unknown>;
  return {
    generatedAt: data.generatedAt ? String(data.generatedAt) : null,
    period: (data.period as DashboardDTO["period"]) ?? "today",
    totalTracked: Number(data.totalTracked) || 0,
    missionCenter: parseWidget<MissionCenterData>(
      data.missionCenter as Record<string, unknown> | null | undefined,
    ),
    decisionQueue: parseWidget<DecisionQueueData>(
      data.decisionQueue as Record<string, unknown> | null | undefined,
    ),
    intelligenceFeed: parseWidget<IntelligenceFeedData>(
      data.intelligenceFeed as Record<string, unknown> | null | undefined,
    ),
    aiBrief: parseWidget<AIBriefData>(
      data.aiBrief as Record<string, unknown> | null | undefined,
    ),
    marketPulse: parseWidget<MarketPulseData>(
      data.marketPulse as Record<string, unknown> | null | undefined,
    ),
    recentActivity: parseWidget<RecentActivityData>(
      data.recentActivity as Record<string, unknown> | null | undefined,
    ),
    pipeline: parseWidget<PipelineDTOData>(
      data.pipeline as Record<string, unknown> | null | undefined,
    ),
    companyHealth: parseWidget<CompanyHealthDTOData>(
      data.companyHealth as Record<string, unknown> | null | undefined,
    ),
    companyEngagement: parseWidget<CompanyEngagementDTO>(
      data.companyEngagement as Record<string, unknown> | null | undefined,
    ),
    emailIntelligence: parseWidget<EmailMetricsDTO>(
      data.emailIntelligence as Record<string, unknown> | null | undefined,
    ),
    calendarIntelligence: parseWidget<CalendarMetricsDTO>(
      data.calendarIntelligence as Record<string, unknown> | null | undefined,
    ),
    followupCenter: parseWidget<FollowupDashboardDTO>(
      data.followupCenter as Record<string, unknown> | null | undefined,
    ),
    companyScoring: parseWidget<CompanyScoringData>(
      data.companyScoring as Record<string, unknown> | null | undefined,
    ),
  };
}
