'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { EmailIntelligenceContainer } from './EmailIntelligenceContainer'

export const EmailIntelligenceWidget = createWorkspaceWidget(
  { id: 'emailIntelligence', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.email,
  {
    metadata: { title: 'ذكاء البريد' },
    render: ({ data }) => <EmailIntelligenceContainer data={data} />,
  },
)
