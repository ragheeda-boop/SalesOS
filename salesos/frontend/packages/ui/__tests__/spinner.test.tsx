import { render } from '@testing-library/react'
import { Spinner } from '../src/spinner'

describe('Spinner', () => {
  it('renders a spinning icon', () => {
    const { container } = render(<Spinner />)
    const svg = container.querySelector('svg.animate-spin')
    expect(svg).toBeInTheDocument()
  })
})
