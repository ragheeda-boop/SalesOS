'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { AICoachContainer } from './AICoachContainer'

export const AICoachWidget = createWorkspaceWidget(
  { id: 'aiCoach', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.aiCoach,
  {
    metadata: { title: 'المدرب الذكي', category: 'decisions', priority: 'high' },
    render: ({ data }) => <AICoachContainer actions={data} />,
  },
)
