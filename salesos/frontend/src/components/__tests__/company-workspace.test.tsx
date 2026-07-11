import { render, screen } from '@testing-library/react'

jest.mock('../company-workspace', () => ({
  CompanyWorkspace: () => <div data-testid="company-workspace">Company Workspace</div>,
}))

import { CompanyWorkspace } from '../company-workspace'

describe('CompanyWorkspace', () => {
  it('renders', () => {
    render(<CompanyWorkspace />)
    expect(screen.getByTestId('company-workspace')).toBeInTheDocument()
  })
})
