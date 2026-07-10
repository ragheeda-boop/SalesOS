import { render, screen, fireEvent } from '@testing-library/react'
import { Sidebar } from '../src/sidebar'

describe('Sidebar', () => {
  const items = [
    { icon: <span>H</span>, label: 'Home', href: '/' },
    { icon: <span>S</span>, label: 'Settings', href: '/settings', badge: 3 },
  ]

  it('renders all items', () => {
    render(<Sidebar items={items} />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('shows badge count', () => {
    render(<Sidebar items={items} />)
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders toggle button', () => {
    render(<Sidebar items={items} />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('calls onToggle when toggle button clicked', () => {
    const onToggle = jest.fn()
    render(<Sidebar items={items} onToggle={onToggle} />)
    fireEvent.click(screen.getByRole('button'))
    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('applies collapsed width', () => {
    const { container } = render(<Sidebar items={items} collapsed />)
    expect(container.firstChild).toHaveClass('w-16')
  })
})
