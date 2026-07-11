import { render, screen, fireEvent } from '@testing-library/react'
import { SearchResultCard } from '../SearchResultCard'

const result = {
  id: 'r-1',
  entityType: 'company' as const,
  title: 'شركة',
  subtitle: 'نشط',
  description: '',
  score: 0.85,
  source: 'CR',
  highlights: [],
  badges: [{ variant: 'success' as const, label: 'نشط' }],
  relationships: [],
}

describe('SearchResultCard', () => {
  it('renders result', () => {
    const { container } = render(<SearchResultCard result={result as any} />)
    expect(container.querySelector('[role="option"]')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const onClick = jest.fn()
    render(<SearchResultCard result={result as any} onClick={onClick} />)
    fireEvent.click(screen.getByRole('option'))
    expect(onClick).toHaveBeenCalledWith(result)
  })
})
