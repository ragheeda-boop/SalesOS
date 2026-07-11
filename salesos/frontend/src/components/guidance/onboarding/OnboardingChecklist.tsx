"use client"

import Link from "next/link"
import { cn } from "@salesos/ui"
import { Check, ChevronLeft, Rocket } from "lucide-react"
import { useOnboarding } from "./OnboardingProvider"
import { useTour } from "../tour"
import { TOUR_REGISTRY, TOUR_LABELS } from "../tour"
import { Card, CardHeader, CardContent } from "@/components/foundation/card"

export function OnboardingChecklist() {
  const { items, completed, completeItem, progress, isComplete } = useOnboarding()
  const { startTour } = useTour()

  if (isComplete) return null

  return (
    <Card variant="bordered" accent="orange" className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Rocket className="h-5 w-5 text-[var(--muhide-orange)]" />
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">
            البدء مع SalesOS
          </h3>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-1">
            <span>تقدم الإعداد</span>
            <span>{completed.length} / {items.length}</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-neutral-100 dark:bg-neutral-800">
            <div
              className="h-full rounded-full bg-[var(--muhide-orange)] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <ul className="space-y-1">
          {items.map((item) => {
            const done = completed.includes(item.id)
            return (
              <li key={item.id}>
                <Link
                  href={item.href}
                  onClick={() => {
                    if (!done) completeItem(item.id)
                  }}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors",
                    done
                      ? "text-[var(--text-muted)] line-through"
                      : "text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]",
                  )}
                >
                  <span
                    className={cn(
                      "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border",
                      done
                        ? "border-success-500 bg-success-500/10"
                        : "border-[var(--border-default)]",
                    )}
                  >
                    {done ? (
                      <Check className="h-3 w-3 text-success-600" />
                    ) : (
                      <span className="h-2 w-2 rounded-full bg-neutral-300" />
                    )}
                  </span>
                  <span className="flex-1">{item.label}</span>
                  {item.tourId && !done && (
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        if (TOUR_REGISTRY[item.tourId]) {
                          startTour(item.tourId, TOUR_REGISTRY[item.tourId])
                        }
                      }}
                      className="text-xs text-[var(--muhide-orange)] hover:underline shrink-0"
                    >
                      {TOUR_LABELS[item.tourId] || "جولة تعريفية"}
                    </button>
                  )}
                  <ChevronLeft className="h-4 w-4 text-[var(--text-muted)] shrink-0" />
                </Link>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
