import { deriveStatus, type WidgetStatus } from '@salesos/workspace'
import type {
  CompanyIntelligenceDTO, CompanyDNA, AIRecommendation, DecisionMaker,
  TimelineEvent, SignalItem, GovernmentRecord, DocumentItem, BuyingJourney, GoldenRecordEntry,
} from './company-intelligence.dto'

export type CompanyWidgetId =
  | 'companyDNA' | 'aiRecommendation' | 'decisionMakers' | 'relationshipGraph'
  | 'smartTimeline' | 'signalsFeed' | 'governmentIntelligence' | 'documentIntelligence'
  | 'buyingJourney' | 'goldenRecord'

export interface CompanyWidgetMap {
  companyDNA: { data: CompanyDNA | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  aiRecommendation: { data: AIRecommendation | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  decisionMakers: { data: DecisionMaker[] | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  relationshipGraph: { data: { nodes: CompanyIntelligenceDTO['relationships']['nodes']; edges: CompanyIntelligenceDTO['relationships']['edges'] } | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  smartTimeline: { data: TimelineEvent[] | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  signalsFeed: { data: SignalItem[] | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  governmentIntelligence: { data: GovernmentRecord[] | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  documentIntelligence: { data: DocumentItem[] | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  buyingJourney: { data: BuyingJourney | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
  goldenRecord: { data: GoldenRecordEntry[] | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void }
}

function w<T>(data: T | null | undefined, isLoading: boolean, isError: boolean, lastUpdated: string | null): { data: T | null; status: WidgetStatus; lastUpdated: string | null; error: Error | null; refetch: () => void } {
  return {
    data: data ?? null,
    status: deriveStatus(data, isLoading, isError),
    lastUpdated,
    error: isError ? new Error('فشل تحميل البيانات') : null,
    refetch: () => {},
  }
}

export function deriveCompanyIntelligenceWidgets(
  dto: CompanyIntelligenceDTO | undefined,
  isLoading: boolean,
  isError: boolean,
): CompanyWidgetMap {
  const lu = dto?.generatedAt ?? null
  return {
    companyDNA: w(dto?.dna, isLoading, isError, lu),
    aiRecommendation: w(dto?.aiRecommendation, isLoading, isError, lu),
    decisionMakers: w(dto?.decisionMakers, isLoading, isError, lu),
    relationshipGraph: w(dto?.relationships ? { nodes: dto.relationships.nodes, edges: dto.relationships.edges } : null, isLoading, isError, lu),
    smartTimeline: w(dto?.timeline, isLoading, isError, lu),
    signalsFeed: w(dto?.signals, isLoading, isError, lu),
    governmentIntelligence: w(dto?.government, isLoading, isError, lu),
    documentIntelligence: w(dto?.documents, isLoading, isError, lu),
    buyingJourney: w(dto?.buyingJourney, isLoading, isError, lu),
    goldenRecord: w(dto?.goldenRecord, isLoading, isError, lu),
  }
}
