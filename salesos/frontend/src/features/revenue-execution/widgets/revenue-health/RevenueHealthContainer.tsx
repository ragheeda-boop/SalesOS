'use client'

import { createWidget } from '@salesos/workspace'
import type { RevenueHealthData } from './types'
import { RevenueHealthView } from './RevenueHealthView'

const sample: RevenueHealthData = {
  totalPortfolio: 85, activeAccounts: 62, atRisk: 8, growthAccounts: 15,
  healthDistribution: [{ label: 'ممتاز', count: 25, value: 40, color: 'bg-green-500' }, { label: 'جيد', count: 22, value: 35, color: 'bg-blue-500' }, { label: 'متوسط', count: 15, value: 25, color: 'bg-amber-500' }, { label: 'ضعيف', count: 8, value: 12, color: 'bg-red-500' }],
}

export const RevenueHealthWidget = createWidget({
  metadata: { id: 'revenueHealth', title: 'صحة الإيرادات', category: 'intelligence', priority: 'high', permissions: ['revenue:health:read'], featureFlag: { enabled: true }, minHeight: '280px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <RevenueHealthView data={data} />,
})
