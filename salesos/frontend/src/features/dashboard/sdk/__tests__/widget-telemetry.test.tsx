import { widgetTelemetry } from '../widget-telemetry'

describe('widgetTelemetry', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    widgetTelemetry.clear()
  })

  it('records widget events', () => {
    widgetTelemetry.record('widget.mounted', 'widget-1')
    const events = widgetTelemetry.getAll()
    expect(events).toHaveLength(1)
    expect(events[0].type).toBe('widget.mounted')
    expect(events[0].widgetId).toBe('widget-1')
  })

  it('includes extra data in events', () => {
    widgetTelemetry.record('widget.failed', 'widget-1', { error: 'Something broke', status: 'error' })
    const events = widgetTelemetry.getAll()
    expect(events[0].error).toBe('Something broke')
    expect(events[0].status).toBe('error')
  })
})
