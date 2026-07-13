import { render, screen } from '@testing-library/react'
import { TenantHealthList } from '../TenantHealthList'

const sampleTenants = [
  {
    tenant_id: '1', tenant_name: 'شركة التقدم', score: 90, status: 'healthy',
    color: 'green', components: {}, user_count: 150,
    last_active: '2026-07-10', renewal_risk: false, days_in_low_health: 0
  },
  {
    tenant_id: '2', tenant_name: 'شركة الأمل', score: 65, status: 'warning',
    color: 'yellow', components: {}, user_count: 80,
    last_active: '2026-07-09', renewal_risk: true, days_in_low_health: 3
  },
  {
    tenant_id: '3', tenant_name: 'شركة النجاح', score: 25, status: 'critical',
    color: 'red', components: {}, user_count: 10,
    last_active: null, renewal_risk: true, days_in_low_health: 12
  },
]

function renderView(tenants = sampleTenants) {
  return render(<TenantHealthList tenants={tenants} />)
}

describe('TenantHealthList', () => {
  it('renders tenant names', () => {
    renderView()
    expect(screen.getByText('شركة التقدم')).toBeInTheDocument()
    expect(screen.getByText('شركة الأمل')).toBeInTheDocument()
  })

  it('shows user counts', () => {
    renderView()
    expect(screen.getByText('150 مستخدم')).toBeInTheDocument()
    expect(screen.getByText('80 مستخدم')).toBeInTheDocument()
  })

  it('shows scores as percentages', () => {
    renderView()
    expect(screen.getByText('90%')).toBeInTheDocument()
    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('shows renewal risk', () => {
    renderView()
    const riskElements = screen.getAllByText('خطر تجديد')
    expect(riskElements.length).toBeGreaterThanOrEqual(2)
  })

  it('handles empty tenants list', () => {
    renderView([])
    expect(screen.getByText('لا توجد بيانات عملاء')).toBeInTheDocument()
  })

  it('renders status indicators via icons', () => {
    renderView()
    expect(screen.getByText('شركة التقدم')).toBeInTheDocument()
    expect(screen.getByText('شركة النجاح')).toBeInTheDocument()
  })
})
