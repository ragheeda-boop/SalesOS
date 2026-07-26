'use client'

import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { LoadingState, ErrorState, EmptyState } from '../../_components/states'
import { CompanyDNAView } from '@/features/company-intelligence/widgets/company-dna/CompanyDNAView'
import { AIRecommendationView } from '@/features/company-intelligence/widgets/ai-recommendation/AIRecommendationView'
import { DecisionMakersView } from '@/features/company-intelligence/widgets/decision-makers/DecisionMakersView'
import { RelationshipGraphView } from '@/features/company-intelligence/widgets/relationship-graph/RelationshipGraphView'
import { SmartTimelineView } from '@/features/company-intelligence/widgets/smart-timeline/SmartTimelineView'
import { SignalsFeedView } from '@/features/company-intelligence/widgets/signals-feed/SignalsFeedView'
import { GovernmentIntelligenceView } from '@/features/company-intelligence/widgets/government-intelligence/GovernmentIntelligenceView'
import { DocumentIntelligenceView } from '@/features/company-intelligence/widgets/document-intelligence/DocumentIntelligenceView'
import { BuyingJourneyView } from '@/features/company-intelligence/widgets/buying-journey/BuyingJourneyView'
import { GoldenRecordView } from '@/features/company-intelligence/widgets/golden-record/GoldenRecordView'

function WidgetCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
      <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">{title}</h3>
      {children}
    </div>
  )
}

export function IntelligenceTab({ companyId }: { companyId: string }) {
  const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)

  if (isLoading) return <LoadingState label="Loading intelligence…" />
  if (isError) return (
    <ErrorState
      title="Failed to load intelligence"
      description={error instanceof Error ? error.message : undefined}
      onRetry={() => void refetch()}
    />
  )
  if (!data) return (
    <EmptyState
      title="No intelligence available"
      description="Company intelligence data has not been generated yet."
    />
  )

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <WidgetCard title="Company DNA">
          <CompanyDNAView dna={data.dna} />
        </WidgetCard>
        <WidgetCard title="AI Recommendation">
          <AIRecommendationView recommendation={data.aiRecommendation} />
        </WidgetCard>
        <WidgetCard title="Decision Makers">
          <DecisionMakersView makers={data.decisionMakers} />
        </WidgetCard>
        <WidgetCard title="Relationship Graph">
          <RelationshipGraphView nodes={data.relationships.nodes} edges={data.relationships.edges} />
        </WidgetCard>
        <WidgetCard title="Buying Journey">
          <BuyingJourneyView journey={data.buyingJourney} />
        </WidgetCard>
        <WidgetCard title="Golden Record">
          <GoldenRecordView entries={data.goldenRecord} dna={data.dna} />
        </WidgetCard>
      </div>
      <WidgetCard title="Signals">
        <SignalsFeedView signals={data.signals} />
      </WidgetCard>
      <WidgetCard title="Smart Timeline">
        <SmartTimelineView events={data.timeline} />
      </WidgetCard>
      <div className="grid gap-4 md:grid-cols-2">
        <WidgetCard title="Government Intelligence">
          <GovernmentIntelligenceView records={data.government} />
        </WidgetCard>
        <WidgetCard title="Document Intelligence">
          <DocumentIntelligenceView documents={data.documents} />
        </WidgetCard>
      </div>
    </div>
  )
}
