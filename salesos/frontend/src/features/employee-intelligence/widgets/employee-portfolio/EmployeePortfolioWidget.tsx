'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import { EmployeePortfolioContainer } from './EmployeePortfolioContainer'

export const EmployeePortfolioWidget = createWorkspaceWidget(
  { id: 'employeePortfolio', minHeight: '340px' },
  useWorkspaceContext,
  (widgets) => widgets.portfolio,
  {
    metadata: { title: 'محفظة الأعمال' },
    render: ({ data }) => <EmployeePortfolioContainer portfolio={data} />,
  },
)
