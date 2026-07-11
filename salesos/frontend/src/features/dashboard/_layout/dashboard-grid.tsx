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
      className={className}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap,
        width: '100%',
        ...style,
      }}
    >
      {children}
    </div>
  )
}
