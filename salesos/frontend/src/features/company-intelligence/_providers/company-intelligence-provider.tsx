'use client'

import { createWorkspaceProvider } from '@salesos/workspace'
import { useCompanyIntelligence } from '@/application/company-intelligence/useCompanyIntelligence'
import { deriveCompanyIntelligenceWidgets, type CompanyWidgetMap } from '@/application/company-intelligence/company-intelligence.store'

export const { WorkspaceProvider: CompanyIntelligenceProvider, useWorkspaceContext: useCompanyIntelligenceContext } =
  createWorkspaceProvider<CompanyWidgetMap, { companyId: string }>(
    ({ companyId }) => {
      const { data, isLoading, isError, error, refetch } = useCompanyIntelligence(companyId)
      return { data, isLoading, isError, error, refetch }
    },
    (data, isLoading, isError) =>
      deriveCompanyIntelligenceWidgets(data as any, isLoading, isError),
  )
