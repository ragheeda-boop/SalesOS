'use client'

import { Component, type ReactNode, type ErrorInfo } from 'react'
import { dashboardTelemetry } from '../_telemetry/dashboard-telemetry'

interface Props {
  widgetId: string
  fallback?: ReactNode
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class DashboardErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    dashboardTelemetry.error(this.props.widgetId, error.message)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div
            role="alert"
            style={{
              padding: '1rem',
              borderRadius: '0.5rem',
              border: '1px solid #fca5a5',
              background: '#fef2f2',
              color: '#991b1b',
              fontSize: '0.875rem',
            }}
          >
            <p style={{ fontWeight: 600, margin: 0 }}>Widget Error</p>
            <p style={{ margin: '0.25rem 0 0' }}>{this.state.error?.message}</p>
          </div>
        )
      )
    }

    return this.props.children
  }
}
