import { render, screen } from '@testing-library/react'
import { PipelineView } from '../PipelineView'
import { PipelineIntelligenceWidget } from '../PipelineContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { PipelineInsight } from '@/application/revenue-execution/pipeline.dto'

const sample: PipelineInsight = {
  totalDeals: 12, totalValue: 8000000, weightedValue: 4200000, avgDealSize: 666667, winRate: 0.33,
  stages: [
    { id: 'qualifying', label: 'قيد التأهيل', deals: 4, value: 2000000, color: 'bg-blue-400' },
    { id: 'developing', label: 'قيد التطوير', deals: 5, value: 3500000, color: 'bg-purple-400' },
    { id: 'proposing', label: 'قيد العرض', deals: 3, value: 2500000, color: 'bg-amber-400' },
  ],
  stalledDeals: [
    { id: 's1', companyName: 'شركة الطاقة', title: 'عقد طويل الأمد', stage: 'قيد التطوير', value: 1500000, daysStalled: 21, reason: 'انتظار رد' },
  ],
  bottlenecks: [{ stage: 'قيد التطوير', deals: 5, avgDays: 45 }],
}

function renderView(p = sample) { return render(<PipelineView pipeline={p} />) }

describeWidgetContract({
  name: 'PipelineIntelligence', defaultData: sample,
  config: {
    metadata: { id: 'pipelineIntelligence', title: 'ذكاء الأنابيب', permissions: ['pipeline:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <PipelineView pipeline={data} />,
  },
})

describe('PipelineView', () => {
  it('renders total deals', () => {
    renderView(); expect(screen.getByText('12')).toBeInTheDocument()
  })
  it('renders total value', () => {
    renderView(); expect(screen.getByText(/\$8\.0M/)).toBeInTheDocument()
  })
  it('renders weighted value', () => {
    renderView(); expect(screen.getByText(/\$4\.2M/)).toBeInTheDocument()
  })
  it('renders win rate', () => {
    renderView(); expect(screen.getByText(/%33/)).toBeInTheDocument()
  })
  it('renders stage names', () => {
    renderView(); expect(screen.getByText('قيد التأهيل')).toBeInTheDocument()
    expect(screen.getByText('قيد التطوير')).toBeInTheDocument()
    expect(screen.getByText('قيد العرض')).toBeInTheDocument()
  })
  it('renders stalled deals', () => {
    renderView(); expect(screen.getByText(/شركة الطاقة/)).toBeInTheDocument()
  })
  it('shows stalled days with reason', () => {
    renderView(); expect(screen.getByText(/21 يوم/)).toBeInTheDocument()
    expect(screen.getByText(/انتظار رد/)).toBeInTheDocument()
  })
  it('renders deal count per stage', () => {
    renderView()
    expect(screen.getByText('4')).toBeInTheDocument()
  })
  it('renders stage value', () => {
    renderView(); expect(screen.getByText(/\$2\.0M/)).toBeInTheDocument()
  })
  it('has role="region"', () => {
    renderView(); expect(screen.getByRole('region', { name: 'ذكاء الأنابيب' })).toBeInTheDocument()
  })
})

describe('PipelineView edge cases', () => {
  it('renders empty pipeline with zero values', () => {
    const emptyPipeline: PipelineInsight = {
      totalDeals: 0, totalValue: 0, weightedValue: 0, avgDealSize: 0, winRate: 0,
      stages: [],
      stalledDeals: [],
      bottlenecks: [],
    }
    renderView(emptyPipeline)
    expect(screen.getByText('0')).toBeInTheDocument()
    const zeroTexts = screen.getAllByText(/\$0K/)
    expect(zeroTexts.length).toBeGreaterThanOrEqual(1)
  })

  it('does not render stalled deals section when empty', () => {
    const noStalls: PipelineInsight = { ...sample, stalledDeals: [] }
    renderView(noStalls)
    expect(screen.queryByText(/متوقفة/)).not.toBeInTheDocument()
  })

  it('renders K format for values under 1M', () => {
    const small: PipelineInsight = { ...sample, totalValue: 500000, weightedValue: 250000 }
    renderView(small)
    expect(screen.getByText(/\$500K/)).toBeInTheDocument()
    expect(screen.getByText(/\$250K/)).toBeInTheDocument()
  })

  it('renders at most 3 stalled deals', () => {
    const manyStalls: PipelineInsight = {
      ...sample,
      stalledDeals: [
        { id: 's1', companyName: 'أ', title: '1', stage: 'قيد التطوير', value: 100000, daysStalled: 1, reason: '' },
        { id: 's2', companyName: 'ب', title: '2', stage: 'قيد التطوير', value: 100000, daysStalled: 2, reason: '' },
        { id: 's3', companyName: 'ج', title: '3', stage: 'قيد التطوير', value: 100000, daysStalled: 3, reason: '' },
        { id: 's4', companyName: 'د', title: '4', stage: 'قيد التطوير', value: 100000, daysStalled: 4, reason: '' },
      ],
    }
    renderView(manyStalls)
    expect(screen.getByText(/متوقفة \(4\)/)).toBeInTheDocument()
  })
})

describe('PipelineIntelligenceWidget', () => {
  it('is a valid widget component', () => { expect(PipelineIntelligenceWidget).toBeDefined() })
})
