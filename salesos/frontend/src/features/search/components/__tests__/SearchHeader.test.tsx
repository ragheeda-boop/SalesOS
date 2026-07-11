import { render } from '@testing-library/react'
import { SearchHeader } from '../SearchHeader'

describe('SearchHeader', () => {
  it('renders with total and query', () => {
    const { container } = render(<SearchHeader total={42} query="test" />)
    expect(container.textContent).toContain('42')
    expect(container.textContent).toContain('test')
  })
})
