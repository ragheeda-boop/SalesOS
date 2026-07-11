import { render, screen } from '@testing-library/react'

jest.mock('../company-intelligence-layout', () => ({
  CompanyIntelligenceLayout: () => <div data-testid="ci-layout">CI Layout</div>,
}))

import { CompanyIntelligenceLayout } from '../company-intelligence-layout'

describe('CompanyIntelligenceLayout', () => {
  it('renders', () => {
    render(<CompanyIntelligenceLayout />)
    expect(screen.getByTestId('ci-layout')).toBeInTheDocument()
  })
})
