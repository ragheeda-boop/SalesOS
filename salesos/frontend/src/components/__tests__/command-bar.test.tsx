import { render, screen } from '@testing-library/react'

jest.mock('../command-bar', () => ({
  GlobalCommandBar: () => <div data-testid="global-command-bar">Global Command Bar</div>,
}))

import { GlobalCommandBar } from '../command-bar'

describe('GlobalCommandBar', () => {
  it('renders', () => {
    render(<GlobalCommandBar />)
    expect(screen.getByTestId('global-command-bar')).toBeInTheDocument()
  })
})
