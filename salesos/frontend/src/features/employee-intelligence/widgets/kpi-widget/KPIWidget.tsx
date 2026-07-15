'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { KPIContainer } from './KPIContainer'

export const KPIWidget = createWorkspaceWidget(
  { id: 'employeeKPIs', minHeight: '320px' },
  useWorkspaceContext,
  (widgets) => widgets.kpis,
  {
    metadata: { title: 'مؤشرات الأداء' },
    render: ({ data }) => <KPIContainer data={data} />,
  },
)
