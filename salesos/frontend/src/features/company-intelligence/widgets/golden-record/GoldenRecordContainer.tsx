'use client'

import { createWidget } from '@salesos/workspace'
import { useCompanyIntelligenceContext, COMPANY_INTELLIGENCE_WIDGET_CONFIG } from '../../index'
import { GoldenRecordView } from './GoldenRecordView'

export const GoldenRecordWidget = createWidget({
  metadata: {
    id: 'goldenRecord', title: 'السجل الذهبي', category: 'intelligence', priority: 'low',
    permissions: ['company:golden-record:read'], featureFlag: { enabled: true },
    minHeight: COMPANY_INTELLIGENCE_WIDGET_CONFIG.goldenRecord.minHeight,
  },
  useData: () => {
    const ctx = useCompanyIntelligenceContext()
    return {
      data: { entries: ctx.widgets.goldenRecord.data, dna: ctx.widgets.companyDNA.data },
      status: ctx.widgets.goldenRecord.status,
      lastUpdated: ctx.widgets.goldenRecord.lastUpdated,
      error: ctx.widgets.goldenRecord.error,
      refetch: ctx.widgets.goldenRecord.refetch,
    }
  },
  render: ({ data }) => <GoldenRecordView entries={data.entries ?? []} dna={data.dna} />,
})
