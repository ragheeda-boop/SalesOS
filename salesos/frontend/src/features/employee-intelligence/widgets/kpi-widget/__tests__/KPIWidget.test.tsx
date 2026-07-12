import { render, screen } from '@testing-library/react'
import { KPIView } from '../KPIWidget'
import type { EmployeeKPIs } from '@/lib/api'

const baseKPIs: EmployeeKPIs = {
  revenue: 1500000,
  pipeline: 5000000,
  win_rate: 0.65,
  response_rate: 0.8,
  follow_up_rate: 0.7,
  activities: 42,
  productivity: 0.75,
  forecast: 3000000,
}

describe('KPIView', () => {
  it('renders revenue', () => {
    render(<KPIView data={baseKPIs} />)
    expect(screen.getByText(/1[,.]?500[,.]?000/)).toBeInTheDocument()
  })

  it('renders pipeline value', () => {
    render(<KPIView data={baseKPIs} />)
    expect(screen.getByText(/5[,.]?000[,.]?000/)).toBeInTheDocument()
  })

  it('renders win rate as percentage', () => {
    render(<KPIView data={baseKPIs} />)
    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('renders productivity', () => {
    render(<KPIView data={baseKPIs} />)
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('renders forecast', () => {
    render(<KPIView data={baseKPIs} />)
    expect(screen.getByText(/3[,.]?000[,.]?000/)).toBeInTheDocument()
  })

  it('renders activities count', () => {
    render(<KPIView data={baseKPIs} />)
    expect(screen.getByText('42')).toBeInTheDocument()
  })
})
