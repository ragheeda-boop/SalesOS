import { render, screen, fireEvent } from '@testing-library/react'
import { OpportunityListView } from '../OpportunityListView'
import { OpportunityListWidget } from '../OpportunityListContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { RevenueOpportunity } from '@/application/revenue-execution/opportunity.dto'

const sample: RevenueOpportunity[] = [
  { id: 'o1', companyId: 'c1', companyName: 'أرامكو السعودية', title: 'توسع في الطاقة المتجددة', source: 'nba', estimatedValue: 500000, confidence: 0.85, winProbability: 0.45, stage: 'developing', createdAt: '2026-07-01', buyingIntent: 0.82, relationshipStrength: 0.70, riskLevel: 'low', tags: [], notes: [], lastActivityAt: '2026-07-10' },
  { id: 'o2', companyId: 'c2', companyName: 'STC', title: 'منصة تقنية مالية', source: 'nba', estimatedValue: 300000, confidence: 0.72, winProbability: 0.30, stage: 'qualifying', createdAt: '2026-07-05', buyingIntent: 0.65, relationshipStrength: 0.50, riskLevel: 'medium', tags: [], notes: [] },
]

function renderView(opps = sample) {
  return render(<OpportunityListView opportunities={opps} />)
}

describeWidgetContract({
  name: 'OpportunityList', defaultData: sample,
  config: {
    metadata: { id: 'opportunityList', title: 'الفرص', permissions: ['opportunity:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <OpportunityListView opportunities={data} />,
  },
})

describe('OpportunityListView', () => {
  it('renders opportunity titles', () => {
    renderView()
    expect(screen.getByText('توسع في الطاقة المتجددة')).toBeInTheDocument()
    expect(screen.getByText('منصة تقنية مالية')).toBeInTheDocument()
  })

  it('renders company names', () => {
    renderView()
    expect(screen.getByText('أرامكو السعودية')).toBeInTheDocument()
    expect(screen.getByText('STC')).toBeInTheDocument()
  })

  it('renders stage labels', () => {
    renderView()
    const dev = screen.getAllByText('قيد التطوير')
    expect(dev.length).toBeGreaterThanOrEqual(1)
    const qual = screen.getAllByText('قيد التأهيل')
    expect(qual.length).toBeGreaterThanOrEqual(1)
  })

  it('renders active count', () => {
    renderView()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('renders total value', () => {
    renderView()
    expect(screen.getByText(/\$800K/)).toBeInTheDocument()
  })

  it('shows stage filter buttons', () => {
    renderView()
    expect(screen.getByText(/الكل/)).toBeInTheDocument()
    const devFilters = screen.getAllByText(/قيد التطوير/)
    expect(devFilters.length).toBeGreaterThanOrEqual(1)
  })

  it('filters by stage on click', () => {
    renderView()
    const filters = screen.getAllByText(/قيد التأهيل/)
    fireEvent.click(filters[0])
    expect(screen.queryByText('توسع في الطاقة المتجددة')).not.toBeInTheDocument()
  })

  it('calls onSelect when opportunity clicked', () => {
    const onSelect = jest.fn()
    render(<OpportunityListView opportunities={sample} onSelect={onSelect} />)
    fireEvent.click(screen.getByText('توسع في الطاقة المتجددة'))
    expect(onSelect).toHaveBeenCalledWith(sample[0])
  })

  it('shows empty state', () => {
    renderView([])
    expect(screen.getByText('لا توجد فرص بعد')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'قائمة الفرص' })).toBeInTheDocument()
  })
})

describe('OpportunityListWidget', () => {
  it('is a valid widget component', () => {
    expect(OpportunityListWidget).toBeDefined()
  })
})
