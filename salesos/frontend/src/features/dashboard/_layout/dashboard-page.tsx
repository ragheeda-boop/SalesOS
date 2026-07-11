'use client'

import { DashboardProvider, useDashboardContext } from '../_providers/dashboard-provider'
import { DashboardGrid } from './dashboard-grid'
import { DashboardLoading } from './dashboard-loading'
import { widgetRegistry } from '../widget-registry'

function DashboardBody() {
  const { isLoading, isError, error, refetch } = useDashboardContext()

  if (isLoading) return <DashboardLoading />

  if (isError) {
    return (
      <div
        role="alert"
        style={{
          padding: '2rem',
          textAlign: 'center',
          color: '#991b1b',
          background: '#fef2f2',
          borderRadius: '0.5rem',
          border: '1px solid #fca5a5',
        }}
      >
        <p style={{ fontWeight: 600, margin: 0 }}>فشل تحميل لوحة المعلومات</p>
        <p style={{ fontSize: '0.875rem', margin: '0.5rem 0' }}>{error?.message}</p>
        <button
          onClick={() => refetch()}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            border: 'none',
            background: '#f97316',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          إعادة المحاولة
        </button>
      </div>
    )
  }

  return (
    <DashboardGrid>
      {widgetRegistry.map((entry) => (
        <entry.Container key={entry.id} />
      ))}
    </DashboardGrid>
  )
}

export function DashboardPage() {
  return (
    <DashboardProvider>
      <DashboardBody />
    </DashboardProvider>
  )
}
