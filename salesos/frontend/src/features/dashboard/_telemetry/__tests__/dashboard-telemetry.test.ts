jest.mock('@/lib/analytics', () => ({
  track: jest.fn(),
}))

import { track } from '@/lib/analytics'
import { recordDashboardEvent, recordWidgetEvent } from '../dashboard-telemetry'

describe('dashboard-telemetry', () => {
  beforeEach(() => { jest.clearAllMocks() })

  it('records dashboard events', () => {
    recordDashboardEvent('viewed', { page: 'main' })
    expect(track).toHaveBeenCalledWith({
      type: 'pilot.session_started',
      metadata: { action: 'viewed', page: 'main' },
    })
  })

  it('records widget events', () => {
    recordWidgetEvent('widget-1', 'interacted', { action: 'click' })
    expect(track).toHaveBeenCalledWith({
      type: 'widget.interacted',
      widgetId: 'widget-1',
      metadata: { action: 'click' },
    })
  })
})
