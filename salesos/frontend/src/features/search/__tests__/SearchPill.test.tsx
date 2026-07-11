import { render, screen, fireEvent } from '@testing-library/react'
import { SearchPill } from '../components/SearchPill'

describe('SearchPill', () => {
  it('renders label', () => {
    render(<SearchPill label="القطاع: الطاقة" />)
    expect(screen.getByText('القطاع: الطاقة')).toBeInTheDocument()
  })

  it('calls onRemove when remove button clicked', () => {
    const onRemove = jest.fn()
    render(<SearchPill label="test" onRemove={onRemove} />)
    fireEvent.click(screen.getByLabelText('إزالة test'))
    expect(onRemove).toHaveBeenCalled()
  })

  it('does not show remove button when onRemove not provided', () => {
    render(<SearchPill label="test" />)
    expect(screen.queryByLabelText('إزالة test')).not.toBeInTheDocument()
  })
})
