'use client'

import { useQuery } from '@tanstack/react-query'
import { companyIntelligenceKeys } from './company-intelligence.keys'
import { getTenantId } from '@/lib/hooks/useTenant'
import type { CompanyIntelligenceDTO } from './company-intelligence.dto'

export function useCompanyIntelligence(companyId: string) {
  return useQuery<CompanyIntelligenceDTO>({
    queryKey: companyIntelligenceKeys.detail(companyId),
    queryFn: async () => {
      const res = await fetch(`/api/v1/companies/${companyId}/intelligence`, {
        headers: { 'X-Tenant-Id': getTenantId() },
      })
      if (!res.ok) throw new Error('فشل تحميل ذكاء الشركة')
      return res.json()
    },
    enabled: !!companyId,
    staleTime: 30_000,
  })
}
