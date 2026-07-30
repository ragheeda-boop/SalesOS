"use client"

import { useEffect } from "react"

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error("[Dashboard Error]", error)
  }, [error])

  return (
    <div className="flex items-center justify-center min-h-[60vh] p-8">
      <div className="text-center space-y-4 max-w-md">
        <div className="rounded-full bg-[var(--status-danger-bg)] w-16 h-16 flex items-center justify-center mx-auto">
          <span className="text-2xl">!</span>
        </div>
        <h1 className="text-xl font-display text-[var(--text-primary)]">
          Something went wrong
        </h1>
        <p className="text-sm text-[var(--text-muted)]">
          An unexpected error occurred. Please try again.
        </p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg text-sm hover:opacity-90"
        >
          Try again
        </button>
      </div>
    </div>
  )
}