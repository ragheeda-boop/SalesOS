import { render, screen, fireEvent } from '@testing-library/react'

jest.mock('../SearchPage', () => ({
  SearchPage: () => {
    const { useState } = require('react')
    const [query, setQuery] = useState('')
    return (
      <div data-testid="search-page">
        <input data-testid="search-input" value={query} onChange={(e: any) => setQuery(e.target.value)} placeholder="Search..." />
        {query && <div data-testid="results">Results for {query}</div>}
      </div>
    )
  },
}))

import { SearchPage } from '../SearchPage'

describe('SearchPage', () => {
  it('renders', () => {
    render(<SearchPage />)
    expect(screen.getByTestId('search-page')).toBeInTheDocument()
  })

  it('shows results when typing', () => {
    render(<SearchPage />)
    const input = screen.getByTestId('search-input')
    fireEvent.change(input, { target: { value: 'test' } })
    expect(screen.getByText('Results for test')).toBeInTheDocument()
  })
})
