'use client'

import { createWidget } from '@salesos/workspace'
import type { ExpansionData } from './types'
import { ExpansionView } from './ExpansionView'

const sample: ExpansionData = {
  opportunities: [
    { companyName: 'أرامكو', product: 'حلول الطاقة المتجددة', value: 2500000, confidence: 0.82, reason: 'ارتفاع الطلب على الطاقة النظيفة' },
    { companyName: 'STC', product: 'الخدمات السحابية', value: 1800000, confidence: 0.75, reason: 'توسع في البنية التحتية' },
  ],
  totalValue: 4300000, avgConfidence: 0.78,
}

export const ExpansionIntelligenceWidget = createWidget({
  metadata: { id: 'expansionIntelligence', title: 'فرص التوسع', category: 'intelligence', priority: 'high', permissions: ['expansion:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <ExpansionView data={data} />,
})
