import { renderHook, act } from '@testing-library/react'
import { track, usePageTracking, useWidgetTracking } from '../analytics'

beforeEach(() => {
  jest.clearAllMocks()
  jest.useFakeTimers()
  Object.defineProperty(navigator, 'sendBeacon', {
    value: jest.fn().mockReturnValue(true),
    configurable: true,
    writable: true,
  })
})

afterEach(() => {
  jest.useRealTimers()
})

describe('track', () => {
  it('queues events and flushes on threshold', () => {
    for (let i = 0; i < 50; i++) {
      track({ type: 'widget.rendered', widgetId: `w-${i}` })
    }

    expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
    const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
    expect(body.events).toHaveLength(50)
  })

  it('flushes on interval', () => {
    track({ type: 'nba.viewed', metadata: { id: '1' } })
    expect(navigator.sendBeacon).not.toHaveBeenCalled()

    act(() => { jest.advanceTimersByTime(10_000) })

    expect(navigator.sendBeacon).toHaveBeenCalledTimes(1)
  })
})

describe('usePageTracking', () => {
  it('tracks page on mount', () => {
    renderHook(() => usePageTracking('dashboard'))

    act(() => { jest.advanceTimersByTime(10_000) })

    expect(navigator.sendBeacon).toHaveBeenCalled()
    const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
    expect(body.events[0].type).toBe('pilot.session_started')
    expect(body.events[0].metadata?.page).toBe('dashboard')
  })
})

describe('useWidgetTracking', () => {
  it('tracks widget rendered on mount', () => {
    const { result } = renderHook(() => useWidgetTracking('widget-1'))

    act(() => { jest.advanceTimersByTime(10_000) })

    expect(navigator.sendBeacon).toHaveBeenCalled()
    const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
    expect(body.events[0].type).toBe('widget.rendered')
    expect(body.events[0].widgetId).toBe('widget-1')
  })

  it('returns interact function that tracks interaction', () => {
    const { result } = renderHook(() => useWidgetTracking('widget-1'))

    act(() => { result.current.interact('click', { target: 'button' }) })
    act(() => { jest.advanceTimersByTime(10_000) })

    expect(navigator.sendBeacon).toHaveBeenCalled()
    const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
    const event = body.events.find((e: any) => e.type === 'widget.interacted')
    expect(event).toBeDefined()
    expect(event.widgetId).toBe('widget-1')
    expect(event.metadata?.action).toBe('click')
  })

  it('only tracks rendered once even with widgetId change', () => {
    const { rerender } = renderHook((id: string) => useWidgetTracking(id), { initialProps: 'widget-1' })
    rerender('widget-2')

    act(() => { jest.advanceTimersByTime(10_000) })

    const body = JSON.parse((navigator.sendBeacon as jest.Mock).mock.calls[0][1] as string)
    const rendered = body.events.filter((e: any) => e.type === 'widget.rendered')
    expect(rendered.length).toBe(1)
  })
})
