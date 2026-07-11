import { render, screen } from '@testing-library/react'

jest.mock('../pipeline-kanban', () => ({
  PipelineKanban: () => <div data-testid="pipeline-kanban">Pipeline Kanban</div>,
}))

import { PipelineKanban } from '../pipeline-kanban'

describe('PipelineKanban', () => {
  it('renders', () => {
    render(<PipelineKanban />)
    expect(screen.getByTestId('pipeline-kanban')).toBeInTheDocument()
  })
})
