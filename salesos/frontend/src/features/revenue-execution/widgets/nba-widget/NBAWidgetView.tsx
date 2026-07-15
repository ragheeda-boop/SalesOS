"use client"

import { cn } from "@salesos/ui"
import { RecommendationCard } from "./RecommendationCard"
import type { NBARecommendation } from "./useNBA"

interface NBAWidgetViewProps {
  recommendation: NBARecommendation | null
  loading: boolean
  error: boolean
  onAccept: () => void
  onDismiss: () => void
  onRefresh: () => void
  onRetry: () => void
}

export function NBAWidgetView({ recommendation, loading, error, onAccept, onDismiss, onRefresh, onRetry }: NBAWidgetViewProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4" role="status" aria-label="Loading recommendation">
        <div className="space-y-3 animate-pulse">
          <div className="h-4 w-24 bg-neutral-200 rounded" />
          <div className="h-10 w-full bg-neutral-200 rounded" />
          <div className="h-3 w-3/4 bg-neutral-200 rounded" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 text-center">
        <p className="text-sm text-[var(--text-muted)] mb-2">تعذر تحميل التوصية</p>
        <button onClick={onRetry} className="text-sm text-[var(--muhide-orange)] hover:underline">حاول مرة أخرى</button>
      </div>
    )
  }

  if (!recommendation) {
    return (
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 text-center">
        <p className="text-sm text-[var(--text-muted)]">لا توجد توصيات متاحة حاليًا</p>
        <button onClick={onRefresh} className="text-sm text-[var(--muhide-orange)] hover:underline mt-1">تحديث</button>
      </div>
    )
  }

  return (
    <RecommendationCard
      recommendation={recommendation}
      onAccept={onAccept}
      onDismiss={onDismiss}
      onRefresh={onRefresh}
    />
  )
}
