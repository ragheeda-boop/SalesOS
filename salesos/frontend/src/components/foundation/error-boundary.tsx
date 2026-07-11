import React from 'react'
import { cn } from "@salesos/ui"

interface ErrorFallbackProps {
  title?: string
  message?: string
  onRetry?: () => void
  className?: string
}

export function ErrorFallback({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
  className,
}: ErrorFallbackProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)} role="alert" aria-label="Error">
      <svg className="mx-auto mb-4 h-12 w-12 text-danger-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
      <h3 className="text-base font-semibold text-[var(--text-primary)]">{title}</h3>
      {message && (
        <p className="mt-1 text-sm text-[var(--text-muted)] max-w-sm">{message}</p>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm font-medium text-white hover:brightness-110 transition-all"
        >
          Try again
        </button>
      )}
    </div>
  )
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode | ((props: { error: Error; resetError: () => void }) => React.ReactNode)
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.props.onError?.(error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        if (typeof this.props.fallback === 'function') {
          return this.props.fallback({ error: this.state.error!, resetError: this.handleReset })
        }
        return this.props.fallback
      }

      return (
        <ErrorFallback
          title={this.state.error?.message || 'Something went wrong'}
          message="An unexpected error occurred. Please try again."
          onRetry={this.handleReset}
        />
      )
    }

    return this.props.children
  }
}
