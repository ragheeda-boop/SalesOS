import { deriveNextBestAction } from '../nba.engine'
import type { CompanyDNA, AIRecommendation, TimelineEvent, SignalItem, DecisionMaker } from '@/application/company-intelligence/company-intelligence.dto'

const dna: CompanyDNA = {
  industry: 'energy', businessModel: 'b2b', size: { employees: 15000, revenue: '1.2B', label: 'enterprise' },
  growthPattern: 'accelerating', buyingBehaviour: { score: 78, intent: 'high' },
  technologyProfile: {}, financialHealth: { score: 82, revenue: 1_200_000_000, growth: 12.5, trend: 'up' },
  governmentExposure: { level: 'high', contracts: 45 },
  expansionPotential: { score: 72, markets: [] }, digitalPresence: { score: 68, website: 'active', social: 'active' },
  hiringTrend: { trend: 'growing', openings: 120 }, procurementMaturity: { score: 65, level: 'managed' },
  relationshipStrength: { score: 70, connections: 15 }, buyingIntent: { score: 82, confidence: 0.88 },
  riskLevel: { score: 25, level: 'low' }, confidenceScore: 0.92,
  dataFreshness: { score: 90, updatedAt: '2026-07-10' }, goldenRecordStatus: { status: 'clean', sources: 5 },
}

const recommendation: AIRecommendation = {
  action: 'meeting', actionLabel: 'ترتيب اجتماع', reasoning: 'ارتفاع نية الشراء', confidence: 0.85,
  expectedRevenue: 500000, expectedImpact: 'high', estimatedTime: 'أسبوعين',
  alternatives: [{ action: 'send_proposal', actionLabel: 'إرسال عرض', confidence: 0.7 }],
  risks: ['مورد بديل'],
}

const timeline: TimelineEvent[] = [
  { id: 't1', type: 'signal', summary: 'إعلان توسع', date: '2026-07-10', source: 'News', aiHighlighted: true },
]

const signals: SignalItem[] = [
  { id: 's1', type: 'hiring', title: 'توظيف كبير', description: '', source: 'LinkedIn', severity: 'high', timestamp: '2026-07-10T08:00:00Z', aiConfidence: 0.9 },
]

const makers: DecisionMaker[] = [
  { id: 'dm1', name: 'أحمد', role: 'CEO', department: '', influence: 'high', connected: true },
]

describe('deriveNextBestAction', () => {
  it('returns null when no DNA', () => {
    expect(deriveNextBestAction(null, null, [], [], [])).toBeNull()
  })

  it('returns action with DNA only', () => {
    const action = deriveNextBestAction(dna, null, [], [], [])
    expect(action).not.toBeNull()
    expect(action!.actionLabel).toBeDefined()
    expect(action!.score).toBeGreaterThan(0)
  })

  it('includes recommendation data when available', () => {
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action!.reasoning).toContain('ارتفاع نية الشراء')
    expect(action!.expectedRevenue).toBe(500000)
  })

  it('calculates priority correctly for high intent', () => {
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(['critical', 'high']).toContain(action!.priority)
  })

  it('includes risk information', () => {
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action!.risks.length).toBeGreaterThanOrEqual(1)
  })

  it('includes alternatives when available', () => {
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action!.alternatives.length).toBeGreaterThanOrEqual(1)
  })

  it('sets createsOpportunity for high scores', () => {
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action!.createsOpportunity).toBe(true)
  })

  it('includes score breakdown', () => {
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action!.scoreBreakdown.buyingIntent).toBeGreaterThan(0)
    expect(action!.scoreBreakdown.relationshipStrength).toBeGreaterThan(0)
    expect(action!.scoreBreakdown.aiConfidence).toBeGreaterThan(0)
  })

  it('assigns playbook based on industry', () => {
    const action = deriveNextBestAction(dna, recommendation, timeline, signals, makers)
    expect(action!.playbookId).toBe('playbook-energy')
  })

  it('returns low priority for low intent company', () => {
    const lowDna: CompanyDNA = {
      ...dna,
      buyingIntent: { score: 15, confidence: 0.2 },
      relationshipStrength: { score: 10, connections: 0 },
      financialHealth: { score: 30, revenue: 100_000, growth: -5, trend: 'down' },
    }
    const action = deriveNextBestAction(lowDna, null, [], [], [])
    expect(action!.priority).toBe('low')
  })
})
