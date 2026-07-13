import { dashboardTelemetry } from '../dashboard-telemetry'

beforeAll(() => {
  if (typeof performance !== 'undefined') {
    if (typeof performance.mark !== 'function') {
      (performance as any).mark = jest.fn()
    }
    if (typeof performance.measure !== 'function') {
      (performance as any).measure = jest.fn()
    }
  }
})

describe('dashboard-telemetry', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('records dashboard load event', () => {
    const eventsBefore = dashboardTelemetry.getAll().length
    dashboardTelemetry.error('dashboard', 'test error')
    const events = dashboardTelemetry.getAll()
    expect(events.length).toBe(eventsBefore + 1)
    expect(events[events.length - 1].measure).toBe('widget.error')
  })

  it('records widget render event via start/end', () => {
    const span = dashboardTelemetry.start('widget.render', 'widget-1')
    span.end()
    const events = dashboardTelemetry.getAll()
    const renderEvents = events.filter((e) => e.measure === 'widget.render')
    expect(renderEvents.length).toBeGreaterThanOrEqual(1)
  })

  it('records widget error event', () => {
    dashboardTelemetry.error('widget-1', 'Error occurred')
    const events = dashboardTelemetry.getAll()
    const errorEvent = events[events.length - 1]
    expect(errorEvent.measure).toBe('widget.error')
    expect(errorEvent.error).toBe('Error occurred')
  })
})
