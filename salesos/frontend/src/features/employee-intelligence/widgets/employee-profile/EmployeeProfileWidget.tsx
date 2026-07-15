'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { EmployeeProfileContainer } from './EmployeeProfileContainer'

export const EmployeeProfileWidget = createWorkspaceWidget(
  { id: 'employeeProfile', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.profile,
  {
    metadata: { title: 'الملف الشخصي' },
    render: () => <EmployeeProfileContainer />,
  },
)
