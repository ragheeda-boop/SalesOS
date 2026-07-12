import { render, screen } from '@testing-library/react'
import { EmployeePortfolioView } from '../EmployeePortfolioWidget'
import type { EmployeePortfolio } from '@/lib/api'

const basePortfolio: EmployeePortfolio = {
  companies: [{ id: 'c1', name: 'Acme Corp' }, { id: 'c2', name: 'Globex' }],
  contacts: [{ id: 'p1', name: 'John' }, { id: 'p2', name: 'Jane' }],
  pipeline: [
    { id: 'opp1', name: 'Big Deal', type: 'new', value: 500000, status: 'negotiation' },
    { id: 'opp2', name: 'Mid Deal', type: 'renewal', value: 200000, status: 'proposal' },
  ],
  revenue: 1000000,
  contracts: [
    { id: 'ct1', name: 'Annual Contract', type: 'service', value: 300000, status: 'active' },
  ],
  projects: [],
}

describe('EmployeePortfolioView', () => {
  it('renders active deals', () => {
    render(<EmployeePortfolioView portfolio={basePortfolio} />)
    expect(screen.getByText('Big Deal')).toBeInTheDocument()
    expect(screen.getByText('Mid Deal')).toBeInTheDocument()
  })

  it('renders contracts', () => {
    render(<EmployeePortfolioView portfolio={basePortfolio} />)
    expect(screen.getByText('Annual Contract')).toBeInTheDocument()
  })

  it('renders pipeline total', () => {
    render(<EmployeePortfolioView portfolio={basePortfolio} />)
    expect(screen.getByText(/7[,.]?00[,.]?000/)).toBeInTheDocument()
  })

  it('renders empty state when no data', () => {
    const empty: EmployeePortfolio = { companies: [], contacts: [], pipeline: [], revenue: 0, contracts: [], projects: [] }
    render(<EmployeePortfolioView portfolio={empty} />)
    expect(screen.getByText('لا توجد بيانات محفظة')).toBeInTheDocument()
  })
})
