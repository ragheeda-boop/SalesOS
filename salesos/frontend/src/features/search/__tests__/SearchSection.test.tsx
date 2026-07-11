import { render, screen } from '@testing-library/react'
import { SearchSection } from '../components/SearchSection'

describe('SearchSection', () => {
  it('renders title', () => {
    render(<SearchSection title="النتائج">content</SearchSection>)
    expect(screen.getByText('النتائج')).toBeInTheDocument()
  })

  it('renders count', () => {
    render(<SearchSection title="النتائج" count={5}>content</SearchSection>)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders children', () => {
    render(<SearchSection title="test"><span>child</span></SearchSection>)
    expect(screen.getByText('child')).toBeInTheDocument()
  })
})
