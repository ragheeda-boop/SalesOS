"use client"

import { cn } from "@salesos/ui"
import { HeartPulse, TrendingUp, TrendingDown } from "lucide-react"

interface HealthScoreCardProps {
  score: number
  label: string
  thresholds: { green: number; yellow: number }
}

export function HealthScoreCard({ score, label, thresholds }: HealthScoreCardProps) {
  const color = score >= thresholds.green
    ? "text-green-600"
    : score >= thresholds.yellow
      ? "text-yellow-600"
      : "text-red-600"

  const bgColor = score >= thresholds.green
    ? "bg-green-50 border-green-200"
    : score >= thresholds.yellow
      ? "bg-yellow-50 border-yellow-200"
      : "bg-red-50 border-red-200"

  return (
    <div className={cn("rounded-xl border p-4", bgColor)}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-[var(--text-muted)]">{label}</p>
        <HeartPulse className={cn("h-5 w-5", color)} />
      </div>
      <p className={cn("text-2xl font-display font-bold", color)}>{score.toFixed(0)}%</p>
      <div className="flex items-center gap-1 mt-1">
        {score >= thresholds.green ? (
          <TrendingUp className="h-3 w-3 text-green-500" />
        ) : (
          <TrendingDown className="h-3 w-3 text-red-500" />
        )}
        <span className="text-xs text-[var(--text-muted)]">
          {score >= thresholds.green ? "جيد" : score >= thresholds.yellow ? "بحاجة للتحسين" : "حرج"}
        </span>
      </div>
    </div>
  )
}
