import { render, screen } from '@testing-library/react'

jest.mock('../search-panel', () => ({
  SearchPanel: () => <div data-testid="search-panel">Search Panel</div>,
}))

import { SearchPanel } from '../search-panel'

describe('SearchPanel', () => {
  it('renders', () => {
    render(<SearchPanel />)
    expect(screen.getByTestId('search-panel')).toBeInTheDocument()
  })
})
