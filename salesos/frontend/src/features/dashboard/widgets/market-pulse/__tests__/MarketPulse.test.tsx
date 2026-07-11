import { render, screen, fireEvent } from '@testing-library/react'
import { MarketPulseView } from '../MarketPulseView'
import { MarketPulseWidget } from '../MarketPulseContainer'
import { describeWidgetContract } from '../../../sdk/testing'
import type { MarketPulseViewProps } from '../types'
import type { MarketTrend, CompanyMover } from '@/application/dashboard/dashboard.dto'

const sampleTrends: MarketTrend[] = [
  { name: 'قطاع التقنية', direction: 'up', change: 12.5, description: 'نمو متسارع' },
  { name: 'قطاع الطاقة', direction: 'down', change: 3.2, description: 'تراجع طفيف' },
  { name: 'قطاع الرعاية الصحية', direction: 'stable', change: 0.8, description: 'مستقر' },
]

const sampleMovers: CompanyMover[] = [
  { companyId: 'c1', companyName: 'أرامكو', scoreChange: 15, reason: 'نتائج قوية' },
  { companyId: 'c2', companyName: 'سابك', scoreChange: -8, reason: 'انخفاض الأرباح' },
  { companyId: 'c3', companyName: 'STC', scoreChange: 5, reason: 'توسع رقمي' },
]

const defaultProps: MarketPulseViewProps = {
  trends: sampleTrends,
  topMovers: sampleMovers,
}

function renderView(overrides?: Partial<MarketPulseViewProps>) {
  return render(<MarketPulseView {...defaultProps} {...overrides} />)
}

// ─── Contract Tests ───────────────────────────────────────────

describeWidgetContract({
  name: 'MarketPulse',
  defaultData: { trends: sampleTrends, topMovers: sampleMovers },
  config: {
    metadata: {
      id: 'market-pulse',
      title: 'نبض السوق',
      minHeight: '320px',
      permissions: ['market:read'],
      featureFlag: { enabled: true, tier: 'enterprise' },
    },
    render: ({ data }) => (
      <MarketPulseView trends={data.trends ?? []} topMovers={data.topMovers ?? []} />
    ),
  },
})

// ─── View Unit Tests ──────────────────────────────────────────

describe('MarketPulseView', () => {
  // 1. Rendering - Trends
  it('renders market trends section', () => {
    renderView()
    expect(screen.getByText('اتجاهات السوق')).toBeInTheDocument()
    expect(screen.getByText('قطاع التقنية')).toBeInTheDocument()
    expect(screen.getByText('قطاع الطاقة')).toBeInTheDocument()
    expect(screen.getByText('قطاع الرعاية الصحية')).toBeInTheDocument()
  })

  it('renders trend descriptions', () => {
    renderView()
    expect(screen.getByText('نمو متسارع')).toBeInTheDocument()
    expect(screen.getByText('تراجع طفيف')).toBeInTheDocument()
    expect(screen.getByText('مستقر')).toBeInTheDocument()
  })

  // 2. Rendering - Movers
  it('renders top movers section', () => {
    renderView()
    expect(screen.getByText('أبرز التحركات')).toBeInTheDocument()
    expect(screen.getByText('أرامكو')).toBeInTheDocument()
    expect(screen.getByText('سابك')).toBeInTheDocument()
    expect(screen.getByText('STC')).toBeInTheDocument()
  })

  it('renders mover reasons', () => {
    renderView()
    expect(screen.getByText('نتائج قوية')).toBeInTheDocument()
    expect(screen.getByText('انخفاض الأرباح')).toBeInTheDocument()
    expect(screen.getByText('توسع رقمي')).toBeInTheDocument()
  })

  // 3. Direction Indicators
  it('renders direction indicators for up/down/stable', () => {
    renderView()
    expect(screen.getByLabelText(/قطاع التقنية - صاعد/)).toBeInTheDocument()
    expect(screen.getByLabelText(/قطاع الطاقة - هابط/)).toBeInTheDocument()
    expect(screen.getByLabelText(/قطاع الرعاية الصحية - مستقر/)).toBeInTheDocument()
  })

  it('renders change percentages with direction arrows', () => {
    renderView()
    const techRow = screen.getByLabelText(/قطاع التقنية/)
    expect(techRow).toHaveTextContent('↑')
    expect(techRow).toHaveTextContent('12.5%')

    const energyRow = screen.getByLabelText(/قطاع الطاقة/)
    expect(energyRow).toHaveTextContent('↓')
    expect(energyRow).toHaveTextContent('3.2%')

    const healthRow = screen.getByLabelText(/قطاع الرعاية الصحية/)
    expect(healthRow).toHaveTextContent('→')
    expect(healthRow).toHaveTextContent('0.8%')
  })

  // 4. Score Changes with Colors
  it('renders score changes with correct signs', () => {
    renderView()
    expect(screen.getByText('+15%')).toBeInTheDocument()
    expect(screen.getByText('-8%')).toBeInTheDocument()
    expect(screen.getByText('+5%')).toBeInTheDocument()
  })

  it('has emerald color for positive scores and danger for negative', () => {
    renderView()
    const positiveScore = screen.getByText('+15%')
    expect(positiveScore.className).toContain('emerald')

    const negativeScore = screen.getByText('-8%')
    expect(negativeScore.className).toContain('danger')
  })

  // 5. Empty State
  it('shows empty state when no data', () => {
    renderView({ trends: [], topMovers: [] })
    expect(screen.getByText('بيانات السوق غير متاحة حالياً')).toBeInTheDocument()
    expect(screen.getByText(/يمكنك المحاولة لاحقاً/)).toBeInTheDocument()
  })

  it('shows trends section when trends exist but movers is empty', () => {
    renderView({ topMovers: [] })
    expect(screen.getByText('اتجاهات السوق')).toBeInTheDocument()
    expect(screen.queryByText('أبرز التحركات')).not.toBeInTheDocument()
  })

  it('shows movers section when movers exist but trends is empty', () => {
    renderView({ trends: [] })
    expect(screen.queryByText('اتجاهات السوق')).not.toBeInTheDocument()
    expect(screen.getByText('أبرز التحركات')).toBeInTheDocument()
  })

  // 6. Accessibility
  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'نبض السوق' })).toBeInTheDocument()
  })

  it('has role="list" for trends and movers sections', () => {
    renderView()
    const lists = screen.getAllByRole('list')
    expect(lists).toHaveLength(2)
    expect(lists[0]).toHaveAttribute('aria-label', 'اتجاهات السوق')
    expect(lists[1]).toHaveAttribute('aria-label', 'أبرز التحركات')
  })

  it('each trend has descriptive aria-label', () => {
    renderView()
    expect(screen.getByLabelText(/قطاع التقنية - صاعد - 12\.5%/)).toBeInTheDocument()
    expect(screen.getByLabelText(/قطاع الطاقة - هابط - 3\.2%/)).toBeInTheDocument()
  })

  it('each mover has descriptive aria-label', () => {
    renderView()
    expect(screen.getByLabelText(/أرامكو - تحسن 15 نقطة/)).toBeInTheDocument()
    expect(screen.getByLabelText(/سابك - انخفاض 8 نقطة/)).toBeInTheDocument()
  })

  it('trend items are focusable when onClick provided', () => {
    renderView({ onTrendClick: jest.fn() })
    const items = screen.getAllByRole('button')
    expect(items.length).toBeGreaterThanOrEqual(3)
  })

  it('non-clickable items do not have role="button"', () => {
    renderView({ onTrendClick: undefined, onMoverClick: undefined })
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  // 7. Interaction
  it('calls onTrendClick when trend is clicked', () => {
    const onTrendClick = jest.fn()
    renderView({ onTrendClick })
    fireEvent.click(screen.getByLabelText(/قطاع التقنية - صاعد/))
    expect(onTrendClick).toHaveBeenCalledWith('قطاع التقنية')
  })

  it('calls onMoverClick when mover is clicked', () => {
    const onMoverClick = jest.fn()
    renderView({ onMoverClick })
    fireEvent.click(screen.getByLabelText(/أرامكو - تحسن 15 نقطة/))
    expect(onMoverClick).toHaveBeenCalledWith('c1')
  })

  it('supports keyboard Enter on trend item', () => {
    const onTrendClick = jest.fn()
    renderView({ onTrendClick })
    fireEvent.keyDown(screen.getByLabelText(/قطاع التقنية - صاعد/), { key: 'Enter' })
    expect(onTrendClick).toHaveBeenCalledWith('قطاع التقنية')
  })

  it('supports keyboard Space on mover item', () => {
    const onMoverClick = jest.fn()
    renderView({ onMoverClick })
    fireEvent.keyDown(screen.getByLabelText(/أرامكو - تحسن 15 نقطة/), { key: ' ' })
    expect(onMoverClick).toHaveBeenCalledWith('c1')
  })

  // 8. Dark Mode
  it('has dark mode variant classes', () => {
    renderView()
    const container = document.querySelector('[class*="dark:"]')
    expect(container).toBeInTheDocument()
  })

  // 9. Reduced Motion
  it('items have motion-reduce class', () => {
    renderView()
    const elements = document.querySelectorAll('[class*="motion-reduce"]')
    expect(elements.length).toBeGreaterThanOrEqual(1)
  })
})

// ─── SDK Integration ──────────────────────────────────────────

describe('MarketPulseWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(MarketPulseWidget).toBeDefined()
    expect(typeof MarketPulseWidget === 'function' || typeof MarketPulseWidget === 'object').toBe(true)
  })
})
