import { render, screen, fireEvent } from '@testing-library/react'
import { SearchResultCard } from '../SearchResultCard'

describe('SearchResultCard', () => {
  it('renders result data', () => {
    render(<SearchResultCard title="شركة" subtitle="نشط" type="company" />)
    expect(screen.getByText('شركة')).toBeInTheDocument()
    expect(screen.getByText('نشط')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const onClick = jest.fn()
    render(<SearchResultCard title="Test" type="company" onClick={onClick} />)
    fireEvent.click(screen.getByText('Test'))
    expect(onClick).toHaveBeenCalled()
  })
})
