'use client'

import { cn } from '@salesos/ui'
import { FileText, Sparkles } from 'lucide-react'
import type { DocumentIntelligenceViewProps } from './types'

const TYPE_L = { contract: 'عقد', pdf: 'PDF', government: 'حكومي', report: 'تقرير', legal: 'قانوني' }

export function DocumentIntelligenceView({ documents }: DocumentIntelligenceViewProps) {
  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <FileText className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد مستندات</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="المستندات" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      {documents.map((doc) => (
        <div key={doc.id} className="rounded-lg px-3 py-2 transition hover:bg-[var(--bg-tertiary)]">
          <div className="flex items-start gap-2.5">
            <FileText className="mt-0.5 h-4 w-4 shrink-0 text-[var(--text-muted)]" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-xs font-medium text-[var(--text-primary)]">{doc.title}</span>
                <span className="shrink-0 rounded bg-[var(--bg-tertiary)] px-1 py-0.5 text-[9px] text-[var(--text-muted)] dark:bg-neutral-800">
                  {TYPE_L[doc.type] ?? doc.type}
                </span>
              </div>
              {doc.aiSummary && (
                <div className="mt-0.5 flex items-start gap-1">
                  <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-purple-500" />
                  <p className="text-[10px] text-purple-600 dark:text-purple-400 line-clamp-2">{doc.aiSummary}</p>
                </div>
              )}
              <div className="mt-0.5 flex items-center gap-2 text-[9px] text-[var(--text-muted)]">
                <span>{new Date(doc.date).toLocaleDateString('ar-SA')}</span>
                <span>%{Math.round(doc.confidence * 100)}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
