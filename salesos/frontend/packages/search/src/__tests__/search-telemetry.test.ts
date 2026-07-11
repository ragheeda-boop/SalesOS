import { searchTelemetry } from '../search-telemetry'

beforeEach(() => {
  // Reset the internal log by calling getAll and discarding
  searchTelemetry.getAll()
})

describe('searchTelemetry', () => {
  it('records a telemetry event', () => {
    searchTelemetry.record('search.query', { query: 'test', resultCount: 5 })
    const events = searchTelemetry.getAll()
    expect(events.length).toBeGreaterThanOrEqual(1)
  })

  it('startQuery returns an end function', () => {
    const timer = searchTelemetry.startQuery('test')
    expect(typeof timer.end).toBe('function')
    timer.end(5)
    const events = searchTelemetry.getAll()
    expect(events.length).toBeGreaterThanOrEqual(1)
  })

  it('click records result_click event', () => {
    searchTelemetry.click('comp_1', 'company', 0, 'test')
    const events = searchTelemetry.getAll()
    expect(events.some((e) => e.type === 'search.result_click')).toBe(true)
  })

  it('error records error event', () => {
    searchTelemetry.error('Something went wrong')
    const events = searchTelemetry.getAll()
    expect(events.some((e) => e.type === 'search.error')).toBe(true)
  })
})
