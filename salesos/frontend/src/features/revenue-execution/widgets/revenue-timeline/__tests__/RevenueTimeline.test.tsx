import { render, screen } from '@testing-library/react'
import { RevenueTimelineView } from '../RevenueTimelineView'
import { RevenueTimelineWidget } from '../RevenueTimelineContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { RevenueTimelineEvent } from '../types'

const sample: RevenueTimelineEvent[] = [
  { id: 'rt1', type: 'meeting', summary: 'اجتماع مع شركة الطاقة', date: '2026-07-10', entityName: 'شركة الطاقة' },
  { id: 'rt2', type: 'deal', summary: 'فرصة توسع في الطاقة', date: '2026-07-09', entityName: 'شركة الطاقة', value: 500000 },
  { id: 'rt3', type: 'task', summary: 'متابعة عرض STC', date: '2026-07-08', entityName: 'STC' },
]

function renderView(e: RevenueTimelineEvent[] = sample) { return render(<RevenueTimelineView events={e} />) }

describeWidgetContract({
  name: 'RevenueTimeline', defaultData: sample,
  config: { metadata: { id: 'revenueTimeline', title: 'الجدول الزمني للإيرادات', permissions: ['revenue:timeline:read'], featureFlag: { enabled: true } }, render: ({ data }) => <RevenueTimelineView events={data} /> },
})

describe('RevenueTimelineView', () => {
  it('renders event summaries', () => {
    renderView(); expect(screen.getByText('اجتماع مع شركة الطاقة')).toBeInTheDocument()
    expect(screen.getByText('فرصة توسع في الطاقة')).toBeInTheDocument()
  })
  it('renders entity names', () => { renderView(); const c = screen.getAllByText(/شركة الطاقة/); expect(c.length).toBeGreaterThanOrEqual(1) })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'الجدول الزمني للإيرادات' })).toBeInTheDocument() })
  it('shows empty state', () => { renderView([]); expect(screen.getByText('لا توجد أحداث')).toBeInTheDocument() })
})
describe('RevenueTimelineWidget', () => { it('is a valid widget', () => { expect(RevenueTimelineWidget).toBeDefined() }) })
