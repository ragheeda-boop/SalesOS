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
  it('renders win rate', () => {
    renderView(); expect(screen.getByText(/%33/)).toBeInTheDocument()
  })
  it('renders stage names', () => {
    renderView(); expect(screen.getByText('قيد التأهيل')).toBeInTheDocument()
  })
  it('renders stalled deals', () => {
    renderView(); expect(screen.getByText(/شركة الطاقة/)).toBeInTheDocument()
  })
  it('shows stalled days', () => {
    renderView(); expect(screen.getByText(/21 يوم/)).toBeInTheDocument()
  })
  it('has role="region"', () => {
    renderView(); expect(screen.getByRole('region', { name: 'ذكاء الأنابيب' })).toBeInTheDocument()
  })
})

describe('PipelineIntelligenceWidget', () => {
  it('is a valid widget component', () => { expect(PipelineIntelligenceWidget).toBeDefined() })
})
