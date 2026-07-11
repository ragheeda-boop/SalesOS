import { render, screen, fireEvent } from '@testing-library/react'
import { SearchSuggestion } from '../SearchSuggestion'

describe('SearchSuggestion', () => {
  const defaultProps = {
    suggestions: [{ text: 'شركة', type: 'company' as const }, { text: 'اتصال', type: 'contact' as const }],
    onSelect: jest.fn(),
  }

  it('renders suggestions', () => {
    render(<SearchSuggestion {...defaultProps} />)
    expect(screen.getByText('شركة')).toBeInTheDocument()
    expect(screen.getByText('اتصال')).toBeInTheDocument()
  })

  it('calls onSelect when clicked', () => {
    render(<SearchSuggestion {...defaultProps} />)
    fireEvent.click(screen.getByText('شركة'))
    expect(defaultProps.onSelect).toHaveBeenCalledWith('شركة')
  })
})
