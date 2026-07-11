jest.mock('../widget-config', () => ({
  COMPANY_INTELLIGENCE_WIDGETS: [
    { id: 'company-dna', title: 'Company DNA', component: 'CompanyDNA' },
    { id: 'ai-recommendation', title: 'AI Recommendation', component: 'AIRecommendation' },
    { id: 'decision-makers', title: 'Decision Makers', component: 'DecisionMakers' },
    { id: 'relationship-graph', title: 'Relationship Graph', component: 'RelationshipGraph' },
    { id: 'smart-timeline', title: 'Smart Timeline', component: 'SmartTimeline' },
    { id: 'signals-feed', title: 'Signals Feed', component: 'SignalsFeed' },
    { id: 'government-intelligence', title: 'Government Intelligence', component: 'GovernmentIntelligence' },
    { id: 'document-intelligence', title: 'Document Intelligence', component: 'DocumentIntelligence' },
    { id: 'buying-journey', title: 'Buying Journey', component: 'BuyingJourney' },
    { id: 'golden-record', title: 'Golden Record', component: 'GoldenRecord' },
  ],
  getCompanyWidgets: () => ['company-dna', 'ai-recommendation', 'decision-makers', 'relationship-graph', 'smart-timeline', 'signals-feed', 'government-intelligence', 'document-intelligence', 'buying-journey', 'golden-record'],
}))

import { COMPANY_INTELLIGENCE_WIDGETS, getCompanyWidgets } from '../widget-config'

describe('company-intelligence widget-config', () => {
  it('exports all widgets', () => {
    expect(COMPANY_INTELLIGENCE_WIDGETS).toHaveLength(10)
  })

  it('returns widget IDs', () => {
    const ids = getCompanyWidgets()
    expect(ids).toHaveLength(10)
    expect(ids).toContain('company-dna')
    expect(ids).toContain('golden-record')
  })
})
