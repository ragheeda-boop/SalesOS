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
    __esModule: true,
    default: {
      interceptors,
      get: jest.fn(),
      post: jest.fn(),
    },
  }
})

describe('monitoring-init', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('registers axios interceptors', () => {
    jest.isolateModules(() => {
      const originalNodeEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'production'

      const { initMonitoring } = require('../monitoring-init')
      const api = require('../api').default

      initMonitoring()

      expect(api.interceptors.request.use).toHaveBeenCalled()
      expect(api.interceptors.response.use).toHaveBeenCalled()
      process.env.NODE_ENV = originalNodeEnv
    })
  })

  it('only initializes once', () => {
    jest.isolateModules(() => {
      const originalNodeEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'production'

      const { initMonitoring } = require('../monitoring-init')
      const api = require('../api').default

      initMonitoring()
      initMonitoring()

      expect(api.interceptors.request.use).toHaveBeenCalledTimes(1)
      process.env.NODE_ENV = originalNodeEnv
    })
  })

  it('does not initialize in non-production', () => {
    jest.isolateModules(() => {
      const originalNodeEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'development'

      const { initMonitoring } = require('../monitoring-init')
      const api = require('../api').default

      initMonitoring()

      expect(api.interceptors.request.use).not.toHaveBeenCalled()

      process.env.NODE_ENV = originalNodeEnv
    })
  })
})
