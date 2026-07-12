'use client'

/// <reference types="web" />

export interface MonitoringEvent {
  type: 'api_call' | 'error' | 'render' | 'metric' | 'page_load' | 'web_vital'
  timestamp: string
  method?: string
  path?: string
  duration_ms?: number
  status?: number
  error_message?: string
  error_stack?: string
  context?: string
  component_name?: string
  name?: string
  value?: number
  tags?: Record<string, string>
  route?: string
  fcp?: number
  lcp?: number
  fid?: number
  cls?: number
  memory_used_mb?: number
  dom_interactive?: number
  dom_complete?: number
}

const FLUSH_INTERVAL = 60_000
const FLUSH_THRESHOLD = 100
const API_ENDPOINT = '/api/v1/monitoring/events'

export class Monitor {
  private enabled: boolean
  private buffer: MonitoringEvent[] = []
  private flushTimer: ReturnType<typeof setInterval> | null = null
  private debugMode: boolean

  constructor(debug = false) {
    this.enabled = process.env.NODE_ENV === 'production'
    this.debugMode = debug
    if (typeof window !== 'undefined' && this.enabled) {
      this.flushTimer = setInterval(() => this.flush(), FLUSH_INTERVAL)
    }
  }

  enable(): void {
    this.enabled = true
    if (typeof window !== 'undefined' && !this.flushTimer) {
      this.flushTimer = setInterval(() => this.flush(), FLUSH_INTERVAL)
    }
  }

  disable(): void {
    this.enabled = false
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
      this.flushTimer = null
    }
  }

  trackApiCall(method: string, path: string, durationMs: number, status: number): void {
    if (!this.enabled) return
    this.push({
      type: 'api_call',
      method,
      path,
      duration_ms: Math.round(durationMs),
      status,
    })
  }

  trackError(error: Error, context?: string): void {
    if (!this.enabled) return
    this.push({
      type: 'error',
      error_message: error.message,
      error_stack: error.stack,
      context,
    })
  }

  trackRender(componentName: string, durationMs: number): void {
    if (!this.enabled) return
    this.push({
      type: 'render',
      component_name: componentName,
      duration_ms: Math.round(durationMs),
    })
  }

  trackMetric(name: string, value: number, tags?: Record<string, string>): void {
    if (!this.enabled) return
    this.push({
      type: 'metric',
      name,
      value,
      tags,
    })
  }

  trackPageLoad(): void {
    if (!this.enabled || typeof window === 'undefined') return
    const perf = window.performance
    if (!perf) return
    const nav = perf.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
    const perfWithMemory = performance as Performance & { memory?: { usedJSHeapSize: number } }
    const mem = perfWithMemory.memory
    if (nav) {
      this.push({
        type: 'page_load',
        route: window.location.pathname,
        duration_ms: Math.round(nav.loadEventEnd - nav.startTime),
        dom_interactive: Math.round(nav.domInteractive - nav.startTime),
        dom_complete: Math.round(nav.domComplete - nav.startTime),
        fcp: Math.round(nav.domContentLoadedEventEnd - nav.startTime),
        memory_used_mb: mem ? Math.round(mem.usedJSHeapSize / 1024 / 1024) : undefined,
      })
    }
  }

  private push(event: Omit<MonitoringEvent, 'timestamp'>): void {
    const full: MonitoringEvent = { ...event, timestamp: new Date().toISOString() }
    this.buffer.push(full)
    if (this.debugMode) {
      console.debug('[Monitor]', full.type, full)
    }
    if (this.buffer.length >= FLUSH_THRESHOLD) {
      this.flush()
    }
  }

  flush(): void {
    if (this.buffer.length === 0) return
    const batch = this.buffer.splice(0, this.buffer.length)
    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      navigator.sendBeacon(API_ENDPOINT, JSON.stringify({ events: batch }))
      return
    }
    fetch(API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: batch }),
      keepalive: true,
    }).catch(() => {})
  }
}

export const monitor = new Monitor()
