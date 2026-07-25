'use client'

import { type ReactNode } from 'react'
import { setDashboardDependencies } from '@salesos/widget-sdk'
import { DashboardProvider, useDashboardContext } from '../_providers/dashboard-provider'
import { getWidgetConfig } from '../_registry/widget-config'
import { DashboardGrid } from './dashboard-grid'
import { DashboardLoading } from './dashboard-loading'

setDashboardDependencies(
 useDashboardContext,
 (id: string) => getWidgetConfig(id as Parameters<typeof getWidgetConfig>[0]),
)

function DashboardInner({ children }: { children: ReactNode }) {
 const { isLoading } = useDashboardContext()

 if (isLoading) return <DashboardLoading />

 return <DashboardGrid>{children}</DashboardGrid>
}

export function DashboardLayout({ children }: { children: ReactNode }) {
 return (
 <DashboardProvider>
 <DashboardInner>{children}</DashboardInner>
 </DashboardProvider>
 )
}
