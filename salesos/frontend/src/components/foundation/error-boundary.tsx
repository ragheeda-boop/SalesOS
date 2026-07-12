"use client"

import { cn } from "@salesos/ui"
import { useTranslation } from "@/lib/i18n"

interface ErrorFallbackProps {
  title?: string
  message?: string
  onRetry?: () => void
  className?: string
  showDetails?: boolean
  errorDetails?: string
}

export function ErrorFallback({
  title,
  message,
  onRetry,
  className,
  showDetails = false,
  errorDetails,
}: ErrorFallbackProps) {
  const { t } = useTranslation()

  const defaultTitle = title || t("error.default_title")
  const defaultMessage = message || t("error.default_message")

  return (
    <div className={cn("flex flex-col items-center justify-center py-12 text-center", className)} role="alert" aria-label={defaultTitle}>
      <svg className="mx-auto mb-4 h-12 w-12 text-danger-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
      <h3 className="text-base font-semibold text-[var(--text-primary)]">{defaultTitle}</h3>
      {defaultMessage && (
        <p className="mt-1 text-sm text-[var(--text-muted)] max-w-sm">{defaultMessage}</p>
      )}
      {showDetails && errorDetails && (
        <details className="mt-3 max-w-md w-full">
          <summary className="cursor-pointer text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)]">
            {t("error.show_details")}
          </summary>
          <pre className="mt-2 text-left text-xs p-3 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 overflow-auto max-h-40">
            {errorDetails}
          </pre>
        </details>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm font-medium text-white hover:brightness-110 transition-all"
        >
          {t("error.retry")}
        </button>
      )}
    </div>
  )
}
