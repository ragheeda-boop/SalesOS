import { Monitor, monitor } from '../monitoring'

jest.useFakeTimers()

describe('Monitor', () => {
  let m: Monitor

  beforeEach(() => {
    jest.clearAllMocks()
    jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)
    m = new Monitor(true)
    m.enable()
  })

  afterEach(() => {
    m.disable()
  })

  describe('enable/disable', () => {
    it('starts disabled by default in dev', () => {
      const mon = new Monitor()
      mon.trackApiCall('GET', '/test', 100, 200)
      jest.advanceTimersByTime(60_000)
      expect(navigator.sendBeacon).not.toHaveBeenCalled()
    })

    it('enable() starts the flush timer', () => {
      const mon = new Monitor()
      mon.enable()
      mon.trackApiCall('GET', '/test', 100, 200)
      jest.advanceTimersByTime(60_000)
      expect(navigator.sendBeacon).toHaveBeenCalled()
    })

    it('disable() stops the flush timer', () => {
      m.disable()
      m.trackApiCall('GET', '/test', 100, 200)
      jest.advanceTimersByTime(60_000)
      expect(navigator.sendBeacon).not.toHaveBeenCalled()
    })
  })

  describe('trackApiCall', () => {
    it('records API call events', () => {
      m.trackApiCall('POST', '/api/test', 150, 201)
      jest.advanceTimersByTime(60_000)

      const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
      expect(body.events[0].type).toBe('api_call')
      expect(body.events[0].method).toBe('POST')
      expect(body.events[0].path).toBe('/api/test')
      expect(body.events[0].duration_ms).toBe(150)
      expect(body.events[0].status).toBe(201)
    })
  })

  describe('trackError', () => {
    it('records error events', () => {
      const error = new Error('Something broke')
      m.trackError(error, 'test-context')
      jest.advanceTimersByTime(60_000)

      const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
      expect(body.events[0].type).toBe('error')
      expect(body.events[0].error_message).toBe('Something broke')
      expect(body.events[0].context).toBe('test-context')
    })
  })

  describe('trackRender', () => {
    it('records render events', () => {
      m.trackRender('TestComponent', 42)
      jest.advanceTimersByTime(60_000)

      const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
      expect(body.events[0].type).toBe('render')
      expect(body.events[0].component_name).toBe('TestComponent')
      expect(body.events[0].duration_ms).toBe(42)
    })
  })

  describe('trackMetric', () => {
    it('records metric events with tags', () => {
      m.trackMetric('lcp', 2500, { type: 'web_vital' })
      jest.advanceTimersByTime(60_000)

      const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
      expect(body.events[0].type).toBe('metric')
      expect(body.events[0].name).toBe('lcp')
      expect(body.events[0].value).toBe(2500)
      expect(body.events[0].tags?.type).toBe('web_vital')
    })
  })

  describe('flush', () => {
    it('flushes buffer via sendBeacon', () => {
      m.trackMetric('test', 1)
      m.flush()

      expect(navigator.sendBeacon).toHaveBeenCalledWith(
        '/api/v1/monitoring/events',
        expect.any(String),
      )
    })

    it('does nothing when buffer empty', () => {
      m.flush()
      expect(navigator.sendBeacon).not.toHaveBeenCalled()
    })

    it('flushes automatically at threshold', () => {
      for (let i = 0; i < 100; i++) {
        m.trackMetric(`m-${i}`, i)
      }

      expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
    })
  })
})

describe('monitor singleton', () => {
  it('is a Monitor instance', () => {
    expect(monitor).toBeInstanceOf(Monitor)
  })
})
