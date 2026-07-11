export interface TelemetryEvent {
  name: string
  value: number
  tags: Record<string, string | number | boolean>
  timestamp: string
}

export class TelemetryCollector {
  private events: TelemetryEvent[] = []

  record(name: string, value: number, tags: Record<string, string | number | boolean> = {}): void {
    this.events.push({ name, value, tags, timestamp: new Date().toISOString() })
  }

  flush(): TelemetryEvent[] {
    const events = [...this.events]
    this.events = []
    return events
  }

  getEvents(): TelemetryEvent[] {
    return [...this.events]
  }

  summary(): Record<string, { count: number; avg: number; min: number; max: number }> {
    const groups: Record<string, number[]> = {}
    for (const e of this.events) {
      if (!groups[e.name]) groups[e.name] = []
      groups[e.name].push(e.value)
    }
    const result: Record<string, { count: number; avg: number; min: number; max: number }> = {}
    for (const [name, values] of Object.entries(groups)) {
      const sum = values.reduce((a, b) => a + b, 0)
      result[name] = {
        count: values.length,
        avg: sum / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
      }
    }
    return result
  }
}

export const telemetry = new TelemetryCollector()
