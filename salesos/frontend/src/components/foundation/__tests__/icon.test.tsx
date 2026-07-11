import { render, screen } from '@testing-library/react'
import { Icon } from '../icon'

describe('Icon', () => {
  it('renders children', () => {
    render(<Icon><svg data-testid="icon" /></Icon>)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('is hidden by default', () => {
    const { container } = render(<Icon><svg /></Icon>)
    expect(container.firstChild).toHaveAttribute('aria-hidden', 'true')
  })

  it('has img role when label is provided', () => {
    render(<Icon label="Search"><svg /></Icon>)
    const el = screen.getByRole('img')
    expect(el).toHaveAttribute('aria-label', 'Search')
  })

  it('applies color classes', () => {
    const { container } = render(<Icon color="brand"><svg /></Icon>)
    expect(container.firstChild).toHaveClass('text-[var(--muhide-orange)]')
  })

  it('sets inline width and height', () => {
    const { container } = render(<Icon size="lg"><svg /></Icon>)
    expect((container.firstChild as HTMLElement).style.width).toBe('20px')
    expect((container.firstChild as HTMLElement).style.height).toBe('20px')
  })
})
