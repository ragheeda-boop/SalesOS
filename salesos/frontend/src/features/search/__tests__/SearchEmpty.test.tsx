import { render, screen } from '@testing-library/react'
import { SearchEmpty } from '../components/SearchEmpty'

describe('SearchEmpty', () => {
  it('renders default message', () => {
    render(<SearchEmpty />)
    expect(screen.getByText('لا توجد نتائج')).toBeInTheDocument()
  })

  it('renders with query', () => {
    render(<SearchEmpty query="test" />)
    expect(screen.getByText(/لا توجد نتائج لـ/)).toBeInTheDocument()
  })

  it('renders with suggestion', () => {
    render(<SearchEmpty suggestion="حاول استخدام كلمات مختلفة" />)
    expect(screen.getByText('حاول استخدام كلمات مختلفة')).toBeInTheDocument()
  })
})
