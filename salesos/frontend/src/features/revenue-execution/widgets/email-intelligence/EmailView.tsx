'use client'

import { cn } from '@salesos/ui'
import { Mail, Sparkles, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react'
import type { EmailViewProps } from './types'

const PRIORITY_S = { high: 'text-red-500', medium: 'text-amber-500', low: 'text-green-500' }
const PRIORITY_L = { high: 'عالي', medium: 'متوسط', low: 'منخفض' }

export function EmailView({ emails }: EmailViewProps) {
  if (emails.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Mail className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد رسائل بريد</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="ذكاء البريد" className="space-y-1.5 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {emails.map((email) => (
        <div key={email.threadId} className="rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]">
          <div className="flex items-start gap-2">
            <Mail className="mt-0.5 h-4 w-4 shrink-0 text-[var(--text-muted)]" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-xs font-medium text-[var(--text-primary)]">{email.subject}</span>
                <span className={cn('mr-auto text-[9px] font-medium', PRIORITY_S[email.priority])}>{PRIORITY_L[email.priority]}</span>
              </div>
              <p className="mt-0.5 text-[10px] text-[var(--text-muted)]">{email.sender} · {new Date(email.date).toLocaleDateString('ar-SA')}</p>
              <div className="mt-1 flex items-start gap-1">
                <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-purple-500" />
                <p className="text-[10px] text-purple-600 dark:text-purple-400">{email.summary}</p>
              </div>
              {email.suggestedReply && (
                <div className="mt-1 flex items-start gap-1 rounded-lg bg-[var(--bg-tertiary)] p-1.5 dark:bg-neutral-800">
                  <ArrowRight className="mt-0.5 h-3 w-3 shrink-0 text-[var(--text-muted)]" />
                  <p className="text-[9px] text-[var(--text-muted)]">{email.suggestedReply}</p>
                </div>
              )}
              {email.actionItems.length > 0 && (
                <div className="mt-1 space-y-0.5">
                  {email.actionItems.map((item, i) => (
                    <div key={i} className="flex items-start gap-1">
                      <CheckCircle className="mt-0.5 h-2.5 w-2.5 shrink-0 text-green-500" />
                      <span className="text-[9px] text-[var(--text-muted)]">{item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
