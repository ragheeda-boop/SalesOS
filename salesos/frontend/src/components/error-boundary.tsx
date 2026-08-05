"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { useTranslation } from "@/lib/i18n";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  t?: (key: string) => string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.props.onError?.(error, errorInfo);
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("sentry:capture", { detail: { error, errorInfo } }));
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      const t = this.props.t || ((key: string) => key);

      return (
        <div
          role="alert"
          className="flex flex-col items-center justify-center rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)] p-8 text-center"
        >
          <AlertTriangle className="mb-3 h-8 w-8 text-[var(--muhide-orange)]" aria-hidden="true" />
          <h3 className="mb-1 text-sm font-semibold text-[var(--text-primary)]">
            {t("error.unexpected")}
          </h3>
          <p className="mb-4 max-w-sm text-xs text-[var(--text-muted)]">
            {this.state.error?.message || t("error.component_failed")}
          </p>
          <button
            onClick={this.handleRetry}
            className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-2 text-xs font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-tertiary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            {t("common.retry")}
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

function ErrorBoundaryWrapper({
  children,
  fallback,
  onError,
}: {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}) {
  const { t } = useTranslation();
  return (
    <ErrorBoundary fallback={fallback} onError={onError} t={t}>
      {children}
    </ErrorBoundary>
  );
}

export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) {
  function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundaryWrapper fallback={fallback} onError={onError}>
        <WrappedComponent {...props} />
      </ErrorBoundaryWrapper>
    );
  }

  WithErrorBoundary.displayName = `WithErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;
  return WithErrorBoundary;
}
