'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { ActivityIntelligenceContainer } from './ActivityIntelligenceContainer'

export const ActivityIntelligenceWidget = createWorkspaceWidget(
  { id: 'activityIntelligence', minHeight: '340px' },
  useWorkspaceContext,
  (widgets) => widgets.activity,
  {
    metadata: { title: 'ذكاء النشاطات' },
    render: () => <ActivityIntelligenceContainer />,
  },
)
