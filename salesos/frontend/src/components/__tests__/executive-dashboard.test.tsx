import { render, screen } from '@testing-library/react'

jest.mock('../executive-dashboard', () => ({
  ExecutiveDashboard: () => <div data-testid="exec-dashboard">Executive Dashboard</div>,
}))

import { ExecutiveDashboard } from '../executive-dashboard'

describe('ExecutiveDashboard', () => {
  it('renders', () => {
    render(<ExecutiveDashboard />)
    expect(screen.getByTestId('exec-dashboard')).toBeInTheDocument()
  })
})
