import { WidgetLifecycle } from '../widget-lifecycle'

describe('WidgetLifecycle', () => {
  let lifecycle: WidgetLifecycle

  beforeEach(() => {
    lifecycle = new WidgetLifecycle('widget-1')
  })

  it('starts in initial state', () => {
    expect(lifecycle.getState()).toBe('idle')
  })

  it('transitions through states', () => {
    lifecycle.mount()
    expect(lifecycle.getState()).toBe('mounted')

    lifecycle.activate()
    expect(lifecycle.getState()).toBe('active')

    lifecycle.deactivate()
    expect(lifecycle.getState()).toBe('inactive')

    lifecycle.unmount()
    expect(lifecycle.getState()).toBe('unmounted')
  })

  it('fires callbacks on state change', () => {
    const onMount = jest.fn()
    lifecycle.onMount(onMount)
    lifecycle.mount()
    expect(onMount).toHaveBeenCalled()
  })
})
