import { render, screen } from '@testing-library/react'

jest.mock('../copilot-panel', () => ({
  CopilotPanel: () => <div data-testid="copilot-panel">Copilot Panel</div>,
}))

import { CopilotPanel } from '../copilot-panel'

describe('CopilotPanel', () => {
  it('renders', () => {
    render(<CopilotPanel />)
    expect(screen.getByTestId('copilot-panel')).toBeInTheDocument()
  })
})
