import { render, screen } from '@testing-library/react'
import { Loading } from '../loading'

describe('Loading', () => {
  it('renders with default spinner variant', () => {
    const { container } = render(<Loading />)
    expect(container.querySelector('svg.animate-spin')).toBeInTheDocument()
  })

  it('renders dots variant', () => {
    const { container } = render(<Loading variant="dots" />)
    expect(container.querySelector('.animate-bounce')).toBeInTheDocument()
  })

  it('renders pulse variant', () => {
    const { container } = render(<Loading variant="pulse" />)
    expect(container.querySelector('.animate-ping')).toBeInTheDocument()
  })

  it('sets role="status" and aria-label for accessibility', () => {
    const { container } = render(<Loading label="Loading data" />)
    const statusEl = container.querySelector('[role="status"]')
    expect(statusEl).toBeInTheDocument()
    expect(statusEl).toHaveAttribute('aria-label', 'Loading data')
  })

  it('sets aria-live="polite"', () => {
    const { container } = render(<Loading />)
    expect(container.querySelector('[aria-live="polite"]')).toBeInTheDocument()
  })

  it('renders overlay mode', () => {
    const { container } = render(<Loading overlay />)
    expect(container.firstChild).toHaveClass('fixed', 'inset-0', 'z-overlay')
  })

  it('renders label text', () => {
    render(<Loading label="Please wait..." />)
    expect(screen.getByText('Please wait...')).toBeInTheDocument()
  })
})
