import type { WidgetStatus, WidgetAction, DashboardWidget } from '../widget.contract'

describe('Widget types', () => {
  it('WidgetStatus accepts valid values', () => {
    const statuses: WidgetStatus[] = ['ready', 'loading', 'degraded', 'error']
    expect(statuses).toHaveLength(4)
  })

  it('WidgetAction has required fields', () => {
    const action: WidgetAction = { id: 'a1', label: 'Refresh', type: 'refresh' }
    expect(action.id).toBe('a1')
    expect(action.type).toBe('refresh')
  })

  it('DashboardWidget is generic', () => {
    const widget: DashboardWidget<{ value: number }> = {
      id: 'w-1', title: 'Test', status: 'ready', lastUpdated: null, data: { value: 42 }, actions: [],
    }
    expect(widget.data?.value).toBe(42)
  })
})
