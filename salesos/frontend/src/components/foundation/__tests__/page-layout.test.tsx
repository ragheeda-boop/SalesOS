import { render, screen } from '@testing-library/react'
import { PageLayout } from '../page-layout'

describe('PageLayout', () => {
  it('renders children', () => {
    render(<PageLayout>Content</PageLayout>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders header', () => {
    render(<PageLayout header={<header>Header</header>}>Content</PageLayout>)
    expect(screen.getByText('Header')).toBeInTheDocument()
  })

  it('renders sidebar', () => {
    render(<PageLayout sidebar={<aside>Sidebar</aside>}>Content</PageLayout>)
    expect(screen.getByText('Sidebar')).toBeInTheDocument()
  })

  it('applies maxWidth class', () => {
    const { container } = render(<PageLayout maxWidth="sm">Content</PageLayout>)
    expect(container.querySelector('.max-w-screen-sm')).toBeInTheDocument()
  })
})
