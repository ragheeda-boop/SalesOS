import { deriveCompanyIntelligenceWidgets } from '../company-intelligence.store'
import type { CompanyIntelligenceDTO } from '../company-intelligence.dto'

const sampleDTO: CompanyIntelligenceDTO = {
  companyId: 'c-1',
  generatedAt: '2026-07-11T12:00:00Z',
  dna: null,
  aiRecommendation: null,
  decisionMakers: [],
  relationships: { nodes: [], edges: [] },
  timeline: [],
  signals: [],
  government: [],
  documents: [],
  buyingJourney: null,
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
