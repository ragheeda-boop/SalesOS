import { render, screen } from '@testing-library/react'
import { Typography } from '../typography'

describe('Typography', () => {
  it('renders children', () => {
    render(<Typography>Hello</Typography>)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders as h1 by default for h1 variant', () => {
    const { container } = render(<Typography variant="h1">Title</Typography>)
    expect(container.querySelector('h1')).toBeInTheDocument()
  })

  it('renders as p for body variant', () => {
    const { container } = render(<Typography variant="body">Body</Typography>)
    expect(container.querySelector('p')).toBeInTheDocument()
  })

  it('renders as custom element via as prop', () => {
    const { container } = render(<Typography variant="body" as="span">Custom</Typography>)
    expect(container.querySelector('span')).toBeInTheDocument()
  })

  it('applies color class', () => {
    const { container } = render(<Typography color="muted">Muted</Typography>)
    expect(container.firstChild).toHaveClass('text-[var(--text-muted)]')
  })

  it('applies brand color', () => {
    const { container } = render(<Typography color="brand">Brand</Typography>)
    expect(container.firstChild).toHaveClass('text-[var(--muhide-orange)]')
  })

  it('applies truncate class', () => {
    const { container } = render(<Typography truncate>Long text</Typography>)
    expect(container.firstChild).toHaveClass('truncate')
  })

  it('has display font for headings', () => {
    const { container } = render(<Typography variant="h2">Heading</Typography>)
    expect(container.firstChild).toHaveClass('font-display')
  })

  it('has mono font for code', () => {
    const { container } = render(<Typography variant="code">code</Typography>)
    expect(container.firstChild).toHaveClass('font-mono')
  })
})
