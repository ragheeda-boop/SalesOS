'use client'

import { cn } from '@salesos/ui'
import { Code, Activity, Clock, AlertTriangle, BarChart3 } from 'lucide-react'
import type { APIData } from './types'

const METH_C: Record<string, string> = { GET: 'text-green-600', POST: 'text-blue-600', PUT: 'text-amber-600', DELETE: 'text-red-600' }

export function APIView({ data }: { data: APIData }) {
  return (
    <div role="region" aria-label="منصة API" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="grid grid-cols-4 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]"><Code className="h-3 w-3 inline" /> الـ endpoints</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{data.totalEndpoints}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]"><Activity className="h-3 w-3 inline" /> الاستدعاءات</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{data.totalCalls.toLocaleString()}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]"><Clock className="h-3 w-3 inline" /> الزمن</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{data.avgLatency}ms</p>
        </div>
        <div className={cn('rounded-lg p-2', data.errorRate > 5 ? 'bg-red-50 dark:bg-red-900/10' : 'bg-[var(--bg-tertiary)] dark:bg-neutral-800')}>
          <p className="text-[9px] text-[var(--text-muted)]"><AlertTriangle className="h-3 w-3 inline" /> الأخطاء</p>
          <p className="text-sm font-bold text-red-600">%{data.errorRate}</p>
        </div>
      </div>
      {data.endpoints.map((ep, i) => (
        <div key={i} className="flex items-center gap-2 rounded-lg px-3 py-1.5 transition hover:bg-[var(--bg-tertiary)]">
          <span className={cn('w-12 text-[9px] font-mono font-bold', METH_C[ep.method] ?? 'text-neutral-500')}>{ep.method}</span>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-mono text-[var(--text-primary)] truncate">{ep.path}</p>
            <p className="text-[8px] text-[var(--text-muted)]">{ep.description}</p>
          </div>
          <div className="text-right">
            <p className="text-[9px] text-[var(--text-muted)]">{ep.calls.toLocaleString()}</p>
            <p className="text-[8px] text-[var(--text-muted)]">{ep.avgLatency}ms</p>
          </div>
        </div>
      ))}
    </div>
  )
}
