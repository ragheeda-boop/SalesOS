"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { X } from "lucide-react"
import { useCoachMark } from "./CoachMarkProvider"
import { useTour } from "../tour"
import { TOUR_REGISTRY } from "../tour"

interface BubblePosition {
  top: number
  left: number
}

function computeBubblePosition(target: string, bubbleWidth: number, bubbleHeight: number): BubblePosition | null {
  const el = document.querySelector(target)
  if (!el) return null
  const rect = el.getBoundingClientRect()
  return {
    top: rect.bottom + 8 + window.scrollY,
    left: Math.max(8, rect.left + rect.width / 2 - bubbleWidth / 2 + window.scrollX),
  }
}

export function CoachMarkBubble({
  hintId,
  target,
  message,
  tourId,
}: {
  hintId: string
  target: string
  message: string
  tourId?: string
}) {
  const { dismissHint } = useCoachMark()
  const { startTour } = useTour()
  const [position, setPosition] = useState<BubblePosition | null>(null)
  const bubbleRef = useRef<HTMLDivElement>(null)

  const recalc = useCallback(() => {
    if (bubbleRef.current) {
      const { offsetWidth, offsetHeight } = bubbleRef.current
      setPosition(computeBubblePosition(target, offsetWidth, offsetHeight))
    }
  }, [target])

  useEffect(() => {
    recalc()
    const handleResize = () => recalc()
    window.addEventListener("resize", handleResize)
    window.addEventListener("scroll", handleResize, true)
    return () => {
      window.removeEventListener("resize", handleResize)
      window.removeEventListener("scroll", handleResize, true)
    }
  }, [recalc])

  const handleShowMore = () => {
    dismissHint(hintId)
    if (tourId && TOUR_REGISTRY[tourId]) {
      startTour(tourId, TOUR_REGISTRY[tourId])
    }
  }

  if (!position) return null

  return (
    <div
      ref={bubbleRef}
      className="fixed z-[9997] rounded-lg bg-[var(--muhide-orange)] px-4 py-2.5 shadow-muhide-4"
      style={{ top: position.top, left: position.left, maxWidth: 280 }}
      role="status"
      aria-live="polite"
    >
      <div
        className="absolute -top-1.5 left-4 h-3 w-3 rotate-45 bg-[var(--muhide-orange)]"
        aria-hidden="true"
      />
      <div className="flex items-start gap-2">
        <p className="text-sm text-white flex-1 leading-snug">
          {message}
        </p>
        <button
          onClick={() => dismissHint(hintId)}
          className="shrink-0 rounded-full p-0.5 text-white/70 hover:text-white transition-colors"
          aria-label="إغلاق"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
      <div className="flex items-center justify-between mt-1.5">
        {tourId ? (
          <button
            onClick={handleShowMore}
            className="text-xs font-medium text-white/80 hover:text-white underline underline-offset-2 transition-colors"
          >
            اعرف المزيد
          </button>
        ) : (
          <div />
        )}
        <button
          onClick={() => dismissHint(hintId)}
          className="rounded bg-white/20 px-2 py-0.5 text-xs font-medium text-white hover:bg-white/30 transition-colors"
        >
          فهمت
        </button>
      </div>
    </div>
  )
}
