'use client'

import { cn } from '@salesos/ui'
import { Shield, CheckCircle, XCircle, Users, Key, FileText, Activity } from 'lucide-react'
import type { SecurityData } from './types'

export function SecurityView({ data }: { data: SecurityData }) {
  const features = [
    { label: 'SSO', enabled: data.ssoEnabled }, { label: 'RBAC', enabled: data.rbacEnabled },
    { label: 'Audit', enabled: data.auditEnabled }, { label: 'MFA', enabled: data.mfaEnabled },
  ]
  return (
    <div role="region" aria-label="الأمان" className="space-y-2 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="flex gap-1.5">
        {features.map((f) => (
          <div key={f.label} className={cn('flex items-center gap-1 rounded-lg px-2 py-1 text-[9px] font-medium', f.enabled ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300' : 'bg-neutral-100 text-neutral-400 dark:bg-neutral-800')}>
            {f.enabled ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
            {f.label}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-2">
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]"><Users className="h-3 w-3 inline" /> المستخدمون</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{data.activeUsers}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]"><Key className="h-3 w-3 inline" /> الأدوار</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{data.roles}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[9px] text-[var(--text-muted)]"><FileText className="h-3 w-3 inline" /> الأحداث</p>
          <p className="text-sm font-bold text-[var(--text-primary)]">{data.auditEvents.toLocaleString()}</p>
        </div>
        <div className={cn('rounded-lg p-2', data.pendingActions > 0 ? 'bg-amber-50 dark:bg-amber-900/10' : 'bg-[var(--bg-tertiary)] dark:bg-neutral-800')}>
          <p className="text-[9px] text-[var(--text-muted)]">معلق</p>
          <p className="text-sm font-bold text-amber-600">{data.pendingActions}</p>
        </div>
      </div>
      {data.recentAudit.length > 0 && (
        <div>
          <p className="mb-1 text-[9px] font-medium text-[var(--text-muted)]">آخر الأحداث</p>
          {data.recentAudit.slice(0, 3).map((a, i) => (
            <div key={i} className="flex items-center justify-between py-0.5">
              <span className="text-[9px] text-[var(--text-muted)]">{a.action}</span>
              <span className="text-[8px] text-[var(--text-muted)]">{a.user} · {new Date(a.timestamp).toLocaleDateString('ar-SA')}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
