'use client'

import { useMy360 } from '@/lib/hooks/employeeQueries'
import { createWorkspaceProvider, WorkspaceGrid } from '@salesos/workspace'
import { EmployeeIntelligenceLayout } from '../_layout/EmployeeIntelligenceLayout'
import { EmployeeProfileWidget } from '../widgets/employee-profile/EmployeeProfileWidget'
import { EmployeePortfolioWidget } from '../widgets/employee-portfolio/EmployeePortfolioWidget'
import { ActivityIntelligenceWidget } from '../widgets/activity-intelligence/ActivityIntelligenceWidget'
import { CalendarIntelligenceWidget } from '../widgets/calendar-intelligence/CalendarIntelligenceWidget'
import { EmailIntelligenceWidget } from '../widgets/email-intelligence/EmailIntelligenceWidget'
import { KPIWidget } from '../widgets/kpi-widget/KPIWidget'
import { AICoachWidget } from '../widgets/ai-coach/AICoachWidget'
import type { Employee360Response } from '@/lib/api'
import type { WidgetData, WidgetStatus } from '@salesos/workspace'

interface EmployeeIntelligenceWidgets {
  [key: string]: WidgetData<unknown>
  profile: WidgetData<Employee360Response['profile']>
  portfolio: WidgetData<Employee360Response['portfolio']>
  activity: WidgetData<Employee360Response['activity_intelligence']>
  calendar: WidgetData<Employee360Response['calendar_intelligence']>
  email: WidgetData<Employee360Response['email_intelligence']>
  kpis: WidgetData<Employee360Response['kpis']>
  aiCoach: WidgetData<Employee360Response['ai_coach']>
}

function deriveStatus(isLoading: boolean, isError: boolean): WidgetStatus {
  if (isError) return 'error'
  if (isLoading) return 'loading'
  return 'ready'
}

function useDataHook() {
  const { data, isLoading, isError, error, refetch } = useMy360()
  const status = deriveStatus(isLoading, isError)
  const now = new Date().toISOString()

  function widgetData<T>(extract: (d: Employee360Response) => T): WidgetData<T> {
    return {
      data: data ? extract(data) : null,
      status,
      lastUpdated: data ? now : null,
      error,
      refetch,
    }
  }

  return {
    data: {
      profile: widgetData((d) => d.profile),
      portfolio: widgetData((d) => d.portfolio),
      activity: widgetData((d) => d.activity_intelligence),
      calendar: widgetData((d) => d.calendar_intelligence),
      email: widgetData((d) => d.email_intelligence),
      kpis: widgetData((d) => d.kpis),
      aiCoach: widgetData((d) => d.ai_coach),
    } as EmployeeIntelligenceWidgets,
    isLoading,
    isError,
    error,
    refetch,
  }
}

const { WorkspaceProvider, useWorkspaceContext } = createWorkspaceProvider<EmployeeIntelligenceWidgets>(
  useDataHook,
  (data) => data as EmployeeIntelligenceWidgets,
)

function WorkspaceGridContent() {
  return (
    <WorkspaceGrid columns={6} gap="1rem">
      <div style={{ gridColumn: 'span 2' }}>
        <EmployeeProfileWidget />
      </div>
      <div style={{ gridColumn: 'span 2' }}>
        <KPIWidget />
      </div>
      <div style={{ gridColumn: 'span 2' }}>
        <AICoachWidget />
      </div>
      <div style={{ gridColumn: 'span 3' }}>
        <EmployeePortfolioWidget />
      </div>
      <div style={{ gridColumn: 'span 3' }}>
        <ActivityIntelligenceWidget />
      </div>
      <div style={{ gridColumn: 'span 3' }}>
        <CalendarIntelligenceWidget />
      </div>
      <div style={{ gridColumn: 'span 3' }}>
        <EmailIntelligenceWidget />
      </div>
    </WorkspaceGrid>
  )
}

export function EmployeeWorkspace() {
  return (
    <WorkspaceProvider>
      <EmployeeIntelligenceLayout>
        <WorkspaceGridContent />
      </EmployeeIntelligenceLayout>
    </WorkspaceProvider>
  )
}

export { useWorkspaceContext }
