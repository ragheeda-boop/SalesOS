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

jest.mock('../monitoring', () => ({
  monitor: {
    trackApiCall: jest.fn(),
    trackError: jest.fn(),
    trackMetric: jest.fn(),
    trackPageLoad: jest.fn(),
  },
}))

describe('monitoring-init interceptor registration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    process.env.NODE_ENV = 'production'
  })

  afterEach(() => {
    process.env.NODE_ENV = 'test'
  })

  it('registers axios interceptors on init', () => {
    jest.isolateModules(() => {
      const { initMonitoring } = require('../monitoring-init')
      const api = require('../api').default

      initMonitoring()

      expect(api.interceptors.request.use).toHaveBeenCalled()
      expect(api.interceptors.response.use).toHaveBeenCalled()
    })
  })

  it('tracks API calls via response interceptor', () => {
    jest.isolateModules(() => {
      const { initMonitoring } = require('../monitoring-init')
      const api = require('../api').default
      const { monitor } = require('../monitoring')
      jest.spyOn(monitor, 'trackApiCall')

      initMonitoring()

      const reqHandler = api.interceptors.request.use.mock.calls[0][0]
      const resHandler = api.interceptors.response.use.mock.calls[0][0]

      const config: any = { method: 'get', url: '/api/v1/test' }
      reqHandler(config)
      expect(config._monitorStart).toBeDefined()

      const response = { config, status: 200 }
      resHandler(response)
      expect(monitor.trackApiCall).toHaveBeenCalledWith('GET', '/api/v1/test', expect.any(Number), 200)
    })
  })
})
