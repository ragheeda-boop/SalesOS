import { render, screen, fireEvent } from '@testing-library/react'
import { SearchFilters } from '../SearchFilters'

describe('SearchFilters', () => {
  const filters = [
    { id: 'type', label: 'Type', options: [{ value: 'company', label: 'Company' }, { value: 'contact', label: 'Contact' }] },
  ]

  it('renders filter options', () => {
    render(<SearchFilters filters={filters} activeFilters={{}} onChange={jest.fn()} />)
    expect(screen.getByText('Company')).toBeInTheDocument()
    expect(screen.getByText('Contact')).toBeInTheDocument()
  })

  it('calls onChange when filter is selected', () => {
    const onChange = jest.fn()
    render(<SearchFilters filters={filters} activeFilters={{}} onChange={onChange} />)
    fireEvent.click(screen.getByText('Company'))
    expect(onChange).toHaveBeenCalled()
  })
})
