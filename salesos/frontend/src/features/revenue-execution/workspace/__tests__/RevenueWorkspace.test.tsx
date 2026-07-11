import { render, screen } from '@testing-library/react'

jest.mock('../revenue/RevenueWorkspace', () => ({
  RevenueWorkspace: () => <div data-testid="revenue-workspace">Revenue Workspace</div>,
}))

import { RevenueWorkspace } from '../revenue/RevenueWorkspace'

describe('RevenueWorkspace', () => {
  it('renders', () => {
    render(<RevenueWorkspace />)
    expect(screen.getByTestId('revenue-workspace')).toBeInTheDocument()
  })
})
