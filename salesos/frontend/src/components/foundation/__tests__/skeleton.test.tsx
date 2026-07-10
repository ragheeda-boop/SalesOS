import { render, screen } from '@testing-library/react'
import { Skeleton } from '../skeleton'

describe('Skeleton', () => {
  it('renders with default text variant', () => {
    const { container } = render(<Skeleton />)
    const items = container.querySelectorAll('.animate-pulse')
    expect(items.length).toBe(1)
  })

  it('renders multiple items with count', () => {
    const { container } = render(<Skeleton count={3} />)
    const items = container.querySelectorAll('.animate-pulse')
    expect(items.length).toBe(3)
  })

  it('renders table-row variant with avatar + title layout', () => {
    const { container } = render(<Skeleton variant="table-row" />)
    expect(container.querySelector('[role="status"]')).toBeInTheDocument()
    const items = container.querySelectorAll('.animate-pulse')
    expect(items.length).toBeGreaterThanOrEqual(3)
  })

  it('renders chart variant with bars', () => {
    const { container } = render(<Skeleton variant="chart" count={4} />)
    expect(container.firstChild).toHaveClass('flex', 'items-end', 'gap-2')
  })

  it('sets aria-hidden on individual items', () => {
    const { container } = render(<Skeleton />)
    expect(container.querySelector('[aria-hidden="true"]')).toBeInTheDocument()
  })

  it('sets role="status" on container', () => {
    const { container } = render(<Skeleton />)
    expect(container.querySelector('[role="status"]')).toBeInTheDocument()
  })
})
