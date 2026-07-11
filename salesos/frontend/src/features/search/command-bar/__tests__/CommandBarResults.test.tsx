import { render, screen } from '@testing-library/react'

jest.mock('@salesos/search', () => ({
  useSearchContext: () => ({
    results: [{ id: 'r-1', entityType: 'company', title: 'شركة', subtitle: '', description: '', score: 0.9, source: 'CR', highlights: [], badges: [], relationships: [] }],
    total: 1,
    isLoading: false,
    query: { text: 'شركة' },
    suggestions: [],
    history: [],
    search: jest.fn(),
    setQuery: jest.fn(),
    clearSearch: jest.fn(),
  }),
  SearchHighlight: ({ text }: { text: string }) => <span>{text}</span>,
}))

jest.mock('../../components', () => ({
  SearchSection: ({ children }: any) => <div>{children}</div>,
  SearchResultCard: ({ result, highlighted, onClick }: any) => (
    <div role="option" aria-selected={highlighted} onClick={() => onClick?.(result)}>
      {result.title}
    </div>
  ),
  SearchLoading: () => <div>Loading...</div>,
  SearchEmpty: () => <div>Empty</div>,
}))

import { CommandBarResults } from '../CommandBarResults'

describe('CommandBarResults', () => {
  it('renders results', () => {
    render(<CommandBarResults highlightedIndex={0} onResultClick={jest.fn()} onSuggestionClick={jest.fn()} onHistoryClick={jest.fn()} />)
    expect(screen.getByText('شركة')).toBeInTheDocument()
  })
})
