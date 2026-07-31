import type { DashboardWidget, WidgetStatus } from "./widget.contract";
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

type WidgetId =
  | "missionCenter"
  | "decisionQueue"
  | "intelligenceFeed"
  | "aiBrief"
  | "marketPulse"
  | "recentActivity"
  | "pipeline"
  | "companyHealth"
  | "companyEngagement"
  | "emailIntelligence"
  | "calendarIntelligence"
  | "followupCenter"
  | "companyScoring";

const WIDGET_META: Record<WidgetId, { id: string; title: string }> = {
  missionCenter: { id: "mission-center", title: "Mission Center" },
  decisionQueue: { id: "decision-queue", title: "Decision Queue" },
  intelligenceFeed: { id: "intelligence-feed", title: "Intelligence Feed" },
  aiBrief: { id: "ai-brief", title: "AI Brief" },
  marketPulse: { id: "market-pulse", title: "Market Pulse" },
  recentActivity: { id: "recent-activity", title: "Recent Activity" },
  pipeline: { id: "pipeline", title: "Pipeline" },
  companyHealth: { id: "company-health", title: "Company Health" },
  companyEngagement: { id: "company-engagement", title: "Company Engagement" },
  emailIntelligence: { id: "email-intelligence", title: "Email Intelligence" },
  calendarIntelligence: {
    id: "calendar-intelligence",
    title: "Calendar Intelligence",
  },
  followupCenter: { id: "followup-center", title: "Follow-up Center" },
  companyScoring: { id: "company-scoring", title: "Company Scoring" },
};

export type WidgetMap = {
  missionCenter: DashboardWidget<MissionCenterData>;
  decisionQueue: DashboardWidget<DecisionQueueData>;
  intelligenceFeed: DashboardWidget<IntelligenceFeedData>;
  aiBrief: DashboardWidget<AIBriefData>;
  marketPulse: DashboardWidget<MarketPulseData>;
  recentActivity: DashboardWidget<RecentActivityData>;
  pipeline: DashboardWidget<PipelineDTOData>;
  companyHealth: DashboardWidget<CompanyHealthDTOData>;
  companyEngagement: DashboardWidget<CompanyEngagementDTO>;
  emailIntelligence: DashboardWidget<EmailMetricsDTO>;
  calendarIntelligence: DashboardWidget<CalendarMetricsDTO>;
  followupCenter: DashboardWidget<FollowupDashboardDTO>;
  companyScoring: DashboardWidget<CompanyScoringData>;
};

export function deriveStatus(
  data: unknown,
  isLoading: boolean,
  isError: boolean,
): WidgetStatus {
  if (isLoading && !data) return "loading";
  if (isLoading && data) return "degraded";
  if (isError && !data) return "error";
  if (isError && data) return "degraded";
  // Widget absent from API or empty data — treat as ready, not error.
  if (!data) return "ready";
  return "ready";
}

function buildWidget<T>(
  id: WidgetId,
  data: T | null | undefined,
  isLoading: boolean,
  isError: boolean,
): DashboardWidget<T> {
  const meta = WIDGET_META[id];
  return {
    id: meta.id,
    title: meta.title,
    status: deriveStatus(data, isLoading, isError),
    lastUpdated: null,
    data: data ?? null,
    actions: [{ id: `${meta.id}.refresh`, label: "Refresh", type: "refresh" }],
  };
}

function resolveFromDto<T>(
  id: WidgetId,
  widget: DashboardWidget<T> | null | undefined,
  isLoading: boolean,
  isError: boolean,
): DashboardWidget<T> {
  if (!widget) {
    return buildWidget<T>(id, null, isLoading, isError);
  }
  if (isLoading && !widget.data) {
    return { ...widget, status: "loading" };
  }
  if (isLoading && widget.data) {
    return { ...widget, status: "degraded" };
  }
  // API-reported error with no data = empty state, not an error
  if (widget.status === "error") {
    return { ...widget, status: deriveStatus(widget.data, isLoading, isError) };
  }
  if (widget.status === "ready" || widget.status === "degraded") {
    return widget;
  }
  return { ...widget, status: deriveStatus(widget.data, isLoading, isError) };
}

export function deriveWidgets(
  dto: DashboardDTO | undefined,
  isLoading: boolean,
  isError: boolean,
): WidgetMap {
  return {
    missionCenter: resolveFromDto(
      "missionCenter",
      dto?.missionCenter,
      isLoading,
      isError,
    ),
    decisionQueue: resolveFromDto(
      "decisionQueue",
      dto?.decisionQueue,
      isLoading,
      isError,
    ),
    intelligenceFeed: resolveFromDto(
      "intelligenceFeed",
      dto?.intelligenceFeed,
      isLoading,
      isError,
    ),
    aiBrief: resolveFromDto("aiBrief", dto?.aiBrief, isLoading, isError),
    marketPulse: resolveFromDto(
      "marketPulse",
      dto?.marketPulse,
      isLoading,
      isError,
    ),
    recentActivity: resolveFromDto(
      "recentActivity",
      dto?.recentActivity,
      isLoading,
      isError,
    ),
    pipeline: resolveFromDto("pipeline", dto?.pipeline, isLoading, isError),
    companyHealth: resolveFromDto(
      "companyHealth",
      dto?.companyHealth,
      isLoading,
      isError,
    ),
    companyEngagement: resolveFromDto(
      "companyEngagement",
      dto?.companyEngagement,
      isLoading,
      isError,
    ),
    emailIntelligence: resolveFromDto(
      "emailIntelligence",
      dto?.emailIntelligence,
      isLoading,
      isError,
    ),
    calendarIntelligence: resolveFromDto(
      "calendarIntelligence",
      dto?.calendarIntelligence,
      isLoading,
      isError,
    ),
    followupCenter: resolveFromDto(
      "followupCenter",
      dto?.followupCenter,
      isLoading,
      isError,
    ),
    companyScoring: resolveFromDto(
      "companyScoring",
      dto?.companyScoring,
      isLoading,
      isError,
    ),
  };
}
