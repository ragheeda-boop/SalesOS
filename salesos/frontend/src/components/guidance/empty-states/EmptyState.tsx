"use client"

import type { ReactNode } from "react"
import { cn } from "@salesos/ui"
import { useTour } from "../tour"
import { TOUR_REGISTRY } from "../tour"

interface EmptyStateAction {
  label: string
  onClick: () => void
}

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description: string
  action?: EmptyStateAction
  secondaryAction?: EmptyStateAction
  tourId?: string
  className?: string
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  tourId,
  className,
}: EmptyStateProps) {
  const { startTour, shouldShowTour } = useTour()

  const handleTourClick = () => {
    if (tourId && TOUR_REGISTRY[tourId]) {
      startTour(tourId, TOUR_REGISTRY[tourId])
    }
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-4 text-center",
        className,
      )}
      role="status"
    >
      <div className="mb-4 text-[var(--text-muted)]">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-[var(--text-primary)]">
        {title}
      </h3>
      <p className="mt-1.5 text-sm text-[var(--text-muted)] max-w-sm leading-relaxed">
        {description}
      </p>
      <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
        {action && (
          <button
            type="button"
            onClick={action.onClick}
            className="inline-flex items-center rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm font-medium text-white hover:brightness-110 transition-all"
          >
            {action.label}
          </button>
        )}
        {secondaryAction && (
          <button
            type="button"
            onClick={secondaryAction.onClick}
            className="inline-flex items-center rounded-lg border border-[var(--border-default)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-all"
          >
            {secondaryAction.label}
          </button>
        )}
        {tourId && shouldShowTour(tourId) && (
          <button
            type="button"
            onClick={handleTourClick}
            className="inline-flex items-center gap-1 rounded-lg px-4 py-2 text-sm font-medium text-[var(--muhide-orange)] hover:bg-[var(--muhide-orange)]/5 transition-all"
          >
            جولة تعريفية
          </button>
        )}
      </div>
    </div>
  )
}
