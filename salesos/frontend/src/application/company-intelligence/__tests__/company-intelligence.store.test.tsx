import { deriveCompanyIntelligenceWidgets } from '../company-intelligence.store'
import type { CompanyIntelligenceDTO } from '../company-intelligence.dto'

const sampleDTO: CompanyIntelligenceDTO = {
  companyId: 'c-1',
  generatedAt: '2026-07-11T12:00:00Z',
  dna: { industry: 'tech', businessModel: 'b2b', size: { employees: 100, revenue: '10M', label: 'smb' }, growthPattern: 'stable', buyingBehaviour: { score: 50, intent: 'medium' }, technologyProfile: {}, financialHealth: { score: 70, revenue: 10_000_000, growth: 5, trend: 'up' }, governmentExposure: { level: 'low', contracts: 0 }, expansionPotential: { score: 50, markets: [] }, digitalPresence: { score: 50, website: 'active', social: 'active' }, hiringTrend: { trend: 'stable', openings: 10 }, procurementMaturity: { score: 50, level: 'basic' }, relationshipStrength: { score: 50, connections: 5 }, buyingIntent: { score: 50, confidence: 0.5 }, riskLevel: { score: 30, level: 'low' }, confidenceScore: 0.5, dataFreshness: { score: 80, updatedAt: '2026-07-11' }, goldenRecordStatus: { status: 'clean', sources: 2 } },
  aiRecommendation: { action: 'follow_up', actionLabel: 'متابعة', reasoning: '', confidence: 0.5, expectedRevenue: 0, expectedImpact: 'low', estimatedTime: '', alternatives: [], risks: [] },
  decisionMakers: [],
  relationships: { nodes: [], edges: [] },
  timeline: [],
  signals: [],
  government: [],
  documents: [],
  buyingJourney: { stages: [], currentStage: '', progress: 0, signals: [], nextMilestone: '' },
  goldenRecord: [],
  firmographic: null,
}

describe('deriveCompanyIntelligenceWidgets', () => {
  it('returns loading status when isLoading', () => {
    const widgets = deriveCompanyIntelligenceWidgets(undefined, true, false)
    Object.values(widgets).forEach((w) => {
      expect(w.status).toBe('loading')
    })
  })

  it('returns error status when isError', () => {
    const widgets = deriveCompanyIntelligenceWidgets(undefined, false, true)
    Object.values(widgets).forEach((w) => {
      expect(w.status).toBe('error')
    })
  })

  it('returns ready status when data is loaded', () => {
    const widgets = deriveCompanyIntelligenceWidgets(sampleDTO, false, false)
    Object.values(widgets).forEach((w) => {
      expect(w.status).toBe('ready')
    })
  })

  it('sets lastUpdated from generatedAt', () => {
    const widgets = deriveCompanyIntelligenceWidgets(sampleDTO, false, false)
    expect(widgets.companyDNA.lastUpdated).toBe('2026-07-11T12:00:00Z')
  })

  it('returns all widget entries', () => {
    const widgets = deriveCompanyIntelligenceWidgets(sampleDTO, false, false)
    expect(Object.keys(widgets)).toEqual([
      'companyDNA', 'aiRecommendation', 'decisionMakers', 'relationshipGraph',
      'smartTimeline', 'signalsFeed', 'governmentIntelligence', 'documentIntelligence',
      'buyingJourney', 'goldenRecord',
    ])
  })
})
