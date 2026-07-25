import { render, screen, fireEvent } from '@testing-library/react'
import { Pagination } from '../src/pagination'

describe('Pagination', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 10,
    totalItems: 200,
    pageSize: 20,
    onPageChange: jest.fn(),
  }

  it('renders showing text', () => {
    render(<Pagination {...defaultProps} />)
    expect(screen.getByText('Showing 1–20 of 200')).toBeInTheDocument()
  })

  it('has aria-label', () => {
    render(<Pagination {...defaultProps} />)
    expect(screen.getByLabelText('pagination')).toBeInTheDocument()
  })

  it('renders page buttons', () => {
    render(<Pagination {...defaultProps} />)
    expect(screen.getByLabelText('Page 1')).toBeInTheDocument()
    expect(screen.getByLabelText('Page 2')).toBeInTheDocument()
  })

  it('highlights current page', () => {
    render(<Pagination {...defaultProps} currentPage={3} />)
    const page3 = screen.getByLabelText('Page 3')
    expect(page3).toHaveAttribute('aria-current', 'page')
  })

  it('calls onPageChange on click', () => {
    const onPageChange = jest.fn()
    render(<Pagination {...defaultProps} onPageChange={onPageChange} />)
    fireEvent.click(screen.getByLabelText('Page 2'))
    expect(onPageChange).toHaveBeenCalledWith(2)
  })

  it('shows page size selector when onPageSizeChange provided', () => {
    render(<Pagination {...defaultProps} onPageSizeChange={jest.fn()} />)
    expect(screen.getByText('Rows per page:')).toBeInTheDocument()
  })

  it('disables prev/first on first page', () => {
    render(<Pagination {...defaultProps} currentPage={1} />)
    expect(screen.getByLabelText('First page')).toBeDisabled()
    expect(screen.getByLabelText('Previous page')).toBeDisabled()
  })

  it('disables next/last on last page', () => {
    render(<Pagination {...defaultProps} currentPage={10} />)
    expect(screen.getByLabelText('Next page')).toBeDisabled()
    expect(screen.getByLabelText('Last page')).toBeDisabled()
  })

  it('renders nothing when totalPages is 0', () => {
    const { container } = render(<Pagination {...defaultProps} totalPages={0} totalItems={0} />)
    expect(container.innerHTML).toBe('')
  })
})
