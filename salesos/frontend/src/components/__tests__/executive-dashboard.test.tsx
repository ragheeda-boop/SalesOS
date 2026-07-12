import { render, screen } from '@testing-library/react'

jest.mock('@/lib/hooks/executiveQueries', () => ({
  useExecutiveDashboard: jest.fn(),
}))

import { useExecutiveDashboard } from '@/lib/hooks/executiveQueries'
import { ExecutiveDashboard } from '../executive-dashboard'

const mockUseExecutiveDashboard = useExecutiveDashboard as jest.Mock

function makeDashData(overrides: Record<string, unknown> = {}) {
  return {
    revenue: { total_booked: 1500000, forecast: 2000000, total_pipeline: 3500000, weighted_pipeline: 1800000 },
    team: { active_employees: 12, total_employees: 15, avg_win_rate: 0.35 },
    risk: { expiring_contracts: 3, stalled_deals: 2 },
    pipeline: {
      total_deals: 20, won_deals: 7, lost_deals: 3, win_rate: 0.35, total_value: 3500000, avg_deal_size: 175000,
      by_stage: [
        { stage: 'استكشاف', val: 1000000 },
        { stage: 'تأهيل', val: 800000 },
      ],
    },
    growth: { new_companies_30d: 8, new_contacts_30d: 25, new_opportunities_30d: 12, new_contracts_30d: 5 },
    renewals: { due_next_30_days: 4, due_next_90_days: 11 },
    health: { overall_health: 'good' as const, sync_status: 'synced' as const, data_completeness: 0.87 },
    ...overrides,
  }
}

describe('ExecutiveDashboard', () => {
  beforeEach(() => jest.clearAllMocks())

  it('shows loading skeletons', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: undefined, isLoading: true })
    const { container } = render(<ExecutiveDashboard />)
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('shows error when data is null', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: null, isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('فشل تحميل البيانات')).toBeInTheDocument()
  })

  it('renders header title', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('لوحة القيادة التنفيذية')).toBeInTheDocument()
  })

  it('renders health badge as good', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('صحي')).toBeInTheDocument()
  })

  it('renders health badge as warning', () => {
    mockUseExecutiveDashboard.mockReturnValue({
      data: makeDashData({ health: { overall_health: 'warning', sync_status: 'synced', data_completeness: 0.7 } }),
      isLoading: false,
    })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('تحذير')).toBeInTheDocument()
  })

  it('renders health badge as critical', () => {
    mockUseExecutiveDashboard.mockReturnValue({
      data: makeDashData({ health: { overall_health: 'critical', sync_status: 'synced', data_completeness: 0.5 } }),
      isLoading: false,
    })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('حرج')).toBeInTheDocument()
  })

  it('renders KPI cards with formatted revenue', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('الإيرادات المسجلة')).toBeInTheDocument()
    expect(screen.getByText(/١٬٥٠٠٬٠٠٠/)).toBeInTheDocument()
  })

  it('renders team stats', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('الموظفين النشطين')).toBeInTheDocument()
    expect(screen.getByText('12 / 15')).toBeInTheDocument()
  })

  it('renders risk card', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('مخاطر')).toBeInTheDocument()
    expect(screen.getAllByText('5').length).toBeGreaterThanOrEqual(1)
  })

  it('renders pipeline stats', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('صحة الصفقات')).toBeInTheDocument()
    expect(screen.getByText('20')).toBeInTheDocument()
  })

  it('renders pipeline stages', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('حسب المرحلة')).toBeInTheDocument()
    expect(screen.getByText('استكشاف')).toBeInTheDocument()
    expect(screen.getByText('تأهيل')).toBeInTheDocument()
  })

  it('renders average deal size', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('متوسط حجم الصفقة')).toBeInTheDocument()
    expect(screen.getByText(/١٧٥٬٠٠٠/)).toBeInTheDocument()
  })

  it('renders growth section', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('النمو (آخر 30 يوم)')).toBeInTheDocument()
    expect(screen.getByText('شركات جديدة')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('renders renewals section', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('تجديد العقود')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('11')).toBeInTheDocument()
  })

  it('renders sync status as synced', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('متزامن')).toBeInTheDocument()
  })

  it('renders sync status as not synced', () => {
    mockUseExecutiveDashboard.mockReturnValue({
      data: makeDashData({ health: { overall_health: 'good', sync_status: 'not_synced', data_completeness: 0.9 } }),
      isLoading: false,
    })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('غير متزامن')).toBeInTheDocument()
  })

  it('renders data completeness percentage', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('87%')).toBeInTheDocument()
  })

  it('renders win rate percentage', () => {
    mockUseExecutiveDashboard.mockReturnValue({ data: makeDashData(), isLoading: false })
    render(<ExecutiveDashboard />)
    expect(screen.getByText('نسبة الفوز')).toBeInTheDocument()
    expect(screen.getByText('35%')).toBeInTheDocument()
  })

  it('hides stages when by_stage is empty', () => {
    mockUseExecutiveDashboard.mockReturnValue({
      data: makeDashData({ pipeline: { total_deals: 20, won_deals: 7, lost_deals: 3, win_rate: 0.35, total_value: 3500000, avg_deal_size: 175000, by_stage: [] } }),
      isLoading: false,
    })
    render(<ExecutiveDashboard />)
    expect(screen.queryByText('حسب المرحلة')).not.toBeInTheDocument()
  })
})
