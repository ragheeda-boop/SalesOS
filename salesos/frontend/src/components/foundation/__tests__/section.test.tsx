import { render, screen } from '@testing-library/react'
import { Section } from '../section'

describe('Section', () => {
  it('renders children', () => {
    render(<Section>Content</Section>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders title and description', () => {
    render(<Section title="Overview" description="Summary of data">Content</Section>)
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Summary of data')).toBeInTheDocument()
  })

  it('renders as section by default', () => {
    const { container } = render(<Section>Content</Section>)
    expect(container.querySelector('section')).toBeInTheDocument()
  })

  it('sets aria-labelledby when title is provided', () => {
    const { container } = render(<Section title="Overview">Content</Section>)
    expect(container.firstChild).toHaveAttribute('aria-labelledby')
  })
})
