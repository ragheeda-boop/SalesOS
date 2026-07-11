'use client'

import { type ReactNode, type CSSProperties } from 'react'

export interface WorkspaceGridProps {
  children: ReactNode
  columns?: number
  gap?: string
  className?: string
  style?: CSSProperties
}

export function WorkspaceGrid({ children, columns = 6, gap = '1rem', className, style }: WorkspaceGridProps) {
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
