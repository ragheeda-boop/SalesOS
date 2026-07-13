import { render, screen, fireEvent } from '@testing-library/react'
import { DecisionQueueView } from '../DecisionQueueView'
import { DecisionQueueWidget } from '../DecisionQueueContainer'
import { describeWidgetContract } from '../../../sdk/testing'
import type { DecisionQueueViewProps } from '../types'
import type { DecisionItem } from '@/application/dashboard/dashboard.dto'

const sampleItems: DecisionItem[] = [
  { id: 'd1', companyId: 'c1', companyName: 'ACME Corp', type: 'opportunity', title: 'صفقة استراتيجية كبرى', priority: 'high', dueBy: '2026-07-15T00:00:00Z', score: 92 },
  { id: 'd2', companyId: 'c2', companyName: 'Beta Ltd', type: 'risk', title: 'تأخير في التسليم', priority: 'high', dueBy: '2026-07-12T00:00:00Z', score: 78 },
  { id: 'd3', companyId: 'c3', companyName: 'Gamma Co', type: 'recommendation', title: 'اقتراح تجديد العقد', priority: 'medium', score: 65 },
  { id: 'd4', companyId: 'c4', companyName: 'Delta Inc', type: 'opportunity', title: 'فرصة توسع في الرياض', priority: 'low', score: 45 },
]

const defaultProps: DecisionQueueViewProps = {
  items: sampleItems,
  total: sampleItems.length,
  decision: null,
  nbaItems: [],
  isDecisionLoading: false,
}

function renderView(overrides?: Partial<DecisionQueueViewProps>) {
  return render(<DecisionQueueView {...defaultProps} {...overrides} />)
}

// ─── Contract Tests ───────────────────────────────────────────

describeWidgetContract({
  name: 'DecisionQueue',
  defaultData: { items: sampleItems, total: sampleItems.length },
  config: {
    metadata: {
      id: 'decision-queue',
      title: 'قرارات معلقة',
      minHeight: '320px',
      permissions: ['decisions:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => (
      <DecisionQueueView items={data.items ?? []} total={data.total ?? 0} />
    ),
  },
})

// ─── View Unit Tests ──────────────────────────────────────────

describe('DecisionQueueView', () => {
  // 1. Rendering
  it('renders all decision items', () => {
    renderView()
    expect(screen.getByText('صفقة استراتيجية كبرى')).toBeInTheDocument()
    expect(screen.getByText('تأخير في التسليم')).toBeInTheDocument()
    expect(screen.getByText('اقتراح تجديد العقد')).toBeInTheDocument()
    expect(screen.getByText('فرصة توسع في الرياض')).toBeInTheDocument()
  })

  it('renders company names', () => {
    renderView()
    expect(screen.getByText('ACME Corp')).toBeInTheDocument()
    expect(screen.getByText('Beta Ltd')).toBeInTheDocument()
  })

  it('renders priority labels', () => {
    renderView()
    expect(screen.getAllByText('عاجل')).toHaveLength(2)
    expect(screen.getByText('متوسط')).toBeInTheDocument()
    expect(screen.getByText('عادي')).toBeInTheDocument()
  })

  it('renders type labels', () => {
    renderView()
    expect(screen.getAllByText('فرصة')).toHaveLength(2)
    expect(screen.getByText('مخاطرة')).toBeInTheDocument()
    expect(screen.getByText('توصية')).toBeInTheDocument()
  })

  it('renders AI scores', () => {
    renderView()
    const aiScore = (n: number) => screen.getByText((c) => c.includes(`AI ${n}%`))
    expect(aiScore(92)).toBeInTheDocument()
    expect(aiScore(78)).toBeInTheDocument()
    expect(aiScore(65)).toBeInTheDocument()
    expect(aiScore(45)).toBeInTheDocument()
  })

  // 2. Priority Ordering
  it('sorts items by priority (high first, then medium, then low)', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    const items = screen.getAllByRole('button')
    expect(items[0]).toHaveTextContent('صفقة استراتيجية كبرى')
    expect(items[1]).toHaveTextContent('تأخير في التسليم')
  })

  // 3. Empty State
  it('shows empty state when no items', () => {
    renderView({ items: [], total: 0 })
    expect(screen.getByText('لا توجد قرارات معلقة')).toBeInTheDocument()
    expect(screen.getByText(/سيتم عرض القرارات/)).toBeInTheDocument()
  })

  // 4. Total Counter
  it('shows item count when total exceeds displayed items', () => {
    renderView({ items: sampleItems, total: 10 })
    expect(screen.getByText(/4 من أصل 10 قرار/)).toBeInTheDocument()
  })

  it('hides count when total equals displayed items', () => {
    renderView({ items: sampleItems, total: 4 })
    expect(screen.queryByText(/من أصل/)).not.toBeInTheDocument()
  })

  // 5. Interaction
  it('calls onItemClick when decision is clicked', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    fireEvent.click(screen.getByLabelText(/صفقة استراتيجية كبرى/))
    expect(onItemClick).toHaveBeenCalledWith('d1')
  })

  it('supports keyboard Enter on clickable item', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    fireEvent.keyDown(screen.getByLabelText(/صفقة استراتيجية كبرى/), { key: 'Enter' })
    expect(onItemClick).toHaveBeenCalledWith('d1')
  })

  it('supports keyboard Space on clickable item', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    fireEvent.keyDown(screen.getByLabelText(/صفقة استراتيجية كبرى/), { key: ' ' })
    expect(onItemClick).toHaveBeenCalledWith('d1')
  })

  // 6. Accessibility
  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'قرارات معلقة' })).toBeInTheDocument()
  })

  it('each item has descriptive aria-label', () => {
    renderView()
    expect(screen.getByLabelText(/صفقة استراتيجية كبرى - ACME Corp - عاجل/)).toBeInTheDocument()
    expect(screen.getByLabelText(/تأخير في التسليم - Beta Ltd - عاجل/)).toBeInTheDocument()
  })

  it('non-clickable items do not have role="button"', () => {
    renderView({ onItemClick: undefined })
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  // 7. Dark Mode
  it('has dark mode variant classes', () => {
    renderView()
    const container = document.querySelector('[class*="dark:"]')
    expect(container).toBeInTheDocument()
  })

  // 8. Reduced Motion
  it('items have motion-reduce class', () => {
    renderView()
    const elements = document.querySelectorAll('[class*="motion-reduce"]')
    expect(elements.length).toBeGreaterThanOrEqual(1)
  })
})

// ─── SDK Integration ──────────────────────────────────────────

describe('DecisionQueueWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(DecisionQueueWidget).toBeDefined()
    expect(typeof DecisionQueueWidget === 'function' || typeof DecisionQueueWidget === 'object').toBe(true)
  })
})

// ─── DecisionProvider Integration ─────────────────────────────

describe('DecisionQueueView — DecisionProvider', () => {
  it('shows skeleton when isDecisionLoading with empty items', () => {
    renderView({ isDecisionLoading: true, items: [], total: 0 })
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByLabelText('جاري تحميل القرارات')).toBeInTheDocument()
  })

  it('renders decision summary when decision is provided', () => {
    renderView({
      decision: {
        context_type: 'dashboard',
        factors: [],
        confidence: 0.85,
        summary: 'توصية بتحسين أداء الأنبوب',
        generated_at: '2026-07-13T00:00:00Z',
      },
    })
    expect(screen.getByText(/ملخص القرارات/)).toBeInTheDocument()
    expect(screen.getByText(/توصية بتحسين أداء الأنبوب/)).toBeInTheDocument()
  })

  it('renders NBA items when provided', () => {
    renderView({
      nbaItems: [
        {
          id: 'nba1',
          company_id: 'c1',
          company_name: 'ACME Corp',
          action: 'متابعة الصفقة',
          reason: 'احتمالية عالية',
          confidence: 0.9,
          confidence_label: 'high',
          priority: 1,
          source: 'ai',
          status: 'active',
          created_at: '2026-07-13T00:00:00Z',
        },
      ],
    })
    expect(screen.getByText('توصيات AI')).toBeInTheDocument()
    const acmeCorps = screen.getAllByText('ACME Corp')
    expect(acmeCorps.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/متابعة الصفقة/)).toBeInTheDocument()
  })

  it('announces item count via aria-live', () => {
    renderView()
    const live = document.querySelector('[aria-live="polite"][aria-atomic="true"].sr-only')
    expect(live).toBeInTheDocument()
    expect(live).toHaveTextContent('4 قرار معلق')
  })
})
