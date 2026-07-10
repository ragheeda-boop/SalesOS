import { render, screen } from '@testing-library/react'
import { Grid } from '../grid'

describe('Grid', () => {
  it('renders children', () => {
    render(<Grid><span>Item</span></Grid>)
    expect(screen.getByText('Item')).toBeInTheDocument()
  })

  it('defaults to cols-1', () => {
    const { container } = render(<Grid><span>A</span></Grid>)
    expect(container.firstChild).toHaveClass('grid', 'grid-cols-1')
  })

  it('applies column count', () => {
    const { container } = render(<Grid cols={3}><span>A</span></Grid>)
    expect(container.firstChild).toHaveClass('grid-cols-3')
  })

  it('applies responsive columns', () => {
    const { container } = render(<Grid cols={{ default: 1, md: 2, lg: 3 }}><span>A</span></Grid>)
    expect(container.firstChild).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3')
  })

  it('applies gap', () => {
    const { container } = render(<Grid gap={6}><span>A</span></Grid>)
    expect(container.firstChild).toHaveClass('gap-6')
  })
})
