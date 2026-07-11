'use client'

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useDashboard } from '@/application/dashboard/useDashboard'
import { deriveWidgets, type WidgetMap } from '@/application/dashboard/widget.store'
import { dashboardTelemetry } from '../_telemetry/dashboard-telemetry'

interface DashboardContextValue {
  widgets: WidgetMap
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}

const DashboardContext = createContext<DashboardContextValue | null>(null)

export function DashboardProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, isError, error, refetch } = useDashboard()
  const telemetry = useMemo(() => dashboardTelemetry.start('dashboard.load'), [])
  const widgets = useMemo(() => deriveWidgets(data, isLoading, isError), [data, isLoading, isError])

  useMemo(() => {
    telemetry.end(isError ? error?.message : undefined)
  }, [isError, error, telemetry])

  const value = useMemo<DashboardContextValue>(
    () => ({ widgets, isLoading, isError, error, refetch }),
    [widgets, isLoading, isError, error, refetch]
  )

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>
}

export function useDashboardContext(): DashboardContextValue {
  const ctx = useContext(DashboardContext)
  if (!ctx) throw new Error('useDashboardContext must be used within <DashboardProvider>')
  return ctx
}
