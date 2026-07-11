'use client'

import { createWidget } from '@salesos/workspace'
import type { ChurnData } from './types'
import { ChurnView } from './ChurnView'

const sample: ChurnData = {
  atRiskAccounts: [
    { companyName: 'شركة البترول', riskScore: 0.85, revenue: 1200000, reason: 'لا نشاط منذ 45 يوم + انخفاض التفاعل', daysSinceActivity: 45 },
    { companyName: 'مؤسسة الرياض', riskScore: 0.72, revenue: 800000, reason: 'تأخر في تجديد العقد', daysSinceActivity: 30 },
    { companyName: 'مجموعة النور', riskScore: 0.65, revenue: 500000, reason: 'انخفاض استخدام المنتج', daysSinceActivity: 60 },
  ],
  totalAtRisk: 3, totalRevenue: 2500000, avgRiskScore: 0.74,
}

export const ChurnIntelligenceWidget = createWidget({
  metadata: { id: 'churnIntelligence', title: 'مخاطر التوقف', category: 'intelligence', priority: 'critical', permissions: ['churn:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <ChurnView data={data} />,
})
