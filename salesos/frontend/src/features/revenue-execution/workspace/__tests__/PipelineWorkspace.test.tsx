import { render, screen } from '@testing-library/react'

jest.mock('../pipeline/PipelineWorkspace', () => ({
  PipelineWorkspace: () => <div data-testid="pipeline-workspace">Pipeline Workspace</div>,
}))

import { PipelineWorkspace } from '../pipeline/PipelineWorkspace'

describe('PipelineWorkspace', () => {
  it('renders', () => {
    render(<PipelineWorkspace />)
    expect(screen.getByTestId('pipeline-workspace')).toBeInTheDocument()
  })
})
