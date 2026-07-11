import { render, screen, fireEvent } from '@testing-library/react'
import { SearchError } from '../components/SearchError'

describe('SearchError', () => {
  it('renders error message', () => {
    render(<SearchError message="فشل البحث" />)
    expect(screen.getByText('فشل البحث')).toBeInTheDocument()
  })

  it('has role="alert"', () => {
    render(<SearchError />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('shows retry button when onRetry provided', () => {
    const onRetry = jest.fn()
    render(<SearchError onRetry={onRetry} />)
    fireEvent.click(screen.getByText('إعادة المحاولة'))
    expect(onRetry).toHaveBeenCalled()
  })

  it('does not show retry button when onRetry not provided', () => {
    render(<SearchError />)
    expect(screen.queryByText('إعادة المحاولة')).not.toBeInTheDocument()
  })
})
