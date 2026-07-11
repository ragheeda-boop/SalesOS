'use client'

import { useCallback } from 'react'
import { cn } from '@salesos/ui'
import type { RecentActivityViewProps } from './types'

const ACTIVITY_ICON: Record<string, string> = {
  signal: '📡',
  decision: '⚡',
  update: '🔄',
  note: '📝',
}

const TYPE_LABEL: Record<string, string> = {
  signal: 'إشارة',
  decision: 'قرار',
  update: 'تحديث',
  note: 'ملاحظة',
}

function ActivityRow({
  item,
  onItemClick,
}: {
  item: RecentActivityViewProps['items'][number]
  onItemClick?: (id: string) => void
}) {
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
        onItemClick && 'cursor-pointer hover:bg-[var(--bg-tertiary)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${item.title}${item.companyName ? ` - ${item.companyName}` : ''} - ${TYPE_LABEL[item.type] ?? item.type}`}
    >
      <span className="shrink-0 text-base" aria-hidden="true">{ACTIVITY_ICON[item.type] ?? '•'}</span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium text-[var(--text-primary)]">{item.title}</span>
          <span className="shrink-0 rounded-full bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-muted)]">
            {TYPE_LABEL[item.type] ?? item.type}
          </span>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-[var(--text-muted)]">
          {item.companyName && <span>{item.companyName}</span>}
          {item.timestamp && (
            <span>· {new Date(item.timestamp).toLocaleDateString('ar-SA')}</span>
          )}
        </div>
      </div>
    </div>
  )
}

export function RecentActivityView({ items, total, onItemClick }: RecentActivityViewProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <span className="text-2xl" aria-hidden="true">📭</span>
        <p className="mt-2 text-sm text-[var(--text-muted)]">لا توجد نشاطات حديثة</p>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">سيتم عرض النشاطات الجديدة هنا فور ظهورها</p>
      </div>
    )
  }

  const displayed = items.slice(0, 10)

  return (
    <div role="region" aria-label="النشاطات الحديثة" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {total > displayed.length && (
        <div className="px-1 pb-1 text-[10px] font-medium text-[var(--text-muted)]">
          {displayed.length} من أصل {total} نشاط
        </div>
      )}
      <div role="list" aria-live="polite">
        {displayed.map((item) => (
          <div key={item.id} role="listitem">
            <ActivityRow item={item} onItemClick={onItemClick} />
          </div>
        ))}
      </div>
    </div>
  )
}
