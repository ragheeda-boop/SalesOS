import { render, screen } from '@testing-library/react'
import { Surface } from '../surface'

describe('Surface', () => {
  it('renders children', () => {
    render(<Surface>Content</Surface>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders as different element', () => {
    const { container } = render(<Surface as="section">Section</Surface>)
    expect(container.querySelector('section')).toBeInTheDocument()
  })

  it('renders with elevated variant', () => {
    const { container } = render(<Surface variant="elevated">Elevated</Surface>)
    expect(container.firstChild).toHaveClass('shadow-[var(--shadow-card)]')
  })

  it('renders with dark variant', () => {
    const { container } = render(<Surface variant="dark">Dark</Surface>)
    expect(container.firstChild).toHaveClass('text-white')
  })

  it('renders with bordered variant', () => {
    const { container } = render(<Surface variant="bordered">Bordered</Surface>)
    expect(container.firstChild).toHaveClass('border')
  })

  it('renders with glass variant', () => {
    const { container } = render(<Surface variant="glass">Glass</Surface>)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('applies padding sizes', () => {
    const { container: sm } = render(<Surface padding="sm">S</Surface>)
    const { container: lg } = render(<Surface padding="lg">L</Surface>)
    expect(sm.firstChild).toHaveClass('p-3')
    expect(lg.firstChild).toHaveClass('p-8')
  })

  it('applies rounded sizes', () => {
    const { container: none } = render(<Surface rounded="none">N</Surface>)
    const { container: xl } = render(<Surface rounded="xl">XL</Surface>)
    expect(none.firstChild).not.toHaveClass('rounded-sm')
    expect(xl.firstChild).toHaveClass('rounded-xl')
  })
})
