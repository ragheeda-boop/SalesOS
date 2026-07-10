import { render, screen } from '@testing-library/react'
import { Divider } from '../divider'

describe('Divider', () => {
  it('renders with role="separator"', () => {
    const { container } = render(<Divider />)
    expect(container.firstChild).toHaveAttribute('role', 'separator')
  })

  it('renders with label', () => {
    render(<Divider label="Section" />)
    expect(screen.getByText('Section')).toBeInTheDocument()
  })

  it('renders label with aria-label', () => {
    const { container } = render(<Divider label="Section" />)
    expect(container.firstChild).toHaveAttribute('aria-label', 'Section')
  })

  it('applies variant classes', () => {
    const { container: full } = render(<Divider variant="full" />)
    const { container: light } = render(<Divider variant="light" />)
    expect(full.firstChild).toHaveClass('border-[var(--border-subtle)]')
    expect(light.firstChild).toHaveClass('border-[var(--border-muted)]')
  })
})
