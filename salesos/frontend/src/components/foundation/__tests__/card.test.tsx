import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardContent } from '../card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Content</Card>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('applies default variant classes', () => {
    const { container } = render(<Card>Content</Card>)
    expect(container.firstChild).toHaveClass('bg-[var(--bg-primary)]', 'border', 'shadow-muhide-1')
  })

  it('applies dark variant', () => {
    const { container } = render(<Card variant="dark">Content</Card>)
    expect(container.firstChild).toHaveClass('bg-[var(--muhide-ink)]', 'text-white')
  })

  it('applies bordered variant', () => {
    const { container } = render(<Card variant="bordered">Content</Card>)
    expect(container.firstChild).toHaveClass('bg-[var(--bg-primary)]', 'border')
    expect(container.firstChild).not.toHaveClass('shadow-muhide-1')
  })

  it('applies padding sizes', () => {
    const { container: sm } = render(<Card padding="sm">C</Card>)
    const { container: md } = render(<Card padding="md">C</Card>)
    const { container: lg } = render(<Card padding="lg">C</Card>)
    expect(sm.firstChild).toHaveClass('p-3')
    expect(md.firstChild).toHaveClass('p-4')
    expect(lg.firstChild).toHaveClass('p-5')
  })

  it('applies accent classes', () => {
    const { container } = render(<Card accent="orange">Content</Card>)
    expect(container.firstChild).toHaveClass('border-l-[3px]', 'border-l-[var(--muhide-orange)]')
  })

  it('combines custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})

describe('CardHeader', () => {
  it('renders children', () => {
    render(<CardHeader>Header</CardHeader>)
    expect(screen.getByText('Header')).toBeInTheDocument()
  })
})

describe('CardContent', () => {
  it('renders children', () => {
    render(<CardContent>Content</CardContent>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })
})
