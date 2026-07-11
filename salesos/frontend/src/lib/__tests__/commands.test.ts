import { registerBuiltinCommands } from '../commands'

const mockRegisterCommand = jest.fn()

jest.mock('@salesos/hooks', () => ({
  registerCommand: (...args: any[]) => mockRegisterCommand(...args),
}))

describe('registerBuiltinCommands', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('registers all builtin commands', () => {
    const mockRouter = { push: jest.fn() } as any
    registerBuiltinCommands(mockRouter)

    expect(mockRegisterCommand).toHaveBeenCalledTimes(8)
  })

  it('registers navigation commands with correct router pushes', () => {
    const mockRouter = { push: jest.fn() } as any
    registerBuiltinCommands(mockRouter)

    const dashboardCmd = mockRegisterCommand.mock.calls.find((c: any) => c[0].id === 'go.dashboard')
    dashboardCmd[0].handler()
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard')

    const companiesCmd = mockRegisterCommand.mock.calls.find((c: any) => c[0].id === 'go.companies')
    companiesCmd[0].handler()
    expect(mockRouter.push).toHaveBeenCalledWith('/companies')
  })

  it('registers action commands that dispatch custom events', () => {
    const dispatchSpy = jest.spyOn(window, 'dispatchEvent')
    const mockRouter = { push: jest.fn() } as any
    registerBuiltinCommands(mockRouter)

    const copilotCmd = mockRegisterCommand.mock.calls.find((c: any) => c[0].id === 'action.copilot')
    copilotCmd[0].handler()
    expect(dispatchSpy).toHaveBeenCalledWith(expect.objectContaining({ type: 'salesos:toggle-copilot' }))
  })
})
