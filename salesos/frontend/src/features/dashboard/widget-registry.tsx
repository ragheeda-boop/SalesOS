"use client";

import { createRegistry, type RegistryEntry } from "./_registry/widget-registry";
import { withErrorBoundary } from "@/components/error-boundary";
import { MissionCenterWidget } from "./widgets/mission-center";
import { DecisionQueueWidget } from "./widgets/decision-queue";
import { IntelligenceFeedWidget } from "./widgets/intelligence-feed";
import { AIBriefWidget } from "./widgets/ai-brief";
import { MarketPulseWidget } from "./widgets/market-pulse";
import { RecentActivityWidget } from "./widgets/recent-activity";
import { PipelineWidget } from "./widgets/pipeline";
import { CompanyHealthWidget } from "./widgets/company-health";
import { CompanyEngagementWidget } from "./widgets/company-engagement";
import { EmailIntelligenceWidget } from "./widgets/email-intelligence";
import { CalendarIntelligenceWidget } from "./widgets/calendar-intelligence";
import { FollowupCenterWidget } from "./widgets/followup-center";
import { CompanyScoringWidget } from "@/features/scoring/widgets/company-scoring";

const MissionCenterBounded = withErrorBoundary(
  MissionCenterWidget,
  <WidgetFallback title="Mission Center" />
);
const DecisionQueueBounded = withErrorBoundary(
  DecisionQueueWidget,
  <WidgetFallback title="Decision Queue" />
);
const IntelligenceFeedBounded = withErrorBoundary(
  IntelligenceFeedWidget,
  <WidgetFallback title="Intelligence Feed" />
);
const AIBriefBounded = withErrorBoundary(AIBriefWidget, <WidgetFallback title="AI Brief" />);
const MarketPulseBounded = withErrorBoundary(
  MarketPulseWidget,
  <WidgetFallback title="Market Pulse" />
);
const RecentActivityBounded = withErrorBoundary(
  RecentActivityWidget,
  <WidgetFallback title="Recent Activity" />
);
const PipelineBounded = withErrorBoundary(PipelineWidget, <WidgetFallback title="Pipeline" />);
const CompanyHealthBounded = withErrorBoundary(
  CompanyHealthWidget,
  <WidgetFallback title="Company Health" />
);
const CompanyEngagementBounded = withErrorBoundary(
  CompanyEngagementWidget,
  <WidgetFallback title="Company Engagement" />
);
const EmailIntelligenceBounded = withErrorBoundary(
  EmailIntelligenceWidget,
  <WidgetFallback title="Email Intelligence" />
);
const CalendarIntelligenceBounded = withErrorBoundary(
  CalendarIntelligenceWidget,
  <WidgetFallback title="Calendar Intelligence" />
);
const FollowupCenterBounded = withErrorBoundary(
  FollowupCenterWidget,
  <WidgetFallback title="Follow-up Center" />
);
const CompanyScoringBounded = withErrorBoundary(
  CompanyScoringWidget,
  <WidgetFallback title="Company Scoring" />
);

function WidgetFallback({ title }: { title: string }) {
  return (
    <div
      className="flex h-full items-center justify-center p-4"
      role="status"
      aria-label={`${title} widget loading error`}
    >
      <div className="text-center">
        <p className="text-sm font-medium text-[var(--text-primary)]">{title}</p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">حدث خطأ في تحميل هذا المكون</p>
      </div>
    </div>
  );
}

export const widgetRegistry: RegistryEntry[] = createRegistry([
  { id: "missionCenter", Container: MissionCenterBounded },
  { id: "decisionQueue", Container: DecisionQueueBounded },
  { id: "intelligenceFeed", Container: IntelligenceFeedBounded },
  { id: "aiBrief", Container: AIBriefBounded },
  { id: "marketPulse", Container: MarketPulseBounded },
  { id: "recentActivity", Container: RecentActivityBounded },
  { id: "pipeline", Container: PipelineBounded },
  { id: "companyHealth", Container: CompanyHealthBounded },
  { id: "companyEngagement", Container: CompanyEngagementBounded },
  { id: "emailIntelligence", Container: EmailIntelligenceBounded },
  { id: "calendarIntelligence", Container: CalendarIntelligenceBounded },
  { id: "followupCenter", Container: FollowupCenterBounded },
  { id: "companyScoring", Container: CompanyScoringBounded },
]);
