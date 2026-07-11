import { render, screen, fireEvent } from '@testing-library/react'
import { IntelligenceFeedView } from '../IntelligenceFeedView'
import { IntelligenceFeedWidget } from '../IntelligenceFeedContainer'
import { describeWidgetContract } from '../../../sdk/testing'
import type { IntelligenceFeedViewProps, SignalItemData } from '../types'

const sampleSignals: SignalItemData[] = [
  {
    id: '1', companyId: 'c1', companyName: 'ACME Corp',
    category: 'tender', title: 'مناقصة جديدة', summary: 'تفاصيل المناقصة',
    severity: 'high', source: 'منصة اعتماد', timestamp: '2026-07-10T08:00:00Z', isUnseen: true,
  },
  {
    id: '2', companyId: 'c2', companyName: 'Beta Ltd',
    category: 'competitor', title: 'إطلاق منتج منافس', summary: 'إطلاق منتج جديد',
    severity: 'critical', source: 'تحليل السوق', timestamp: '2026-07-10T07:00:00Z', isUnseen: true,
  },
  {
    id: '3', companyId: 'c3', companyName: 'Gamma Co',
    category: 'financial', title: 'تقرير مالي ربع سنوي', summary: 'نتائج مالية إيجابية',
    severity: 'medium', source: 'السوق المالية', timestamp: '2026-07-09T10:00:00Z', isUnseen: false,
  },
]

const defaultProps: IntelligenceFeedViewProps = {
  items: sampleSignals,
  total: 3,
  unseenCount: 2,
}

function renderView(overrides?: Partial<IntelligenceFeedViewProps>) {
  return render(<IntelligenceFeedView {...defaultProps} {...overrides} />)
}

// ─── Contract Tests ───────────────────────────────────────────

describeWidgetContract({
  name: 'IntelligenceFeed',
  defaultData: {
    items: sampleSignals,
    total: 3,
    unseenCount: 2,
  },
  config: {
    metadata: {
      id: 'intelligence-feed',
      title: 'Intelligence Feed',
      minHeight: '400px',
      permissions: ['intelligence:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => (
      <IntelligenceFeedView
        items={data.items ?? []}
        total={data.total ?? 0}
        unseenCount={data.unseenCount ?? 0}
      />
    ),
  },
})

// ─── View Unit Tests ──────────────────────────────────────────

describe('IntelligenceFeedView', () => {
  // 1. Rendering
  it('renders unseen count badge', () => {
    renderView()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('إشارة جديدة')).toBeInTheDocument()
  })

  it('renders all signal items', () => {
    renderView()
    expect(screen.getByText('مناقصة جديدة')).toBeInTheDocument()
    expect(screen.getByText('إطلاق منتج منافس')).toBeInTheDocument()
    expect(screen.getByText('تقرير مالي ربع سنوي')).toBeInTheDocument()
  })

  it('renders company names', () => {
    renderView()
    expect(screen.getByText('ACME Corp')).toBeInTheDocument()
    expect(screen.getByText('Beta Ltd')).toBeInTheDocument()
  })

  it('renders severity labels', () => {
    renderView()
    expect(screen.getByText('عالٍ')).toBeInTheDocument()
    expect(screen.getByText('حرج')).toBeInTheDocument()
    expect(screen.getByText('متوسط')).toBeInTheDocument()
  })

  // 2. Show More
  it('shows more button when items exceed MAX_VISIBLE (6)', () => {
    const manySignals = Array.from({ length: 8 }, (_, i) => ({
      id: String(i), companyId: 'c', companyName: 'Co',
      category: 'news' as const, title: `Signal ${i}`, summary: '',
      severity: 'low' as const, source: '', timestamp: '', isUnseen: false,
    }))
    renderView({ items: manySignals, total: 8, unseenCount: 0 })
    expect(screen.getByText('+2 إشارة أخرى')).toBeInTheDocument()
  })

  it('caps visible items at 6', () => {
    const manySignals = Array.from({ length: 8 }, (_, i) => ({
      id: String(i), companyId: 'c', companyName: 'Co',
      category: 'news' as const, title: `Signal ${i}`, summary: '',
      severity: 'low' as const, source: '', timestamp: '', isUnseen: false,
    }))
    renderView({ items: manySignals, total: 8, unseenCount: 0 })
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(6)
  })

  it('does not show more button when items <= 6', () => {
    renderView()
    expect(screen.queryByText(/إشارة أخرى/)).not.toBeInTheDocument()
  })

  // 3. Empty State
  it('shows empty state when no items', () => {
    renderView({ items: [], total: 0, unseenCount: 0 })
    expect(screen.getByText('لا توجد إشارات جديدة')).toBeInTheDocument()
    expect(screen.getByText('ستظهر الإشارات الذكية هنا عند توفرها')).toBeInTheDocument()
  })

  it('does not render list in empty state', () => {
    renderView({ items: [], total: 0, unseenCount: 0 })
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('does not show unseen badge when count is zero', () => {
    renderView({ items: sampleSignals, total: 3, unseenCount: 0 })
    expect(screen.queryByText('إشارة جديدة')).not.toBeInTheDocument()
  })

  // 4. Interaction
  it('calls onItemClick when signal is clicked', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    fireEvent.click(screen.getByLabelText(/مناقصة جديدة/))
    expect(onItemClick).toHaveBeenCalledWith('1')
  })

  it('calls onShowAll when show more clicked', () => {
    const onShowAll = jest.fn()
    const manySignals = Array.from({ length: 8 }, (_, i) => ({
      id: String(i), companyId: 'c', companyName: 'Co',
      category: 'news' as const, title: `Signal ${i}`, summary: '',
      severity: 'low' as const, source: '', timestamp: '', isUnseen: false,
    }))
    renderView({ items: manySignals, total: 8, unseenCount: 0, onShowAll })
    fireEvent.click(screen.getByText('+2 إشارة أخرى'))
    expect(onShowAll).toHaveBeenCalledTimes(1)
  })

  it('supports keyboard Enter on clickable signal', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    const signal = screen.getByLabelText(/مناقصة جديدة/)
    fireEvent.keyDown(signal, { key: 'Enter' })
    expect(onItemClick).toHaveBeenCalledWith('1')
  })

  it('supports keyboard Space on clickable signal', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    const signal = screen.getByLabelText(/مناقصة جديدة/)
    fireEvent.keyDown(signal, { key: ' ' })
    expect(onItemClick).toHaveBeenCalledWith('1')
  })

  // 5. Accessibility
  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'Intelligence Feed' })).toBeInTheDocument()
  })

  it('each signal has descriptive aria-label', () => {
    renderView()
    expect(screen.getByLabelText(/مناقصة جديدة - ACME Corp/)).toBeInTheDocument()
    expect(screen.getByLabelText(/إطلاق منتج منافس - Beta Ltd/)).toBeInTheDocument()
  })

  it('signals list has role="list"', () => {
    renderView()
    expect(screen.getByRole('list', { name: 'Intelligence signals' })).toBeInTheDocument()
  })

  it('each signal has role="listitem"', () => {
    renderView()
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(3)
  })

  it('unseen badge has aria-live polite', () => {
    renderView()
    const live = document.querySelector('[aria-live="polite"]')
    expect(live).toBeInTheDocument()
    expect(live).toHaveAttribute('aria-atomic', 'true')
  })

  it('show more button has aria-label', () => {
    const manySignals = Array.from({ length: 8 }, (_, i) => ({
      id: String(i), companyId: 'c', companyName: 'Co',
      category: 'news' as const, title: `Signal ${i}`, summary: '',
      severity: 'low' as const, source: '', timestamp: '', isUnseen: false,
    }))
    renderView({ items: manySignals, total: 8, unseenCount: 0 })
    expect(screen.getByLabelText('عرض الكل (8 إشارة)')).toBeInTheDocument()
  })

  // 6. Dark Mode
  it('uses CSS variables for backgrounds', () => {
    renderView()
    expect(screen.getByText('مناقصة جديدة').className).toContain('text-[var(--text-primary)]')
  })

  it('has dark mode variant classes', () => {
    renderView()
    const container = document.querySelector('[class*="dark:"]')
    expect(container).toBeInTheDocument()
  })

  // 7. Reduced Motion
  it('signals have motion-reduce class', () => {
    renderView()
    const elements = document.querySelectorAll('[class*="motion-reduce"]')
    expect(elements.length).toBeGreaterThanOrEqual(1)
  })
})

// ─── SDK Integration ──────────────────────────────────────────

describe('IntelligenceFeedWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(IntelligenceFeedWidget).toBeDefined()
    expect(typeof IntelligenceFeedWidget === 'function' || typeof IntelligenceFeedWidget === 'object').toBe(true)
  })
})
