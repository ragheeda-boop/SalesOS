import { render, screen, fireEvent } from '@testing-library/react'
import { OpportunityDetailView } from '../OpportunityDetailView'
import { OpportunityDetailWidget } from '../OpportunityDetailContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { RevenueOpportunity } from '@/application/revenue-execution/opportunity.dto'

const sample: RevenueOpportunity = {
  id: 'o1', companyId: 'c1', companyName: 'أرامكو السعودية', title: 'توسع في الطاقة المتجددة',
  source: 'nba', estimatedValue: 500000, confidence: 0.85, winProbability: 0.45,
  stage: 'developing', createdAt: '2026-07-01', lastActivityAt: '2026-07-10',
  buyingIntent: 0.82, relationshipStrength: 0.70, riskLevel: 'low',
  tags: [], notes: [
    { id: 'n1', text: 'تم التواصل مع صانع القرار', createdAt: '2026-07-08', author: 'أحمد' },
  ],
}

function renderView(opp = sample) {
  return render(<OpportunityDetailView opportunity={opp} />)
}

describeWidgetContract({
  name: 'OpportunityDetail', defaultData: sample,
  config: {
    metadata: { id: 'opportunityDetail', title: 'تفاصيل الفرصة', permissions: ['opportunity:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <OpportunityDetailView opportunity={data} />,
  },
})

describe('OpportunityDetailView', () => {
  it('renders title', () => {
    renderView()
    expect(screen.getByText('توسع في الطاقة المتجددة')).toBeInTheDocument()
  })

  it('renders company name', () => {
    renderView()
    expect(screen.getByText('أرامكو السعودية')).toBeInTheDocument()
  })

  it('renders stage', () => {
    renderView()
    expect(screen.getByText('قيد التطوير')).toBeInTheDocument()
  })

  it('renders estimated value', () => {
    renderView()
    expect(screen.getByText(/\$500K/)).toBeInTheDocument()
  })

  it('renders win probability', () => {
    renderView()
    expect(screen.getByText(/%45/)).toBeInTheDocument()
  })

  it('renders risk level', () => {
    renderView()
    expect(screen.getByText('منخفض')).toBeInTheDocument()
  })

  it('renders notes', () => {
    renderView()
    expect(screen.getByText('تم التواصل مع صانع القرار')).toBeInTheDocument()
  })

  it('calls onStageChange when stage clicked', () => {
    const onStageChange = jest.fn()
    render(<OpportunityDetailView opportunity={sample} onStageChange={onStageChange} />)
    const stages = screen.getAllByText('6')
    fireEvent.click(stages[0])
    expect(onStageChange).toHaveBeenCalledWith('o1', 'closing')
  })

  it('shows empty state', () => {
    renderView(null)
    expect(screen.getByText('اختر فرصة لعرض التفاصيل')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: /تفاصيل الفرصة/ })).toBeInTheDocument()
  })
})

describe('OpportunityDetailWidget', () => {
  it('is a valid widget component', () => {
    expect(OpportunityDetailWidget).toBeDefined()
  })
})
