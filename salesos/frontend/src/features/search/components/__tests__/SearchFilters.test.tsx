import { render, screen, fireEvent } from '@testing-library/react'
import { SearchFilters } from '../SearchFilters'

describe('SearchFilters', () => {
  const facets = [{ field: 'type', label: 'Type', values: [{ value: 'company', count: 10 }, { value: 'contact', count: 5 }] }]

  it('renders facet values', () => {
    render(<SearchFilters facets={facets as any} selectedFilters={{}} onToggle={jest.fn()} />)
    expect(screen.getByText('company')).toBeInTheDocument()
    expect(screen.getByText('contact')).toBeInTheDocument()
  })

  it('calls onToggle when value is clicked', () => {
    const onToggle = jest.fn()
    render(<SearchFilters facets={facets as any} selectedFilters={{}} onToggle={onToggle} />)
    fireEvent.click(screen.getByText('company'))
    expect(onToggle).toHaveBeenCalledWith('type', 'company')
  })
})
