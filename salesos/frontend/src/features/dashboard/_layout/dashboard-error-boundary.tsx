'use client'

import { Component, type ReactNode, type ErrorInfo } from 'react'
import { dashboardTelemetry } from '../_telemetry/dashboard-telemetry'

interface Props {
 widgetId: string
 fallback?: ReactNode
 children: ReactNode
 onError?: (error: Error) => void
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
 this.props.onError?.(error)
 }

 handleRetry = () => {
 this.setState({ hasError: false, error: null })
 }

 render() {
 if (this.state.hasError) {
 return (
 this.props.fallback ?? (
 <div
 role="alert"
 className="flex flex-col items-center gap-3 rounded-xl border border-danger-200 bg-danger-50 p-4 text-center dark:border-danger-800 dark:bg-danger-950/30"
 >
 <p className="text-sm font-semibold text-danger-800 dark:text-danger-200">Widget Error</p>
 <p className="text-xs text-danger-600 dark:text-danger-400">{this.state.error?.message}</p>
 <button
 onClick={this.handleRetry}
 className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:opacity-90"
 >
 إعادة المحاولة
 </button>
 </div>
 )
 )
 }

 return this.props.children
 }
}
