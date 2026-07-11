import { render, screen } from '@testing-library/react'

jest.mock('../company-intelligence-provider', () => ({
  CompanyIntelligenceProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="ci-provider">{children}</div>,
  useCompanyIntelligenceContext: () => ({ widgets: {}, companyId: 'c-1', loading: false }),
}))

import { CompanyIntelligenceProvider, useCompanyIntelligenceContext } from '../company-intelligence-provider'

describe('CompanyIntelligenceProvider', () => {
  it('renders children', () => {
    render(<CompanyIntelligenceProvider companyId="c-1"><div data-testid="child">Content</div></CompanyIntelligenceProvider>)
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })
})

describe('useCompanyIntelligenceContext', () => {
  it('returns context', () => {
    const ctx = useCompanyIntelligenceContext()
    expect(ctx.companyId).toBe('c-1')
    expect(ctx).toHaveProperty('widgets')
  })
})
