'use client'

import { useCallback } from 'react'
import { cn, Badge } from '@salesos/ui'
import type { MissionActionProps } from './types'

const PRIORITY_CONFIG = {
  high: { label: 'عاجل', variant: 'danger' as const },
  medium: { label: 'متوسط', variant: 'warning' as const },
  low: { label: 'عادي', variant: 'default' as const },
}

export function MissionAction({ id, title, priority, companyName, dueBy, onAction }: MissionActionProps) {
  const config = PRIORITY_CONFIG[priority]
  const clickable = !!onAction

  const handleActivate = useCallback(() => {
    onAction?.(id)
  }, [id, onAction])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onAction?.(id)
    }
  }, [id, onAction])

  return (
    <div
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      aria-label={`${title}${companyName ? ` - ${companyName}` : ''} - أولوية ${config.label}`}
      aria-disabled={!clickable}
      className={cn(
        'flex items-center justify-between rounded-lg px-3 py-2 text-sm',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--muhide-orange)] focus-visible:ring-offset-1',
        clickable && 'cursor-pointer transition motion-reduce:transition-none',
        priority === 'high' ? 'bg-danger-50 hover:bg-danger-100 dark:bg-danger-900/20 dark:hover:bg-danger-900/30' :
        priority === 'medium' ? 'bg-warning-50 hover:bg-warning-100 dark:bg-warning-900/20 dark:hover:bg-warning-900/30' :
        'bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)]',
      )}
      onClick={clickable ? handleActivate : undefined}
      onKeyDown={clickable ? handleKeyDown : undefined}
    >
      <div className="flex items-center gap-2 min-w-0">
        <Badge variant={config.variant} className="shrink-0">{config.label}</Badge>
        <span className="truncate font-medium text-[var(--text-primary)]">{title}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {companyName && <span className="text-xs text-[var(--text-muted)] truncate max-w-[120px]">{companyName}</span>}
        {dueBy && <span className="text-[10px] text-[var(--text-muted)]" aria-label={`مستحق ${dueBy}`}>{dueBy}</span>}
      </div>
    </div>
  )
}
