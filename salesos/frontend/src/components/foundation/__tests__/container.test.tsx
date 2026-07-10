import { render, screen } from '@testing-library/react'
import { Container } from '../container'

describe('Container', () => {
  it('renders children', () => {
    render(<Container>Content</Container>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('defaults to xl size', () => {
    const { container } = render(<Container>Content</Container>)
    expect(container.firstChild).toHaveClass('max-w-[1280px]')
  })

  it('applies sm size', () => {
    const { container } = render(<Container size="sm">Content</Container>)
    expect(container.firstChild).toHaveClass('max-w-[640px]')
  })

  it('renders as custom element', () => {
    const { container } = render(<Container as="section">Content</Container>)
    expect(container.querySelector('section')).toBeInTheDocument()
  })
})
