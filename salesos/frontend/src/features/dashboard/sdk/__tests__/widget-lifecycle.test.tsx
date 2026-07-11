import { renderHook } from '@testing-library/react'
import { useWidgetLifecycle } from '../widget-lifecycle'

describe('useWidgetLifecycle', () => {
  it('calls onMount on mount', () => {
    const onMount = jest.fn()
    renderHook(() => useWidgetLifecycle('widget-1', {}, 'loading', { onMount }))
    expect(onMount).toHaveBeenCalledWith({ id: 'widget-1', metadata: {} })
  })

  it('calls onUnmount on unmount', () => {
    const onUnmount = jest.fn()
    const { unmount } = renderHook(() => useWidgetLifecycle('widget-1', {}, 'loading', { onUnmount }))
    unmount()
    expect(onUnmount).toHaveBeenCalledWith({ id: 'widget-1', metadata: {} })
  })

  it('notifies refresh', () => {
    const onRefresh = jest.fn()
    const { result } = renderHook(() => useWidgetLifecycle('widget-1', {}, 'ready', { onRefresh }))
    result.current.notifyRefresh()
    expect(onRefresh).toHaveBeenCalledWith({ id: 'widget-1', metadata: {} })
  })

  it('notifies error', () => {
    const onError = jest.fn()
    const { result } = renderHook(() => useWidgetLifecycle('widget-1', {}, 'ready', { onError }))
    const error = new Error('Test error')
    result.current.notifyError(error)
    expect(onError).toHaveBeenCalledWith({ id: 'widget-1', metadata: {}, error })
  })
})
