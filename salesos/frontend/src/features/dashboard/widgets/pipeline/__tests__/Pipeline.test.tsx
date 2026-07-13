import { render, screen, fireEvent } from '@testing-library/react'
import { PipelineView } from '../PipelineView'
import { PipelineWidget } from '../PipelineContainer'
import { describeWidgetContract } from '../../../sdk/testing'
import type { PipelineViewProps, PipelineStage, PipelineDeal } from '../types'

const sampleStages: PipelineStage[] = [
  { id: 's1', name: 'استكشاف', count: 12, value: 3_500_000, color: '#3b82f6' },
  { id: 's2', name: 'تقديم عرض', count: 8, value: 5_200_000, color: '#f97316' },
  { id: 's3', name: 'تفاوض', count: 4, value: 2_100_000, color: '#8b5cf6' },
  { id: 's4', name: 'إغلاق', count: 2, value: 1_800_000, color: '#22c55e' },
]

const sampleDeals: PipelineDeal[] = [
  { id: 'd1', companyId: 'c1', companyName: 'ACME Corp', title: 'صفقة الاستحواذ', stage: 'تقديم عرض', value: 2_500_000, probability: 75, daysInStage: 12 },
  { id: 'd2', companyId: 'c2', companyName: 'Beta Ltd', title: 'توسع الرياض', stage: 'استكشاف', value: 1_200_000, probability: 40, daysInStage: 5 },
  { id: 'd3', companyId: 'c3', companyName: 'Gamma Co', title: 'تجديد العقد', stage: 'تفاوض', value: 800_000, probability: 90, daysInStage: 3 },
]

const defaultProps: PipelineViewProps = {
  stages: sampleStages,
  deals: sampleDeals,
  totalValue: 12_600_000,
  dealCount: 26,
}

function renderView(overrides?: Partial<PipelineViewProps>) {
  return render(<PipelineView {...defaultProps} {...overrides} />)
}

describeWidgetContract({
  name: 'Pipeline',
  defaultData: { stages: sampleStages, deals: sampleDeals, totalValue: 12_600_000, dealCount: 26 },
  config: {
    metadata: {
      id: 'pipeline',
      title: 'أنابيب المبيعات',
      minHeight: '300px',
      permissions: ['pipeline:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => (
      <PipelineView
        stages={data.stages ?? []}
        deals={data.deals ?? []}
        totalValue={data.totalValue ?? 0}
        dealCount={data.dealCount ?? 0}
      />
    ),
  },
})

describe('PipelineView', () => {
  it('renders all stages', () => {
    renderView()
    expect(screen.getByText('استكشاف')).toBeInTheDocument()
    expect(screen.getByText('تقديم عرض')).toBeInTheDocument()
    expect(screen.getByText('تفاوض')).toBeInTheDocument()
    expect(screen.getByText('إغلاق')).toBeInTheDocument()
  })

  it('renders stage counts', () => {
    renderView()
    expect(screen.getByText('12 صفقة')).toBeInTheDocument()
    expect(screen.getByText('8 صفقة')).toBeInTheDocument()
  })

  it('renders deal count summary', () => {
    renderView()
    const dealCounts = screen.getAllByText(/26 صفقة/)
    expect(dealCounts.length).toBeGreaterThanOrEqual(1)
  })

  it('renders all deals', () => {
    renderView()
    expect(screen.getByText('صفقة الاستحواذ')).toBeInTheDocument()
    expect(screen.getByText('توسع الرياض')).toBeInTheDocument()
    expect(screen.getByText('تجديد العقد')).toBeInTheDocument()
  })

  it('renders company names', () => {
    renderView()
    expect(screen.getByText('ACME Corp')).toBeInTheDocument()
    expect(screen.getByText('Beta Ltd')).toBeInTheDocument()
  })

  it('renders deal probabilities', () => {
    renderView()
    expect(screen.getByText(/75%/)).toBeInTheDocument()
    expect(screen.getByText(/40%/)).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    renderView({ stages: [], deals: [], totalValue: 0, dealCount: 0 })
    expect(screen.getByText('لا توجد بيانات الأنبوب')).toBeInTheDocument()
  })

  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'أنابيب المبيعات' })).toBeInTheDocument()
  })

  it('renders progress bars for stages', () => {
    renderView()
    const progressBars = screen.getAllByRole('progressbar')
    expect(progressBars.length).toBe(4)
  })

  it('calls onDealClick when deal is clicked', () => {
    const onDealClick = jest.fn()
    renderView({ onDealClick })
    fireEvent.click(screen.getByLabelText(/صفقة الاستحواذ/))
    expect(onDealClick).toHaveBeenCalledWith('d1')
  })

  it('supports keyboard Enter on deal', () => {
    const onDealClick = jest.fn()
    renderView({ onDealClick })
    fireEvent.keyDown(screen.getByLabelText(/صفقة الاستحواذ/), { key: 'Enter' })
    expect(onDealClick).toHaveBeenCalledWith('d1')
  })

  it('shows skeleton when loading', () => {
    renderView({ isDecisionLoading: true, stages: [], deals: [] })
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('has motion-reduce classes', () => {
    renderView()
    const elements = document.querySelectorAll('[class*="motion-reduce"]')
    expect(elements.length).toBeGreaterThanOrEqual(1)
  })
})

describe('PipelineWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(PipelineWidget).toBeDefined()
    expect(typeof PipelineWidget === 'function' || typeof PipelineWidget === 'object').toBe(true)
  })
})
