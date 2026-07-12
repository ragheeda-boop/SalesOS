import dynamic from "next/dynamic"
import type { ComponentType } from "react"

interface SearchPanelProps { open: boolean; onClose: () => void }
interface CopilotPanelProps { open: boolean; onClose: () => void; entityType?: string; entityId?: string; context?: Record<string, unknown> }

function skeleton(height = "h-48") {
  return function Skeleton() {
    return (
      <div className={`w-full ${height} animate-pulse rounded-lg bg-neutral-200 dark:bg-neutral-700`} />
    )
  }
}

export const DynamicSearchPanel = dynamic(
  () => import("@/components/search-panel").then((m) => ({ default: m.SearchPanel as ComponentType<SearchPanelProps> })),
  { ssr: false, loading: () => <div className="hidden" /> }
)

export const DynamicCopilotPanel = dynamic(
  () => import("@/components/copilot-panel").then((m) => ({ default: m.CopilotPanel as ComponentType<CopilotPanelProps> })),
  { ssr: false, loading: () => <div className="hidden" /> }
)

export const DynamicExecutiveDashboard = dynamic(
  () => import("@/components/executive-dashboard").then((m) => ({ default: m.ExecutiveDashboard })),
  { ssr: false, loading: skeleton("h-96") }
)

export const DynamicPipelineKanban = dynamic(
  () => import("@/components/pipeline-kanban").then((m) => ({ default: m.PipelineKanban })),
  { ssr: false, loading: skeleton("h-96") }
)

export const DynamicTimelineWidget = dynamic(
  () => import("@/components/timeline-widget").then((m) => ({ default: m.TimelineWidget })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicMissionCenterView = dynamic(
  () => import("@/features/dashboard/widgets/mission-center/MissionCenterView").then((m) => ({ default: m.MissionCenterView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicSmartTimelineView = dynamic(
  () => import("@/features/company-intelligence/widgets/smart-timeline/SmartTimelineView").then((m) => ({ default: m.SmartTimelineView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicSignalsFeedView = dynamic(
  () => import("@/features/company-intelligence/widgets/signals-feed/SignalsFeedView").then((m) => ({ default: m.SignalsFeedView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicRelationshipGraphView = dynamic(
  () => import("@/features/company-intelligence/widgets/relationship-graph/RelationshipGraphView").then((m) => ({ default: m.RelationshipGraphView })),
  { ssr: false, loading: skeleton("h-80") }
)

export const DynamicCompanyDNAView = dynamic(
  () => import("@/features/company-intelligence/widgets/company-dna/CompanyDNAView").then((m) => ({ default: m.CompanyDNAView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicAIRecommendationView = dynamic(
  () => import("@/features/company-intelligence/widgets/ai-recommendation/AIRecommendationView").then((m) => ({ default: m.AIRecommendationView })),
  { ssr: false, loading: skeleton("h-48") }
)

export const DynamicDecisionMakersView = dynamic(
  () => import("@/features/company-intelligence/widgets/decision-makers/DecisionMakersView").then((m) => ({ default: m.DecisionMakersView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicBuyingJourneyView = dynamic(
  () => import("@/features/company-intelligence/widgets/buying-journey/BuyingJourneyView").then((m) => ({ default: m.BuyingJourneyView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicRevenueHealthView = dynamic(
  () => import("@/features/revenue-execution/widgets/revenue-health/RevenueHealthView").then((m) => ({ default: m.RevenueHealthView })),
  { ssr: false, loading: skeleton("h-48") }
)

export const DynamicForecastView = dynamic(
  () => import("@/features/revenue-execution/widgets/forecast-intelligence/ForecastView").then((m) => ({ default: m.ForecastView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicOpportunityListView = dynamic(
  () => import("@/features/revenue-execution/widgets/opportunity-list/OpportunityListView").then((m) => ({ default: m.OpportunityListView })),
  { ssr: false, loading: skeleton("h-64") }
)

export const DynamicMeetingIntelligenceWidget = dynamic(
  () => import("@/features/revenue-execution/widgets/meeting-intelligence/MeetingIntelligenceWidget").then((m) => ({ default: m.MeetingIntelligenceWidget })),
  { ssr: false, loading: skeleton("h-48") }
)
