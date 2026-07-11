import { renderHook, act } from '@testing-library/react'
import { track, usePageTracking, useWidgetTracking } from '../analytics'

beforeEach(() => {
  jest.clearAllMocks()
  jest.useFakeTimers()
})

afterEach(() => {
  jest.useRealTimers()
})

describe('track', () => {
  it('queues events and flushes on threshold', () => {
    const spy = jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)

    for (let i = 0; i < 50; i++) {
      track({ type: 'widget.rendered', widgetId: `w-${i}` })
    }

    expect(spy).toHaveBeenCalledTimes(1)
    const url = spy.mock.calls[0][0]
    const body = JSON.parse(spy.mock.calls[0][1] as string)
    expect(url).toBe('/api/v1/analytics/events')
    expect(body.events).toHaveLength(50)
  })

  it('flushes on interval', () => {
    const spy = jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)

    track({ type: 'nba.viewed', metadata: { id: '1' } })
    expect(spy).not.toHaveBeenCalled()

    act(() => { jest.advanceTimersByTime(10_000) })

    expect(spy).toHaveBeenCalledTimes(1)
  })
})

describe('usePageTracking', () => {
  it('tracks page on mount', () => {
    const spy = jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)

    renderHook(() => usePageTracking('dashboard'))

    act(() => { jest.advanceTimersByTime(10_000) })

    expect(spy).toHaveBeenCalled()
    const body = JSON.parse(spy.mock.calls[0][1] as string)
    expect(body.events[0].type).toBe('pilot.session_started')
    expect(body.events[0].metadata?.page).toBe('dashboard')
  })
})

describe('useWidgetTracking', () => {
  it('tracks widget rendered on mount', () => {
    const spy = jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)

    const { result } = renderHook(() => useWidgetTracking('widget-1'))

    act(() => { jest.advanceTimersByTime(10_000) })

    expect(spy).toHaveBeenCalled()
    const body = JSON.parse(spy.mock.calls[0][1] as string)
    expect(body.events[0].type).toBe('widget.rendered')
    expect(body.events[0].widgetId).toBe('widget-1')
  })

  it('returns interact function that tracks interaction', () => {
    const spy = jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)

    const { result } = renderHook(() => useWidgetTracking('widget-1'))

    act(() => { result.current.interact('click', { target: 'button' }) })

    act(() => { jest.advanceTimersByTime(10_000) })

    expect(spy).toHaveBeenCalled()
    const body = JSON.parse(spy.mock.calls[0][1] as string)
    const event = body.events.find((e: any) => e.type === 'widget.interacted')
    expect(event).toBeDefined()
    expect(event.widgetId).toBe('widget-1')
    expect(event.metadata?.action).toBe('click')
  })

  it('only tracks rendered once even with widgetId change', () => {
    const spy = jest.spyOn(navigator, 'sendBeacon').mockReturnValue(true)

    const { rerender } = renderHook((id: string) => useWidgetTracking(id), { initialProps: 'widget-1' })
    rerender('widget-2')

    act(() => { jest.advanceTimersByTime(10_000) })

    const body = JSON.parse(spy.mock.calls[0][1] as string)
    const rendered = body.events.filter((e: any) => e.type === 'widget.rendered')
    expect(rendered.length).toBe(1)
  })
})
