jest.mock('@salesos/hooks', () => ({
  registerCommand: jest.fn(),
}))

import { registerCommand } from '@salesos/hooks'
import { registerBuiltinCommands } from '../commands'

describe('registerBuiltinCommands', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('registers all builtin commands', () => {
    const mockRouter = { push: jest.fn() } as any
    registerBuiltinCommands(mockRouter)
    expect(registerCommand).toHaveBeenCalledTimes(9)
  })

  it('registers navigation commands with correct router pushes', () => {
    const mockRouter = { push: jest.fn() } as any
    registerBuiltinCommands(mockRouter)

    const dashboardCall = (registerCommand as jest.Mock).mock.calls.find((c: any) => c[0].id === 'go.dashboard')
    dashboardCall[0].handler()
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard')
  })

  it('registers action commands that dispatch custom events', () => {
    const dispatchSpy = jest.spyOn(window, 'dispatchEvent')
    const mockRouter = { push: jest.fn() } as any
    registerBuiltinCommands(mockRouter)

    const copilotCall = (registerCommand as jest.Mock).mock.calls.find((c: any) => c[0].id === 'action.copilot')
    copilotCall[0].handler()
    expect(dispatchSpy).toHaveBeenCalledWith(expect.objectContaining({ type: 'salesos:toggle-copilot' }))
  })
})
