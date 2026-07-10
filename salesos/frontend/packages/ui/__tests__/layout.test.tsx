import { render, screen } from '@testing-library/react'
import { Layout, LayoutHeader, LayoutSidebar, LayoutContent } from '../src/layout'

describe('Layout', () => {
  it('renders children', () => {
    render(<Layout>Content</Layout>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders as flex h-screen container', () => {
    const { container } = render(<Layout>Content</Layout>)
    expect(container.firstChild).toHaveClass('flex', 'h-screen')
  })
})

describe('LayoutHeader', () => {
  it('renders children', () => {
    render(<Layout><LayoutHeader>Header</LayoutHeader></Layout>)
    expect(screen.getByText('Header')).toBeInTheDocument()
  })
})

describe('LayoutSidebar', () => {
  it('renders children', () => {
    render(<Layout><LayoutSidebar>Side</LayoutSidebar></Layout>)
    expect(screen.getByText('Side')).toBeInTheDocument()
  })
})

describe('LayoutContent', () => {
  it('renders as main element', () => {
    const { container } = render(<Layout><LayoutContent>Body</LayoutContent></Layout>)
    expect(container.querySelector('main')).toBeInTheDocument()
  })
})
