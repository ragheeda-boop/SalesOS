import { widgetTelemetry } from '../widget-telemetry'

export class TelemetrySpy {
  private events: ReturnType<typeof widgetTelemetry.getAll> = []

  start() {
    this.events = widgetTelemetry.getAll()
  }

  eventsOf(type: string): ReturnType<typeof widgetTelemetry.getAll> {
    return this.events.filter((e) => e.type === type)
  }

  has(type: string, widgetId?: string): boolean {
    return this.events.some((e) => {
      if (e.type !== type) return false
      if (widgetId !== undefined && e.widgetId !== widgetId) return false
      return true
    })
  }

  count(type: string): number {
    return this.events.filter((e) => e.type === type).length
  }

  clear(): void {
    this.events = []
  }
}

export function createTelemetrySpy(): TelemetrySpy {
  return new TelemetrySpy()
}
