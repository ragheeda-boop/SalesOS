'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { CalendarIntelligenceContainer } from './CalendarIntelligenceContainer'

export const CalendarIntelligenceWidget = createWorkspaceWidget(
  { id: 'calendarIntelligence', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.calendar,
  {
    metadata: { title: 'ذكاء التقويم' },
    render: ({ data }) => <CalendarIntelligenceContainer data={data} />,
  },
)
