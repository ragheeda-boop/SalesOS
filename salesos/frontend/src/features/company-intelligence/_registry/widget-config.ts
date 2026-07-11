export type CompanyWidgetId =
  | 'companyDNA' | 'aiRecommendation' | 'decisionMakers' | 'relationshipGraph'
  | 'smartTimeline' | 'signalsFeed' | 'governmentIntelligence' | 'documentIntelligence'
  | 'buyingJourney' | 'goldenRecord'

export const COMPANY_INTELLIGENCE_WIDGET_CONFIG: Record<CompanyWidgetId, {
  id: CompanyWidgetId; gridColumn: string; minHeight: string; refreshIntervalMs: number; staleThresholdMs: number
}> = {
  companyDNA:            { id: 'companyDNA',            gridColumn: 'span 2', minHeight: '420px', refreshIntervalMs: 300_000, staleThresholdMs: 600_000 },
  aiRecommendation:      { id: 'aiRecommendation',      gridColumn: 'span 4', minHeight: '420px', refreshIntervalMs: 60_000,  staleThresholdMs: 120_000 },
  decisionMakers:        { id: 'decisionMakers',        gridColumn: 'span 2', minHeight: '320px', refreshIntervalMs: 300_000, staleThresholdMs: 600_000 },
  relationshipGraph:     { id: 'relationshipGraph',     gridColumn: 'span 4', minHeight: '320px', refreshIntervalMs: 300_000, staleThresholdMs: 600_000 },
  smartTimeline:         { id: 'smartTimeline',         gridColumn: 'span 6', minHeight: '400px', refreshIntervalMs: 60_000,  staleThresholdMs: 120_000 },
  signalsFeed:           { id: 'signalsFeed',           gridColumn: 'span 3', minHeight: '300px', refreshIntervalMs: 60_000,  staleThresholdMs: 120_000 },
  governmentIntelligence:{ id: 'governmentIntelligence',gridColumn: 'span 3', minHeight: '300px', refreshIntervalMs: 300_000, staleThresholdMs: 600_000 },
  documentIntelligence:  { id: 'documentIntelligence',  gridColumn: 'span 3', minHeight: '300px', refreshIntervalMs: 300_000, staleThresholdMs: 600_000 },
  buyingJourney:         { id: 'buyingJourney',         gridColumn: 'span 2', minHeight: '280px', refreshIntervalMs: 60_000,  staleThresholdMs: 120_000 },
  goldenRecord:          { id: 'goldenRecord',          gridColumn: 'span 3', minHeight: '300px', refreshIntervalMs: 300_000, staleThresholdMs: 600_000 },
}

export function getCompanyWidgetConfig(id: CompanyWidgetId) {
  return COMPANY_INTELLIGENCE_WIDGET_CONFIG[id]
}
