import { render, screen } from '@testing-library/react'
import { SearchGroup } from '../SearchGroup'

describe('SearchGroup', () => {
  it('renders label and children', () => {
    render(<SearchGroup label="Companies"><div>Child</div></SearchGroup>)
    expect(screen.getByText('Companies')).toBeInTheDocument()
    expect(screen.getByText('Child')).toBeInTheDocument()
  })
})
