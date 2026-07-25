import { render, screen } from '@testing-library/react'

jest.mock('@/features/rules/RulesWorkspace', () => ({
  RulesWorkspace: () => <div data-testid="rules-workspace">RulesWorkspace</div>,
}))

import RulesPage from '../page'

describe('RulesPage', () => {
  it('renders without crashing', () => {
    render(<RulesPage />)
    expect(screen.getByTestId('rules-workspace')).toBeInTheDocument()
  })

  it('delegates to RulesWorkspace', () => {
    render(<RulesPage />)
    expect(screen.getByText('RulesWorkspace')).toBeInTheDocument()
  })
})
