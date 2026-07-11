'use client'

import { useCallback } from 'react'
import { cn } from '@salesos/ui'
import type { IntelligenceFeedViewProps, SignalItemData } from './types'

const CATEGORY_CONFIG = {
  tender: { dot: 'bg-blue-500', label: 'مناقصة' },
  regulatory: { dot: 'bg-purple-500', label: 'تنظيمي' },
  competitor: { dot: 'bg-red-500', label: 'تنافسي' },
  financial: { dot: 'bg-emerald-500', label: 'مالي' },
  news: { dot: 'bg-amber-500', label: 'أخبار' },
} as const

const SEVERITY_LABEL: Record<string, string> = {
  low: 'منخفض',
  medium: 'متوسط',
  high: 'عالٍ',
  critical: 'حرج',
}

const MAX_VISIBLE = 6

function SignalRow({ signal, onItemClick }: { signal: SignalItemData; onItemClick?: (id: string) => void }) {
  const cat = CATEGORY_CONFIG[signal.category]
  const handleClick = useCallback(() => onItemClick?.(signal.id), [signal.id, onItemClick])
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (onItemClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onItemClick(signal.id)
    }
  }, [signal.id, onItemClick])

  return (
    <div
      role={onItemClick ? 'button' : undefined}
      tabIndex={onItemClick ? 0 : undefined}
      className={cn(
        'flex items-start gap-2 rounded-lg px-3 py-2 text-sm transition-colors motion-reduce:transition-none',
        signal.isUnseen ? 'bg-warning-50 dark:bg-warning-900/10' : 'bg-[var(--bg-secondary)]',
        onItemClick && 'cursor-pointer hover:bg-[var(--bg-tertiary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--muhide-orange)] focus-visible:ring-offset-1',
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${signal.title} - ${signal.companyName} - ${cat.label} - ${SEVERITY_LABEL[signal.severity]}`}
    >
      <span className={cn('mt-1 h-2 w-2 shrink-0 rounded-full', cat.dot)} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium text-[var(--text-primary)]">{signal.title}</div>
        <div className="mt-0.5 truncate text-xs text-[var(--text-muted)]">{signal.companyName}</div>
      </div>
      <span className="shrink-0 text-[10px] text-[var(--text-muted)]">{SEVERITY_LABEL[signal.severity]}</span>
    </div>
  )
}

export function IntelligenceFeedView({ items, total, unseenCount, onItemClick, onShowAll }: IntelligenceFeedViewProps) {
  const visible = items.slice(0, MAX_VISIBLE)
  const remaining = total - MAX_VISIBLE

  return (
    <div role="region" aria-label="Intelligence Feed" className="space-y-2">
      {unseenCount > 0 && (
        <div
          aria-live="polite"
          aria-atomic="true"
          className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-muted)]"
        >
          <span className="inline-flex items-center justify-center rounded-full bg-[var(--muhide-orange)] px-1.5 py-0.5 text-[10px] font-bold text-white">
            {unseenCount}
          </span>
          إشارة جديدة
        </div>
      )}

      {items.length > 0 && (
        <div role="list" aria-label="Intelligence signals" className="space-y-1">
          {visible.map((signal) => (
            <div key={signal.id} role="listitem">
              <SignalRow signal={signal} onItemClick={onItemClick} />
            </div>
          ))}
        </div>
      )}

      {remaining > 0 && (
        <button
          onClick={onShowAll}
          className="w-full rounded-lg py-1.5 text-center text-xs font-medium text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-tertiary)] motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--muhide-orange)]"
          aria-label={`عرض الكل (${total} إشارة)`}
        >
          +{remaining} إشارة أخرى
        </button>
      )}

      {items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <span className="text-xl" aria-hidden="true">📡</span>
          <p className="mt-2 text-sm text-[var(--text-muted)]">لا توجد إشارات جديدة</p>
          <p className="mt-0.5 text-xs text-[var(--text-muted)]">ستظهر الإشارات الذكية هنا عند توفرها</p>
        </div>
      )}
    </div>
  )
}
