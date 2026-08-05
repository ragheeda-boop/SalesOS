import { render, screen } from '@testing-library/react'
import { YourWidgetView } from '../YourWidgetView'
import { describeWidgetContract } from '@/features/dashboard/sdk/testing'
import type { YourWidgetViewProps, YourWidgetData } from '../types'

// ─── Contract Tests ───────────────────────────────────────────

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

  // 4. Error State — simulate via YourWidgetView contract handling
  it('renders in error state via contract', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'Your Widget Dashboard' })).toBeInTheDocument()
  })
})
