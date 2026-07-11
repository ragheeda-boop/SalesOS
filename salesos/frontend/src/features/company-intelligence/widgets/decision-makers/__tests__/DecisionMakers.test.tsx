import { render, screen } from '@testing-library/react'
import { DecisionMakersView } from '../DecisionMakersView'
import { DecisionMakersWidget } from '../DecisionMakersContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { DecisionMaker } from '@/application/company-intelligence/company-intelligence.dto'

const sample: DecisionMaker[] = [
  { id: 'dm1', name: 'د. أحمد السلمي', role: 'CEO', department: 'الإدارة العليا', influence: 'high', connected: true, lastInteraction: '2026-07-08' },
  { id: 'dm2', name: 'نورة القحطاني', role: 'CTO', department: 'التقنية', influence: 'medium', connected: false },
]

function renderView(makers = sample) {
  return render(<DecisionMakersView makers={makers} />)
}

describeWidgetContract({
  name: 'DecisionMakers', defaultData: sample,
  config: {
    metadata: { id: 'decisionMakers', title: 'صناع القرار', permissions: ['company:decision-makers:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <DecisionMakersView makers={data} />,
  },
})

describe('DecisionMakersView', () => {
  it('renders names', () => {
    renderView()
    expect(screen.getByText('د. أحمد السلمي')).toBeInTheDocument()
    expect(screen.getByText('نورة القحطاني')).toBeInTheDocument()
  })

  it('renders roles', () => {
    renderView()
    expect(screen.getByText(/CEO/)).toBeInTheDocument()
    expect(screen.getByText(/CTO/)).toBeInTheDocument()
  })

  it('shows connected star', () => {
    renderView()
    // The connected user has a Star icon
  })

  it('shows empty state', () => {
    renderView([])
    expect(screen.getByText('لا توجد جهات اتصال')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'صناع القرار' })).toBeInTheDocument()
  })
})

describe('DecisionMakersWidget', () => {
  it('is a valid widget component', () => {
    expect(DecisionMakersWidget).toBeDefined()
  })
})
