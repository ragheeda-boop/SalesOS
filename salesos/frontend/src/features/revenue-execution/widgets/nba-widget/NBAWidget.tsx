"use client"

import { useEffect, useState } from "react"
import { useNBA, type NBARecommendation } from "./useNBA"
import { RecommendationCard } from "./RecommendationCard"

interface NBAWidgetProps {
  opportunityId: string
}

export function NBAWidget({ opportunityId }: NBAWidgetProps) {
  const [recommendation, setRecommendation] = useState<NBARecommendation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const { getNBA, refreshNBA, acceptNBA, dismissNBA } = useNBA(opportunityId)

  const load = async () => {
    setLoading(true)
    setError(false)
    try {
      const nba = await getNBA()
      setRecommendation(nba)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [opportunityId])

  const handleAccept = async () => {
    if (!recommendation) return
    await acceptNBA(recommendation.id)
    setRecommendation((prev) => prev ? { ...prev, status: 'accepted' } : null)
  }

  const handleDismiss = async () => {
    if (!recommendation) return
    await dismissNBA(recommendation.id)
    setRecommendation(null)
  }

  const handleRefresh = async () => {
    setLoading(true)
    const nba = await refreshNBA()
    setRecommendation(nba)
    setLoading(false)
  }

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
        <button onClick={load} className="text-sm text-[var(--muhide-orange)] hover:underline">حاول مرة أخرى</button>
      </div>
    )
  }

  if (!recommendation) {
    return (
      <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 text-center">
        <p className="text-sm text-[var(--text-muted)]">لا توجد توصيات متاحة حاليًا</p>
        <button onClick={handleRefresh} className="text-sm text-[var(--muhide-orange)] hover:underline mt-1">تحديث</button>
      </div>
    )
  }

  return (
    <RecommendationCard
      recommendation={recommendation}
      onAccept={handleAccept}
      onDismiss={handleDismiss}
      onRefresh={handleRefresh}
    />
  )
}
