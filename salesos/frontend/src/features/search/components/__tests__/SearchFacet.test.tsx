import { render, screen, fireEvent } from '@testing-library/react'
import { SearchFacetGroup } from '../SearchFacet'

describe('SearchFacetGroup', () => {
  const facet = { label: 'Status', values: [{ value: 'active', count: 10 }, { value: 'inactive', count: 5 }] }

  it('renders facet label and values', () => {
    render(<SearchFacetGroup facet={facet as any} selectedValues={[]} onToggle={jest.fn()} />)
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('calls onToggle when value is clicked', () => {
    const onToggle = jest.fn()
    render(<SearchFacetGroup facet={facet as any} selectedValues={[]} onToggle={onToggle} />)
    fireEvent.click(screen.getByText('active'))
    expect(onToggle).toHaveBeenCalledWith('active')
  })
})
