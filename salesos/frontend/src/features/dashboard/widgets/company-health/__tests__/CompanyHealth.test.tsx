import { render, screen, fireEvent } from '@testing-library/react'
import { CompanyHealthView } from '../CompanyHealthView'
import { CompanyHealthWidget } from '../CompanyHealthContainer'
import { describeWidgetContract } from '../../../sdk/testing'
import type { CompanyHealthViewProps, HealthMetric, HealthAlert } from '../types'

const sampleMetrics: HealthMetric[] = [
  { id: 'm1', label: 'معدل الإغلاق', value: 78, unit: '%', trend: 'up', trendValue: 5, color: '#22c55e' },
  { id: 'm2', label: 'متوسط صفقة', value: 450, unit: 'K', trend: 'up', trendValue: 12, color: '#3b82f6' },
  { id: 'm3', label: 'مدة الدورة', value: 32, unit: ' يوم', trend: 'down', trendValue: 8, color: '#f97316' },
  { id: 'm4', label: 'رضا العملاء', value: 92, unit: '%', trend: 'stable', trendValue: 1, color: '#8b5cf6' },
]

const sampleAlerts: HealthAlert[] = [
  { id: 'a1', type: 'critical', message: 'صفقة بقيمة 2M معرضة للخسارة', companyId: 'c1', companyName: 'ACME Corp', timestamp: '2026-07-13T00:00:00Z' },
  { id: 'a2', type: 'warning', message: 'تأخير في التسليم لأكثر من 14 يوم', companyId: 'c2', companyName: 'Beta Ltd', timestamp: '2026-07-12T00:00:00Z' },
]

const defaultProps: CompanyHealthViewProps = {
  overallScore: 76,
  metrics: sampleMetrics,
  alerts: sampleAlerts,
  companyName: 'ACME Corp',
}

function renderView(overrides?: Partial<CompanyHealthViewProps>) {
  return render(<CompanyHealthView {...defaultProps} {...overrides} />)
}

describeWidgetContract({
  name: 'CompanyHealth',
  defaultData: {
    overallScore: 76,
    metrics: sampleMetrics,
    alerts: sampleAlerts,
    companyName: 'ACME Corp',
  },
  config: {
    metadata: {
      id: 'company-health',
      title: 'صحة الشركة',
      minHeight: '300px',
      permissions: ['company:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => (
      <CompanyHealthView
        overallScore={data.overallScore}
        metrics={data.metrics ?? []}
        alerts={data.alerts ?? []}
        companyName={data.companyName}
      />
    ),
  },
})

describe('CompanyHealthView', () => {
  it('renders company name', () => {
    renderView()
    expect(screen.getByText('ACME Corp')).toBeInTheDocument()
  })

  it('renders overall score', () => {
    renderView()
    expect(screen.getByText('76')).toBeInTheDocument()
  })

  it('renders all metrics', () => {
    renderView()
    expect(screen.getByText('معدل الإغلاق')).toBeInTheDocument()
    expect(screen.getByText('متوسط صفقة')).toBeInTheDocument()
    expect(screen.getByText('مدة الدورة')).toBeInTheDocument()
    expect(screen.getByText('رضا العملاء')).toBeInTheDocument()
  })

  it('renders metric values with units', () => {
    renderView()
    expect(screen.getByText('78%')).toBeInTheDocument()
    expect(screen.getByText('450K')).toBeInTheDocument()
  })

  it('renders trend indicators', () => {
    renderView()
    expect(screen.getAllByText('↑').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('↓')).toBeInTheDocument()
    expect(screen.getByText('→')).toBeInTheDocument()
  })

  it('renders trend percentages', () => {
    renderView()
    expect(screen.getByText('5%')).toBeInTheDocument()
    expect(screen.getByText('12%')).toBeInTheDocument()
  })

  it('renders alerts', () => {
    renderView()
    expect(screen.getByText('صفقة بقيمة 2M معرضة للخسارة')).toBeInTheDocument()
    expect(screen.getByText('تأخير في التسليم لأكثر من 14 يوم')).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    renderView({ metrics: [], alerts: [], overallScore: 0 })
    expect(screen.getByText('لا توجد بيانات صحة')).toBeInTheDocument()
  })

  it('has role="region" with aria-label', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'صحة الشركة: ACME Corp' })).toBeInTheDocument()
  })

  it('calls onAlertClick when alert is clicked', () => {
    const onAlertClick = jest.fn()
    renderView({ onAlertClick })
    fireEvent.click(screen.getByLabelText(/حرج/))
    expect(onAlertClick).toHaveBeenCalledWith('a1')
  })

  it('calls onMetricClick when metric is clicked', () => {
    const onMetricClick = jest.fn()
    renderView({ onMetricClick })
    fireEvent.click(screen.getByLabelText(/معدل الإغلاق/))
    expect(onMetricClick).toHaveBeenCalledWith('m1')
  })

  it('supports keyboard Enter on alert', () => {
    const onAlertClick = jest.fn()
    renderView({ onAlertClick })
    fireEvent.keyDown(screen.getByLabelText(/حرج/), { key: 'Enter' })
    expect(onAlertClick).toHaveBeenCalledWith('a1')
  })

  it('shows skeleton when loading', () => {
    renderView({ isDecisionLoading: true, metrics: [], alerts: [] })
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('has motion-reduce classes', () => {
    renderView()
    const elements = document.querySelectorAll('[class*="motion-reduce"]')
    expect(elements.length).toBeGreaterThanOrEqual(1)
  })
})

describe('CompanyHealthWidget (SDK integration)', () => {
  it('is a valid React component', () => {
    expect(CompanyHealthWidget).toBeDefined()
    expect(typeof CompanyHealthWidget === 'function' || typeof CompanyHealthWidget === 'object').toBe(true)
  })
})
