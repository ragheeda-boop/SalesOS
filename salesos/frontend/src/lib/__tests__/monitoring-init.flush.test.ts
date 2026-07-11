import { monitor } from '../monitoring'

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

jest.useFakeTimers()

describe('monitoring-init with axios interceptor', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)
  })

  it('tracks API calls via response interceptor', async () => {
    process.env.NODE_ENV = 'production'
    const { initMonitoring } = require('../monitoring-init')
    initMonitoring()

    const api = require('../api').default
    const reqHandler = api.interceptors.request.use.mock.calls[0][0]
    const resHandler = api.interceptors.response.use.mock.calls[0][0]

    const config: any = { method: 'get', url: '/api/v1/test' }
    reqHandler(config)

    const start = config._monitorStart
    expect(start).toBeDefined()

    await jest.advanceTimersByTimeAsync(50)

    const response = { config, status: 200 }
    resHandler(response)

    jest.advanceTimersByTime(60_000)

    expect(navigator.sendBeacon).toHaveBeenCalled()
    const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
    const apiEvent = body.events.find((e: any) => e.type === 'api_call')
    expect(apiEvent).toBeDefined()
    expect(apiEvent.method).toBe('GET')
    expect(apiEvent.path).toBe('/api/v1/test')
    expect(apiEvent.status).toBe(200)
  })
})
