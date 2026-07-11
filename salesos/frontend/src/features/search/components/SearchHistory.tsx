'use client'

import { cn } from '@salesos/ui'
import { Clock, Trash2 } from 'lucide-react'
import type { SearchHistoryEntry } from '@salesos/search'

interface SearchHistoryProps {
  entries: SearchHistoryEntry[]
  onClick: (entry: SearchHistoryEntry) => void
  onClear?: () => void
  className?: string
}

export function SearchHistory({ entries, onClick, onClear, className }: SearchHistoryProps) {
  if (entries.length === 0) return null

  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center justify-between px-4 py-2">
        <span className="text-xs font-semibold text-[var(--text-muted)] uppercase">آخر البحوث</span>
        {onClear && (
          <button onClick={onClear} aria-label="مسح سجل البحث" className="text-[10px] text-[var(--text-muted)] hover:text-red-500">
            <Trash2 className="h-3 w-3" />
          </button>
        )}
      </div>
      {entries.slice(0, 5).map((entry) => (
        <button
          key={entry.id}
          className="flex w-full items-center gap-3 px-4 py-2 text-sm transition hover:bg-[var(--bg-tertiary)]"
          onClick={() => onClick(entry)}
        >
          <Clock className="h-3.5 w-3.5 text-[var(--text-muted)]" />
          <span className="text-[var(--text-primary)]">{entry.text}</span>
          {entry.resultCount !== undefined && (
            <span className="mr-auto text-[10px] text-[var(--text-muted)]">{entry.resultCount} نتيجة</span>
          )}
        </button>
      ))}
    </div>
  )
}
