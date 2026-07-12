import { render, screen } from '@testing-library/react'

jest.mock('@/lib/hooks/employeeQueries', () => ({
  useEmployee360: jest.fn(),
}))

jest.mock('../timeline-widget', () => ({
  TimelineWidget: (props: Record<string, unknown>) => (
    <div data-testid="timeline-widget">TimelineWidget: {String(props.entityType)}</div>
  ),
}))

import { useEmployee360 } from '@/lib/hooks/employeeQueries'
import { Employee360View } from '../employee-360-view'

const mockUseEmployee360 = useEmployee360 as jest.Mock

function makeEmployee360(overrides: Record<string, unknown> = {}) {
  return {
    profile: {
      full_name: 'أحمد محمد العلي',
      full_name_ar: 'أحمد محمد العلي',
      email: 'ahmed@company.com',
      role: 'مدير مبيعات',
      is_active: true,
      avatar_url: '',
      team: [
        { full_name: 'سارة خالد' },
        { full_name: 'محمد أحمد' },
      ],
    },
    kpis: { revenue: 1500000, pipeline: 3500000, win_rate: 0.35, productivity: 0.82 },
    activity_intelligence: { meetings: 15, emails: 42, calls: 28, tasks: 20, notes: 10, documents: 5, total: 120 },
    portfolio: {
      pipeline: [
        { name: 'صفقة 1', company_name: 'أرامكو', value: 500000, status: 'open' },
        { name: 'صفقة 2', company_name: 'سابك', value: 300000, status: 'won' },
      ],
      revenue: 800000,
    },
    ai_coach: [
      { title: 'متابعة العميل', description: 'يجب متابعة أرامكو بخصوص العرض المقدم', priority: 'high' },
      { title: 'تحسين وقت الاستجابة', description: 'متوسط وقت الاستجابة مرتفع', priority: 'medium' },
    ],
    calendar_intelligence: { today_count: 3, week_count: 12, month_count: 45, total_hours: 22.5 },
    ...overrides,
  }
}

describe('Employee360View', () => {
  beforeEach(() => jest.clearAllMocks())

  it('shows loading state', () => {
    mockUseEmployee360.mockReturnValue({ data: undefined, isLoading: true })
    const { container } = render(<Employee360View employeeId="emp-1" />)
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('shows error when data is null', () => {
    mockUseEmployee360.mockReturnValue({ data: null, isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('فشل تحميل البيانات')).toBeInTheDocument()
  })

  it('renders employee name', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('أحمد محمد العلي')).toBeInTheDocument()
  })

  it('renders employee role and email', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText(/مدير مبيعات/)).toBeInTheDocument()
    expect(screen.getByText(/ahmed@company\.com/)).toBeInTheDocument()
  })

  it('shows active badge', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('نشط')).toBeInTheDocument()
  })

  it('shows inactive badge', () => {
    mockUseEmployee360.mockReturnValue({
      data: makeEmployee360({ profile: { ...makeEmployee360().profile, is_active: false } }),
      isLoading: false,
    })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('غير نشط')).toBeInTheDocument()
  })

  it('renders team members', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('سارة خالد')).toBeInTheDocument()
    expect(screen.getByText('محمد أحمد')).toBeInTheDocument()
  })

  it('renders KPI cards', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('الإيرادات')).toBeInTheDocument()
    expect(screen.getByText('قيمة الصفقات')).toBeInTheDocument()
    expect(screen.getByText('نسبة الفوز')).toBeInTheDocument()
    expect(screen.getByText('الإنتاجية')).toBeInTheDocument()
  })

  it('renders activity intelligence', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('نشاطات')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders portfolio pipeline', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('الصفقات')).toBeInTheDocument()
    expect(screen.getByText('صفقة 1')).toBeInTheDocument()
    expect(screen.getByText('صفقة 2')).toBeInTheDocument()
  })

  it('renders AI coach', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('مدرب AI')).toBeInTheDocument()
    expect(screen.getByText('متابعة العميل')).toBeInTheDocument()
    expect(screen.getByText('تحسين وقت الاستجابة')).toBeInTheDocument()
  })

  it('renders calendar intelligence', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('التقويم')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('does not render calendar when today_count is 0', () => {
    mockUseEmployee360.mockReturnValue({
      data: makeEmployee360({ calendar_intelligence: { today_count: 0, week_count: 0, month_count: 0, total_hours: 0 } }),
      isLoading: false,
    })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.queryByText('التقويم')).not.toBeInTheDocument()
  })

  it('shows empty pipeline message', () => {
    mockUseEmployee360.mockReturnValue({
      data: makeEmployee360({ portfolio: { pipeline: [], revenue: 0 } }),
      isLoading: false,
    })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('لا توجد صفقات')).toBeInTheDocument()
  })

  it('shows all-good coach message', () => {
    mockUseEmployee360.mockReturnValue({
      data: makeEmployee360({ ai_coach: [] }),
      isLoading: false,
    })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('كل شيء على ما يرام')).toBeInTheDocument()
  })

  it('renders initials when no avatar', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('أم')).toBeInTheDocument()
  })

  it('renders avatar image when url provided', () => {
    mockUseEmployee360.mockReturnValue({
      data: makeEmployee360({ profile: { ...makeEmployee360().profile, avatar_url: 'https://example.com/photo.jpg' } }),
      isLoading: false,
    })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByAltText('')).toHaveAttribute('src', 'https://example.com/photo.jpg')
  })

  it('passes correct props to TimelineWidget', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByTestId('timeline-widget')).toHaveTextContent('user')
  })

  it('renders total activity count', () => {
    mockUseEmployee360.mockReturnValue({ data: makeEmployee360(), isLoading: false })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('إجمالي 120 نشاط')).toBeInTheDocument()
  })

  it('does not show total when 0', () => {
    mockUseEmployee360.mockReturnValue({
      data: makeEmployee360({ activity_intelligence: { meetings: 0, emails: 0, calls: 0, tasks: 0, notes: 0, documents: 0, total: 0 } }),
      isLoading: false,
    })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.queryByText(/إجمالي 0 نشاط/)).not.toBeInTheDocument()
  })

  it('uses full_name when full_name_ar is not provided', () => {
    mockUseEmployee360.mockReturnValue({
      data: makeEmployee360({ profile: { ...makeEmployee360().profile, full_name_ar: '' } }),
      isLoading: false,
    })
    render(<Employee360View employeeId="emp-1" />)
    expect(screen.getByText('أحمد محمد العلي')).toBeInTheDocument()
  })
})
