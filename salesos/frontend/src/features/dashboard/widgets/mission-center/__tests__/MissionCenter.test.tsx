import { render, screen, fireEvent, within } from '@testing-library/react'
import { MissionCenterView } from '../MissionCenterView'
import { MissionCenterWidget } from '../MissionCenterContainer'
import { MissionMetric } from '../MissionMetric'
import { MissionAction } from '../MissionAction'
import { MissionProgress } from '../MissionProgress'
import { describeWidgetContract } from '../../../sdk/testing'
import type { MissionCenterViewProps } from '../types'
import type { MissionCenterData } from '../../../../../application/dashboard/dashboard.dto'

const sampleData: MissionCenterData = {
  companiesTracked: 42,
  activeDeals: 8,
  pipelineValue: 12_500_000,
  signalsToday: 15,
  decisionsPending: 3,
}

describeWidgetContract({
  name: 'MissionCenter',
  defaultData: sampleData,
  config: {
    metadata: {
      id: 'mission-center',
      title: 'مركز المهمة',
      minHeight: '200px',
      permissions: ['executive:read'],
      featureFlag: { enabled: true, tier: 'enabled' },
    },
    render: ({ data }) => (
      <MissionCenterView
        companiesTracked={data.companiesTracked ?? 0}
        activeDeals={data.activeDeals ?? 0}
        pipelineValue={data.pipelineValue ?? 0}
        signalsToday={data.signalsToday ?? 0}
        decisionsPending={data.decisionsPending ?? 0}
      />
    ),
  },
})

const defaultProps: MissionCenterViewProps = {
  companiesTracked: 42,
  activeDeals: 8,
  pipelineValue: 12_500_000,
  signalsToday: 15,
  decisionsPending: 3,
}

function renderView(overrides?: Partial<MissionCenterViewProps>) {
  return render(<MissionCenterView {...defaultProps} {...overrides} />)
}

describe('MissionCenterView', () => {
  describe('1. Rendering — Today\'s Mission', () => {
    it('renders all 5 metrics', () => {
      renderView()
      const grid = screen.getByRole('list', { name: 'Key metrics' })
      expect(grid.children).toHaveLength(5)
    })

    it('renders companies tracked', () => {
      renderView()
      expect(screen.getByText('42')).toBeInTheDocument()
      expect(screen.getByText('شركات تحت المراقبة')).toBeInTheDocument()
    })

    it('renders active deals', () => {
      renderView()
      expect(screen.getByText('8')).toBeInTheDocument()
      expect(screen.getByText('صفقات نشطة')).toBeInTheDocument()
    })

    it('renders pipeline value formatted', () => {
      renderView()
      expect(screen.getByText('12.5M')).toBeInTheDocument()
      expect(screen.getByText('قيمة الأنابيب')).toBeInTheDocument()
    })

    it('renders signals today with emoji', () => {
      renderView()
      expect(screen.getByText('15')).toBeInTheDocument()
      expect(screen.getByText('إشارات اليوم')).toBeInTheDocument()
    })

    it('renders pending decisions with emoji', () => {
      renderView()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('قرارات معلقة')).toBeInTheDocument()
    })
  })

  describe('2. Priority Actions', () => {
    it('derives high-priority actions from signals', () => {
      renderView()
      expect(screen.getByText('مراجعة 15 إشارة شرائية')).toBeInTheDocument()
    })

    it('derives high-priority actions from pending decisions', () => {
      renderView()
      expect(screen.getByText('3 قرارات معلقة تحتاج اتخاذ')).toBeInTheDocument()
    })

    it('derives medium-priority action from active deals', () => {
      renderView()
      expect(screen.getByText('متابعة 8 صفقة نشطة')).toBeInTheDocument()
    })

    it('derives low-priority action when companies > 10', () => {
      renderView()
      expect(screen.getByText('مراجعة 42 شركة تحت المراقبة')).toBeInTheDocument()
    })

    it('does not show new-companies action when companies <= 10', () => {
      renderView({ companiesTracked: 5 })
      expect(screen.queryByText(/مراجعة.*شركة تحت المراقبة/)).not.toBeInTheDocument()
    })

    it('caps actions at 5 items', () => {
      renderView({
        signalsToday: 5,
        decisionsPending: 5,
        activeDeals: 5,
        companiesTracked: 100,
      })
      const actions = screen.getByRole('list', { name: 'Priority actions' })
      expect(actions.children.length).toBeLessThanOrEqual(5)
    })

    it('hides priority actions section when all counts zero', () => {
      renderView({ signalsToday: 0, decisionsPending: 0, activeDeals: 0, companiesTracked: 5 })
      expect(screen.queryByRole('list', { name: 'Priority actions' })).not.toBeInTheDocument()
    })
  })

  describe('3. Revenue Opportunity', () => {
    it('renders pipeline value formatted with SAR', () => {
      renderView()
      expect(screen.getByText(/SAR/)).toBeInTheDocument()
    })

    it('renders active deal count in revenue card', () => {
      renderView()
      expect(screen.getByText('8 صفقات نشطة')).toBeInTheDocument()
    })
  })

  describe('4. Completion Progress', () => {
    it('renders progress bar', () => {
      renderView()
      const progress = screen.getByRole('progressbar')
      expect(progress).toBeInTheDocument()
    })

    it('has correct aria-valuemin', () => {
      renderView()
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuemin', '0')
    })

    it('has correct aria-valuemax', () => {
      renderView()
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuemax', '100')
    })
  })

  describe('5. Empty State', () => {
    function allZero() {
      return renderView({
        companiesTracked: 0,
        activeDeals: 0,
        pipelineValue: 0,
        signalsToday: 0,
        decisionsPending: 0,
      })
    }

    it('renders empty state when all values zero', () => {
      allZero()
      expect(screen.getByText('لا توجد بيانات بعد')).toBeInTheDocument()
    })

    it('hints to add companies', () => {
      allZero()
      expect(screen.getByText('قم بإضافة شركات لبدء التتبع')).toBeInTheDocument()
    })

    it('does not render metrics grid in empty state', () => {
      allZero()
      expect(screen.queryByRole('list', { name: 'Key metrics' })).not.toBeInTheDocument()
    })

    it('does not render progress bar in empty state', () => {
      allZero()
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })
  })

  describe('6. Summary Banner', () => {
    it('announces active metrics via aria-live region', () => {
      renderView()
      const live = document.querySelector('[aria-live="polite"]')
      expect(live).toBeInTheDocument()
      expect(live).toHaveAttribute('aria-atomic', 'true')
    })

    it('shows zero text when no active metrics', () => {
      renderView({
        companiesTracked: 0,
        activeDeals: 0,
        pipelineValue: 0,
        signalsToday: 0,
        decisionsPending: 0,
      })
      expect(screen.getByText('لا توجد مؤشرات نشطة حالياً')).toBeInTheDocument()
    })
  })

  describe('7. Accessibility — Metrics', () => {
    it('each MissionMetric has aria-label', () => {
      renderView()
      expect(screen.getByLabelText('42 شركات تحت المراقبة')).toBeInTheDocument()
      expect(screen.getByLabelText('8 صفقات نشطة')).toBeInTheDocument()
      expect(screen.getByLabelText('قيمة الأنابيب 12,500,000 ريال')).toBeInTheDocument()
      expect(screen.getByLabelText('15 إشارة جديدة اليوم')).toBeInTheDocument()
      expect(screen.getByLabelText('3 قرارات معلقة')).toBeInTheDocument()
    })

    it('metrics grid has role="list"', () => {
      renderView()
      expect(screen.getByRole('list', { name: 'Key metrics' })).toBeInTheDocument()
    })

    it('each metric has role="listitem"', () => {
      renderView()
      const items = screen.getAllByRole('listitem')
      expect(items.length).toBeGreaterThanOrEqual(5)
    })
  })

  describe('8. Accessibility — Actions', () => {
    it('each MissionAction has descriptive aria-label', () => {
      renderView()
      expect(screen.getByLabelText(/مراجعة 15 إشارة شرائية/)).toBeInTheDocument()
    })

    it('actions without handler have no role="button"', () => {
      renderView()
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })

    it('actions have focus-visible ring class', () => {
      renderView()
      const action = screen.getByLabelText(/مراجعة 15 إشارة شرائية/)
      expect(action.className).toContain('focus-visible:ring-2')
    })
  })

  describe('9. Accessibility — Progress', () => {
    it('progressbar has aria-valuetext', () => {
      renderView()
      const progress = screen.getByRole('progressbar')
      expect(progress).toHaveAttribute('aria-valuetext')
    })

    it('progressbar has descriptive aria-label', () => {
      renderView()
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-label', 'Completion')
    })
  })

  describe('10. Accessibility — Role validation', () => {
    it('dashboard region has correct aria-label', () => {
      renderView()
      expect(screen.getByRole('region', { name: 'Mission Center Dashboard' })).toBeInTheDocument()
    })
  })

  describe('11. Interaction', () => {
    it('action onKeyDown Enter triggers handler', () => {
      const onAction = jest.fn()
      render(
        <MissionAction
          id="test-action"
          title="Test Action"
          priority="high"
          onAction={onAction}
        />
      )
      const button = screen.getByRole('button')
      fireEvent.keyDown(button, { key: 'Enter' })
      expect(onAction).toHaveBeenCalledWith('test-action')
    })

    it('action onKeyDown Space triggers handler', () => {
      const onAction = jest.fn()
      render(
        <MissionAction
          id="test-action"
          title="Test Action"
          priority="high"
          onAction={onAction}
        />
      )
      const button = screen.getByRole('button')
      fireEvent.keyDown(button, { key: ' ' })
      expect(onAction).toHaveBeenCalledWith('test-action')
    })
  })

  describe('12. Dark Mode', () => {
    it('metrics use CSS variables for backgrounds', () => {
      renderView()
      const metric = screen.getByLabelText('42 شركات تحت المراقبة')
      expect(metric.className).toContain('bg-[var(--bg-secondary)]')
    })

    it('contains dark mode Tailwind variant classes', () => {
      renderView()
      const container = document.querySelector('[class*="dark:"]')
      expect(container).toBeInTheDocument()
    })

    it('pipeline value has dark mode class', () => {
      renderView()
      const pipelineValue = screen.getByText('12.5M')
      expect(pipelineValue.className).toContain('dark:text-success-400')
    })
  })

  describe('13. Reduced Motion', () => {
    it('progress bar has motion-reduce class', () => {
      renderView()
      const innerBar = document.querySelector('.motion-reduce\\:transition-none')
      expect(innerBar).toBeInTheDocument()
    })

    it('action items have motion-reduce class', () => {
      renderView()
      const elements = document.querySelectorAll('[class*="motion-reduce"]')
      expect(elements.length).toBeGreaterThanOrEqual(1)
    })
  })
})

describe('MissionMetric', () => {
  it('renders with valueClassName instead of color', () => {
    render(<MissionMetric label="Test" value={100} valueClassName="text-info-600" />)
    const value = screen.getByText('100')
    expect(value.className).toContain('text-info-600')
  })

  it('defaults to orange when no valueClassName', () => {
    render(<MissionMetric label="Test" value={100} />)
    const value = screen.getByText('100')
    expect(value.className).toContain('text-[var(--muhide-orange)]')
  })

  it('renders trend indicator', () => {
    render(<MissionMetric label="Test" value={100} trend={{ direction: 'up', value: 12 }} />)
    expect(screen.getByText('12%')).toBeInTheDocument()
  })

  it('trend has semantic color class for up direction', () => {
    const { container } = render(
      <MissionMetric label="Test" value={100} trend={{ direction: 'up', value: 12 }} />
    )
    const trend = container.querySelector('.text-success-600')
    expect(trend).toBeInTheDocument()
  })
})

describe('MissionAction', () => {
  it('renders priority badge', () => {
    render(<MissionAction id="a" title="Test" priority="high" />)
    expect(screen.getByText('عاجل')).toBeInTheDocument()
  })

  it('renders company name when provided', () => {
    render(<MissionAction id="a" title="Test" priority="medium" companyName="ACME" />)
    expect(screen.getByText('ACME')).toBeInTheDocument()
  })

  it('has no button role when no onAction', () => {
    const { container } = render(<MissionAction id="a" title="Test" priority="low" />)
    expect(container.querySelector('[role="button"]')).not.toBeInTheDocument()
  })

  it('calls onAction on click', () => {
    const onAction = jest.fn()
    render(<MissionAction id="a" title="Test" priority="high" onAction={onAction} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onAction).toHaveBeenCalledWith('a')
  })
})

describe('MissionProgress', () => {
  it('clamps percentage to 100', () => {
    render(<MissionProgress value={200} max={100} label="Test" />)
    const inner = screen.getByRole('progressbar').querySelector('[style*="width"]')
    expect(inner).toHaveStyle('width: 100%')
  })

  it('handles zero max without division errors', () => {
    render(<MissionProgress value={0} max={0} label="Test" />)
    const inner = screen.getByRole('progressbar').querySelector('[style*="width"]')
    expect(inner).toHaveStyle('width: 0%')
  })

  it('displays percentage label', () => {
    render(<MissionProgress value={25} max={100} label="Test" />)
    expect(screen.getByText('25%')).toBeInTheDocument()
  })
})

describe('MissionCenterWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(MissionCenterWidget).toBeDefined()
    expect(typeof MissionCenterWidget === 'function' || typeof MissionCenterWidget === 'object').toBe(true)
  })
})
