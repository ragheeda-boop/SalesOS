import { render, screen } from '@testing-library/react'
import { SearchHeader } from '../SearchHeader'

describe('SearchHeader', () => {
  it('renders title', () => {
    render(<SearchHeader title="Search Results" total={42} />)
    expect(screen.getByText('Search Results')).toBeInTheDocument()
  })

  it('displays total count', () => {
    render(<SearchHeader title="Results" total={100} />)
    expect(screen.getByText('100')).toBeInTheDocument()
  })
})
