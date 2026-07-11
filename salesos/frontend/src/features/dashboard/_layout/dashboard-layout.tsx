'use client'

import { type ReactNode } from 'react'
import { DashboardProvider, useDashboardContext } from '../_providers/dashboard-provider'
import { DashboardGrid } from './dashboard-grid'
import { DashboardLoading } from './dashboard-loading'

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
