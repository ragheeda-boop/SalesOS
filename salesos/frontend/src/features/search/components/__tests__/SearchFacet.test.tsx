import { render, screen, fireEvent } from '@testing-library/react'
import { SearchFacet } from '../SearchFacet'

describe('SearchFacet', () => {
  const facet = { field: 'status', label: 'Status', buckets: [{ value: 'active', count: 10 }, { value: 'inactive', count: 5 }] }

  it('renders facet buckets', () => {
    render(<SearchFacet facet={facet} selected={[]} onToggle={jest.fn()} />)
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('calls onToggle when bucket is clicked', () => {
    const onToggle = jest.fn()
    render(<SearchFacet facet={facet} selected={[]} onToggle={onToggle} />)
    fireEvent.click(screen.getByText('active'))
    expect(onToggle).toHaveBeenCalledWith('status', 'active')
  })
})
