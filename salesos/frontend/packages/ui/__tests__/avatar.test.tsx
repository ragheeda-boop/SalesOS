import { render, screen } from '@testing-library/react'
import { Avatar } from '../src/avatar'

describe('Avatar', () => {
  it('renders fallback initials when no src', () => {
    render(<Avatar fallback="AB" />)
    expect(screen.getByText('AB')).toBeInTheDocument()
  })

  it('renders with src prop', () => {
    const { container } = render(<Avatar src="https://example.com/photo.jpg" alt="User" />)
    expect(container.firstChild).toBeInTheDocument()
    expect(container.firstChild).toHaveClass('h-10', 'w-10')
  })

  it('has default size md', () => {
    const { container } = render(<Avatar fallback="A" />)
    expect(container.firstChild).toHaveClass('h-10', 'w-10', 'text-sm')
  })

  it('applies size sm', () => {
    const { container } = render(<Avatar size="sm" fallback="A" />)
    expect(container.firstChild).toHaveClass('h-8', 'w-8', 'text-xs')
  })
})
