import { render, screen } from '@testing-library/react'
import { SmartTimelineView } from '../SmartTimelineView'
import { SmartTimelineWidget } from '../SmartTimelineContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { TimelineEvent } from '@/application/company-intelligence/company-intelligence.dto'

const sample: TimelineEvent[] = [
  { id: 't1', type: 'signal', summary: 'إعلان توسع في الرياض', date: '2026-07-10', source: 'News', aiHighlighted: true, confidence: 0.92 },
  { id: 't2', type: 'meeting', summary: 'اجتماع مع فريق المبيعات', date: '2026-07-09', source: 'CRM' },
  { id: 't3', type: 'hiring', summary: 'توظيف 50 مهندس', date: '2026-07-08', source: 'LinkedIn' },
]

function renderView(events = sample) {
  return render(<SmartTimelineView events={events} />)
}

describeWidgetContract({
  name: 'SmartTimeline', defaultData: sample,
  config: {
    metadata: { id: 'smartTimeline', title: 'الجدول الزمني الذكي', permissions: ['company:timeline:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <SmartTimelineView events={data} />,
  },
})

describe('SmartTimelineView', () => {
  it('renders event summaries', () => {
    renderView()
    expect(screen.getByText('إعلان توسع في الرياض')).toBeInTheDocument()
    expect(screen.getByText('اجتماع مع فريق المبيعات')).toBeInTheDocument()
  })

  it('renders type labels', () => {
    renderView()
    const labels = screen.getAllByText('إشارة')
    expect(labels.length).toBeGreaterThanOrEqual(1)
  })

  it('shows empty state', () => {
    renderView([])
    expect(screen.getByText('لا توجد أحداث في الجدول الزمني')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'الجدول الزمني الذكي' })).toBeInTheDocument()
  })
})

describe('SmartTimelineWidget', () => {
  it('is a valid widget component', () => {
    expect(SmartTimelineWidget).toBeDefined()
  })
})
