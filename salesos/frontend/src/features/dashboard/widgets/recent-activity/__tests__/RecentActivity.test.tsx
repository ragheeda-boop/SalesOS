import { render, screen, fireEvent } from '@testing-library/react'
import { RecentActivityView } from '../RecentActivityView'
import { RecentActivityWidget } from '../RecentActivityContainer'
import { describeWidgetContract } from '../../../sdk/testing'
import type { RecentActivityViewProps } from '../types'
import type { ActivityItem } from '@/application/dashboard/dashboard.dto'

const sampleItems: ActivityItem[] = [
  { id: 'a1', type: 'signal', title: 'إشارة مناقصة جديدة من أرامكو', companyId: 'c1', companyName: 'أرامكو السعودية', timestamp: '2026-07-10T08:30:00.000Z' },
  { id: 'a2', type: 'decision', title: 'قرار تمديد العقد مع سابك', companyId: 'c2', companyName: 'سابك', timestamp: '2026-07-10T07:15:00.000Z' },
  { id: 'a3', type: 'update', title: 'تحديث بيانات الاتصال للشركة', companyId: 'c3', companyName: 'الراجحي', timestamp: '2026-07-09T16:45:00.000Z' },
  { id: 'a4', type: 'note', title: 'ملاحظة: اجتماع مع فريق المبيعات', companyId: 'c4', companyName: 'STC', timestamp: '2026-07-09T10:00:00.000Z' },
]

const defaultProps: RecentActivityViewProps = {
  items: sampleItems,
  total: sampleItems.length,
}

function renderView(overrides?: Partial<RecentActivityViewProps>) {
  return render(<RecentActivityView {...defaultProps} {...overrides} />)
}

// ─── Contract Tests ───────────────────────────────────────────

describeWidgetContract({
  name: 'RecentActivity',
  defaultData: { items: sampleItems, total: sampleItems.length },
  config: {
    metadata: {
      id: 'recent-activity',
      title: 'نشاطات حديثة',
      minHeight: '320px',
      permissions: ['activity:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => (
      <RecentActivityView items={data.items ?? []} total={data.total ?? 0} />
    ),
  },
})

// ─── View Unit Tests ──────────────────────────────────────────

describe('RecentActivityView', () => {
  // 1. Rendering
  it('renders all activity items', () => {
    renderView()
    expect(screen.getByText('إشارة مناقصة جديدة من أرامكو')).toBeInTheDocument()
    expect(screen.getByText('قرار تمديد العقد مع سابك')).toBeInTheDocument()
    expect(screen.getByText('تحديث بيانات الاتصال للشركة')).toBeInTheDocument()
    expect(screen.getByText('ملاحظة: اجتماع مع فريق المبيعات')).toBeInTheDocument()
  })

  it('renders company names', () => {
    renderView()
    expect(screen.getByText('أرامكو السعودية')).toBeInTheDocument()
    expect(screen.getByText('سابك')).toBeInTheDocument()
    expect(screen.getByText('الراجحي')).toBeInTheDocument()
    expect(screen.getByText('STC')).toBeInTheDocument()
  })

  it('renders type icons', () => {
    renderView()
    const icons = document.querySelectorAll('[aria-hidden="true"]')
    const activityIcons = Array.from(icons).filter((el) => ['📡', '⚡', '🔄', '📝'].includes(el.textContent ?? ''))
    expect(activityIcons.length).toBe(4)
  })

  it('renders type labels', () => {
    renderView()
    expect(screen.getAllByText('إشارة')).toHaveLength(1)
    expect(screen.getByText('قرار')).toBeInTheDocument()
    expect(screen.getByText('تحديث')).toBeInTheDocument()
    expect(screen.getByText('ملاحظة')).toBeInTheDocument()
  })

  it('renders timestamps', () => {
    renderView()
    const timestamps = document.querySelectorAll('[class*="flex items-center gap-2 text-xs"] span:last-child')
    expect(timestamps.length).toBeGreaterThanOrEqual(1)
    expect(timestamps[0].textContent).toContain('·')
  })

  // 2. Capping
  it('caps items at 10', () => {
    const manyItems: ActivityItem[] = Array.from({ length: 15 }, (_, i) => ({
      id: `a${i}`,
      type: 'note' as const,
      title: `نشاط ${i + 1}`,
      timestamp: '2026-07-10T00:00:00.000Z',
    }))
    renderView({ items: manyItems, total: manyItems.length })
    const items = document.querySelectorAll('[role="listitem"]')
    expect(items.length).toBe(10)
  })

  it('shows count when total exceeds 10', () => {
    const manyItems: ActivityItem[] = Array.from({ length: 12 }, (_, i) => ({
      id: `a${i}`,
      type: 'note' as const,
      title: `نشاط ${i + 1}`,
      timestamp: '2026-07-10T00:00:00.000Z',
    }))
    renderView({ items: manyItems, total: manyItems.length })
    expect(screen.getByText(/10 من أصل 12 نشاط/)).toBeInTheDocument()
  })

  it('hides count when total equals displayed count', () => {
    renderView({ items: sampleItems, total: 4 })
    expect(screen.queryByText(/من أصل/)).not.toBeInTheDocument()
  })

  // 3. Empty State
  it('shows empty state when no items', () => {
    renderView({ items: [], total: 0 })
    expect(screen.getByText('لا توجد نشاطات حديثة')).toBeInTheDocument()
    expect(screen.getByText(/سيتم عرض النشاطات/)).toBeInTheDocument()
  })

  // 4. Interaction
  it('calls onItemClick when item clicked', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    fireEvent.click(screen.getByLabelText(/إشارة مناقصة جديدة من أرامكو/))
    expect(onItemClick).toHaveBeenCalledWith('a1')
  })

  it('supports keyboard Enter on clickable item', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    fireEvent.keyDown(screen.getByLabelText(/إشارة مناقصة جديدة من أرامكو/), { key: 'Enter' })
    expect(onItemClick).toHaveBeenCalledWith('a1')
  })

  it('supports keyboard Space on clickable item', () => {
    const onItemClick = jest.fn()
    renderView({ onItemClick })
    fireEvent.keyDown(screen.getByLabelText(/إشارة مناقصة جديدة من أرامكو/), { key: ' ' })
    expect(onItemClick).toHaveBeenCalledWith('a1')
  })

  // 5. Accessibility
  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'النشاطات الحديثة' })).toBeInTheDocument()
  })

  it('has role="list" and role="listitem"', () => {
    renderView()
    expect(screen.getByRole('list')).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(4)
  })

  it('each item has descriptive aria-label', () => {
    renderView({ onItemClick: jest.fn() })
    expect(screen.getByLabelText(/إشارة مناقصة جديدة من أرامكو - أرامكو السعودية - إشارة/)).toBeInTheDocument()
    expect(screen.getByLabelText(/قرار تمديد العقد مع سابك - سابك - قرار/)).toBeInTheDocument()
  })

  it('non-clickable items do not have role="button"', () => {
    renderView({ onItemClick: undefined })
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  // 6. Dark Mode
  it('has dark mode variant classes', () => {
    renderView()
    const container = document.querySelector('[class*="dark:"]')
    expect(container).toBeInTheDocument()
  })

  // 7. Reduced Motion
  it('has motion-reduce class', () => {
    renderView()
    const elements = document.querySelectorAll('[class*="motion-reduce"]')
    expect(elements.length).toBeGreaterThanOrEqual(1)
  })
})

// ─── SDK Integration ──────────────────────────────────────────

describe('RecentActivityWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(RecentActivityWidget).toBeDefined()
    expect(typeof RecentActivityWidget === 'function' || typeof RecentActivityWidget === 'object').toBe(true)
  })
})
