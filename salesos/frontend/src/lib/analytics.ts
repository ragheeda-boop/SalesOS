'use client'

import { useEffect, useCallback, useRef } from 'react'

type EventType =
  | 'widget.rendered' | 'widget.interacted'
  | 'nba.viewed' | 'nba.executed'
  | 'opportunity.created' | 'opportunity.stage_changed'
  | 'search.performed' | 'search.result_clicked'
  | 'company.viewed' | 'company.dna_viewed'
  | 'pilot.feedback_submitted' | 'pilot.session_started'

interface AnalyticsEvent {
  type: EventType
  userId?: string
  companyId?: string
  widgetId?: string
  metadata?: Record<string, unknown>
  timestamp: string
}

const queue: AnalyticsEvent[] = []

function flush() {
  if (queue.length === 0) return
  const batch = queue.splice(0, queue.length)
  if (typeof window !== 'undefined') {
    navigator.sendBeacon?.('/api/v1/analytics/events', JSON.stringify({ events: batch }))
  }
}

let _interval: ReturnType<typeof setInterval> | null = null

function ensureInterval() {
  if (_interval) clearInterval(_interval)
  _interval = setInterval(flush, 10_000)
}

export function track(event: Omit<AnalyticsEvent, 'timestamp'>) {
  ensureInterval()
  queue.push({ ...event, timestamp: new Date().toISOString() })
  if (queue.length >= 50) flush()
}

export function usePageTracking(pageName: string) {
  useEffect(() => {
    track({ type: 'pilot.session_started', metadata: { page: pageName } })
  }, [pageName])
}

export function useWidgetTracking(widgetId: string) {
  const tracked = useRef(false)
  useEffect(() => {
    if (!tracked.current) {
      tracked.current = true
      track({ type: 'widget.rendered', widgetId })
    }
  }, [widgetId])

  const interact = useCallback((action: string, metadata?: Record<string, unknown>) => {
    track({ type: 'widget.interacted', widgetId, metadata: { action, ...metadata } })
  }, [widgetId])

  return { interact }
}
