import { render, screen } from '@testing-library/react'
import { EmployeeIntelligenceLayout } from '../EmployeeIntelligenceLayout'

jest.mock('@/lib/hooks/employeeQueries', () => ({
  useMy360: jest.fn(),
}))

import { useMy360 } from '@/lib/hooks/employeeQueries'
import type { Employee360Response } from '@/lib/api'

const mockData: Employee360Response = {
  profile: {
    id: 'emp-1', full_name: 'Ragheed A.', full_name_ar: null, email: 'r@ex.com', role: 'Sales Director',
    phone: null, avatar_url: null, is_active: true, tenant_id: 't1', created_at: '2026-01-01T00:00:00Z',
    team: [], manager: null,
  },
  portfolio: { companies: [], contacts: [], pipeline: [], revenue: 100000, contracts: [], projects: [] },
  calendar_intelligence: { today_count: 2, week_count: 5, month_count: 12, total_hours: 8, avg_duration_minutes: 30, unique_companies_met: 3, upcoming: [] },
  email_intelligence: { sent: 10, received: 20, replies: 5, avg_response_hours: 1, top_contacts: [], top_companies: [] },
  activity_intelligence: { meetings: 3, emails: 10, calls: 5, tasks: 2, notes: 1, documents: 0, total: 21, recent: [] },
  kpis: { revenue: 100000, pipeline: 500000, win_rate: 0.5, response_rate: 0.8, follow_up_rate: 0.6, activities: 21, productivity: 0.7, forecast: 200000 },
  ai_coach: [],
}

describe('EmployeeIntelligenceLayout', () => {
  it('renders loading skeleton', () => {
    ;(useMy360 as jest.Mock).mockReturnValue({
      data: undefined, isLoading: true, isError: false, error: null, refetch: jest.fn(),
    })
    const { container } = render(<EmployeeIntelligenceLayout><div>content</div></EmployeeIntelligenceLayout>)
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders error state', () => {
    ;(useMy360 as jest.Mock).mockReturnValue({
      data: undefined, isLoading: false, isError: true, error: new Error('Network error'), refetch: jest.fn(),
    })
    render(<EmployeeIntelligenceLayout><div>content</div></EmployeeIntelligenceLayout>)
    expect(screen.getByText('تعذر تحميل بيانات الموظف')).toBeInTheDocument()
  })

  it('renders profile header and stats when data loaded', () => {
    ;(useMy360 as jest.Mock).mockReturnValue({
      data: mockData, isLoading: false, isError: false, error: null, refetch: jest.fn(),
    })
    render(<EmployeeIntelligenceLayout><div>widget content</div></EmployeeIntelligenceLayout>)
    expect(screen.getByText('Ragheed A.')).toBeInTheDocument()
    expect(screen.getByText('Sales Director')).toBeInTheDocument()
    expect(screen.getByText(/100[,.]?000/)).toBeInTheDocument()
  })

  it('renders children content', () => {
    ;(useMy360 as jest.Mock).mockReturnValue({
      data: mockData, isLoading: false, isError: false, error: null, refetch: jest.fn(),
    })
    render(<EmployeeIntelligenceLayout><div>child content</div></EmployeeIntelligenceLayout>)
    expect(screen.getByText('child content')).toBeInTheDocument()
  })
})
