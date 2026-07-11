jest.mock('@/lib/analytics', () => ({
  track: jest.fn(),
}))

import { track } from '@/lib/analytics'
import { WidgetTelemetry } from '../widget-telemetry'

describe('WidgetTelemetry', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('tracks widget rendered', () => {
    const telemetry = new WidgetTelemetry('widget-1')
    telemetry.trackRendered()
    expect(track).toHaveBeenCalledWith({
      type: 'widget.rendered',
      widgetId: 'widget-1',
      metadata: undefined,
    })
  })

  it('tracks widget interaction', () => {
    const telemetry = new WidgetTelemetry('widget-1')
    telemetry.trackInteracted('click', { target: 'button' })
    expect(track).toHaveBeenCalledWith({
      type: 'widget.interacted',
      widgetId: 'widget-1',
      metadata: { action: 'click', target: 'button' },
    })
  })
})
