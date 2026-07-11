'use client'

import { WorkspaceGrid } from './workspace-grid'
import type { WorkspaceWidgetEntry } from './types'

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

export interface WorkspaceLoadingProps {
  entries: WorkspaceWidgetEntry[]
}

export function WorkspaceLoading({ entries }: WorkspaceLoadingProps) {
  return (
    <WorkspaceGrid>
      {entries.map((entry) => (
        <div key={entry.id} style={{ gridColumn: entry.config.gridColumn }}>
          <Skeleton minHeight={entry.config.minHeight} />
        </div>
      ))}
    </WorkspaceGrid>
  )
}
