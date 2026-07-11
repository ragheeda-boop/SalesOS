"use client"

import { Sparkles, ThumbsUp, ThumbsDown } from "lucide-react"

interface NBAAcceptanceWidgetProps {
  nba_views: number
  nba_accepts: number
  nba_rejects: number
  acceptance_rate: number
}

export function NBAAcceptanceWidget({ nba_views, nba_accepts, nba_rejects, acceptance_rate }: NBAAcceptanceWidgetProps) {
  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="h-4 w-4 text-[var(--text-muted)]" />
        <p className="text-xs text-[var(--text-muted)]">قبول NBA</p>
      </div>
      <p className="text-lg font-bold">{nba_views}</p>
      <p className="text-[10px] text-[var(--text-muted)]">إجمالي المشاهدات</p>
      <div className="flex items-center gap-3 mt-2 text-xs">
        <span className="flex items-center gap-1 text-green-600">
          <ThumbsUp className="h-3 w-3" /> {nba_accepts}
        </span>
        <span className="flex items-center gap-1 text-red-600">
          <ThumbsDown className="h-3 w-3" /> {nba_rejects}
        </span>
      </div>
      <div className="mt-2 h-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-green-500 rounded-full transition-all"
          style={{ width: `${acceptance_rate}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-[var(--text-muted)]">معدل القبول: {acceptance_rate.toFixed(0)}%</p>
    </div>
  )
}
