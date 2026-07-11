'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { CompanyDNAView } from './CompanyDNAView'

export const CompanyDNAWidget = createWidget({
  metadata: {
    id: 'companyDNA',
    title: 'الحمض النووي للشركة',
    category: 'intelligence',
    priority: 'critical',
    permissions: ['company:dna:read'],
    featureFlag: { enabled: true, tier: 'enabled' },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.companyDNA.minHeight,
  },
  useData: () => {
    const ctx = useCompanyIntelligenceContext()
    return ctx.widgets.companyDNA
  },
  render: ({ data }) => <CompanyDNAView dna={data} />,
})
