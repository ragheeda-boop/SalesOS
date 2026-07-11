import { render, screen, fireEvent } from '@testing-library/react'
import { SearchSuggestion } from '../SearchSuggestion'

describe('SearchSuggestion', () => {
  const suggestion = { text: 'شركة', type: 'query' as const }

  it('renders suggestion text', () => {
    render(<SearchSuggestion suggestion={suggestion as any} onClick={jest.fn()} />)
    expect(screen.getByText('شركة')).toBeInTheDocument()
  })

  it('calls onClick with suggestion', () => {
    const onClick = jest.fn()
    render(<SearchSuggestion suggestion={suggestion as any} onClick={onClick} />)
    fireEvent.click(screen.getByText('شركة'))
    expect(onClick).toHaveBeenCalledWith(suggestion)
  })
})
