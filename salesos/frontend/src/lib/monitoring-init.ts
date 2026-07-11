'use client'

import { monitor } from './monitoring'
import api from './api'

let initialized = false

export function initMonitoring(): void {
  if (initialized) return
  if (process.env.NODE_ENV !== 'production') return
  if (typeof window === 'undefined') return
  initialized = true

  const start = performance.now()

  api.interceptors.request.use((config) => {
    const ctx = { start: performance.now() }
    ;(config as any)._monitorStart = ctx
    return config
  })

  api.interceptors.response.use(
    (response) => {
      const ctx = (response.config as any)._monitorStart
      if (ctx) {
        const duration = performance.now() - ctx.start
        monitor.trackApiCall(
          response.config.method?.toUpperCase() || 'GET',
          response.config.url || '',
          duration,
          response.status,
        )
      }
      return response
    },
    (error) => {
      const ctx = (error.config as any)?._monitorStart
      if (ctx && error.config) {
        const duration = performance.now() - ctx.start
        monitor.trackApiCall(
          error.config.method?.toUpperCase() || 'GET',
          error.config.url || '',
          duration,
          error.response?.status || 0,
        )
      }
      if (error instanceof Error) {
        monitor.trackError(error, 'api')
      }
      return Promise.reject(error)
    },
  )

  window.onerror = (_message, _source, _lineno, _colno, error) => {
    if (error) monitor.trackError(error, 'window.onerror')
  }

  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
    monitor.trackError(error, 'unhandledrejection')
  })

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'largest-contentful-paint') {
          monitor.trackMetric('lcp', entry.startTime, { type: 'web_vital' })
        }
        if (entry.entryType === 'first-input') {
          const fiEntry = entry as PerformanceEventTiming
          monitor.trackMetric('fid', fiEntry.processingStart - fiEntry.startTime, { type: 'web_vital' })
        }
      }
    })
    observer.observe({ type: 'largest-contentful-paint', buffered: true })
    observer.observe({ type: 'first-input', buffered: true })
  } catch {}

  if ('PerformanceObserver' in window) {
    try {
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0
        for (const entry of list.getEntries()) {
          const layoutShift = entry as LayoutShift
          if (!layoutShift.hadRecentInput) {
            clsValue += layoutShift.value
          }
        }
        monitor.trackMetric('cls', clsValue, { type: 'web_vital' })
      })
      clsObserver.observe({ type: 'layout-shift', buffered: true })
    } catch {}
  }

  window.addEventListener('load', () => {
    setTimeout(() => {
      monitor.trackPageLoad()
      const bootTime = performance.now() - start
      monitor.trackMetric('app_boot_time', bootTime, { type: 'performance' })
    }, 0)
  })
}
