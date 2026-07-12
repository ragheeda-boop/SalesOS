import { useWorkspaceContext } from '../EmployeeWorkspace'

describe('EmployeeWorkspace exports', () => {
  it('exports useWorkspaceContext as a function', () => {
    expect(typeof useWorkspaceContext).toBe('function')
  })
})
