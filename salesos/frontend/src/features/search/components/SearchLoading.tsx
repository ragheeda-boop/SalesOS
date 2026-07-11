'use client'

import { cn } from '@salesos/ui'

interface SearchLoadingProps {
  count?: number
  className?: string
}

function ResultSkeleton() {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <div className="h-8 w-8 shrink-0 rounded-lg bg-[var(--bg-tertiary)] dark:bg-neutral-800 animate-pulse" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-3/4 rounded bg-[var(--bg-tertiary)] dark:bg-neutral-800 animate-pulse" />
        <div className="h-3 w-1/2 rounded bg-[var(--bg-tertiary)] dark:bg-neutral-800 animate-pulse" />
        <div className="h-3 w-1/4 rounded bg-[var(--bg-tertiary)] dark:bg-neutral-800 animate-pulse" />
      </div>
    </div>
  )
}

export function SearchLoading({ count = 5, className }: SearchLoadingProps) {
  return (
    <div className={cn('divide-y divide-[var(--border-color)]', className)}>
      {Array.from({ length: count }, (_, i) => (
        <ResultSkeleton key={i} />
      ))}
    </div>
  )
}
