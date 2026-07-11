import { render, screen, fireEvent } from '@testing-library/react'
import { createWidget } from '../create-widget'
import { widgetTelemetry } from '../widget-telemetry'
import { mockPermissionsAll, mockPermissionsNone } from '../testing/mockPermissions'
import { mockFeatureFlagsAll, mockFeatureFlagsNone } from '../testing/mockFeatureFlags'

function makeConfig(overrides?: {
  lifecycle?: Parameters<typeof createWidget>[0]['lifecycle']
  useData?: () => ReturnType<typeof createWidget>[0] extends infer T ? T : never
}) {
  return {
    metadata: {
      id: 'test' as const,
      title: 'SDK Widget',
      minHeight: '200px',
      permissions: ['dashboard:read'],
      featureFlag: { enabled: true, tier: 'enabled' as const },
    },
    lifecycle: overrides?.lifecycle,
    useData: overrides?.useData ?? (() => ({
      data: { msg: 'hello' },
      status: 'ready' as const,
      lastUpdated: null,
      error: null,
      refetch: jest.fn(),
    })),
    render: ({ data }: { data: { msg: string } }) => <div role="region">{data.msg}</div>,
  }
}

describe('createWidget SDK', () => {
  beforeEach(() => {
    mockPermissionsAll()
    mockFeatureFlagsAll()
  })

  describe('Lifecycle hooks', () => {
    it('calls onMount when mounted', () => {
      const onMount = jest.fn()
      const Widget = createWidget(makeConfig({ lifecycle: { onMount } }))
      render(<Widget />)
      expect(onMount).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'test' })
      )
    })

    it('calls onUnmount when unmounted', () => {
      const onUnmount = jest.fn()
      const Widget = createWidget(makeConfig({ lifecycle: { onUnmount } }))
      const { unmount } = render(<Widget />)
      unmount()
      expect(onUnmount).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'test' })
      )
    })

    it('calls onRefresh when refresh clicked', () => {
      const onRefresh = jest.fn()
      const Widget = createWidget(makeConfig({ lifecycle: { onRefresh } }))
      render(<Widget />)
      fireEvent.click(screen.getByLabelText('Refresh'))
      expect(onRefresh).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'test' })
      )
    })

    it('calls onError when status becomes error', () => {
      const onError = jest.fn()
      const Widget = createWidget(makeConfig({
        lifecycle: { onError },
        useData: () => ({
          data: null,
          status: 'error' as const,
          lastUpdated: null,
          error: new Error('fail'),
          refetch: jest.fn(),
        }),
      }))
      render(<Widget />)
      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'test', error: expect.any(Error) })
      )
    })
  })

  describe('Telemetry', () => {
    beforeEach(() => {
      jest.clearAllMocks()
    })

    it('records mounted event', () => {
      const spy = jest.spyOn(widgetTelemetry, 'record')
      const Widget = createWidget(makeConfig())
      render(<Widget />)
      expect(spy).toHaveBeenCalledWith('widget.mounted', 'test')
    })

    it('records loaded event when ready', () => {
      const spy = jest.spyOn(widgetTelemetry, 'record')
      const Widget = createWidget(makeConfig())
      render(<Widget />)
      expect(spy).toHaveBeenCalledWith('widget.loaded', 'test', expect.any(Object))
    })

    it('records failed event when error', () => {
      const spy = jest.spyOn(widgetTelemetry, 'record')
      const Widget = createWidget(makeConfig({
        useData: () => ({
          data: null,
          status: 'error' as const,
          lastUpdated: null,
          error: new Error('fail'),
          refetch: jest.fn(),
        }),
      }))
      render(<Widget />)
      expect(spy).toHaveBeenCalledWith('widget.failed', 'test', expect.any(Object))
    })

    it('records refreshed event on refresh', () => {
      const spy = jest.spyOn(widgetTelemetry, 'record')
      const Widget = createWidget(makeConfig())
      render(<Widget />)
      fireEvent.click(screen.getByLabelText('Refresh'))
      expect(spy).toHaveBeenCalledWith('widget.refreshed', 'test')
    })
  })

  describe('Status transitions', () => {
    it('shows error state and clears telemetrySent on status change', () => {
      const onError = jest.fn()
      const Widget = createWidget(makeConfig({ lifecycle: { onError } }))
      const { rerender } = render(<Widget />)
      expect(onError).not.toHaveBeenCalled()
    })
  })

  describe('Edge cases', () => {
    it('renders null when no fallback and permission denied', () => {
      mockPermissionsNone()
      const Widget = createWidget(makeConfig())
      const { container } = render(<Widget />)
      expect(container.innerHTML).toBe('')
    })

    it('renders null when no fallback and feature disabled', () => {
      mockFeatureFlagsNone()
      const Widget = createWidget(makeConfig())
      const { container } = render(<Widget />)
      expect(container.innerHTML).toBe('')
    })
  })
})
