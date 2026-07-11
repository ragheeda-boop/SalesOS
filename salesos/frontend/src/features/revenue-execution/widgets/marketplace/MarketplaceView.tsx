'use client'

import { useState } from 'react'
import { cn } from '@salesos/ui'
import { Package, Download, CheckCircle, Grid, Search } from 'lucide-react'
import type { MarketplaceViewProps } from './types'

export function MarketplaceView({ data }: MarketplaceViewProps) {
  const [filter, setFilter] = useState<'all' | 'installed'>('all')
  const filtered = filter === 'all' ? data.plugins : data.plugins.filter((p) => p.installed)

  return (
    <div role="region" aria-label="المتجر" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {(['all', 'installed'] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)} className={cn('rounded-lg px-2 py-0.5 text-[9px] font-medium', filter === f ? 'bg-primary-500 text-white' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)]')}>
              {f === 'all' ? 'الكل' : 'مثبت'} ({f === 'all' ? data.available : data.installed})
            </button>
          ))}
        </div>
        <span className="text-[9px] text-[var(--text-muted)]">{data.installed}/{data.available} مثبت</span>
      </div>
      {filtered.map((p) => (
        <div key={p.id} className="flex items-start gap-2.5 rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-tertiary)] dark:bg-neutral-800">
            <Package className="h-4 w-4 text-[var(--text-muted)]" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-[var(--text-primary)]">{p.name}</span>
              <span className="text-[9px] text-[var(--text-muted)]">v{p.version}</span>
              {p.installed && <CheckCircle className="h-3 w-3 shrink-0 text-green-500" />}
            </div>
            <p className="text-[10px] text-[var(--text-muted)]">{p.description}</p>
            <span className="text-[8px] text-[var(--text-muted)]">{p.category}</span>
          </div>
          {!p.installed && <Download className="h-4 w-4 shrink-0 text-[var(--text-muted)]" />}
        </div>
      ))}
    </div>
  )
}
