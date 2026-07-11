export type SearchTelemetryEventType =
  | 'search.query'
  | 'search.result_click'
  | 'search.ai_answer'
  | 'search.command_bar_open'
  | 'search.fallback'
  | 'search.error'
  | 'search.suggestion_click'
  | 'search.filter_change'
  | 'search.page_change'

export interface SearchTelemetryEvent {
  type: SearchTelemetryEventType
  query?: string
  resultId?: string
  entityType?: string
  position?: number
  durationMs?: number
  resultCount?: number
  error?: string
  timestamp: string
  metadata?: Record<string, unknown>
}

const log: SearchTelemetryEvent[] = []

function emit(event: SearchTelemetryEvent) {
  log.push(event)
  if (log.length > 200) log.shift()
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('search:telemetry', { detail: event }))
  }
}

export function createTelemetryTimer() {
  if (typeof performance === 'undefined') return { stop: () => {} }
  const start = performance.now()
  return {
    stop: (type: SearchTelemetryEventType, extra?: Partial<SearchTelemetryEvent>) => {
      const durationMs = Math.round(performance.now() - start)
      emit({ type, durationMs, timestamp: new Date().toISOString(), ...extra })
    },
  }
}

export const searchTelemetry = {
  record(type: SearchTelemetryEventType, extra?: Partial<SearchTelemetryEvent>) {
    emit({ type, timestamp: new Date().toISOString(), ...extra })
  },

  startQuery(query: string) {
    const timer = createTelemetryTimer()
    return {
      end: (resultCount: number, extra?: Partial<SearchTelemetryEvent>) => {
        timer.stop('search.query', { query, resultCount, ...extra })
      },
    }
  },

  click(resultId: string, entityType: string, position: number, query?: string) {
    emit({
      type: 'search.result_click',
      resultId,
      entityType,
      position,
      query,
      timestamp: new Date().toISOString(),
    })
  },

  aiAnswer(durationMs: number, extra?: Partial<SearchTelemetryEvent>) {
    emit({ type: 'search.ai_answer', durationMs, timestamp: new Date().toISOString(), ...extra })
  },

  error(error: string, query?: string) {
    emit({ type: 'search.error', error, query, timestamp: new Date().toISOString() })
  },

  getAll(): SearchTelemetryEvent[] {
    return [...log]
  },
}
