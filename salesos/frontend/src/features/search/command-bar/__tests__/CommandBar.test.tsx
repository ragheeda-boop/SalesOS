import { render } from '@testing-library/react'

jest.mock('@salesos/search', () => ({
  SearchProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="search-provider">{children}</div>,
  useSearchContext: () => ({
    query: { text: '' },
    search: jest.fn(),
    setQuery: jest.fn(),
    clearSearch: jest.fn(),
  }),
}))

import { CommandBar } from '../CommandBar'

describe('CommandBar', () => {
  it('renders SearchProvider wrapper', () => {
    const { container } = render(<CommandBar />)
    expect(container.querySelector('[data-testid="search-provider"]')).toBeInTheDocument()
  })

  it('inner component returns null when not open', () => {
    const { container } = render(<CommandBar />)
    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument()
  })
})
