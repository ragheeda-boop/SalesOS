import { render, screen } from '@testing-library/react'
import { CommandBarResults } from '../CommandBarResults'

describe('CommandBarResults', () => {
  it('renders results', () => {
    render(<CommandBarResults results={[{ id: '1', label: 'Result 1' }, { id: '2', label: 'Result 2' }]} />)
    expect(screen.getByText('Result 1')).toBeInTheDocument()
    expect(screen.getByText('Result 2')).toBeInTheDocument()
  })

  it('shows empty state', () => {
    render(<CommandBarResults results={[]} emptyMessage="No results" />)
    expect(screen.getByText('No results')).toBeInTheDocument()
  })
})
