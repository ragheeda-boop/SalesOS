import { render, screen, waitFor } from '@testing-library/react'

jest.mock('axios', () => ({
  get: jest.fn().mockResolvedValue({ data: { id: 'o-1', name: 'Deal', companyId: 'c-1', stage: 'negotiation', value: 500000, currency: 'SAR', probability: 0.7, health: 'healthy', ownerId: 'u-1', status: 'active', description: 'Big deal', createdAt: '2026-01-01', updatedAt: '2026-07-10' } }),
}))

jest.mock('../../widgets/nba-widget/NBAWidget', () => ({
  NBAWidget: () => <div data-testid="nba-widget">NBA</div>,
}))

import { OpportunityWorkspace } from '../OpportunityWorkspace'

describe('OpportunityWorkspace', () => {
  it('shows loading then renders data', async () => {
    const { container } = render(<OpportunityWorkspace opportunityId="o-1" />)
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Deal')).toBeInTheDocument())
  })

  it('renders NBA widget when loaded', async () => {
    render(<OpportunityWorkspace opportunityId="o-1" />)
    expect(await screen.findByTestId('nba-widget')).toBeInTheDocument()
  })
})
