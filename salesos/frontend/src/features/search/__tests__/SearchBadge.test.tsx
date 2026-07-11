import { render, screen } from '@testing-library/react'
import { SearchBadge } from '../components/SearchBadge'

describe('SearchBadge', () => {
  it('renders label', () => {
    render(<SearchBadge label="نشط" />)
    expect(screen.getByText('نشط')).toBeInTheDocument()
  })

  it('renders with info variant', () => {
    const { container } = render(<SearchBadge label="معلومات" variant="info" />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('renders with danger variant', () => {
    const { container } = render(<SearchBadge label="خطأ" variant="danger" />)
    expect(container.firstChild).toBeInTheDocument()
  })
})
