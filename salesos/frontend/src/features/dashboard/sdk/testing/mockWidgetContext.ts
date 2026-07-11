import type { WidgetStatus, WidgetData } from '../types'

export function createMockWidget<T>(defaultData: T): {
  ready: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
  loading: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
  degraded: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
  error: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
} {
  const base = (status: WidgetStatus): WidgetData<T> => ({
    data: null,
    status,
    lastUpdated: null,
    error: null,
    refetch: jest.fn(),
  })

  return {
    ready: (overrides) => ({
      ...base('ready'),
      data: defaultData,
      lastUpdated: '2026-07-10T00:00:00.000Z',
      ...overrides,
    }),
    loading: (overrides) => ({
      ...base('loading'),
      ...overrides,
    }),
    degraded: (overrides) => ({
      ...base('degraded'),
      data: defaultData,
      ...overrides,
    }),
    error: (overrides) => ({
      ...base('error'),
      error: new Error('Test error'),
      ...overrides,
    }),
  }
}

export function createEmptyWidget<T>(): WidgetData<T> {
  return {
    data: null,
    status: 'ready',
    lastUpdated: null,
    error: null,
    refetch: jest.fn(),
  }
}
