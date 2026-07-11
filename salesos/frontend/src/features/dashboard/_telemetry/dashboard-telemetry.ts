type Measure = 'dashboard.load' | 'widget.render' | 'widget.load' | 'widget.error'

interface TelemetryEvent {
  measure: Measure
  widgetId?: string
  durationMs?: number
  error?: string
  timestamp: string
}

const events: TelemetryEvent[] = []

export const dashboardTelemetry = {
  start(measure: Measure, widgetId?: string) {
    if (typeof performance === 'undefined') return { end: () => {} }
    const start = performance.now()
    const label = widgetId ? `${measure}:${widgetId}` : measure
    performance.mark(`${label}:start`)
    return {
      end: (error?: string) => {
        performance.mark(`${label}:end`)
        performance.measure(label, `${label}:start`, `${label}:end`)
        const durationMs = performance.now() - start
        const event: TelemetryEvent = {
          measure,
          widgetId,
          durationMs: Math.round(durationMs),
          error,
          timestamp: new Date().toISOString(),
        }
        events.push(event)
        if (events.length > 100) events.shift()
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('dashboard:telemetry', { detail: event }))
        }
      },
    }
  },

  error(widgetId: string, error: string) {
    const event: TelemetryEvent = {
      measure: 'widget.error',
      widgetId,
      error,
      timestamp: new Date().toISOString(),
    }
    events.push(event)
    if (events.length > 100) events.shift()
  },

  getAll(): TelemetryEvent[] {
    return [...events]
  },
}
