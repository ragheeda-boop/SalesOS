import { render, screen } from '@testing-library/react'
import { SignalsFeedView } from '../SignalsFeedView'
import { SignalsFeedWidget } from '../SignalsFeedContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { SignalItem } from '@/application/company-intelligence/company-intelligence.dto'

const sample: SignalItem[] = [
  { id: 's1', type: 'hiring', title: 'توظيف 500 مهندس', description: 'خطة توسعية في الطاقة', source: 'LinkedIn', severity: 'high', timestamp: '2026-07-10T08:00:00Z', aiConfidence: 0.92 },
  { id: 's2', type: 'partnership', title: 'شراكة مع STC', description: 'اتفاقية تقنية مالية', source: 'Bloomberg', severity: 'critical', timestamp: '2026-07-10T06:00:00Z', aiConfidence: 0.88 },
]

function renderView(signals = sample) {
  return render(<SignalsFeedView signals={signals} />)
}

describeWidgetContract({
  name: 'SignalsFeed', defaultData: sample,
  config: {
    metadata: { id: 'signalsFeed', title: 'الإشارات', permissions: ['company:signals:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <SignalsFeedView signals={data} />,
  },
})

describe('SignalsFeedView', () => {
  it('renders signal titles', () => {
    renderView()
    expect(screen.getByText('توظيف 500 مهندس')).toBeInTheDocument()
    expect(screen.getByText('شراكة مع STC')).toBeInTheDocument()
  })

  it('shows severity labels', () => {
    renderView()
    expect(screen.getByText('عالي')).toBeInTheDocument()
    expect(screen.getByText('حرج')).toBeInTheDocument()
  })

  it('shows AI confidence', () => {
    renderView()
    expect(screen.getByText(/%92/)).toBeInTheDocument()
  })

  it('shows empty state', () => {
    renderView([])
    expect(screen.getByText('لا توجد إشارات')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'الإشارات' })).toBeInTheDocument()
  })
})

describe('SignalsFeedWidget', () => {
  it('is a valid widget component', () => {
    expect(SignalsFeedWidget).toBeDefined()
  })
})
