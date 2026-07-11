import { render, screen } from '@testing-library/react'

jest.mock('../dashboard-provider', () => ({
  DashboardProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="dashboard-provider">{children}</div>,
  useDashboardContext: () => ({ widgets: {}, refresh: jest.fn(), loading: false }),
}))

import { DashboardProvider, useDashboardContext } from '../dashboard-provider'

describe('DashboardProvider', () => {
  it('renders children', () => {
    render(<DashboardProvider><div data-testid="child">Content</div></DashboardProvider>)
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })
})

describe('useDashboardContext', () => {
  it('returns default context', () => {
    const ctx = useDashboardContext()
    expect(ctx).toHaveProperty('widgets')
    expect(ctx).toHaveProperty('refresh')
    expect(ctx).toHaveProperty('loading')
  })
})
