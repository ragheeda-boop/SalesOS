'use client'

import { useEffect, useId, useRef } from 'react'
import { Sparkles, X } from 'lucide-react'
import { cn } from '@salesos/ui'

export const V3_AI_OPEN_EVENT = 'salesos-v3-open-ai'

export type V3AiOpenDetail = {
 contextLabel?: string
}

type V3AiPopupProps = {
 open: boolean
 onClose: () => void
 contextLabel?: string
}

/**
 * AI lives only in this modal — never as a permanent page rail or tab body.
 * Preview / honesty: not Production GA.
 */
export function V3AiPopup({ open, onClose, contextLabel }: V3AiPopupProps) {
 const titleId = useId()
 const closeRef = useRef<HTMLButtonElement>(null)

 useEffect(() => {
 if (!open) return
 closeRef.current?.focus()
 const onKey = (e: KeyboardEvent) => {
 if (e.key === 'Escape') {
 e.preventDefault()
 onClose()
 }
 }
 window.addEventListener('keydown', onKey)
 const prev = document.body.style.overflow
 document.body.style.overflow = 'hidden'
 return () => {
 window.removeEventListener('keydown', onKey)
 document.body.style.overflow = prev
 }
 }, [open, onClose])

 if (!open) return null

 return (
 <div className="fixed inset-0 z-[var(--z-modal,50)] flex items-end justify-center p-4 sm:items-center">
 <button
 type="button"
 className="absolute inset-0 bg-black/50"
 aria-label="Close AI dialog"
 onClick={onClose}
 />
 <div
 role="dialog"
 aria-modal="true"
 aria-labelledby={titleId}
 className={cn(
 'relative z-10 flex max-h-[min(85vh,640px)] w-full max-w-lg flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-[var(--shadow-card,0_12px_40px_rgba(0,0,0,0.18))]',
 )}
 >
 <header className="flex items-start justify-between gap-3 border-b border-[var(--border-default)] px-4 py-3">
 <div className="min-w-0 space-y-1">
 <div className="flex flex-wrap items-center gap-2">
 <Sparkles className="h-4 w-4 text-[var(--muhide-orange)]" aria-hidden />
 <h2 id={titleId} className="text-sm font-semibold text-[var(--text-primary)]">
 Ask AI
 </h2>
 <span className="rounded-full border border-[var(--border-default)] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)]">
 Preview
 </span>
 </div>
 {contextLabel ? (
 <p className="truncate text-[12px] text-[var(--text-muted)]">Context: {contextLabel}</p>
 ) : (
 <p className="text-[12px] text-[var(--text-muted)]">
 Separate from the workspace layout — AI assists; humans decide.
 </p>
 )}
 </div>
 <button
 ref={closeRef}
 type="button"
 onClick={onClose}
 className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 aria-label="Close"
 >
 <X className="h-4 w-4" aria-hidden />
 </button>
 </header>

 <div className="flex-1 space-y-3 overflow-auto px-4 py-4 text-sm leading-relaxed text-[var(--text-secondary)]">
 <p>
 Copilot stays gated (<code className="font-mono text-[12px]">feature_ai_copilot</code>{' '}
 default off). This dialog does not generate account narratives or take layout space on
 product pages.
 </p>
 <p className="text-[var(--text-muted)]">
 Use Decision Center for evidence-backed decisions. When AI is enabled later, actions with
 side effects will require human approval.
 </p>
 <label className="block space-y-1.5">
 <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--text-muted)]">
 Message
 </span>
 <textarea
 rows={4}
 disabled
 placeholder="AI input disabled in Preview…"
 className="w-full resize-none rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-muted)]"
 />
 </label>
 </div>

 <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--border-default)] px-4 py-3">
 <a
 href="/decisions"
 className="text-[12px] font-medium text-[var(--muhide-orange)] hover:underline"
 >
 Open Decision Center
 </a>
 <button
 type="button"
 onClick={onClose}
 className="rounded-[var(--radius-md)] bg-[var(--muhide-orange)] px-3 py-1.5 text-[12px] font-medium text-white hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 >
 Done
 </button>
 </footer>
 </div>
 </div>
 )
}

export function openV3AiPopup(detail?: V3AiOpenDetail) {
 if (typeof window === 'undefined') return
 window.dispatchEvent(new CustomEvent(V3_AI_OPEN_EVENT, { detail }))
}
