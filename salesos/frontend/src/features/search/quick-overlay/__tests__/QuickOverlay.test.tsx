import { render } from '@testing-library/react'

jest.mock('@salesos/search', () => ({
  SearchProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="search-provider">{children}</div>,
  useSearchContext: () => ({ query: { text: '' }, results: [], total: 0, isLoading: false, history: [], search: jest.fn(), setQuery: jest.fn(), clearSearch: jest.fn() }),
}))

import { QuickOverlay } from '../QuickOverlay'

describe('QuickOverlay', () => {
  it('renders when open', () => {
    const { container } = render(<QuickOverlay open={true} onClose={jest.fn()} />)
    expect(container.querySelector('.fixed')).toBeInTheDocument()
  })

  it('inner component returns null when closed', () => {
    const { container } = render(<QuickOverlay open={false} onClose={jest.fn()} />)
    expect(container.querySelector('.fixed')).not.toBeInTheDocument()
  })
})
