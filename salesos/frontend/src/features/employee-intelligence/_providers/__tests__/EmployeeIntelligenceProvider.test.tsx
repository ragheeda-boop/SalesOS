import { render, screen } from '@testing-library/react'
import { EmployeeIntelligenceProvider, useEmployeeIntelligence } from '../EmployeeIntelligenceProvider'

jest.mock('@/lib/hooks/employeeQueries', () => ({
  useMy360: jest.fn(),
}))

import { useMy360 } from '@/lib/hooks/employeeQueries'

function TestConsumer() {
  const ctx = useEmployeeIntelligence()
  return (
    <div>
      <span data-testid="loading">{String(ctx.isLoading)}</span>
      <span data-testid="error">{String(ctx.isError)}</span>
      <span data-testid="has-data">{String(ctx.data !== null)}</span>
    </div>
  )
}

describe('EmployeeIntelligenceProvider', () => {
  it('provides loading state', () => {
    ;(useMy360 as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: jest.fn(),
    })
    render(
      <EmployeeIntelligenceProvider>
        <TestConsumer />
      </EmployeeIntelligenceProvider>,
    )
    expect(screen.getByTestId('loading')).toHaveTextContent('true')
    expect(screen.getByTestId('has-data')).toHaveTextContent('false')
  })

  it('provides data state', () => {
    ;(useMy360 as jest.Mock).mockReturnValue({
      data: { profile: { full_name: 'Test' } },
      isLoading: false,
      isError: false,
      error: null,
      refetch: jest.fn(),
    })
    render(
      <EmployeeIntelligenceProvider>
        <TestConsumer />
      </EmployeeIntelligenceProvider>,
    )
    expect(screen.getByTestId('loading')).toHaveTextContent('false')
    expect(screen.getByTestId('has-data')).toHaveTextContent('true')
  })

  it('provides error state', () => {
    ;(useMy360 as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed'),
      refetch: jest.fn(),
    })
    render(
      <EmployeeIntelligenceProvider>
        <TestConsumer />
      </EmployeeIntelligenceProvider>,
    )
    expect(screen.getByTestId('error')).toHaveTextContent('true')
  })

  it('throws when used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<TestConsumer />)).toThrow('useEmployeeIntelligence must be used within')
    consoleSpy.mockRestore()
  })
})
