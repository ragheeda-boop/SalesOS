import { render, screen } from '@testing-library/react'
import { GovernmentIntelligenceView } from '../GovernmentIntelligenceView'
import { GovernmentIntelligenceWidget } from '../GovernmentIntelligenceContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { GovernmentRecord } from '@/application/company-intelligence/company-intelligence.dto'

const sample: GovernmentRecord[] = [
  { id: 'g1', type: 'cr', title: 'السجل التجاري', status: 'active', source: 'وزارة التجارة', confidence: 0.95, freshness: '2026-07-10', expiryDate: '2027-01-01' },
  { id: 'g2', type: 'municipality', title: 'رخصة البلدية', status: 'expired', source: 'البلدي', confidence: 0.90, freshness: '2026-06-01', expiryDate: '2026-06-01' },
]

function renderView(records = sample) {
  return render(<GovernmentIntelligenceView records={records} />)
}

describeWidgetContract({
  name: 'GovernmentIntelligence', defaultData: sample,
  config: {
    metadata: { id: 'governmentIntelligence', title: 'البيانات الحكومية', permissions: ['company:government:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <GovernmentIntelligenceView records={data} />,
  },
})

describe('GovernmentIntelligenceView', () => {
  it('renders record titles', () => {
    renderView()
    expect(screen.getByText('السجل التجاري')).toBeInTheDocument()
    expect(screen.getByText('رخصة البلدية')).toBeInTheDocument()
  })

  it('shows status labels', () => {
    renderView()
    expect(screen.getByText('ساري')).toBeInTheDocument()
    expect(screen.getByText('منتهي')).toBeInTheDocument()
  })

  it('shows empty state', () => {
    renderView([])
    expect(screen.getByText('لا توجد سجلات حكومية')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'البيانات الحكومية' })).toBeInTheDocument()
  })
})

describe('GovernmentIntelligenceWidget', () => {
  it('is a valid widget component', () => {
    expect(GovernmentIntelligenceWidget).toBeDefined()
  })
})
