import { render, screen } from '@testing-library/react'

jest.mock('axios', () => ({
  get: jest.fn().mockResolvedValue({ data: { id: 'o-1', name: 'Deal', stage: 'negotiation', value: 500000, currency: 'SAR', probability: 0.7, health: 'healthy', ownerId: 'u-1', status: 'active', description: 'Big deal', createdAt: '2026-01-01', updatedAt: '2026-07-10' } }),
}))

jest.mock('../../widgets/nba-widget/NBAWidget', () => ({
  NBAWidget: () => <div data-testid="nba-widget">NBA</div>,
}))

import { OpportunityWorkspace } from '../OpportunityWorkspace'

describe('OpportunityWorkspace', () => {
  it('renders loading state', () => {
    render(<OpportunityWorkspace opportunityId="o-1" />)
    expect(screen.getByText('Deal')).toBeInTheDocument()
  })

  it('renders opportunity name when loaded', async () => {
    render(<OpportunityWorkspace opportunityId="o-1" />)
    expect(await screen.findByText('Deal')).toBeInTheDocument()
  })

  it('renders NBA widget', async () => {
    render(<OpportunityWorkspace opportunityId="o-1" />)
    expect(await screen.findByTestId('nba-widget')).toBeInTheDocument()
  })
})
