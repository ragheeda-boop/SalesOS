import { render, screen } from '@testing-library/react'
import { GoldenRecordView } from '../GoldenRecordView'
import { GoldenRecordWidget } from '../GoldenRecordContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { GoldenRecordEntry, CompanyDNA } from '@/application/company-intelligence/company-intelligence.dto'

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

const entries: GoldenRecordEntry[] = [
  { id: 'gr1', entityName: 'أرامكو السعودية', source: 'CRM', confidence: 0.98, conflicts: [], freshness: '2026-07-10', status: 'matched' },
  { id: 'gr2', entityName: 'Saudi Aramco', source: 'Bloomberg', confidence: 0.85, conflicts: ['name'], freshness: '2026-07-09', status: 'potential_duplicate' },
]

function renderView(e = entries, d = dna) {
  return render(<GoldenRecordView entries={e} dna={d} />)
}

describeWidgetContract({
  name: 'GoldenRecord', defaultData: { entries, dna },
  config: {
    metadata: { id: 'goldenRecord', title: 'السجل الذهبي', permissions: ['company:golden-record:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <GoldenRecordView entries={data.entries} dna={data.dna} />,
  },
})

describe('GoldenRecordView', () => {
  it('renders entry names', () => {
    renderView()
    expect(screen.getByText('أرامكو السعودية')).toBeInTheDocument()
    expect(screen.getByText('Saudi Aramco')).toBeInTheDocument()
  })

  it('shows golden record status', () => {
    renderView()
    expect(screen.getByText('سجل ذهبي نظيف')).toBeInTheDocument()
  })

  it('shows source count', () => {
    renderView()
    expect(screen.getByText(/5 مصادر/)).toBeInTheDocument()
  })

  it('shows empty state', () => {
    renderView([], null)
    expect(screen.getByText('لا توجد بيانات السجل الذهبي')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'السجل الذهبي' })).toBeInTheDocument()
  })
})

describe('GoldenRecordWidget', () => {
  it('is a valid widget component', () => {
    expect(GoldenRecordWidget).toBeDefined()
  })
})
