"use client"

import { cn } from "@salesos/ui"

interface SkeletonProps {
  className?: string
  lines?: number
  variant?: "text" | "title" | "avatar" | "card" | "list"
}

function SkeletonPulse({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-[var(--bg-tertiary)]",
        "motion-reduce:animate-none",
        className
      )}
      aria-hidden="true"
    />
  )
}

export function Skeleton({ className, variant = "text", lines = 1 }: SkeletonProps) {
  if (variant === "avatar") {
    return <SkeletonPulse className={cn("h-10 w-10 rounded-full", className)} />
  }

  if (variant === "title") {
    return <SkeletonPulse className={cn("h-5 w-40", className)} />
  }

  if (variant === "card") {
    return (
      <div className={cn("space-y-3 rounded-xl border border-[var(--border-default)] p-4", className)} aria-hidden="true">
        <SkeletonPulse className="h-4 w-3/4" />
        <SkeletonPulse className="h-3 w-full" />
        <SkeletonPulse className="h-3 w-5/6" />
        <div className="flex gap-2 pt-2">
          <SkeletonPulse className="h-6 w-16 rounded-full" />
          <SkeletonPulse className="h-6 w-16 rounded-full" />
        </div>
      </div>
    )
  }

  if (variant === "list") {
    return (
      <div className={cn("space-y-2", className)} aria-hidden="true">
        {Array.from({ length: lines }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <SkeletonPulse className="h-8 w-8 shrink-0 rounded-lg" />
            <div className="flex-1 space-y-1.5">
              <SkeletonPulse className="h-3.5 w-3/4" />
              <SkeletonPulse className="h-2.5 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={cn("space-y-2", className)} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonPulse
          key={i}
          className={cn("h-3.5", i === lines - 1 ? "w-2/3" : "w-full")}
        />
      ))}
    </div>
  )
}

export function WidgetSkeleton({ title }: { title?: string }) {
  return (
    <div
      className="flex flex-col rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] overflow-hidden"
      role="status"
      aria-label={`جاري تحميل ${title || "المكون"}...`}
    >
      <div className="flex items-center justify-between border-b border-[var(--border-default)] px-4 py-3">
        <div className="flex items-center gap-2">
          <SkeletonPulse className="h-4 w-32" />
        </div>
      </div>
      <div className="flex-1 p-4 space-y-3">
        <SkeletonPulse className="h-3 w-full" />
        <SkeletonPulse className="h-3 w-5/6" />
        <SkeletonPulse className="h-3 w-4/6" />
        <div className="pt-2 flex gap-2">
          <SkeletonPulse className="h-6 w-16 rounded-full" />
          <SkeletonPulse className="h-6 w-16 rounded-full" />
        </div>
      </div>
      <span className="sr-only">جاري التحميل...</span>
    </div>
  )
}
