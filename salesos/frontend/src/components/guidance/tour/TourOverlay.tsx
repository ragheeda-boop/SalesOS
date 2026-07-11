"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { cn } from "@salesos/ui"
import { X, ChevronLeft, ChevronRight, Check } from "lucide-react"
import { useTour } from "./TourProvider"
import type { TourStep } from "./TourStep"

interface TargetRect {
  top: number
  left: number
  width: number
  height: number
}

interface TooltipStyle {
  position: 'top' | 'bottom' | 'left' | 'right' | 'center'
}

function getTargetRect(target: string): TargetRect | null {
  const el = document.querySelector(target)
  if (!el) return null
  const rect = el.getBoundingClientRect()
  return {
    top: rect.top + window.scrollY,
    left: rect.left + window.scrollX,
    width: rect.width,
    height: rect.height,
  }
}

function computeTooltipPosition(
  targetRect: TargetRect | null,
  position: TourStep['position'],
  tooltipWidth: number,
  tooltipHeight: number,
): { top: number; left: number } {
  const gap = 12
  const centerX = targetRect ? targetRect.left + targetRect.width / 2 : window.innerWidth / 2
  const centerY = targetRect ? targetRect.top + targetRect.height / 2 : window.innerHeight / 2

  if (position === 'center' || !targetRect) {
    return {
      top: Math.max(16, (window.innerHeight - tooltipHeight) / 2 + window.scrollY),
      left: Math.max(16, (window.innerWidth - tooltipWidth) / 2 + window.scrollX),
    }
  }

  let top = centerY
  let left = centerX

  switch (position) {
    case 'top':
      top = targetRect.top - tooltipHeight - gap + window.scrollY
      left = Math.max(16, targetRect.left + targetRect.width / 2 - tooltipWidth / 2 + window.scrollX)
      break
    case 'bottom':
      top = targetRect.top + targetRect.height + gap + window.scrollY
      left = Math.max(16, targetRect.left + targetRect.width / 2 - tooltipWidth / 2 + window.scrollX)
      break
    case 'left':
      top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2 + window.scrollY
      left = Math.max(16, targetRect.left - tooltipWidth - gap + window.scrollX)
      break
    case 'right':
      top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2 + window.scrollY
      left = targetRect.left + targetRect.width + gap + window.scrollX
      break
  }

  top = Math.max(16, Math.min(top, window.innerHeight + window.scrollY - tooltipHeight - 16))
  left = Math.max(16, Math.min(left, window.innerWidth + window.scrollX - tooltipWidth - 16))

  return { top, left }
}

export function TourOverlay() {
  const { isActive, currentStep, steps, nextStep, prevStep, endTour, tourProgress } = useTour()
  const step = steps[currentStep]
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const [tooltipDims, setTooltipDims] = useState({ width: 320, height: 200 })

  const recalc = useCallback(() => {
    if (!step || step.position === 'center') {
      setTargetRect(null)
      return
    }
    const rect = getTargetRect(step.target)
    setTargetRect(rect)
    if (!rect && process.env.NODE_ENV === 'development') {
      console.warn(`[TourOverlay] Target element not found: "${step.target}" for step "${step.title}"`)
    }
  }, [step])

  useEffect(() => {
    recalc()
    const handleResize = () => recalc()
    window.addEventListener('resize', handleResize)
    window.addEventListener('scroll', handleResize, true)
    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('scroll', handleResize, true)
    }
  }, [recalc])

  useEffect(() => {
    if (tooltipRef.current) {
      const { offsetWidth, offsetHeight } = tooltipRef.current
      setTooltipDims({ width: offsetWidth || 320, height: offsetHeight || 200 })
    }
  }, [step])

  useEffect(() => {
    if (isActive) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isActive])

  if (!isActive || !step) return null

  const isFirst = currentStep === 0
  const isLast = currentStep === steps.length - 1
  const tooltipPos = computeTooltipPosition(targetRect, step.position, tooltipDims.width, tooltipDims.height)

  return (
    <>
      <div
        className="fixed inset-0 z-[9998]"
        style={{
          background: 'rgba(0, 0, 0, 0.6)',
        }}
        aria-hidden="true"
      />

      {targetRect && (
        <div
          className="fixed z-[9999] pointer-events-none"
          style={{
            top: targetRect.top - 4 + window.scrollY,
            left: targetRect.left - 4 + window.scrollX,
            width: targetRect.width + 8,
            height: targetRect.height + 8,
            borderRadius: '12px',
            boxShadow: '0 0 0 4px rgba(249, 115, 22, 0.6), 0 0 0 9999px rgba(0, 0, 0, 0.6)',
          }}
        />
      )}

      <div
        ref={tooltipRef}
        className="fixed z-[9999] w-[320px] sm:w-[360px] rounded-xl bg-white shadow-muhide-6 overflow-hidden"
        style={{
          top: tooltipPos.top,
          left: tooltipPos.left,
        }}
        role="dialog"
        aria-label={`خطوة ${currentStep + 1} من ${steps.length}: ${step.title}`}
      >
        <div className="relative">
          {step.image && (
            <img
              src={step.image}
              alt=""
              className="w-full h-32 object-cover"
            />
          )}
          <button
            onClick={endTour}
            className="absolute top-2 left-2 rounded-full bg-white/80 p-1 hover:bg-white transition-colors"
            aria-label="إغلاق الجولة"
          >
            <X className="h-4 w-4 text-neutral-600" />
          </button>
        </div>

        <div className="p-4">
          <p className="text-xs font-medium text-[var(--muhide-orange)] mb-1">
            الخطوة {currentStep + 1} من {steps.length}
          </p>
          <h3 className="text-base font-semibold text-neutral-900 mb-1">
            {step.title}
          </h3>
          <p className="text-sm text-neutral-600 leading-relaxed">
            {step.description}
          </p>
        </div>

        <div className="flex items-center justify-between border-t border-neutral-100 px-4 py-3">
          <div className="flex gap-1">
            {steps.map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 rounded-full transition-all",
                  i === currentStep
                    ? "w-4 bg-[var(--muhide-orange)]"
                    : i < currentStep
                    ? "w-1.5 bg-[var(--muhide-orange)]/40"
                    : "w-1.5 bg-neutral-200"
                )}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            {!isFirst && (
              <button
                onClick={prevStep}
                className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium text-neutral-600 hover:bg-neutral-100 transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
                السابق
              </button>
            )}
            {isLast ? (
              <button
                onClick={endTour}
                className="flex items-center gap-1 rounded-lg bg-[var(--muhide-orange)] px-4 py-1.5 text-sm font-medium text-white hover:brightness-110 transition-all"
              >
                <Check className="h-4 w-4" />
                تم
              </button>
            ) : (
              <button
                onClick={nextStep}
                className="flex items-center gap-1 rounded-lg bg-[var(--muhide-orange)] px-4 py-1.5 text-sm font-medium text-white hover:brightness-110 transition-all"
              >
                التالي
                <ChevronLeft className="h-4 w-4" />
              </button>
            )}
            {!isFirst && (
              <button
                onClick={endTour}
                className="text-xs text-neutral-400 hover:text-neutral-600 transition-colors px-2"
              >
                تخطي
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
