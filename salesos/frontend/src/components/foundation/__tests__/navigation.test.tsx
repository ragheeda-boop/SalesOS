import { render, screen, fireEvent } from '@testing-library/react'
import { Navigation } from '../navigation'

const sections = [
  {
    id: 'nav',
    label: 'Navigation',
    items: [
      { id: 'home', label: 'Home', icon: <span>H</span>, href: '/', active: true },
      { id: 'about', label: 'About', icon: <span>A</span>, href: '/about' },
      { id: 'disabled', label: 'Disabled', icon: <span>X</span>, disabled: true },
    ],
  },
]

describe('Navigation', () => {
  it('renders sections and items', () => {
    render(<Navigation sections={sections} />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
  })

  it('shows active state', () => {
    render(<Navigation sections={sections} />)
    const homeLink = screen.getByText('Home').closest('a')!
    expect(homeLink).toHaveAttribute('aria-current', 'page')
  })

  it('disables disabled items', () => {
    render(<Navigation sections={sections} />)
    const disabledBtn = screen.getByText('Disabled')
    expect(disabledBtn).toHaveAttribute('aria-disabled', 'true')
    expect(disabledBtn).toHaveAttribute('tabindex', '-1')
  })

  it('renders horizontal orientation', () => {
    const { container } = render(<Navigation sections={sections} orientation="horizontal" />)
    expect(container.querySelector('nav')).toBeInTheDocument()
  })

  it('renders pill variant', () => {
    const { container } = render(<Navigation sections={sections} variant="pills" />)
    expect(container.querySelector('nav')).toBeInTheDocument()
  })

  it('renders tabs variant', () => {
    const { container } = render(<Navigation sections={sections} variant="tabs" />)
    expect(container.querySelector('nav')).toBeInTheDocument()
  })

  it('renders different sizes', () => {
    const { container: sm } = render(<Navigation sections={sections} size="sm" />)
    const { container: lg } = render(<Navigation sections={sections} size="lg" />)
    expect(sm.querySelector('nav')).toBeInTheDocument()
    expect(lg.querySelector('nav')).toBeInTheDocument()
  })
})
