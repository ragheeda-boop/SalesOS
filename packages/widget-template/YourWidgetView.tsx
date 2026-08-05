'use client'

import { useCallback } from 'react'
import { cn } from '@salesos/ui'
import type { YourWidgetViewProps, YourWidgetItem } from './types'

function YourWidgetItemRow({ item }: { item: YourWidgetItem }) {
  return (
    <div
      className="flex items-center justify-between rounded-lg px-3 py-2 text-sm"
      aria-label={`${item.label}: ${item.value}`}
    >
      <span className="truncate text-[var(--text-primary)]">{item.label}</span>
      <span className="shrink-0 font-medium text-[var(--text-secondary)]">{item.value}</span>
    </div>
  )
}

export function YourWidgetView({ count, items, isLoading }: YourWidgetViewProps) {
  if (isLoading) {
    return (
      <div role="status" aria-label="Loading" className="flex items-center justify-center py-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--muhide-orange)]" />
      </div>
    )
  }

  if (!items || items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <p className="text-sm text-[var(--text-muted)]">لا توجد عناصر بعد</p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">ستظهر العناصر هنا عند توفرها</p>
      </div>
    )
  }

  return (
    <div
      role="region"
      aria-label="Your Widget Dashboard"
      className="space-y-1"
    >
      <div
        aria-live="polite"
        aria-atomic="true"
        className="mb-3 text-xs font-medium text-[var(--text-muted)]"
      >
        {count} عنصر
      </div>
      <div role="list" aria-label="Widget items" className="space-y-1">
        {items.map((item) => (
          <div key={item.id} role="listitem">
            <YourWidgetItemRow item={item} />
          </div>
        ))}
      </div>
    </div>
  )
}
