'use client'

import type { ReactNode } from 'react'
import { WorkspaceGrid, WorkspaceErrorBoundary, WorkspaceLoading } from '@salesos/workspace'
import { COMPANY_INTELLIGENCE_WIDGET_CONFIG, type CompanyWidgetId } from '../_registry/widget-config'

export function CompanyIntelligenceLoading() {
  return (
    <WorkspaceLoading
      entries={Object.values(COMPANY_INTELLIGENCE_WIDGET_CONFIG).map((c) => ({
        id: c.id,
        config: { gridColumn: c.gridColumn, minHeight: c.minHeight, refreshIntervalMs: c.refreshIntervalMs, staleThresholdMs: c.staleThresholdMs },
      }))}
    />
  )
}

export function CompanyIntelligenceGrid({ children, isLoading }: { children: ReactNode; isLoading?: boolean }) {
  if (isLoading) return <CompanyIntelligenceLoading />
  return <WorkspaceGrid columns={6}>{children}</WorkspaceGrid>
}

export function CompanyIntelligenceWidgetShell({ widgetId, children }: { widgetId: CompanyWidgetId; children: ReactNode }) {
  const config = COMPANY_INTELLIGENCE_WIDGET_CONFIG[widgetId]
  return (
    <div key={widgetId} style={{ gridColumn: config.gridColumn }}>
      <WorkspaceErrorBoundary widgetId={widgetId}>{children}</WorkspaceErrorBoundary>
    </div>
  )
}
