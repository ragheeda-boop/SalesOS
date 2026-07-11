import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../src/button'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick handler', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click</Button>)
    fireEvent.click(screen.getByText('Click'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('renders with primary variant by default', () => {
    render(<Button>Primary</Button>)
    const btn = screen.getByText('Primary')
    expect(btn.className).toContain('bg-[var(--muhide-orange)]')
  })

  it('renders with different variants', () => {
    const { rerender } = render(<Button variant="danger">Danger</Button>)
    expect(screen.getByText('Danger').className).toContain('bg-danger-600')

    rerender(<Button variant="outline">Outline</Button>)
    expect(screen.getByText('Outline').className).toContain('border')
  })

  it('renders with different sizes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>)
    expect(screen.getByText('Small').className).toContain('h-8')

    rerender(<Button size="lg">Large</Button>)
    expect(screen.getByText('Large').className).toContain('h-12')
  })

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>)
    const btn = screen.getByText('Loading')
    expect(btn).toBeDisabled()
  })

  it('disables when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByText('Disabled')).toBeDisabled()
  })

  it('renders left icon', () => {
    const { container } = render(<Button leftIcon={<span data-testid="icon">*</span>}>With Icon</Button>)
    expect(container.querySelector('[data-testid="icon"]')).toBeInTheDocument()
  })
})
