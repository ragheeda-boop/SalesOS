jest.mock('../monitoring', () => ({
  monitor: {
    trackApiCall: jest.fn(),
    trackError: jest.fn(),
    trackMetric: jest.fn(),
    trackPageLoad: jest.fn(),
  },
}))

jest.mock('../api', () => {
  const interceptors = { request: { use: jest.fn() }, response: { use: jest.fn() } }
  return {
    default: {
      interceptors,
      get: jest.fn(),
      post: jest.fn(),
    },
  }
})

describe('monitoring-init', () => {
  beforeEach(() => {
    jest.resetModules()
    jest.clearAllMocks()
  })

  it('registers axios interceptors', () => {
    const originalNodeEnv = process.env.NODE_ENV
    Object.defineProperty(process.env, 'NODE_ENV', { value: 'production', configurable: true })

    const { initMonitoring } = require('../monitoring-init')
    const api = require('../api').default

    initMonitoring()

    expect(api.interceptors.request.use).toHaveBeenCalled()
    expect(api.interceptors.response.use).toHaveBeenCalled()
    Object.defineProperty(process.env, 'NODE_ENV', { value: originalNodeEnv, configurable: true })
  })

  it('only initializes once', () => {
    const originalNodeEnv = process.env.NODE_ENV
    Object.defineProperty(process.env, 'NODE_ENV', { value: 'production', configurable: true })

    const { initMonitoring } = require('../monitoring-init')
    const api = require('../api').default

    initMonitoring()
    initMonitoring()

    expect(api.interceptors.request.use).toHaveBeenCalledTimes(1)
    Object.defineProperty(process.env, 'NODE_ENV', { value: originalNodeEnv, configurable: true })
  })

  it('does not initialize in non-production', () => {
    const originalNodeEnv = process.env.NODE_ENV
    Object.defineProperty(process.env, 'NODE_ENV', { value: 'development', configurable: true })

    const { initMonitoring } = require('../monitoring-init')
    const api = require('../api').default

    initMonitoring()

    expect(api.interceptors.request.use).not.toHaveBeenCalled()

    Object.defineProperty(process.env, 'NODE_ENV', { value: originalNodeEnv, configurable: true })
  })
})
