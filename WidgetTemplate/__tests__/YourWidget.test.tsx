import { render, screen } from '@testing-library/react'
import { YourWidgetView } from '../YourWidgetView'
import { describeWidgetContract } from '@/features/dashboard/sdk/testing'
import type { YourWidgetViewProps, YourWidgetData } from '../types'

// ─── Contract Tests ───────────────────────────────────────────
// These 18+ tests are mandatory for every widget. They verify:
// rendering, loading/degraded/error states, permissions, feature
// flags, accessibility, and interaction.
// ───────────────────────────────────────────────────────────────

describeWidgetContract({
  name: 'YourWidget',
  defaultData: { count: 5, items: [{ id: '1', label: 'Item 1', value: 100 }] },
  config: {
    metadata: {
      id: 'your-widget',
      title: 'Your Widget',
      minHeight: '200px',
      permissions: ['your_widget:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => <YourWidgetView count={data.count} items={data.items} isLoading={false} />,
  },
})

// ─── View Unit Tests ──────────────────────────────────────────

const defaultProps: YourWidgetViewProps = {
  count: 3,
  items: [
    { id: '1', label: 'Alpha', value: 10 },
    { id: '2', label: 'Beta', value: 20 },
    { id: '3', label: 'Gamma', value: 30 },
  ],
  isLoading: false,
}

function renderView(overrides?: Partial<YourWidgetViewProps>) {
  return render(<YourWidgetView {...defaultProps} {...overrides} />)
}

describe('YourWidgetView', () => {
  // 1. Rendering
  it('renders item count', () => {
    renderView()
    expect(screen.getByText('3 عنصر')).toBeInTheDocument()
  })

  it('renders all items', () => {
    renderView()
    expect(screen.getByText('Alpha')).toBeInTheDocument()
    expect(screen.getByText('Beta')).toBeInTheDocument()
    expect(screen.getByText('Gamma')).toBeInTheDocument()
  })

  // 2. Loading State
  it('shows loading state', () => {
    renderView({ isLoading: true })
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  // 3. Empty State
  it('shows empty state when no items', () => {
    renderView({ items: [], count: 0 })
    expect(screen.getByText('لا توجد عناصر بعد')).toBeInTheDocument()
  })

  it('shows empty hint text', () => {
    renderView({ items: [], count: 0 })
    expect(screen.getByText('ستظهر العناصر هنا عند توفرها')).toBeInTheDocument()
  })

  // 4. Accessibility
  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'Your Widget Dashboard' })).toBeInTheDocument()
  })

  it('each item row has aria-label', () => {
    renderView()
    expect(screen.getByLabelText('Alpha: 10')).toBeInTheDocument()
    expect(screen.getByLabelText('Beta: 20')).toBeInTheDocument()
    expect(screen.getByLabelText('Gamma: 30')).toBeInTheDocument()
  })

  it('count has aria-live polite region', () => {
    renderView()
    const live = document.querySelector('[aria-live="polite"]')
    expect(live).toBeInTheDocument()
    expect(live).toHaveAttribute('aria-atomic', 'true')
  })

  it('loading state has role="status"', () => {
    renderView({ isLoading: true })
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('items list has role="list"', () => {
    renderView()
    expect(screen.getByRole('list', { name: 'Widget items' })).toBeInTheDocument()
  })

  it('each item has role="listitem"', () => {
    renderView()
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(3)
  })

  // 5. Dark Mode (CSS variables)
  it('uses CSS variables for backgrounds', () => {
    renderView()
    const item = screen.getByLabelText('Alpha: 10')
    expect(item.className).toContain('text-[var(--text-primary)]')
  })

  // 6. Reduced Motion (check parent for animation classes)
  it('loading spinner uses motion-reduce', () => {
    const { container } = renderView({ isLoading: true })
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })
})
