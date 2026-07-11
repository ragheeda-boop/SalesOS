import { render, screen, fireEvent } from '@testing-library/react'
import { SearchBar } from '../SearchBar'

jest.mock('../SearchInput', () => ({
  SearchInput: ({ value, onChange, onSearch, placeholder }: any) => (
    <input
      data-testid="search-input"
      value={value}
      onChange={(e: any) => onChange(e.target.value)}
      onKeyDown={(e: any) => e.key === 'Enter' && onSearch(value)}
      placeholder={placeholder || 'Search'}
      role="searchbox"
    />
  ),
}))

describe('SearchBar', () => {
  it('renders search input', () => {
    render(<SearchBar onSearch={jest.fn()} />)
    expect(screen.getByTestId('search-input')).toBeInTheDocument()
  })

  it('calls onSearch when input has value', () => {
    const onSearch = jest.fn()
    render(<SearchBar onSearch={onSearch} />)
    const input = screen.getByTestId('search-input')
    fireEvent.change(input, { target: { value: 'test' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onSearch).toHaveBeenCalledWith('test')
  })
})
