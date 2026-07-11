'use client'

import { useState, useCallback } from 'react'
import { cn } from '@salesos/ui'
import { MessageSquare, Star, Send } from 'lucide-react'
import { track } from '@/lib/analytics'

interface FeedbackWidgetProps {
  className?: string
}

const NPS_OPTIONS = Array.from({ length: 11 }, (_, i) => i)

export function FeedbackWidget({ className }: FeedbackWidgetProps) {
  const [open, setOpen] = useState(false)
  const [nps, setNps] = useState<number | null>(null)
  const [comment, setComment] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = useCallback(() => {
    track({ type: 'pilot.feedback_submitted', metadata: { nps, comment: comment.slice(0, 100) } })
    setSubmitted(true)
    setTimeout(() => { setOpen(false); setSubmitted(false); setNps(null); setComment('') }, 2000)
  }, [nps, comment])

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className={cn('fixed bottom-4 left-4 z-40 flex items-center gap-2 rounded-full bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-lg transition hover:bg-primary-700', className)}
      >
        <MessageSquare className="h-4 w-4" />
        تقييم سريع
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 left-4 z-40 w-80 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-primary)] p-4 shadow-2xl dark:border-neutral-700 dark:bg-neutral-900">
      {submitted ? (
        <div className="flex flex-col items-center py-4 text-center">
          <Star className="mb-2 h-8 w-8 text-amber-400" />
          <p className="text-sm font-medium text-[var(--text-primary)]">شكرًا لتقييمك!</p>
        </div>
      ) : (
        <>
          <p className="mb-3 text-sm font-medium text-[var(--text-primary)]">ما رأيك في SalesOS؟</p>
          <p className="mb-2 text-xs text-[var(--text-muted)]">ما مدى احتمالية أن توصي بـ SalesOS لزميلك؟</p>
          <div className="mb-3 flex justify-between gap-0.5">
            {NPS_OPTIONS.map((n) => (
              <button
                key={n}
                onClick={() => setNps(n)}
                className={cn(
                  'h-7 w-7 rounded-lg text-[10px] font-medium transition',
                  nps === n
                    ? n >= 9 ? 'bg-green-500 text-white' : n >= 7 ? 'bg-amber-500 text-white' : 'bg-red-500 text-white'
                    : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:bg-primary-50'
                )}
              >
                {n}
              </button>
            ))}
          </div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="أخبرنا أكثر..."
            rows={2}
            className="mb-2 w-full resize-none rounded-lg border border-[var(--border-color)] bg-transparent p-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-primary-500 focus:outline-none dark:border-neutral-700"
          />
          <div className="flex gap-2">
            <button onClick={() => setOpen(false)} className="flex-1 rounded-lg px-3 py-1.5 text-xs text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]">إلغاء</button>
            <button
              onClick={handleSubmit}
              disabled={nps === null}
              className="flex flex-1 items-center justify-center gap-1 rounded-lg bg-primary-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-primary-700 disabled:opacity-50"
            >
              <Send className="h-3 w-3" /> إرسال
            </button>
          </div>
        </>
      )}
    </div>
  )
}
