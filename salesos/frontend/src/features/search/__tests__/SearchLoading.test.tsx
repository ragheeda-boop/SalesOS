import { render, screen } from '@testing-library/react'
import { SearchLoading } from '../components/SearchLoading'

describe('SearchLoading', () => {
  it('renders skeleton elements', () => {
    const { container } = render(<SearchLoading count={3} />)
    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(3)
  })

  it('renders correct count of skeletons', () => {
    const { container } = render(<SearchLoading count={5} />)
    const resultRows = container.querySelectorAll('.animate-pulse')
    expect(resultRows.length).toBeGreaterThanOrEqual(5)
  })
})
