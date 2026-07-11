export type TelemetryEventType =
  | 'widget.mounted'
  | 'widget.unmounted'
  | 'widget.loaded'
  | 'widget.failed'
  | 'widget.refreshed'
  | 'widget.hidden'
  | 'widget.render'
  | 'workspace.load'

export interface TelemetryEvent {
  type: TelemetryEventType
  widgetId?: string
  workspaceId?: string
  durationMs?: number
  error?: string
  status?: string
  timestamp: string
}

const log: TelemetryEvent[] = []

function emit(event: TelemetryEvent) {
  log.push(event)
  if (log.length > 200) log.shift()
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('workspace:telemetry', { detail: event }))
  }
}

export const widgetTelemetry = {
  record(type: TelemetryEventType, widgetId: string, extra?: { durationMs?: number; error?: string; status?: string }) {
    emit({ type, widgetId, timestamp: new Date().toISOString(), ...extra })
  },

  startTimer(widgetId: string) {
    if (typeof performance === 'undefined' || typeof performance.mark !== 'function') return { stop: () => {} }
    const label = `widget:${widgetId}`
    performance.mark(`${label}:start`)
    return {
      stop: (eventType: TelemetryEventType, extra?: { error?: string; status?: string }) => {
        performance.mark(`${label}:end`)
        performance.measure(label, `${label}:start`, `${label}:end`)
        const entry = performance.getEntriesByName(label)[0]
        const durationMs = entry ? Math.round(performance.now() - entry.startTime) : 0
        emit({ type: eventType, widgetId, durationMs, timestamp: new Date().toISOString(), ...extra })
        performance.clearMeasures(label)
        performance.clearMarks(`${label}:start`)
        performance.clearMarks(`${label}:end`)
      },
    }
  },

  getAll(): TelemetryEvent[] {
    return [...log]
  },
}
