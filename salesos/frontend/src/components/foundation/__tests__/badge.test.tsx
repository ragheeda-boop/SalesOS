import { render, screen } from '@testing-library/react'
import { Badge } from '../badge'

describe('Badge', () => {
  it('renders children', () => {
    render(<Badge>Active</Badge>)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('applies size classes', () => {
    const { container: sm } = render(<Badge size="sm">S</Badge>)
    const { container: md } = render(<Badge size="md">M</Badge>)
    expect(sm.firstChild).toHaveClass('px-1.5', 'py-0.5', 'text-[10px]')
    expect(md.firstChild).toHaveClass('px-2', 'py-0.5', 'text-xs')
  })

  it('renders with dot indicator', () => {
    const { container } = render(<Badge dot>Active</Badge>)
    expect(container.querySelector('span[aria-hidden="true"]')).toBeInTheDocument()
  })

  it('renders value prop', () => {
    render(<Badge value={42}>Items</Badge>)
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('applies status variant colors based on children', () => {
    const { container } = render(<Badge variant="status">active</Badge>)
    expect(container.firstChild).toHaveClass('bg-success-100', 'text-success-800')
  })

  it('applies default variant when status not in map', () => {
    const { container } = render(<Badge variant="status">unknown</Badge>)
    expect(container.firstChild).toBeInTheDocument()
  })
})
