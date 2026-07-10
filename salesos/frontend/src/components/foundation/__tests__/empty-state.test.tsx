import { render, screen, fireEvent } from '@testing-library/react'
import { EmptyState } from '../empty-state'

describe('EmptyState', () => {
  it('renders title', () => {
    render(<EmptyState title="No data" />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders description', () => {
    render(<EmptyState title="Empty" description="Nothing to show" />)
    expect(screen.getByText('Nothing to show')).toBeInTheDocument()
  })

  it('renders action button and handles click', () => {
    const onClick = jest.fn()
    render(<EmptyState title="Empty" action={{ label: 'Retry', onClick }} />)
    const btn = screen.getByText('Retry')
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('sets role="status" for accessibility', () => {
    const { container } = render(<EmptyState title="Empty" />)
    expect(container.firstChild).toHaveAttribute('role', 'status')
  })

  it('has aria-hidden icon', () => {
    const { container } = render(<EmptyState title="Empty" />)
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true')
  })
})
