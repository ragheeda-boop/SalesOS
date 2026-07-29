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

const EMPTY_DASHBOARD_CONTEXT: DashboardContextValue = {
 widgets: {} as WidgetMap,
 isLoading: true,
 isError: false,
 error: null,
 refetch: () => {},
}

export function useDashboardContext(): DashboardContextValue {
 const ctx = useContext(DashboardContext)
 // Never throw — widget-sdk may call this during edge renders; throwing takes down /dashboard.
 return ctx ?? EMPTY_DASHBOARD_CONTEXT
}
