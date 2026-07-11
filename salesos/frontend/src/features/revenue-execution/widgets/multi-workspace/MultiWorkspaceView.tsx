'use client'

import { cn } from '@salesos/ui'
import { LayoutDashboard, Building2, Users, Target, ChevronRight } from 'lucide-react'
import type { WorkspaceData } from './types'

const WS_ICON: Record<string, React.ReactNode> = { dashboard: <LayoutDashboard className="h-4 w-4" />, company: <Building2 className="h-4 w-4" />, employee: <Users className="h-4 w-4" />, crm: <Target className="h-4 w-4" /> }

export function MultiWorkspaceView({ data }: { data: WorkspaceData }) {
  return (
    <div role="region" aria-label="مساحات العمل" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="flex items-center justify-between px-1 py-1">
        <span className="text-[10px] font-medium text-[var(--text-muted)]">{data.active} نشطة من {data.total}</span>
      </div>
      {data.workspaces.map((ws) => (
        <div key={ws.id} className={cn('flex items-center gap-2.5 rounded-lg px-3 py-2 transition cursor-pointer hover:bg-[var(--bg-tertiary)]', ws.active && 'bg-primary-50/50 dark:bg-primary-900/10')}>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-tertiary)] dark:bg-neutral-800">
            {WS_ICON[ws.type] ?? <LayoutDashboard className="h-4 w-4 text-[var(--text-muted)]" />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-[var(--text-primary)]">{ws.name}</span>
              {ws.active && <span className="rounded-full bg-green-100 px-1.5 py-0.5 text-[8px] font-medium text-green-700 dark:bg-green-900/30 dark:text-green-300">نشط</span>}
            </div>
            <p className="text-[9px] text-[var(--text-muted)]">آخر زيارة: {new Date(ws.lastAccessed).toLocaleDateString('ar-SA')}</p>
          </div>
          <ChevronRight className="h-4 w-4 shrink-0 text-[var(--text-muted)]" />
        </div>
      ))}
    </div>
  )
}
