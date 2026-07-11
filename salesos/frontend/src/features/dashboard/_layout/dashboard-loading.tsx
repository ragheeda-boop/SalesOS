'use client'

import { WIDGET_CONFIG, type WidgetId } from '../_registry/widget-config'
import { DashboardGrid } from './dashboard-grid'

function Skeleton({ minHeight }: { minHeight: string }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      style={{
        minHeight,
        borderRadius: '0.5rem',
        background: 'linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
      }}
    />
  )
}

export function DashboardLoading() {
  const ids = Object.keys(WIDGET_CONFIG) as WidgetId[]
  return (
    <DashboardGrid>
      {ids.map((id) => (
        <div key={id} style={{ gridColumn: WIDGET_CONFIG[id].gridColumn }}>
          <Skeleton minHeight={WIDGET_CONFIG[id].minHeight} />
        </div>
      ))}
    </DashboardGrid>
  )
}
