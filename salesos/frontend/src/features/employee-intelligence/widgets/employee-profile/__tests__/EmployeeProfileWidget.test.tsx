import { render, screen } from '@testing-library/react'
import { EmployeeProfileView } from '../EmployeeProfileWidget'
import type { EmployeeProfile } from '@/lib/api'

const baseProfile: EmployeeProfile = {
  id: 'emp-1',
  full_name: 'Ragheed Al-Mousawi',
  full_name_ar: 'رشيد الموسوي',
  email: 'ragheed@example.com',
  role: 'Sales Director',
  phone: '+966 55 123 4567',
  avatar_url: null,
  is_active: true,
  tenant_id: 't1',
  created_at: '2026-01-15T00:00:00Z',
  team: [
    { id: 'm1', full_name: 'Ahmed Ali', role: 'Account Executive' },
    { id: 'm2', full_name: 'Sara Khalid', role: 'SDR' },
  ],
  manager: { id: 'mgr-1', full_name: 'Omar Hassan' },
}

describe('EmployeeProfileView', () => {
  it('renders full name and role', () => {
    render(<EmployeeProfileView profile={baseProfile} />)
    expect(screen.getByText('رشيد الموسوي')).toBeInTheDocument()
    expect(screen.getByText('Sales Director')).toBeInTheDocument()
  })

  it('renders email and phone', () => {
    render(<EmployeeProfileView profile={baseProfile} />)
    expect(screen.getByText('ragheed@example.com')).toBeInTheDocument()
    expect(screen.getByText('+966 55 123 4567')).toBeInTheDocument()
  })

  it('shows active status', () => {
    render(<EmployeeProfileView profile={baseProfile} />)
    expect(screen.getByText('نشط')).toBeInTheDocument()
  })

  it('shows inactive status', () => {
    render(<EmployeeProfileView profile={{ ...baseProfile, is_active: false }} />)
    expect(screen.getByText('غير نشط')).toBeInTheDocument()
  })

  it('renders team members', () => {
    render(<EmployeeProfileView profile={baseProfile} />)
    expect(screen.getByText('فريق العمل (2)')).toBeInTheDocument()
    expect(screen.getByText('Ahmed Ali')).toBeInTheDocument()
    expect(screen.getByText('Sara Khalid')).toBeInTheDocument()
  })

  it('renders empty state when no team or manager', () => {
    render(<EmployeeProfileView profile={{ ...baseProfile, team: [], manager: null }} />)
    expect(screen.getByText('لا توجد معلومات إضافية')).toBeInTheDocument()
  })
})
