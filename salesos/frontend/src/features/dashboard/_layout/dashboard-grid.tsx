'use client'

import { type ReactNode, type CSSProperties } from 'react'

interface DashboardGridProps {
  children: ReactNode
  columns?: number
  gap?: string
  className?: string
  style?: CSSProperties
}

export function DashboardGrid({ children, columns = 6, gap = '1rem', className, style }: DashboardGridProps) {
  return (
    <div
      className={`dashboard-grid ${className || ''}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap,
        width: '100%',
        gridAutoRows: 'min-content',
        ...style,
      }}
    >
      <style>{`
        .dashboard-grid { grid-template-columns: 1fr !important; }
        .dashboard-grid > * { min-width: 0; }
        @media (min-width: 640px) {
          .dashboard-grid { grid-template-columns: repeat(2, 1fr) !important; }
          .dashboard-grid > * { grid-column: span 1 !important; }
        }
        @media (min-width: 768px) {
          .dashboard-grid { grid-template-columns: repeat(4, 1fr) !important; }
        }
        @media (min-width: 1024px) {
          .dashboard-grid { grid-template-columns: repeat(${columns}, 1fr) !important; }
        }
      `}</style>
      {children}
    </div>
  )
}
