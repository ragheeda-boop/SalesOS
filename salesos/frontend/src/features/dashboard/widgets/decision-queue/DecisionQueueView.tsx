'use client'

import { useCallback } from 'react'
import { cn } from '@salesos/ui'
import type { DecisionQueueViewProps } from './types'

const PRIORITY_CONFIG = {
  high: { dot: 'bg-danger-500', label: 'عاجل', ring: 'focus-visible:ring-danger-500', bg: 'bg-danger-50/50 dark:bg-danger-900/10' },
  medium: { dot: 'bg-warning-500', label: 'متوسط', ring: 'focus-visible:ring-warning-500', bg: 'bg-warning-50/50 dark:bg-warning-900/10' },
  low: { dot: 'bg-neutral-400', label: 'عادي', ring: 'focus-visible:ring-neutral-400', bg: '' },
} as const

const TYPE_LABEL: Record<string, string> = {
  opportunity: 'فرصة',
  risk: 'مخاطرة',
  recommendation: 'توصية',
}

function DecisionRow({
  item,
  onItemClick,
}: {
  item: DecisionQueueViewProps['items'][number]
  onItemClick?: (id: string) => void
}) {
  const conf = PRIORITY_CONFIG[item.priority]
  const handleClick = useCallback(() => onItemClick?.(item.id), [item.id, onItemClick])
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (onItemClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      onItemClick(item.id)
    }
  }, [item.id, onItemClick])

  return (
    <div
      role={onItemClick ? 'button' : undefined}
      tabIndex={onItemClick ? 0 : undefined}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors motion-reduce:transition-none',
        conf.bg,
        onItemClick && 'cursor-pointer hover:bg-[var(--bg-tertiary)]',
        conf.ring,
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${item.title} - ${item.companyName} - ${conf.label}`}
    >
      <span className={cn('mt-0.5 h-2 w-2 shrink-0 rounded-full', conf.dot)} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium text-[var(--text-primary)]">{item.title}</span>
          <span className="shrink-0 rounded-full bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-muted)]">
            {TYPE_LABEL[item.type] ?? item.type}
          </span>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <span>{item.companyName}</span>
          {item.score > 0 && <span>· AI {item.score}%</span>}
          {item.dueBy && <span>· مستحق {new Date(item.dueBy).toLocaleDateString('ar-SA')}</span>}
        </div>
      </div>
      <span className={cn('shrink-0 text-[10px] font-medium', conf.dot.replace('bg-', 'text-').replace('-500', '-600'))}>
        {conf.label}
      </span>
    </div>
  )
}

export function DecisionQueueView({ items, total, onItemClick }: DecisionQueueViewProps) {
  const priorityOrder = { high: 0, medium: 1, low: 2 }
  const sorted = [...items].sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority])

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-2xl" aria-hidden="true">✅</span>
        <p className="mt-2 text-sm text-[var(--text-muted)]">لا توجد قرارات معلقة</p>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">سيتم عرض القرارات التي تحتاج اهتمامك هنا</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="قرارات معلقة" className="space-y-1">
      {total > items.length && (
        <div className="px-1 pb-1 text-[10px] font-medium text-[var(--text-muted)]">
          {items.length} من أصل {total} قرار
        </div>
      )}
      {sorted.map((item) => (
        <DecisionRow key={item.id} item={item} onItemClick={onItemClick} />
      ))}
    </div>
  )
}
